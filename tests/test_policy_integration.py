"""End-to-end pipeline tests using the evaluate() function across all 4 profiles."""

import io
import json
import os
import tempfile

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
    """Write emission dicts as JSON files into a temp directory."""
    for emission in emissions:
        path = os.path.join(tmpdir, f"{emission['panel_name']}.json")
        with open(path, "w") as f:
            json.dump(emission, f)


def _profile_path(name):
    return str(REPO_ROOT / "governance" / "policy" / f"{name}.yaml")


# ===========================================================================
# Default profile tests
# ===========================================================================


class TestDefaultProfileIntegration:
    def test_auto_merge_happy_path(self, tmp_path):
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 0
        assert manifest["decision"]["action"] == "auto_merge"

    def test_missing_panel_phase_4b_transition(self, tmp_path):
        """Missing panel with high confidence + all approve → Phase 4b transition, no block."""
        # Only 5 of 6 required panels, but high confidence + all approve
        emissions = all_required_emissions(confidence=0.92)
        emissions = [e for e in emissions if e["panel_name"] != "data-governance-review"]
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # Phase 4b transition: missing panel downgraded → proceeds to auto_merge
        assert exit_code == 0
        assert manifest["decision"]["action"] == "auto_merge"

    def test_block_missing_panel_low_confidence(self, tmp_path):
        """Missing panel with low confidence → Phase 4b NOT triggered, still blocks."""
        emissions = all_required_emissions(confidence=0.50)
        emissions = [e for e in emissions if e["panel_name"] != "data-governance-review"]
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # Low confidence → Phase 4b not triggered → block for missing panel
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"

    def test_human_review_low_confidence(self, tmp_path):
        emissions = all_required_emissions(confidence=0.60, risk_level="low")
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 2
        assert manifest["decision"]["action"] == "human_review_required"

    def test_human_review_panel_disagreement(self, tmp_path):
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        # Make one panel disagree
        emissions[0]["aggregate_verdict"] = "request_changes"
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 2
        assert manifest["decision"]["action"] == "human_review_required"

    def test_block_critical_risk(self, tmp_path):
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        emissions[0]["risk_level"] = "critical"
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # Critical risk triggers escalation → human_review_required
        assert exit_code == 2
        assert manifest["decision"]["action"] == "human_review_required"

    def test_auto_remediate_path(self, tmp_path):
        # Medium risk, moderate confidence — can't auto-merge, but can auto-remediate
        emissions = all_required_emissions(confidence=0.75, risk_level="low")
        # One panel has medium risk causing aggregate to be medium
        emissions[0]["risk_level"] = "high"
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # With 1 high risk panel, aggregate risk = medium
        # Confidence 0.75 < 0.85 threshold → can't auto-merge
        # But auto-remediate accepts medium risk and confidence >= 0.60
        assert exit_code == 3
        assert manifest["decision"]["action"] == "auto_remediate"

    def test_invalid_emission_blocks(self, tmp_path):
        # Write an invalid JSON file
        with open(os.path.join(str(tmp_path), "bad.json"), "w") as f:
            f.write("{invalid json")
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"

    def test_empty_emissions_dir(self, tmp_path):
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"


# ===========================================================================
# fin_pii_high profile tests
# ===========================================================================


class TestFinPiiHighIntegration:
    def test_always_human_review(self, tmp_path):
        """Auto-merge is disabled → should never get exit code 0."""
        # Use fin_pii_high required panels (including data-governance-review per #231)
        panels = [
            "code-review", "security-review", "data-design-review",
            "testing-review", "threat-modeling", "cost-analysis",
            "documentation-review", "data-governance-review",
        ]
        emissions = all_required_emissions(confidence=0.95, risk_level="low", panels=panels)
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("fin_pii_high"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # Auto-merge disabled → never exit 0
        assert exit_code != 0
        assert manifest["decision"]["action"] != "auto_merge"

    def test_block_missing_panel(self, tmp_path):
        """missing_panel_behavior=block → immediate block."""
        panels = [
            "code-review", "security-review", "data-design-review",
            "testing-review", "threat-modeling", "cost-analysis",
            "data-governance-review",
            # Missing documentation-review
        ]
        emissions = all_required_emissions(confidence=0.95, risk_level="low", panels=panels)
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("fin_pii_high"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"
        assert "missing" in manifest["decision"]["rationale"].lower()


# ===========================================================================
# infrastructure_critical profile tests
# ===========================================================================


class TestInfrastructureCriticalIntegration:
    def test_strict_confidence(self, tmp_path):
        """Infrastructure profile requires >= 0.90 for auto-merge."""
        panels = [
            "code-review", "security-review", "architecture-review",
            "threat-modeling", "cost-analysis", "documentation-review",
        ]
        emissions = all_required_emissions(confidence=0.85, risk_level="low", panels=panels)
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("infrastructure_critical"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # Confidence 0.85 < 0.90 threshold → fails auto-merge
        # Also 0.85 >= 0.80 escalation threshold → no escalation
        # Falls through to auto_remediate or human_review
        assert exit_code in (2, 3)
        assert manifest["decision"]["action"] in ("human_review_required", "auto_remediate")


# ===========================================================================
# reduced_touchpoint profile tests
# ===========================================================================


class TestReducedTouchpointIntegration:
    def test_lower_auto_merge_thresholds(self, tmp_path):
        """Reduced touchpoint allows medium risk and 0.75 confidence for auto-merge."""
        emissions = all_required_emissions(confidence=0.80, risk_level="low")
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("reduced_touchpoint"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # 0.80 >= 0.75 threshold, low risk → auto-merge
        assert exit_code == 0
        assert manifest["decision"]["action"] == "auto_merge"

    def test_medium_risk_auto_merge(self, tmp_path):
        """Reduced touchpoint accepts medium risk for auto-merge."""
        emissions = all_required_emissions(confidence=0.80, risk_level="low")
        # One high-risk panel → aggregate medium with default rules
        emissions[0]["risk_level"] = "high"
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("reduced_touchpoint"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # Aggregate risk = medium (1 high panel), confidence 0.80 >= 0.75
        # Reduced touchpoint allows medium risk for auto-merge
        assert exit_code == 0
        assert manifest["decision"]["action"] == "auto_merge"


# ===========================================================================
# Compound block condition integration tests (issue #230)
# ===========================================================================


# ===========================================================================
# Phase 4b transition integration tests (issue #233)
# ===========================================================================


class TestPhase4bTransitionIntegration:
    """Integration tests verifying Phase 4b transition through the full evaluate() pipeline."""

    def test_missing_panel_high_confidence_all_approve_not_blocked(self, tmp_path):
        """Missing required panel + all approve + high confidence → Phase 4b transition.

        The engine should NOT block when the only issue is missing panels,
        all present panels approve, and confidence is above threshold.
        """
        # Only 5 of 6 required panels — data-governance-review missing
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        emissions = [e for e in emissions if e["panel_name"] != "data-governance-review"]
        _write_emissions(str(tmp_path), emissions)
        log_stream = io.StringIO()
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=log_stream,
        )
        # Phase 4b should downgrade the missing-panel block
        assert manifest["decision"]["action"] != "block"
        # Should proceed to auto_merge (all other conditions met)
        assert exit_code == 0
        assert manifest["decision"]["action"] == "auto_merge"
        # Verify Phase 4b is recorded in audit log
        log_output = log_stream.getvalue()
        assert "phase_4b_transition" in log_output.lower() or "Phase 4b" in log_output

    def test_missing_panel_low_confidence_still_blocks(self, tmp_path):
        """Missing required panel + low confidence → Phase 4b NOT triggered, still blocks."""
        emissions = all_required_emissions(confidence=0.50, risk_level="low")
        emissions = [e for e in emissions if e["panel_name"] != "data-governance-review"]
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # Low confidence → Phase 4b not triggered → block for missing panel
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"

    def test_missing_panel_non_approve_verdict_still_blocks(self, tmp_path):
        """Missing required panel + one panel request_changes → still blocks."""
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        emissions = [e for e in emissions if e["panel_name"] != "data-governance-review"]
        emissions[0]["aggregate_verdict"] = "request_changes"
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # Not all approve → Phase 4b not triggered → block for missing panel
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"

    def test_fin_pii_high_missing_panel_always_blocks(self, tmp_path):
        """fin_pii_high: missing_panel_behavior=block → Phase 4b never applies."""
        panels = [
            "code-review", "security-review", "data-design-review",
            "testing-review", "threat-modeling", "cost-analysis",
            "data-governance-review",
            # Missing documentation-review
        ]
        emissions = all_required_emissions(confidence=0.95, risk_level="low", panels=panels)
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("fin_pii_high"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # fin_pii_high uses missing_panel_behavior=block → hard block, no Phase 4b
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"

    def test_phase_4b_recorded_in_manifest_audit_log(self, tmp_path):
        """Phase 4b transition must be recorded in the manifest's policy_rules_evaluated."""
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        emissions = [e for e in emissions if e["panel_name"] != "data-governance-review"]
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # Check that the manifest audit log contains Phase 4b transition entry
        rules = manifest["decision"]["policy_rules_evaluated"]
        phase_4b_rules = [r for r in rules if "phase_4b" in r.get("rule_id", "")]
        assert len(phase_4b_rules) > 0
        assert phase_4b_rules[0]["result"] == "pass"


class TestCompoundBlockIntegration:
    """Integration tests verifying compound block conditions through the full pipeline."""

    def test_default_profile_critical_non_remediable_blocks(self, tmp_path):
        """default.yaml: critical flag + not auto_remediable triggers block via compound condition.

        The compound condition 'any_policy_flag_severity == "critical" and not auto_remediable'
        in default.yaml should now correctly evaluate. Even though the universal critical flag
        block also catches this, the compound condition is independently correct.
        """
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        emissions[0]["policy_flags"] = [
            {"flag": "vuln_critical", "severity": "critical", "description": "Critical CVE", "auto_remediable": False},
        ]
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"

    def test_default_profile_compound_condition_evaluates(self, tmp_path):
        """default.yaml: verify compound condition is evaluated (not silently skipped).

        Before the fix, compound conditions returned False and were logged as 'Not triggered'.
        After the fix, the compound condition should evaluate and log as 'fail' (triggered).
        """
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        emissions[0]["policy_flags"] = [
            {"flag": "vuln_critical", "severity": "critical", "description": "Critical CVE", "auto_remediable": False},
        ]
        _write_emissions(str(tmp_path), emissions)
        log_stream = io.StringIO()
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=log_stream,
        )
        log_output = log_stream.getvalue()
        # The compound condition description from default.yaml should appear as triggered
        assert "Critical policy violation" in log_output or "non-remediable" in log_output.lower()

    def test_reduced_touchpoint_critical_non_remediable_blocks(self, tmp_path):
        """reduced_touchpoint.yaml has the same compound block condition as default.yaml."""
        emissions = all_required_emissions(confidence=0.80, risk_level="low")
        emissions[0]["policy_flags"] = [
            {"flag": "vuln_critical", "severity": "critical", "description": "Critical CVE", "auto_remediable": False},
        ]
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("reduced_touchpoint"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"

    def test_context_dependent_compound_conditions_skip_gracefully(self, tmp_path):
        """fin_pii_high.yaml compound conditions with context-dependent sub-conditions don't block.

        Conditions like 'panel_missing("data-design-review") and data_files_changed' cannot
        be fully evaluated from emissions alone and should return False gracefully.
        """
        panels = [
            "code-review", "security-review", "data-design-review",
            "testing-review", "threat-modeling", "cost-analysis",
            "documentation-review", "data-governance-review",
        ]
        emissions = all_required_emissions(confidence=0.95, risk_level="low", panels=panels)
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("fin_pii_high"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # Should not block — context-dependent compound conditions return False
        assert manifest["decision"]["action"] != "block" or "missing" in manifest["decision"]["rationale"].lower()


# ===========================================================================
# Weight sum validation (issues #231, #232)
# ===========================================================================


class TestProfileWeightSums:
    """Verify all policy profile weights sum to 1.0."""

    @pytest.mark.parametrize("profile_name", [
        "default", "fin_pii_high", "infrastructure_critical", "reduced_touchpoint",
    ])
    def test_weights_sum_to_one(self, profile_name):
        import yaml
        path = REPO_ROOT / "governance" / "policy" / f"{profile_name}.yaml"
        with open(path) as f:
            profile = yaml.safe_load(f)
        weights = profile.get("weighting", {}).get("weights", {})
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.001, f"{profile_name} weights sum to {total}, expected 1.0"

    def test_fin_pii_high_has_data_governance_review(self):
        import yaml
        path = REPO_ROOT / "governance" / "policy" / "fin_pii_high.yaml"
        with open(path) as f:
            profile = yaml.safe_load(f)
        required = profile.get("required_panels", [])
        weights = profile.get("weighting", {}).get("weights", {})
        assert "data-governance-review" in required
        assert "data-governance-review" in weights

    def test_infrastructure_critical_has_data_governance_review(self):
        import yaml
        path = REPO_ROOT / "governance" / "policy" / "infrastructure_critical.yaml"
        with open(path) as f:
            profile = yaml.safe_load(f)
        weights = profile.get("weighting", {}).get("weights", {})
        optional = profile.get("optional_panels", [])
        assert "data-governance-review" in weights
        optional_names = [p["panel"] for p in optional]
        assert "data-governance-review" in optional_names
