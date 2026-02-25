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

    def test_block_missing_panel(self, tmp_path):
        # Only 5 of 6 required panels
        emissions = all_required_emissions(confidence=0.92)
        emissions = [e for e in emissions if e["panel_name"] != "data-governance-review"]
        _write_emissions(str(tmp_path), emissions)
        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path), _profile_path("default"),
            ci_passed=True, log_stream=io.StringIO(),
        )
        # Missing required panel triggers block
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
        # Use fin_pii_high required panels
        panels = [
            "code-review", "security-review", "data-design-review",
            "testing-review", "threat-modeling", "cost-analysis",
            "documentation-review",
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
