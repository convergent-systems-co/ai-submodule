#!/usr/bin/env python3
"""Dark Factory Policy Engine — Phase 4b Runtime.

Evaluates YAML policy profiles against structured panel emissions to produce
deterministic merge decisions, rule-by-rule audit logs, and run manifests.

Usage:
    python governance/bin/policy-engine.py \
        --emissions-dir governance/emissions/ \
        --profile governance/policy/default.yaml \
        --output manifest.json

Exit codes:
    0 = auto_merge
    1 = block
    2 = human_review_required
    3 = auto_remediate
"""

import argparse
import datetime
import json
import os
import sys
import uuid
from pathlib import Path

import yaml
from jsonschema import validate, ValidationError


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

class EvaluationLog:
    """Collects rule-by-rule evaluation results for audit replay."""

    def __init__(self, stream=None):
        self._entries = []
        self._stream = stream or sys.stderr

    def record(self, rule_id: str, result: str, detail: str):
        entry = {"rule_id": rule_id, "result": result, "detail": detail}
        self._entries.append(entry)
        self._stream.write(f"  [{result.upper():4s}] {rule_id}: {detail}\n")

    @property
    def entries(self):
        return list(self._entries)


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------

def find_schema_dir():
    """Locate the governance/schemas/ directory relative to this script."""
    here = Path(__file__).resolve().parent
    candidates = [
        here.parent / "governance" / "schemas",
        here.parent / "schemas",
        here / "schemas",
        Path("governance") / "schemas",
        Path("schemas"),
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return None


def load_schema(name: str):
    schema_dir = find_schema_dir()
    if schema_dir is None:
        raise FileNotFoundError(f"Cannot locate schemas/ directory for {name}")
    path = schema_dir / name
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Emission loading and validation
# ---------------------------------------------------------------------------

def load_emissions(emissions_dir: str, schema: dict, log: EvaluationLog):
    """Load and validate all JSON emissions from a directory."""
    emissions = []
    emissions_path = Path(emissions_dir)
    if not emissions_path.is_dir():
        log.record("load_emissions", "fail", f"Emissions directory not found: {emissions_dir}")
        return emissions, False

    json_files = sorted(emissions_path.glob("*.json"))
    if not json_files:
        log.record("load_emissions", "fail", f"No JSON files found in {emissions_dir}")
        return emissions, False

    all_valid = True
    for fpath in json_files:
        try:
            with open(fpath) as f:
                emission = json.load(f)
            validate(instance=emission, schema=schema)
            emissions.append(emission)
            log.record(
                f"validate_emission_{emission.get('panel_name', fpath.stem)}",
                "pass",
                f"Valid emission from {fpath.name}"
            )
        except (ValidationError, json.JSONDecodeError) as e:
            all_valid = False
            err = e.message if hasattr(e, "message") else str(e)
            log.record(f"validate_emission_{fpath.stem}", "fail", f"{fpath.name}: {err}")
        except OSError as e:
            all_valid = False
            log.record(f"validate_emission_{fpath.stem}", "fail", f"{fpath.name}: file access error: {e}")

    return emissions, all_valid


def validate_emission_consistency(emission: dict, log: EvaluationLog) -> list:
    """Check semantic consistency within a single emission.

    Returns a list of warning strings.  These are logged but do not reject
    the emission — the policy engine's block/escalation rules will catch
    truly dangerous combinations.
    """
    warnings = []
    panel = emission.get("panel_name", "unknown")
    findings = emission.get("findings", [])
    aggregate_verdict = emission.get("aggregate_verdict", "approve")
    risk_level = emission.get("risk_level", "low")
    policy_flags = emission.get("policy_flags", [])

    # Rule 1: If any finding has verdict "block", aggregate_verdict should not be "approve"
    block_findings = [f for f in findings if f.get("verdict") == "block"]
    if block_findings and aggregate_verdict == "approve":
        msg = (
            f"Inconsistency: {panel} has {len(block_findings)} finding(s) with "
            f"verdict='block' but aggregate_verdict='approve'"
        )
        warnings.append(msg)
        log.record(f"consistency_{panel}", "fail", msg)

    # Rule 2: If critical/high policy flags exist, risk_level should not be "negligible"
    severe_flags = [f for f in policy_flags if f.get("severity") in ("critical", "high")]
    if severe_flags and risk_level == "negligible":
        msg = (
            f"Inconsistency: {panel} has {len(severe_flags)} critical/high policy "
            f"flag(s) but risk_level='negligible'"
        )
        warnings.append(msg)
        log.record(f"consistency_{panel}", "fail", msg)

    if not warnings:
        log.record(f"consistency_{panel}", "pass", "Emission semantically consistent")

    return warnings


# ---------------------------------------------------------------------------
# Policy loading
# ---------------------------------------------------------------------------

def load_profile(profile_path: str):
    with open(profile_path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

RISK_ORDER = ["negligible", "low", "medium", "high", "critical"]


def risk_index(level: str) -> int:
    try:
        return RISK_ORDER.index(level)
    except ValueError:
        return 0


def compute_weighted_confidence(emissions, profile, log):
    """Compute weighted average confidence, redistributing missing panel weights."""
    weights = profile.get("weighting", {}).get("weights", {})
    missing_behavior = profile.get("weighting", {}).get("missing_panel_behavior", "redistribute")

    present_panels = {e["panel_name"] for e in emissions}
    total_weight = 0.0
    weighted_sum = 0.0

    # Separate present and missing weights
    present_weight_sum = 0.0
    missing_weight_sum = 0.0
    for panel_name, weight in weights.items():
        if panel_name in present_panels:
            present_weight_sum += weight
        else:
            missing_weight_sum += weight

    if missing_behavior == "redistribute" and present_weight_sum > 0:
        redistribution_factor = 1.0 / present_weight_sum if present_weight_sum < 1.0 else 1.0 / present_weight_sum
    else:
        redistribution_factor = 1.0

    for emission in emissions:
        panel_name = emission["panel_name"]
        base_weight = weights.get(panel_name, 0.10)
        if missing_behavior == "redistribute" and present_weight_sum > 0:
            effective_weight = base_weight / present_weight_sum
        else:
            effective_weight = base_weight

        confidence = emission["confidence_score"]
        weighted_sum += confidence * effective_weight
        total_weight += effective_weight

        log.record(
            f"weight_{panel_name}",
            "pass",
            f"confidence={confidence:.3f} * weight={effective_weight:.3f} "
            f"(base={base_weight:.3f}, redistribution={'yes' if missing_behavior == 'redistribute' else 'no'})"
        )

    aggregate = weighted_sum / total_weight if total_weight > 0 else 0.0
    log.record(
        "aggregate_confidence",
        "pass",
        f"weighted_sum={weighted_sum:.4f} / total_weight={total_weight:.4f} = {aggregate:.4f}"
    )
    return round(aggregate, 4)


def compute_aggregate_risk(emissions, profile, log):
    """Compute aggregate risk using the profile's risk aggregation rules."""
    risk_levels = {e["panel_name"]: e["risk_level"] for e in emissions}
    rules = profile.get("risk_aggregation", {}).get("rules", [])

    max_risk = "negligible"
    for emission in emissions:
        if risk_index(emission["risk_level"]) > risk_index(max_risk):
            max_risk = emission["risk_level"]

    # Evaluate profile-specific rules
    risk_counts = {}
    for r in RISK_ORDER:
        risk_counts[r] = sum(1 for e in emissions if e["risk_level"] == r)

    result_risk = "low"  # default
    matched_rule = None

    for rule in rules:
        condition = rule.get("condition", "")
        rule_result = rule.get("result", "low")
        desc = rule.get("description", condition)

        # Evaluate common condition patterns
        if _evaluate_risk_condition(condition, risk_levels, risk_counts, emissions):
            result_risk = rule_result
            matched_rule = desc
            log.record("risk_aggregation", "pass", f"Rule matched: {desc} → {rule_result}")
            break

    if matched_rule is None:
        result_risk = max_risk
        log.record("risk_aggregation", "pass", f"No rule matched, using highest severity: {max_risk}")

    return result_risk


def _evaluate_risk_condition(condition: str, risk_levels: dict, risk_counts: dict, emissions: list) -> bool:
    """Evaluate a risk aggregation condition string against emission data."""
    cond = condition.strip()

    # Pattern: any_panel_risk == "critical"
    if cond.startswith("any_panel_risk =="):
        level = cond.split('"')[1]
        return any(e["risk_level"] == level for e in emissions)

    # Pattern: any_panel_risk in ["critical", "high"]
    if cond.startswith("any_panel_risk in"):
        levels = _extract_list(cond)
        return any(e["risk_level"] in levels for e in emissions)

    # Pattern: count(panel_risk == "high") >= 2
    if cond.startswith("count(panel_risk =="):
        level = cond.split('"')[1]
        op, threshold = _extract_comparison(cond)
        count = risk_counts.get(level, 0)
        return _compare(count, op, threshold)

    # Pattern: count(panel_risk == "medium") == 1
    if "count(" in cond and "panel_risk" in cond:
        level = cond.split('"')[1]
        op, threshold = _extract_comparison(cond)
        count = risk_counts.get(level, 0)
        return _compare(count, op, threshold)

    # Pattern: all_panels_risk in ["low", "negligible"]
    if cond.startswith("all_panels_risk in"):
        levels = _extract_list(cond)
        return all(e["risk_level"] in levels for e in emissions)

    # Pattern: panel_risk("panel-name") == "level"
    if cond.startswith("panel_risk("):
        parts = cond.split('"')
        if len(parts) >= 4:
            panel_name = parts[1]
            level = parts[3]
            panel_risk = risk_levels.get(panel_name)
            if " or " in cond:
                # Handle: panel_risk("a") == "critical" or panel_risk("b") == "critical"
                or_parts = cond.split(" or ")
                for part in or_parts:
                    p = part.strip().split('"')
                    if len(p) >= 4:
                        pn = p[1]
                        lv = p[3]
                        if risk_levels.get(pn) == lv:
                            return True
                return False
            return panel_risk == level
        return False

    return False


def collect_policy_flags(emissions):
    """Collect all policy flags from all emissions."""
    flags = []
    for emission in emissions:
        flags.extend(emission.get("policy_flags", []))
    return flags


def check_required_panels(emissions, profile, log):
    """Check that all required panels have emissions."""
    required = profile.get("required_panels", [])
    present = {e["panel_name"] for e in emissions}
    missing = [p for p in required if p not in present]

    for panel in required:
        if panel in present:
            log.record(f"required_panel_{panel}", "pass", f"Panel '{panel}' present")
        else:
            log.record(f"required_panel_{panel}", "fail", f"Required panel '{panel}' missing")

    return missing


def evaluate_block_conditions(aggregate_confidence, aggregate_risk, policy_flags, missing_required, ci_passed, profile, log):
    """Evaluate block conditions. Returns (blocked: bool, reason: str)."""
    block_rules = profile.get("block", {}).get("conditions", [])

    # Universal block: missing required panel
    if missing_required:
        reason = f"Required panel(s) missing: {', '.join(missing_required)}"
        log.record("block_required_panel_missing", "fail", reason)
        return True, reason

    # Universal block: CI checks failed
    if not ci_passed:
        reason = "CI checks failed"
        log.record("block_ci_checks", "fail", reason)
        return True, reason

    # Profile-specific block conditions
    for rule in block_rules:
        condition = rule.get("condition", "")
        desc = rule.get("description", condition)

        if _evaluate_block_condition(condition, aggregate_confidence, aggregate_risk, policy_flags):
            log.record(f"block_{_slugify(desc)}", "fail", desc)
            return True, desc
        else:
            log.record(f"block_{_slugify(desc)}", "pass", f"Not triggered: {desc}")

    # Check for critical/high policy flags (universal across all profiles)
    blocking_flags = [f for f in policy_flags if f.get("severity") in ("critical", "high")]
    if blocking_flags:
        flag_names = [f["flag"] for f in blocking_flags]
        reason = f"Critical/high severity policy flags: {', '.join(flag_names)}"
        log.record("block_policy_flags", "fail", reason)
        return True, reason

    log.record("block_evaluation", "pass", "No block conditions triggered")
    return False, ""


def _evaluate_block_condition(condition: str, confidence: float, risk: str, flags: list) -> bool:
    """Evaluate a single block condition string."""
    cond = condition.strip()

    # Handle compound 'and' conditions
    if " and " in cond:
        return _evaluate_compound_block_condition(cond, confidence, risk, flags)

    # Pattern: aggregate_confidence < 0.40
    if cond.startswith("aggregate_confidence <"):
        threshold = float(cond.split("<")[1].strip())
        return confidence < threshold

    # Pattern: any_policy_flag == "pii_exposure"
    if cond.startswith("any_policy_flag =="):
        flag_name = cond.split('"')[1]
        return any(f["flag"] == flag_name for f in flags)

    # Pattern: any_policy_flag starts_with "pii_"
    if "starts_with" in cond and "policy_flag" in cond:
        prefix = cond.split('"')[1]
        return any(f["flag"].startswith(prefix) for f in flags)

    # Pattern: panel_missing("security-review")
    if cond.startswith("panel_missing("):
        # Handled by check_required_panels, skip here
        return False

    return False


def _evaluate_compound_block_condition(condition: str, confidence: float, risk: str, flags: list) -> bool:
    """Evaluate a compound 'and' block condition by splitting and evaluating each sub-condition."""
    parts = condition.split(" and ")
    for part in parts:
        part = part.strip()
        negated = part.startswith("not ")
        if negated:
            part = part[4:].strip()

        result = _evaluate_block_sub_condition(part, confidence, risk, flags)
        if result is None:
            # Context-dependent sub-condition — cannot fully evaluate
            return False
        if negated:
            result = not result
        if not result:
            return False
    return True


def _evaluate_block_sub_condition(sub_cond: str, confidence: float, risk: str, flags: list):
    """Evaluate a single sub-condition within a compound block condition.

    Returns True/False if evaluable, or None if context-dependent.
    """
    cond = sub_cond.strip()

    # Pattern: aggregate_confidence < 0.40
    if cond.startswith("aggregate_confidence"):
        if "<" in cond and ">=" not in cond:
            threshold = float(cond.split("<")[1].strip())
            return confidence < threshold
        if ">=" in cond:
            threshold = float(cond.split(">=")[1].strip())
            return confidence >= threshold

    # Pattern: any_policy_flag_severity == "critical"
    if cond.startswith("any_policy_flag_severity =="):
        level = cond.split('"')[1]
        return any(f.get("severity") == level for f in flags)

    # Pattern: any_policy_flag == "pii_exposure"
    if cond.startswith("any_policy_flag =="):
        flag_name = cond.split('"')[1]
        return any(f["flag"] == flag_name for f in flags)

    # Pattern: any_policy_flag starts_with "pii_"
    if "starts_with" in cond and "policy_flag" in cond:
        prefix = cond.split('"')[1]
        return any(f["flag"].startswith(prefix) for f in flags)

    # Pattern: auto_remediable (bare boolean — True when all flags are auto-remediable)
    if cond == "auto_remediable":
        return all(f.get("auto_remediable", False) for f in flags) if flags else True

    # Pattern: panel_missing("...")
    if cond.startswith("panel_missing("):
        return None  # Context-dependent

    # Context-dependent patterns
    if any(ctx in cond for ctx in [
        "data_files_changed", "auth_files_changed", "deployment_files_changed",
        "infrastructure_files_changed", "panel_executed", "no_rollback_plan",
        "schema_validation_failed", "schema_path_matches",
        "init_script_failed", "error_cause",
        "workflow_name", "error_source",
    ]):
        return None

    return None  # Unknown — treat as context-dependent


def evaluate_escalation_rules(aggregate_confidence, aggregate_risk, policy_flags, emissions, profile, log):
    """Evaluate escalation rules. Returns (escalate: bool, reason: str)."""
    rules = profile.get("escalation", {}).get("rules", [])

    for rule in rules:
        name = rule.get("name", "unknown")
        condition = rule.get("condition", "")
        desc = rule.get("description", condition)
        action = rule.get("action", "human_review_required")

        if _evaluate_escalation_condition(condition, aggregate_confidence, aggregate_risk, policy_flags, emissions):
            log.record(f"escalation_{name}", "fail", f"{desc} → {action}")
            if action == "block":
                return "block", desc
            return "human_review_required", desc
        else:
            log.record(f"escalation_{name}", "pass", f"Not triggered: {desc}")

    # Check if any panel requires human review
    for emission in emissions:
        if emission.get("requires_human_review", False):
            reason = f"Panel '{emission['panel_name']}' requires human review"
            log.record("escalation_panel_human_review", "fail", reason)
            return "human_review_required", reason

    log.record("escalation_evaluation", "pass", "No escalation rules triggered")
    return None, ""


def _evaluate_escalation_condition(condition: str, confidence: float, risk: str, flags: list, emissions: list) -> bool:
    """Evaluate a single escalation condition string."""
    cond = condition.strip()

    # Handle compound 'and' conditions
    if " and " in cond:
        return _evaluate_compound_escalation_condition(cond, confidence, risk, flags, emissions)

    # Pattern: aggregate_confidence < 0.70
    if cond.startswith("aggregate_confidence <"):
        threshold = float(cond.split("<")[1].strip())
        return confidence < threshold

    # Pattern: risk_level == "critical"
    if cond.startswith("risk_level =="):
        level = cond.split('"')[1]
        return risk == level

    # Pattern: risk_level in ["critical", "high", "medium"]
    if cond.startswith("risk_level in"):
        levels = _extract_list(cond)
        return risk in levels

    # Pattern: any_policy_flag_severity in ["critical", "high"]
    if "policy_flag_severity" in cond or ("policy_flag" in cond and "severity" in cond):
        levels = _extract_list(cond)
        return any(f.get("severity") in levels for f in flags)

    # Pattern: any_policy_flag starts_with "pii_"
    if "starts_with" in cond and "policy_flag" in cond:
        prefix = cond.split('"')[1]
        return any(f["flag"].startswith(prefix) for f in flags)

    # Pattern: panel_disagreement_detected == true
    if "panel_disagreement" in cond:
        verdicts = {e.get("aggregate_verdict", "approve") for e in emissions}
        return len(verdicts) > 1

    # Context-dependent conditions (files_changed_in, services_affected_count)
    # These require runtime context not available from emissions alone — skip
    if "files_changed_in" in cond or "services_affected" in cond:
        return False

    return False


def _evaluate_compound_escalation_condition(condition: str, confidence: float, risk: str, flags: list, emissions: list) -> bool:
    """Evaluate a compound 'and' escalation condition by splitting and evaluating each sub-condition."""
    parts = condition.split(" and ")
    for part in parts:
        part = part.strip()
        negated = part.startswith("not ")
        if negated:
            part = part[4:].strip()

        result = _evaluate_escalation_sub_condition(part, confidence, risk, flags, emissions)
        if result is None:
            return False
        if negated:
            result = not result
        if not result:
            return False
    return True


def _evaluate_escalation_sub_condition(sub_cond: str, confidence: float, risk: str, flags: list, emissions: list):
    """Evaluate a single sub-condition within a compound escalation condition.

    Returns True/False if evaluable, or None if context-dependent.
    """
    cond = sub_cond.strip()

    # Pattern: aggregate_confidence < 0.70
    if cond.startswith("aggregate_confidence"):
        if "<" in cond and ">=" not in cond:
            threshold = float(cond.split("<")[1].strip())
            return confidence < threshold
        if ">=" in cond:
            threshold = float(cond.split(">=")[1].strip())
            return confidence >= threshold

    # Pattern: risk_level == "critical"
    if cond.startswith("risk_level =="):
        level = cond.split('"')[1]
        return risk == level

    # Pattern: risk_level in ["critical", "high"]
    if cond.startswith("risk_level in"):
        levels = _extract_list(cond)
        return risk in levels

    # Pattern: any_policy_flag_severity in ["critical", "high"]
    if "policy_flag_severity" in cond or ("policy_flag" in cond and "severity" in cond):
        levels = _extract_list(cond)
        return any(f.get("severity") in levels for f in flags)

    # Pattern: any_policy_flag starts_with "pii_"
    if "starts_with" in cond and "policy_flag" in cond:
        prefix = cond.split('"')[1]
        return any(f["flag"].startswith(prefix) for f in flags)

    # Pattern: panel_disagreement_detected == true
    if "panel_disagreement" in cond:
        verdicts = {e.get("aggregate_verdict", "approve") for e in emissions}
        return len(verdicts) > 1

    # Context-dependent patterns
    if any(ctx in cond for ctx in [
        "files_changed_in", "services_affected",
        "dismissed_finding_severity", "dismissed_finding_panel",
    ]):
        return None

    return None  # Unknown — treat as context-dependent


def evaluate_auto_merge(aggregate_confidence, aggregate_risk, policy_flags, emissions, ci_passed, profile, log):
    """Evaluate auto-merge conditions. Returns True if all conditions pass."""
    auto_merge = profile.get("auto_merge", {})
    if not auto_merge.get("enabled", False):
        log.record("auto_merge_enabled", "skip", "Auto-merge disabled in profile")
        return False

    conditions = auto_merge.get("conditions", [])
    all_pass = True

    for cond_str in conditions:
        passed = _evaluate_auto_merge_condition(cond_str, aggregate_confidence, aggregate_risk, policy_flags, emissions, ci_passed)
        status = "pass" if passed else "fail"
        log.record(f"auto_merge_{_slugify(cond_str)}", status, cond_str)
        if not passed:
            all_pass = False

    return all_pass


def _evaluate_auto_merge_condition(condition: str, confidence: float, risk: str, flags: list, emissions: list, ci_passed: bool) -> bool:
    """Evaluate a single auto-merge condition string."""
    cond = condition.strip()

    # Pattern: aggregate_confidence >= 0.85
    if cond.startswith("aggregate_confidence >="):
        threshold = float(cond.split(">=")[1].strip())
        return confidence >= threshold

    # Pattern: risk_level in ["low", "negligible"]
    if cond.startswith("risk_level in"):
        levels = _extract_list(cond)
        return risk in levels

    # Pattern: no_policy_flags_severity in ["critical", "high"]
    if cond.startswith("no_policy_flags_severity in"):
        levels = _extract_list(cond)
        return not any(f.get("severity") in levels for f in flags)

    # Pattern: all_panel_verdicts in ["approve"]
    if cond.startswith("all_panel_verdicts"):
        allowed = _extract_list(cond)
        return all(e.get("aggregate_verdict", "approve") in allowed for e in emissions)

    # Pattern: requires_human_review == false
    if "requires_human_review" in cond and "false" in cond:
        return not any(e.get("requires_human_review", False) for e in emissions)

    # Pattern: ci_checks_passed == true
    if "ci_checks_passed" in cond:
        return ci_passed

    # Context-dependent conditions — fail-closed: do not auto-merge/remediate
    # without verifiable safety checks
    if "files_changed_in" in cond or "services_affected" in cond:
        return False

    return False


def evaluate_auto_remediate(aggregate_confidence, aggregate_risk, policy_flags, emissions, profile, log):
    """Evaluate auto-remediate conditions. Returns True if all conditions pass."""
    auto_rem = profile.get("auto_remediate", {})
    if not auto_rem.get("enabled", False):
        log.record("auto_remediate_enabled", "skip", "Auto-remediate disabled in profile")
        return False

    conditions = auto_rem.get("conditions", [])
    all_pass = True

    for cond_str in conditions:
        passed = _evaluate_auto_remediate_condition(cond_str, aggregate_confidence, aggregate_risk, policy_flags, emissions)
        status = "pass" if passed else "fail"
        log.record(f"auto_remediate_{_slugify(cond_str)}", status, cond_str)
        if not passed:
            all_pass = False

    return all_pass


def _evaluate_auto_remediate_condition(condition: str, confidence: float, risk: str, flags: list, emissions: list) -> bool:
    """Evaluate a single auto-remediate condition string."""
    cond = condition.strip()

    # Pattern: risk_level == "low"
    if cond.startswith("risk_level =="):
        level = cond.split('"')[1]
        return risk == level

    # Pattern: risk_level in ["low", "medium"]
    if cond.startswith("risk_level in"):
        levels = _extract_list(cond)
        return risk in levels

    # Pattern: all_policy_flags.auto_remediable == true
    if "auto_remediable" in cond and "true" in cond:
        return all(f.get("auto_remediable", False) for f in flags) if flags else True

    # Pattern: aggregate_confidence >= 0.60
    if cond.startswith("aggregate_confidence >="):
        threshold = float(cond.split(">=")[1].strip())
        return confidence >= threshold

    # Pattern: no_policy_flag starts_with "pii_"
    if "no_policy_flag" in cond and "starts_with" in cond:
        prefix = cond.split('"')[1]
        return not any(f["flag"].startswith(prefix) for f in flags)

    # Context-dependent — fail-closed
    if "files_changed_in" in cond:
        return False

    return False


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _extract_list(condition: str) -> list:
    """Extract a list of quoted strings from a condition like: foo in ["a", "b"]."""
    import re
    return re.findall(r'"([^"]+)"', condition)


def _extract_comparison(condition: str):
    """Extract comparison operator and integer threshold from end of condition."""
    import re
    match = re.search(r'\)\s*(>=|<=|==|>|<)\s*(\d+)', condition)
    if match:
        return match.group(1), int(match.group(2))
    return ">=", 0


def _compare(value, op, threshold):
    if op == ">=":
        return value >= threshold
    if op == "<=":
        return value <= threshold
    if op == "==":
        return value == threshold
    if op == ">":
        return value > threshold
    if op == "<":
        return value < threshold
    return False


def _slugify(text: str) -> str:
    """Create a short slug from text for log rule IDs."""
    import re
    slug = re.sub(r'[^a-z0-9]+', '_', text.lower().strip())
    return slug[:50].strip('_')


# ---------------------------------------------------------------------------
# Manifest generation
# ---------------------------------------------------------------------------

def generate_manifest(
    emissions, profile, aggregate_confidence, aggregate_risk,
    decision_action, decision_rationale, evaluation_log,
    commit_sha=None, pr_number=None, repo=None
):
    """Generate a run manifest conforming to run-manifest.schema.json."""
    now = datetime.datetime.now(datetime.timezone.utc)
    short_sha = (commit_sha or "0000000")[:7]
    manifest_id = now.strftime(f"%Y%m%d-%H%M%S-{short_sha}")

    panels_executed = []
    for emission in emissions:
        panels_executed.append({
            "panel_name": emission["panel_name"],
            "verdict": emission.get("aggregate_verdict", "approve"),
            "confidence_score": emission["confidence_score"],
            "artifact_path": f"governance/emissions/{emission['panel_name']}.json"
        })

    manifest = {
        "manifest_version": "1.0.0",
        "manifest_id": manifest_id,
        "timestamp": now.isoformat(),
        "persona_set_commit": commit_sha or ("0" * 40),
        "panel_graph_version": "1.0.0",
        "policy_profile_used": profile.get("profile_name", "unknown"),
        "model_version": "claude-opus-4-6",
        "aggregate_confidence": aggregate_confidence,
        "risk_level": aggregate_risk,
        "human_intervention": {
            "required": decision_action in ("human_review_required", "block"),
            "occurred": False
        },
        "decision": {
            "action": decision_action,
            "rationale": decision_rationale,
            "policy_rules_evaluated": evaluation_log.entries
        },
        "panels_executed": panels_executed
    }

    if repo or pr_number or commit_sha:
        manifest["repository"] = {}
        if repo:
            parts = repo.split("/", 1)
            manifest["repository"]["owner"] = parts[0] if len(parts) > 1 else ""
            manifest["repository"]["name"] = parts[-1]
        if commit_sha:
            manifest["repository"]["commit_sha"] = commit_sha
        if pr_number:
            manifest["repository"]["pr_number"] = pr_number

    return manifest


# ---------------------------------------------------------------------------
# Main evaluation pipeline
# ---------------------------------------------------------------------------

def evaluate(emissions_dir, profile_path, ci_passed=True, commit_sha=None, pr_number=None, repo=None, log_stream=None):
    """Run the full policy evaluation pipeline. Returns (manifest, exit_code)."""
    log = EvaluationLog(stream=log_stream)

    log._stream.write(f"\n{'='*60}\n")
    log._stream.write(f"  Dark Factory Policy Engine v1.0.0\n")
    log._stream.write(f"  Profile: {profile_path}\n")
    log._stream.write(f"  Emissions: {emissions_dir}\n")
    log._stream.write(f"  Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n")
    log._stream.write(f"{'='*60}\n\n")

    # Step 1: Load schemas
    log._stream.write("--- Step 1: Load and validate emissions ---\n")
    try:
        panel_schema = load_schema("panel-output.schema.json")
    except FileNotFoundError as e:
        log.record("load_schema", "fail", str(e))
        manifest = generate_manifest([], {}, 0.0, "critical", "block", str(e), log, commit_sha, pr_number, repo)
        return manifest, 1

    # Step 2: Load emissions
    emissions, all_valid = load_emissions(emissions_dir, panel_schema, log)

    if not all_valid:
        reason = "One or more emissions failed schema validation"
        log.record("emissions_validation", "fail", reason)
        profile = load_profile(profile_path) if os.path.exists(profile_path) else {}
        manifest = generate_manifest(emissions, profile, 0.0, "critical", "block", reason, log, commit_sha, pr_number, repo)
        return manifest, 1

    if not emissions:
        reason = "No valid emissions found"
        log.record("emissions_count", "fail", reason)
        profile = load_profile(profile_path) if os.path.exists(profile_path) else {}
        manifest = generate_manifest(emissions, profile, 0.0, "critical", "block", reason, log, commit_sha, pr_number, repo)
        return manifest, 1

    log.record("emissions_validation", "pass", f"{len(emissions)} valid emission(s) loaded")

    # Step 2b: Semantic consistency checks
    log._stream.write("\n--- Step 1b: Semantic consistency checks ---\n")
    all_consistency_warnings = []
    for emission in emissions:
        warnings = validate_emission_consistency(emission, log)
        all_consistency_warnings.extend(warnings)
    if all_consistency_warnings:
        log.record(
            "consistency_summary", "fail",
            f"{len(all_consistency_warnings)} consistency warning(s) detected"
        )

    # Step 3: Load profile
    log._stream.write("\n--- Step 2: Load policy profile ---\n")
    try:
        profile = load_profile(profile_path)
        log.record("load_profile", "pass", f"Profile '{profile.get('profile_name')}' v{profile.get('profile_version')}")
    except Exception as e:
        reason = f"Failed to load profile: {e}"
        log.record("load_profile", "fail", reason)
        manifest = generate_manifest(emissions, {}, 0.0, "critical", "block", reason, log, commit_sha, pr_number, repo)
        return manifest, 1

    # Step 4: Check required panels
    log._stream.write("\n--- Step 3: Check required panels ---\n")
    missing_required = check_required_panels(emissions, profile, log)

    missing_behavior = profile.get("weighting", {}).get("missing_panel_behavior", "redistribute")
    if missing_required and missing_behavior == "block":
        reason = f"Required panel(s) missing and missing_panel_behavior=block: {', '.join(missing_required)}"
        log.record("required_panels_block", "fail", reason)
        manifest = generate_manifest(emissions, profile, 0.0, "critical", "block", reason, log, commit_sha, pr_number, repo)
        return manifest, 1

    # Step 5: Compute aggregate confidence
    log._stream.write("\n--- Step 4: Compute aggregate confidence ---\n")
    aggregate_confidence = compute_weighted_confidence(emissions, profile, log)

    # Step 6: Compute aggregate risk
    log._stream.write("\n--- Step 5: Compute aggregate risk ---\n")
    aggregate_risk = compute_aggregate_risk(emissions, profile, log)

    # Step 6b: Phase 4b transition — downgrade missing-panel block when all
    # present panels approve with sufficient confidence.  This keeps the
    # decision inside the engine rather than in the CI workflow.
    if missing_required and missing_behavior != "block":
        all_approve = all(
            e.get("aggregate_verdict") == "approve" for e in emissions
        )
        phase_4b_threshold = 0.70
        if all_approve and aggregate_confidence >= phase_4b_threshold:
            log.record(
                "phase_4b_transition", "pass",
                f"Missing panels [{', '.join(missing_required)}] downgraded — "
                f"all present panels approve, confidence={aggregate_confidence:.4f} >= {phase_4b_threshold}"
            )
            missing_required = []  # allow evaluation to continue
        else:
            reasons = []
            if not all_approve:
                reasons.append("not all present panels approve")
            if aggregate_confidence < phase_4b_threshold:
                reasons.append(f"confidence {aggregate_confidence:.4f} < {phase_4b_threshold}")
            log.record(
                "phase_4b_transition", "skip",
                f"Phase 4b transition not applicable: {'; '.join(reasons)}"
            )

    # Step 7: Collect policy flags
    log._stream.write("\n--- Step 6: Collect policy flags ---\n")
    policy_flags = collect_policy_flags(emissions)
    if policy_flags:
        for flag in policy_flags:
            log.record(f"flag_{flag['flag']}", "pass", f"severity={flag['severity']}: {flag['description']}")
    else:
        log.record("policy_flags", "pass", "No policy flags raised")

    # Step 8: Evaluate block conditions
    log._stream.write("\n--- Step 7: Evaluate block conditions ---\n")
    blocked, block_reason = evaluate_block_conditions(
        aggregate_confidence, aggregate_risk, policy_flags, missing_required, ci_passed, profile, log
    )
    if blocked:
        manifest = generate_manifest(
            emissions, profile, aggregate_confidence, aggregate_risk,
            "block", block_reason, log, commit_sha, pr_number, repo
        )
        return manifest, 1

    # Step 9: Evaluate escalation rules
    log._stream.write("\n--- Step 8: Evaluate escalation rules ---\n")
    escalation_result, escalation_reason = evaluate_escalation_rules(
        aggregate_confidence, aggregate_risk, policy_flags, emissions, profile, log
    )
    if escalation_result == "block":
        manifest = generate_manifest(
            emissions, profile, aggregate_confidence, aggregate_risk,
            "block", escalation_reason, log, commit_sha, pr_number, repo
        )
        return manifest, 1
    if escalation_result == "human_review_required":
        manifest = generate_manifest(
            emissions, profile, aggregate_confidence, aggregate_risk,
            "human_review_required", escalation_reason, log, commit_sha, pr_number, repo
        )
        return manifest, 2

    # Step 10: Evaluate auto-merge conditions
    log._stream.write("\n--- Step 9: Evaluate auto-merge conditions ---\n")
    can_auto_merge = evaluate_auto_merge(
        aggregate_confidence, aggregate_risk, policy_flags, emissions, ci_passed, profile, log
    )
    if can_auto_merge:
        reason = f"All auto-merge conditions met. Confidence={aggregate_confidence:.4f}, risk={aggregate_risk}"
        manifest = generate_manifest(
            emissions, profile, aggregate_confidence, aggregate_risk,
            "auto_merge", reason, log, commit_sha, pr_number, repo
        )
        return manifest, 0

    # Step 11: Evaluate auto-remediate conditions
    log._stream.write("\n--- Step 10: Evaluate auto-remediate conditions ---\n")
    can_auto_remediate = evaluate_auto_remediate(
        aggregate_confidence, aggregate_risk, policy_flags, emissions, profile, log
    )
    if can_auto_remediate:
        reason = f"Auto-remediate conditions met. Confidence={aggregate_confidence:.4f}, risk={aggregate_risk}"
        manifest = generate_manifest(
            emissions, profile, aggregate_confidence, aggregate_risk,
            "auto_remediate", reason, log, commit_sha, pr_number, repo
        )
        return manifest, 3

    # Step 12: Default to human_review_required
    log._stream.write("\n--- Step 11: Default decision ---\n")
    reason = f"No auto-merge or auto-remediate path available. Confidence={aggregate_confidence:.4f}, risk={aggregate_risk}"
    log.record("default_decision", "pass", reason)
    manifest = generate_manifest(
        emissions, profile, aggregate_confidence, aggregate_risk,
        "human_review_required", reason, log, commit_sha, pr_number, repo
    )
    return manifest, 2


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Dark Factory Policy Engine — evaluate panel emissions against a policy profile."
    )
    parser.add_argument("--emissions-dir", required=True, help="Directory containing panel emission JSON files")
    parser.add_argument("--profile", required=True, help="Path to YAML policy profile")
    parser.add_argument("--output", required=True, help="Path to write the run manifest JSON")
    parser.add_argument("--log-file", help="Path to write evaluation log (defaults to stderr)")
    parser.add_argument("--ci-checks-passed", default="true", choices=["true", "false"], help="CI check status")
    parser.add_argument("--commit-sha", help="Git commit SHA for manifest")
    parser.add_argument("--pr-number", type=int, help="PR number for manifest context")
    parser.add_argument("--repo", help="Repository name (owner/repo) for manifest context")

    args = parser.parse_args()

    log_stream = sys.stderr
    if args.log_file:
        log_stream = open(args.log_file, "w")

    try:
        manifest, exit_code = evaluate(
            emissions_dir=args.emissions_dir,
            profile_path=args.profile,
            ci_passed=(args.ci_checks_passed == "true"),
            commit_sha=args.commit_sha,
            pr_number=args.pr_number,
            repo=args.repo,
            log_stream=log_stream,
        )

        # Validate manifest against schema before writing
        try:
            manifest_schema = load_schema("run-manifest.schema.json")
            validate(instance=manifest, schema=manifest_schema)
        except (ValidationError, FileNotFoundError) as e:
            log_stream.write(f"\nWARNING: Manifest failed schema validation: {e}\n")

        with open(args.output, "w") as f:
            json.dump(manifest, f, indent=2)

        decision = manifest["decision"]["action"]
        confidence = manifest["aggregate_confidence"]
        risk = manifest["risk_level"]
        log_stream.write(f"\n{'='*60}\n")
        log_stream.write(f"  DECISION: {decision}\n")
        log_stream.write(f"  Confidence: {confidence:.4f}\n")
        log_stream.write(f"  Risk: {risk}\n")
        log_stream.write(f"  Manifest: {args.output}\n")
        log_stream.write(f"{'='*60}\n")

        sys.exit(exit_code)

    finally:
        if args.log_file and log_stream != sys.stderr:
            log_stream.close()


if __name__ == "__main__":
    main()
