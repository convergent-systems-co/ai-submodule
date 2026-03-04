"""Scenario tests — realistic end-to-end policy engine scenarios.

Each test models a real-world situation (e.g. PII leak in a fintech repo,
production outage, routine docs change) and verifies the engine produces
the correct decision, risk level, and exit code.
"""

import io
import json
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

from conftest import (
    policy_engine,
    make_emission,
    make_profile,
    all_required_emissions,
    DEFAULT_REQUIRED_PANELS,
    REPO_ROOT,
)


def _write_emissions(tmpdir, emissions):
    for emission in emissions:
        path = os.path.join(str(tmpdir), f"{emission['panel_name']}.json")
        with open(path, "w") as f:
            json.dump(emission, f)


def _profile_path(name):
    return str(REPO_ROOT / "governance" / "policy" / f"{name}.yaml")


# ===========================================================================
# Scenario 1: Routine documentation change — sails through auto-merge
# ===========================================================================


class TestScenarioRoutineDocsChange:
    """A docs-only PR: all panels approve, high confidence, negligible risk."""

    def test_auto_merges(self, tmp_path):
        emissions = all_required_emissions(confidence=0.95, risk_level="negligible")
        _write_emissions(tmp_path, emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 0
        assert manifest["decision"]["action"] == "auto_merge"
        assert manifest["aggregate_confidence"] >= 0.85
        # Risk aggregation rule: all low/negligible → "low" (not negligible)
        assert manifest["risk_level"] in ("low", "negligible")


# ===========================================================================
# Scenario 2: PII exposure detected — block regardless of confidence
# ===========================================================================


class TestScenarioPiiExposure:
    """Security panel finds PII exposure. Must block on default profile and
    escalate to block on fin_pii_high profile."""

    def test_default_profile_blocks_on_critical_flag(self, tmp_path):
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        emissions[1]["policy_flags"] = [
            {"flag": "pii_exposure", "severity": "critical",
             "description": "PII in logs", "auto_remediable": False}
        ]
        _write_emissions(tmp_path, emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # Critical policy flag → block via evaluate_block_conditions
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"

    def test_fin_pii_high_blocks_pii_flag(self, tmp_path):
        panels = [
            "code-review", "security-review", "data-design-review",
            "testing-review", "threat-modeling", "cost-analysis",
            "documentation-review",
        ]
        emissions = all_required_emissions(confidence=0.95, risk_level="low", panels=panels)
        emissions[1]["policy_flags"] = [
            {"flag": "pii_exposure", "severity": "critical",
             "description": "PII in response body", "auto_remediable": False}
        ]
        _write_emissions(tmp_path, emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("fin_pii_high"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"


# ===========================================================================
# Scenario 3: CI failure — universal block across all profiles
# ===========================================================================


class TestScenarioCiFailure:
    """CI checks fail. Must block on every profile."""

    @pytest.mark.parametrize("profile", [
        "default", "fin_pii_high", "infrastructure_critical", "reduced_touchpoint",
    ])
    def test_ci_failure_blocks(self, tmp_path, profile):
        if profile == "fin_pii_high":
            panels = [
                "code-review", "security-review", "data-design-review",
                "testing-review", "threat-modeling", "cost-analysis",
                "documentation-review",
            ]
        elif profile == "infrastructure_critical":
            panels = [
                "code-review", "security-review", "architecture-review",
                "threat-modeling", "cost-analysis", "documentation-review",
            ]
        else:
            panels = DEFAULT_REQUIRED_PANELS

        emissions = all_required_emissions(confidence=0.95, risk_level="low", panels=panels)
        _write_emissions(tmp_path, emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path(profile),
            ci_passed=False, log_stream=io.StringIO(),
        )
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"


# ===========================================================================
# Scenario 4: Panel disagreement — conflicting verdicts trigger review
# ===========================================================================


class TestScenarioPanelDisagreement:
    """Half the panels approve, half request changes."""

    def test_disagreement_triggers_human_review(self, tmp_path):
        emissions = all_required_emissions(confidence=0.88, risk_level="low")
        emissions[0]["aggregate_verdict"] = "request_changes"
        emissions[1]["aggregate_verdict"] = "request_changes"
        emissions[2]["aggregate_verdict"] = "approve"
        _write_emissions(tmp_path, emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 2
        assert manifest["decision"]["action"] == "human_review_required"


# ===========================================================================
# Scenario 5: Reduced touchpoint — medium risk auto-merges
# ===========================================================================


class TestScenarioReducedTouchpointMediumRisk:
    """Medium aggregate risk with high confidence. Default would escalate,
    but reduced_touchpoint should auto-merge."""

    def test_medium_risk_auto_merges_on_reduced_touchpoint(self, tmp_path):
        emissions = all_required_emissions(confidence=0.85, risk_level="low")
        emissions[0]["risk_level"] = "high"  # triggers aggregate=medium
        _write_emissions(tmp_path, emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("reduced_touchpoint"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 0
        assert manifest["decision"]["action"] == "auto_merge"

    def test_same_scenario_escalates_on_default(self, tmp_path):
        emissions = all_required_emissions(confidence=0.85, risk_level="low")
        emissions[0]["risk_level"] = "high"
        _write_emissions(tmp_path, emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # Default: medium risk not in auto-merge allowed ["low", "negligible"]
        assert exit_code != 0
        assert manifest["decision"]["action"] != "auto_merge"


# ===========================================================================
# Scenario 6: Escalation blocks merge (policy_violation escalation)
# ===========================================================================


class TestScenarioEscalationBlock:
    """High-severity policy flag triggers escalation with action=block on default."""

    def test_escalation_blocks(self, tmp_path):
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        emissions[0]["policy_flags"] = [
            {"flag": "breaking_change", "severity": "high",
             "description": "Breaking API change", "auto_remediable": False}
        ]
        _write_emissions(tmp_path, emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # High severity policy flag → blocked by evaluate_block_conditions (critical/high flags)
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"


# ===========================================================================
# Scenario 7: Default fallback to human_review_required
# ===========================================================================


class TestScenarioDefaultHumanReview:
    """Emissions that can't auto-merge and can't auto-remediate fall through
    to the default human_review_required path."""

    def test_falls_through_to_human_review(self, tmp_path):
        emissions = all_required_emissions(confidence=0.80, risk_level="low")
        # Confidence 0.80 < 0.85 auto-merge threshold but >= 0.70 escalation
        # Risk is low → auto-remediate conditions would pass, but let's make
        # auto-remediate fail by using high risk (not in remediate list)
        emissions[0]["risk_level"] = "high"
        emissions[1]["risk_level"] = "high"
        # 2 high → aggregate risk = "high"
        # high risk not in auto-merge or auto-remediate conditions
        _write_emissions(tmp_path, emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 2
        assert manifest["decision"]["action"] == "human_review_required"


# ===========================================================================
# Scenario 8: Policy flags logged in pipeline
# ===========================================================================


class TestScenarioPolicyFlagLogging:
    """Policy flags present but not blocking severity — should be logged."""

    def test_low_severity_flags_logged_not_blocked(self, tmp_path):
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        emissions[0]["policy_flags"] = [
            {"flag": "missing_tests", "severity": "low",
             "description": "No unit tests for helper", "auto_remediable": True}
        ]
        _write_emissions(tmp_path, emissions)
        log_stream = io.StringIO()
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=log_stream,
        )
        assert exit_code == 0
        assert manifest["decision"]["action"] == "auto_merge"
        log_output = log_stream.getvalue()
        assert "missing_tests" in log_output


# ===========================================================================
# Scenario 9: Emissions directory does not exist
# ===========================================================================


class TestScenarioMissingEmissionsDir:
    """Point the engine at a non-existent directory."""

    def test_nonexistent_dir_blocks(self, tmp_path):
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path / "does-not-exist"),
            _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"


# ===========================================================================
# Scenario 10: Invalid profile path
# ===========================================================================


class TestScenarioInvalidProfile:
    """Point the engine at a non-existent profile YAML."""

    def test_bad_profile_blocks(self, tmp_path):
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        _write_emissions(tmp_path, emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path),
            str(tmp_path / "nonexistent-profile.yaml"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"


# ===========================================================================
# Scenario 11: Mixed valid and invalid emissions
# ===========================================================================


class TestScenarioMixedEmissions:
    """One valid emission and one invalid emission file."""

    def test_partial_invalid_required_blocks(self, tmp_path):
        """Invalid emission for a required panel still blocks (issue #244)."""
        good = make_emission(panel_name="code-review", confidence_score=0.90)
        with open(str(tmp_path / "code-review.json"), "w") as f:
            json.dump(good, f)
        # security-review is a required panel — invalid emission must block
        with open(str(tmp_path / "security-review.json"), "w") as f:
            f.write('{"panel_name": "bad"}')  # Missing required fields
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"

    def test_partial_invalid_optional_does_not_block(self, tmp_path):
        """Invalid emission for an optional panel does not block (issue #244)."""
        good = make_emission(panel_name="code-review", confidence_score=0.90)
        with open(str(tmp_path / "code-review.json"), "w") as f:
            json.dump(good, f)
        # bad-panel is NOT a required panel — invalid emission should not block
        with open(str(tmp_path / "bad-panel.json"), "w") as f:
            f.write('{"panel_name": "bad"}')  # Missing required fields
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code != 1, (
            f"Optional panel failure should not block. "
            f"Decision: {manifest['decision']['rationale']}"
        )


# ===========================================================================
# Scenario 12: Infrastructure profile — panel_risk OR conditions
# ===========================================================================


class TestScenarioInfrastructurePanelRiskOr:
    """Infrastructure profile has OR conditions in risk aggregation:
    panel_risk("architecture-review") == "critical" or panel_risk("security-review") == "critical"
    """

    def test_architecture_critical_triggers_or_condition(self, tmp_path):
        panels = [
            "code-review", "security-review", "architecture-review",
            "threat-modeling", "cost-analysis", "documentation-review",
        ]
        emissions = all_required_emissions(confidence=0.92, risk_level="low", panels=panels)
        # Make architecture-review critical
        for e in emissions:
            if e["panel_name"] == "architecture-review":
                e["risk_level"] = "critical"
        _write_emissions(tmp_path, emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("infrastructure_critical"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert manifest["risk_level"] == "critical"
        # Critical risk → escalation to human_review
        assert exit_code == 2

    def test_security_critical_triggers_or_condition(self, tmp_path):
        panels = [
            "code-review", "security-review", "architecture-review",
            "threat-modeling", "cost-analysis", "documentation-review",
        ]
        emissions = all_required_emissions(confidence=0.92, risk_level="low", panels=panels)
        for e in emissions:
            if e["panel_name"] == "security-review":
                e["risk_level"] = "critical"
        _write_emissions(tmp_path, emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("infrastructure_critical"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert manifest["risk_level"] == "critical"


# ===========================================================================
# Scenario 13: Block condition — starts_with pattern
# ===========================================================================


class TestScenarioBlockStartsWith:
    """Block condition using starts_with pattern on policy flags."""

    def test_block_starts_with_pii(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        flags = [{"flag": "pii_in_logs", "severity": "medium", "description": "PII"}]
        profile = make_profile(block_conditions=[
            {"description": "PII flag blocks", "condition": 'any_policy_flag starts_with "pii_"'}
        ])
        blocked, reason = policy_engine.evaluate_block_conditions(
            0.90, "low", flags, [], True, profile, log
        )
        assert blocked is True

    def test_no_block_when_prefix_doesnt_match(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        flags = [{"flag": "missing_tests", "severity": "medium", "description": "No tests"}]
        profile = make_profile(block_conditions=[
            {"description": "PII flag blocks", "condition": 'any_policy_flag starts_with "pii_"'}
        ])
        blocked, _ = policy_engine.evaluate_block_conditions(
            0.90, "low", flags, [], True, profile, log
        )
        assert blocked is False


# ===========================================================================
# Scenario 14: Risk condition — count with second branch
# ===========================================================================


class TestScenarioRiskCountSecondBranch:
    """Exercise the second count() branch in _evaluate_risk_condition
    (lines 252-256) which handles count conditions that don't start with
    'count(panel_risk =='."""

    def test_alternate_count_syntax(self):
        emissions = [
            make_emission(panel_name="a", risk_level="medium"),
            make_emission(panel_name="b", risk_level="medium"),
        ]
        risk_levels = {e["panel_name"]: e["risk_level"] for e in emissions}
        risk_counts = {"medium": 2, "low": 0, "high": 0, "critical": 0, "negligible": 0}
        # Use a condition that has count() and panel_risk but doesn't start
        # with "count(panel_risk =="
        result = policy_engine._evaluate_risk_condition(
            'total_count(panel_risk == "medium") >= 2',
            risk_levels, risk_counts, emissions,
        )
        assert result is True


# ===========================================================================
# Scenario 15: panel_risk with OR condition
# ===========================================================================


class TestScenarioPanelRiskOrCondition:
    """Exercise the panel_risk("a") == "x" or panel_risk("b") == "x" path."""

    def test_or_condition_first_match(self):
        emissions = [
            make_emission(panel_name="arch-review", risk_level="critical"),
            make_emission(panel_name="sec-review", risk_level="low"),
        ]
        risk_levels = {e["panel_name"]: e["risk_level"] for e in emissions}
        risk_counts = {"critical": 1, "low": 1}
        result = policy_engine._evaluate_risk_condition(
            'panel_risk("arch-review") == "critical" or panel_risk("sec-review") == "critical"',
            risk_levels, risk_counts, emissions,
        )
        assert result is True

    def test_or_condition_second_match(self):
        emissions = [
            make_emission(panel_name="arch-review", risk_level="low"),
            make_emission(panel_name="sec-review", risk_level="critical"),
        ]
        risk_levels = {e["panel_name"]: e["risk_level"] for e in emissions}
        risk_counts = {"critical": 1, "low": 1}
        result = policy_engine._evaluate_risk_condition(
            'panel_risk("arch-review") == "critical" or panel_risk("sec-review") == "critical"',
            risk_levels, risk_counts, emissions,
        )
        assert result is True

    def test_or_condition_no_match(self):
        emissions = [
            make_emission(panel_name="arch-review", risk_level="low"),
            make_emission(panel_name="sec-review", risk_level="low"),
        ]
        risk_levels = {e["panel_name"]: e["risk_level"] for e in emissions}
        risk_counts = {"low": 2}
        result = policy_engine._evaluate_risk_condition(
            'panel_risk("arch-review") == "critical" or panel_risk("sec-review") == "critical"',
            risk_levels, risk_counts, emissions,
        )
        assert result is False

    def test_panel_risk_insufficient_parts(self):
        """panel_risk condition with insufficient quoted parts returns False."""
        emissions = [make_emission(panel_name="a", risk_level="low")]
        risk_levels = {"a": "low"}
        risk_counts = {"low": 1}
        result = policy_engine._evaluate_risk_condition(
            'panel_risk(bad)',
            risk_levels, risk_counts, emissions,
        )
        assert result is False


# ===========================================================================
# Scenario 16: Unrecognized risk condition returns False
# ===========================================================================


class TestScenarioUnrecognizedRiskCondition:
    def test_unknown_condition_returns_false(self):
        result = policy_engine._evaluate_risk_condition(
            "something_unknown == true",
            {}, {}, [],
        )
        assert result is False


# ===========================================================================
# Scenario 17: Auto-remediate — no_policy_flag starts_with condition
# ===========================================================================


class TestScenarioAutoRemediateStartsWith:
    """Exercise the no_policy_flag starts_with path in auto-remediate."""

    def test_pii_flag_blocks_auto_remediate(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        flags = [{"flag": "pii_in_response", "severity": "low", "description": "PII"}]
        profile = make_profile(
            auto_remediate_conditions=[
                'no_policy_flag starts_with "pii_"',
            ],
        )
        result = policy_engine.evaluate_auto_remediate(0.90, "low", flags, [], profile, log)
        assert result is False

    def test_no_pii_flag_allows_auto_remediate(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        flags = [{"flag": "missing_docs", "severity": "low", "description": "Docs"}]
        profile = make_profile(
            auto_remediate_conditions=[
                'no_policy_flag starts_with "pii_"',
            ],
        )
        result = policy_engine.evaluate_auto_remediate(0.90, "low", flags, [], profile, log)
        assert result is True


# ===========================================================================
# Scenario 18: Auto-remediate — aggregate_confidence threshold
# ===========================================================================


class TestScenarioAutoRemediateConfidence:
    def test_low_confidence_blocks_remediate(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(
            auto_remediate_conditions=['aggregate_confidence >= 0.80'],
        )
        result = policy_engine.evaluate_auto_remediate(0.70, "low", [], [], profile, log)
        assert result is False


# ===========================================================================
# Scenario 19: Escalation — risk_level in list condition
# ===========================================================================


class TestScenarioEscalationRiskLevelIn:
    """Exercise the risk_level in [...] escalation path."""

    def test_risk_level_in_list(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(escalation_rules=[
            {"name": "med_risk", "condition": 'risk_level in ["critical", "high", "medium"]',
             "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "medium", [], [], profile, log)
        assert result == "human_review_required"

    def test_risk_level_not_in_list(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(escalation_rules=[
            {"name": "med_risk", "condition": 'risk_level in ["critical", "high"]',
             "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], [], profile, log)
        assert result is None


# ===========================================================================
# Scenario 20: Escalation — starts_with policy flag
# ===========================================================================


class TestScenarioEscalationStartsWith:
    def test_pii_flag_escalates(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        flags = [{"flag": "pii_found", "severity": "medium", "description": "PII"}]
        profile = make_profile(escalation_rules=[
            {"name": "pii", "condition": 'any_policy_flag starts_with "pii_"',
             "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", flags, [], profile, log)
        assert result == "human_review_required"


# ===========================================================================
# Scenario 21: Escalation — context-dependent conditions skipped
# ===========================================================================


class TestScenarioEscalationContextDependent:
    def test_files_changed_in_skipped(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(escalation_rules=[
            {"name": "ctx", "condition": 'files_changed_in ["deploy/"]',
             "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], [], profile, log)
        assert result is None

    def test_services_affected_skipped(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(escalation_rules=[
            {"name": "ctx", "condition": "services_affected_count > 1",
             "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], [], profile, log)
        assert result is None


# ===========================================================================
# Scenario 22: Block condition — policy_flag == specific flag
# ===========================================================================


class TestScenarioBlockPolicyFlagEquals:
    def test_matching_flag_blocks(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        flags = [{"flag": "pii_exposure", "severity": "medium", "description": "PII"}]
        profile = make_profile(block_conditions=[
            {"description": "PII", "condition": 'any_policy_flag == "pii_exposure"'}
        ])
        blocked, _ = policy_engine.evaluate_block_conditions(0.90, "low", flags, [], True, profile, log)
        assert blocked is True

    def test_non_matching_flag_doesnt_block(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        flags = [{"flag": "missing_tests", "severity": "medium", "description": "Tests"}]
        profile = make_profile(block_conditions=[
            {"description": "PII", "condition": 'any_policy_flag == "pii_exposure"'}
        ])
        blocked, _ = policy_engine.evaluate_block_conditions(0.90, "low", flags, [], True, profile, log)
        assert blocked is False


# ===========================================================================
# Scenario 23: load_emissions with non-directory path
# ===========================================================================


class TestScenarioLoadEmissions:
    def test_non_directory_returns_empty(self, tmp_path):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        schema = {"type": "object"}
        emissions, valid, failed = policy_engine.load_emissions(
            str(tmp_path / "not-a-dir"), schema, log
        )
        assert emissions == []
        assert valid is False
        assert failed == []


# ===========================================================================
# Scenario 24: Auto-merge — requires_human_review panel blocks merge
# ===========================================================================


class TestScenarioAutoMergeHumanReviewPanel:
    def test_human_review_panel_blocks_auto_merge(self):
        """requires_human_review=True with non-approve verdict blocks auto-merge."""
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        emissions = [make_emission(requires_human_review=True, aggregate_verdict="request_changes")]
        profile = make_profile()
        result = policy_engine.evaluate_auto_merge(0.95, "low", [], emissions, True, profile, log)
        assert result is False

    def test_human_review_panel_allows_auto_merge_when_verdict_approve(self):
        """Issue #680/#693: requires_human_review=True with approve verdict should NOT block auto-merge."""
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        emissions = [make_emission(requires_human_review=True, aggregate_verdict="approve")]
        profile = make_profile()
        result = policy_engine.evaluate_auto_merge(0.95, "low", [], emissions, True, profile, log)
        assert result is True


# ===========================================================================
# Scenario 25: CLI entry point
# ===========================================================================


class TestScenarioCli:
    """Test the main() CLI entry point via subprocess-like invocation."""

    def test_cli_happy_path(self, tmp_path):
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        emissions_dir = tmp_path / "emissions"
        emissions_dir.mkdir()
        _write_emissions(str(emissions_dir), emissions)

        output_path = tmp_path / "manifest.json"
        log_path = tmp_path / "eval.log"

        with mock.patch("sys.argv", [
            "policy-engine.py",
            "--emissions-dir", str(emissions_dir),
            "--profile", _profile_path("default"),
            "--output", str(output_path),
            "--log-file", str(log_path),
            "--ci-checks-passed", "true",
            "--commit-sha", "a" * 40,
            "--pr-number", "42",
            "--repo", "owner/repo",
        ]):
            with pytest.raises(SystemExit) as exc_info:
                policy_engine.main()
            assert exc_info.value.code == 0

        assert output_path.exists()
        manifest = json.loads(output_path.read_text())
        assert manifest["decision"]["action"] == "auto_merge"
        assert log_path.exists()

    def test_cli_block_path(self, tmp_path):
        emissions_dir = tmp_path / "emissions"
        emissions_dir.mkdir()
        # Empty dir → no emissions → block

        output_path = tmp_path / "manifest.json"

        with mock.patch("sys.argv", [
            "policy-engine.py",
            "--emissions-dir", str(emissions_dir),
            "--profile", _profile_path("default"),
            "--output", str(output_path),
        ]):
            with pytest.raises(SystemExit) as exc_info:
                policy_engine.main()
            assert exc_info.value.code == 1

    def test_cli_without_log_file(self, tmp_path):
        """CLI defaults to stderr when no --log-file is provided."""
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        emissions_dir = tmp_path / "emissions"
        emissions_dir.mkdir()
        _write_emissions(str(emissions_dir), emissions)

        output_path = tmp_path / "manifest.json"

        with mock.patch("sys.argv", [
            "policy-engine.py",
            "--emissions-dir", str(emissions_dir),
            "--profile", _profile_path("default"),
            "--output", str(output_path),
        ]):
            with pytest.raises(SystemExit) as exc_info:
                policy_engine.main()
            assert exc_info.value.code == 0


# ===========================================================================
# Scenario 26: EvaluationLog records correctly
# ===========================================================================


class TestScenarioEvaluationLog:
    def test_log_records_and_streams(self):
        stream = io.StringIO()
        log = policy_engine.EvaluationLog(stream=stream)
        log.record("test_rule", "pass", "it worked")
        assert len(log.entries) == 1
        assert log.entries[0]["rule_id"] == "test_rule"
        assert log.entries[0]["result"] == "pass"
        assert "it worked" in stream.getvalue()

    def test_log_default_stream(self):
        """Log uses stderr by default."""
        log = policy_engine.EvaluationLog()
        assert log._stream is sys.stderr


# ===========================================================================
# Scenario 27: collect_policy_flags aggregates across emissions
# ===========================================================================


class TestScenarioCollectPolicyFlags:
    def test_collects_flags_from_multiple_emissions(self):
        emissions = [
            make_emission(panel_name="a", policy_flags=[
                {"flag": "flag_a", "severity": "low", "description": "A"}
            ]),
            make_emission(panel_name="b", policy_flags=[
                {"flag": "flag_b", "severity": "high", "description": "B"}
            ]),
        ]
        flags = policy_engine.collect_policy_flags(emissions)
        assert len(flags) == 2
        assert {f["flag"] for f in flags} == {"flag_a", "flag_b"}

    def test_empty_flags(self):
        emissions = [make_emission(policy_flags=[])]
        flags = policy_engine.collect_policy_flags(emissions)
        assert flags == []


# ===========================================================================
# Scenario 28: Auto-merge context-dependent conditions fail-closed (#236)
# ===========================================================================


class TestScenarioAutoMergeContextDependent:
    def test_files_changed_in_fails_closed(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(auto_merge_conditions=[
            'not files_changed_in ["deploy/"]',
        ])
        result = policy_engine.evaluate_auto_merge(0.95, "low", [], [], True, profile, log)
        assert result is False

    def test_services_affected_fails_closed(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(auto_merge_conditions=[
            "services_affected_count <= 1",
        ])
        result = policy_engine.evaluate_auto_merge(0.95, "low", [], [], True, profile, log)
        assert result is False


# ===========================================================================
# Scenario 29: Auto-remediate context-dependent conditions fail-closed (#236)
# ===========================================================================


class TestScenarioAutoRemediateContextDependent:
    def test_files_changed_in_fails_closed(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(auto_remediate_conditions=[
            'not files_changed_in ["deploy/"]',
        ])
        result = policy_engine.evaluate_auto_remediate(0.90, "low", [], [], profile, log)
        assert result is False


# ===========================================================================
# Scenario 30: Unknown auto-remediate condition fails-closed (#236)
# ===========================================================================


class TestScenarioAutoRemediateUnknown:
    def test_unknown_condition_fails_closed(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(auto_remediate_conditions=[
            "something_completely_unknown == true",
        ])
        result = policy_engine.evaluate_auto_remediate(0.90, "low", [], [], profile, log)
        assert result is False


# ===========================================================================
# Scenario 31: Escalation with unknown condition returns False
# ===========================================================================


class TestScenarioEscalationUnknown:
    def test_unknown_condition_doesnt_trigger(self):
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(escalation_rules=[
            {"name": "unk", "condition": "completely_unknown_condition",
             "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], [], profile, log)
        assert result is None


# ===========================================================================
# Scenario 32: Escalation compound with NOT (issue #263)
# ===========================================================================


class TestScenarioEscalationCompoundWithNot:
    """Exercise compound escalation conditions using 'condition and not sub_condition' pattern."""

    def test_compound_not_both_true_escalates(self):
        """'risk_level == "critical" and not aggregate_confidence >= 0.90' — both sub-conditions
        are true (risk IS critical AND confidence is NOT >= 0.90) → escalation fires."""
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(escalation_rules=[
            {
                "name": "critical_low_conf",
                "condition": 'risk_level == "critical" and not aggregate_confidence >= 0.90',
                "action": "human_review_required",
            }
        ])
        result, reason = policy_engine.evaluate_escalation_rules(
            0.70, "critical", [], [], profile, log
        )
        assert result == "human_review_required"

    def test_compound_not_negation_prevents_escalation(self):
        """'risk_level == "critical" and not aggregate_confidence >= 0.90' — confidence IS >= 0.90,
        so 'not aggregate_confidence >= 0.90' is False → no escalation."""
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(escalation_rules=[
            {
                "name": "critical_low_conf",
                "condition": 'risk_level == "critical" and not aggregate_confidence >= 0.90',
                "action": "human_review_required",
            }
        ])
        result, _ = policy_engine.evaluate_escalation_rules(
            0.95, "critical", [], [], profile, log
        )
        assert result is None

    def test_compound_not_first_false_no_escalation(self):
        """'risk_level == "critical" and not aggregate_confidence >= 0.90' — risk is low,
        so first sub-condition is False → no escalation regardless of confidence."""
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(escalation_rules=[
            {
                "name": "critical_low_conf",
                "condition": 'risk_level == "critical" and not aggregate_confidence >= 0.90',
                "action": "human_review_required",
            }
        ])
        result, _ = policy_engine.evaluate_escalation_rules(
            0.50, "low", [], [], profile, log
        )
        assert result is None

    def test_compound_not_with_block_action(self):
        """Escalation compound NOT pattern with action='block' should produce block result."""
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        flags = [
            {"flag": "vuln_found", "severity": "critical", "description": "CVE",
             "dismissed": True}
        ]
        emissions = [
            make_emission(panel_name="security-review", policy_flags=flags),
        ]
        profile = make_profile(escalation_rules=[
            {
                "name": "dismissed_critical_block",
                "condition": 'dismissed_finding_severity in ["critical"] and not aggregate_confidence >= 0.95',
                "action": "block",
            }
        ])
        result, reason = policy_engine.evaluate_escalation_rules(
            0.80, "low", [], emissions, profile, log
        )
        assert result == "block"

    def test_compound_not_context_dependent_returns_false(self):
        """Compound with a NOT negated context-dependent sub-condition returns False.

        'risk_level == "critical" and not files_changed_in ["deploy/"]'
        The second sub-condition is context-dependent (returns None) → compound returns False.
        """
        log = policy_engine.EvaluationLog(stream=io.StringIO())
        profile = make_profile(escalation_rules=[
            {
                "name": "critical_deploy",
                "condition": 'risk_level == "critical" and not files_changed_in ["deploy/"]',
                "action": "block",
            }
        ])
        result, _ = policy_engine.evaluate_escalation_rules(
            0.80, "critical", [], [], profile, log
        )
        # Context-dependent sub-condition returns None → compound returns False → no escalation
        assert result is None
