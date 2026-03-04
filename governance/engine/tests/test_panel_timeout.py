"""Tests for panel execution timeout, fallback, and circuit breaker logic."""

import io
import pytest

from conftest import (
    policy_engine,
    make_emission,
    make_profile,
    all_required_emissions,
)

EvaluationLog = policy_engine.EvaluationLog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log():
    return EvaluationLog(stream=io.StringIO())


def _default_timeout_config(**overrides):
    """Return a panel timeout config dict with sensible defaults."""
    cfg = {
        "default_timeout_minutes": 5,
        "max_retries": 1,
        "fallback_strategy": "baseline",
        "fallback_confidence_cap": 0.50,
        "max_fallbacks_per_pr": 2,
        "per_panel_overrides": {},
    }
    cfg.update(overrides)
    return cfg


# ===========================================================================
# apply_execution_status_adjustments
# ===========================================================================


class TestExecutionStatusDefaultSuccess:
    """Emission without execution_status is treated as success."""

    def test_no_execution_status_field(self):
        log = _log()
        cfg = _default_timeout_config()
        emission = make_emission(panel_name="code-review", confidence_score=0.90)
        # Ensure no execution_status key
        assert "execution_status" not in emission

        adjusted, fallback_count, error_panels = (
            policy_engine.apply_execution_status_adjustments([emission], cfg, log)
        )

        assert len(adjusted) == 1
        assert adjusted[0]["confidence_score"] == 0.90  # unchanged
        assert fallback_count == 0
        assert error_panels == []

    def test_explicit_success_status(self):
        log = _log()
        cfg = _default_timeout_config()
        emission = make_emission(
            panel_name="code-review",
            confidence_score=0.90,
            execution_status="success",
        )

        adjusted, fallback_count, error_panels = (
            policy_engine.apply_execution_status_adjustments([emission], cfg, log)
        )

        assert adjusted[0]["confidence_score"] == 0.90
        assert fallback_count == 0
        assert error_panels == []


class TestFallbackConfidenceCap:
    """Fallback emission confidence is capped at fallback_confidence_cap."""

    def test_fallback_caps_high_confidence(self):
        log = _log()
        cfg = _default_timeout_config(fallback_confidence_cap=0.50)
        emission = make_emission(
            panel_name="security-review",
            confidence_score=0.95,
            execution_status="fallback",
        )

        adjusted, fallback_count, _ = (
            policy_engine.apply_execution_status_adjustments([emission], cfg, log)
        )

        assert adjusted[0]["confidence_score"] == 0.50
        assert fallback_count == 1

    def test_fallback_keeps_lower_confidence(self):
        """If original confidence is already below cap, keep the original."""
        log = _log()
        cfg = _default_timeout_config(fallback_confidence_cap=0.50)
        emission = make_emission(
            panel_name="cost-analysis",
            confidence_score=0.30,
            execution_status="fallback",
        )

        adjusted, _, _ = (
            policy_engine.apply_execution_status_adjustments([emission], cfg, log)
        )

        assert adjusted[0]["confidence_score"] == 0.30

    def test_custom_cap_value(self):
        log = _log()
        cfg = _default_timeout_config(fallback_confidence_cap=0.75)
        emission = make_emission(
            panel_name="code-review",
            confidence_score=0.90,
            execution_status="fallback",
        )

        adjusted, _, _ = (
            policy_engine.apply_execution_status_adjustments([emission], cfg, log)
        )

        assert adjusted[0]["confidence_score"] == 0.75


class TestTimeoutWithBaseline:
    """Timeout + baseline available is treated as fallback."""

    def test_timeout_caps_confidence(self):
        log = _log()
        cfg = _default_timeout_config(fallback_confidence_cap=0.50)
        emission = make_emission(
            panel_name="threat-modeling",
            confidence_score=0.85,
            execution_status="timeout",
        )

        adjusted, fallback_count, error_panels = (
            policy_engine.apply_execution_status_adjustments([emission], cfg, log)
        )

        assert adjusted[0]["confidence_score"] == 0.50
        assert fallback_count == 1
        assert error_panels == []

    def test_timeout_counted_as_fallback(self):
        """Timeout emissions contribute to fallback_count."""
        log = _log()
        cfg = _default_timeout_config()
        emissions = [
            make_emission(panel_name="code-review", confidence_score=0.90, execution_status="timeout"),
            make_emission(panel_name="security-review", confidence_score=0.80, execution_status="fallback"),
        ]

        _, fallback_count, _ = (
            policy_engine.apply_execution_status_adjustments(emissions, cfg, log)
        )

        assert fallback_count == 2


class TestTimeoutWithoutBaseline:
    """Timeout + no baseline = error panel (treated as missing)."""

    def test_error_status_treated_as_missing(self):
        log = _log()
        cfg = _default_timeout_config()
        emission = make_emission(
            panel_name="security-review",
            confidence_score=0.90,
            execution_status="error",
        )

        _, fallback_count, error_panels = (
            policy_engine.apply_execution_status_adjustments([emission], cfg, log)
        )

        assert fallback_count == 0
        assert error_panels == ["security-review"]

    def test_error_panel_not_capped(self):
        """Error panels are not confidence-capped (they are dropped as missing)."""
        log = _log()
        cfg = _default_timeout_config()
        emission = make_emission(
            panel_name="code-review",
            confidence_score=0.90,
            execution_status="error",
        )

        adjusted, _, _ = (
            policy_engine.apply_execution_status_adjustments([emission], cfg, log)
        )

        # Confidence left as-is — the emission will be excluded by missing panel logic
        assert adjusted[0]["confidence_score"] == 0.90


# ===========================================================================
# evaluate_panel_execution_rules
# ===========================================================================


class TestMaxFallbacksTriggersHumanReview:
    """3+ fallbacks triggers human_review_required via panel_execution rules."""

    def test_three_fallbacks_triggers_review(self):
        log = _log()
        profile = make_profile()
        profile["panel_execution"] = {
            "rules": [
                {
                    "description": "Fallback emissions cannot trigger auto-merge",
                    "condition": 'any_emission_status == "fallback"',
                    "action": "require_human_review",
                },
                {
                    "description": "More than 2 fallback emissions require human review",
                    "condition": 'count(emission_status == "fallback") > 2',
                    "action": "block_auto_merge",
                },
            ]
        }

        result = policy_engine.evaluate_panel_execution_rules(3, profile, log)
        assert result == "require_human_review"

    def test_single_fallback_triggers_first_rule(self):
        """Even a single fallback triggers the any_emission_status rule."""
        log = _log()
        profile = make_profile()
        profile["panel_execution"] = {
            "rules": [
                {
                    "description": "Fallback emissions cannot trigger auto-merge",
                    "condition": 'any_emission_status == "fallback"',
                    "action": "require_human_review",
                },
            ]
        }

        result = policy_engine.evaluate_panel_execution_rules(1, profile, log)
        assert result == "require_human_review"

    def test_zero_fallbacks_no_trigger(self):
        log = _log()
        profile = make_profile()
        profile["panel_execution"] = {
            "rules": [
                {
                    "description": "Fallback emissions cannot trigger auto-merge",
                    "condition": 'any_emission_status == "fallback"',
                    "action": "require_human_review",
                },
            ]
        }

        result = policy_engine.evaluate_panel_execution_rules(0, profile, log)
        assert result is None

    def test_no_panel_execution_rules(self):
        """Profile without panel_execution section returns None."""
        log = _log()
        profile = make_profile()

        result = policy_engine.evaluate_panel_execution_rules(2, profile, log)
        assert result is None


# ===========================================================================
# Circuit breaker configuration validation
# ===========================================================================


class TestCircuitBreakerTripsAfterThreshold:
    """Validate circuit breaker config is loaded and thresholds respected."""

    def test_circuit_breaker_config_exists(self, governance_root):
        """The circuit-breaker.yaml has a panel_execution section."""
        import yaml

        path = governance_root / "policy" / "circuit-breaker.yaml"
        assert path.exists(), f"Missing: {path}"
        with open(path) as f:
            data = yaml.safe_load(f)

        cb = data.get("circuit_breaker", {})
        pe = cb.get("panel_execution", {})
        assert pe.get("failure_threshold") == 3
        assert pe.get("success_threshold") == 1
        assert pe.get("cooldown_period_minutes") == 15
        assert pe.get("open_action") == "use_baseline_and_escalate"

    def test_panel_timeout_config_exists(self, governance_root):
        """The panel-timeout.yaml exists with expected fields."""
        import yaml

        path = governance_root / "policy" / "panel-timeout.yaml"
        assert path.exists(), f"Missing: {path}"
        with open(path) as f:
            data = yaml.safe_load(f)

        pt = data.get("panel_timeout", {})
        assert pt.get("version") == "1.0.0"
        assert pt.get("default_timeout_minutes") == 5
        assert pt.get("max_retries") == 1
        assert pt.get("fallback_confidence_cap") == 0.50
        assert pt.get("max_fallbacks_per_pr") == 2


# ===========================================================================
# Integration: full evaluate() pipeline with execution_status
# ===========================================================================


class TestEvaluatePipelineWithExecutionStatus:
    """End-to-end tests through the evaluate() pipeline."""

    def test_fallback_emission_prevents_auto_merge(self, tmp_path, governance_root):
        """A fallback emission triggers human_review_required via panel_execution rules."""
        import json

        profile_path = governance_root / "policy" / "default.yaml"
        emissions_dir = tmp_path / "emissions"
        emissions_dir.mkdir()

        # Create all required emissions, one with fallback status
        panels = [
            "code-review", "security-review", "threat-modeling",
            "cost-analysis", "documentation-review", "data-governance-review",
        ]
        for panel in panels:
            emission = make_emission(
                panel_name=panel,
                confidence_score=0.95,
                risk_level="low",
            )
            if panel == "security-review":
                emission["execution_status"] = "fallback"
            with open(emissions_dir / f"{panel}.json", "w") as f:
                json.dump(emission, f)

        manifest, exit_code = policy_engine.evaluate(
            emissions_dir=str(emissions_dir),
            profile_path=str(profile_path),
            ci_passed=True,
            log_stream=io.StringIO(),
        )

        # Should be human_review_required (exit code 2) due to fallback emission
        assert exit_code == 2
        assert manifest["decision"]["action"] == "human_review_required"

    def test_error_emission_on_required_panel_blocks(self, tmp_path, governance_root):
        """An error emission on a required panel blocks the merge."""
        import json

        profile_path = governance_root / "policy" / "default.yaml"
        emissions_dir = tmp_path / "emissions"
        emissions_dir.mkdir()

        panels = [
            "code-review", "security-review", "threat-modeling",
            "cost-analysis", "documentation-review", "data-governance-review",
        ]
        for panel in panels:
            emission = make_emission(
                panel_name=panel,
                confidence_score=0.95,
                risk_level="low",
            )
            if panel == "security-review":
                emission["execution_status"] = "error"
            with open(emissions_dir / f"{panel}.json", "w") as f:
                json.dump(emission, f)

        manifest, exit_code = policy_engine.evaluate(
            emissions_dir=str(emissions_dir),
            profile_path=str(profile_path),
            ci_passed=True,
            log_stream=io.StringIO(),
        )

        # Should block (exit code 1) because security-review is required but errored
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"

    def test_success_emissions_still_auto_merge(self, tmp_path, governance_root):
        """All-success emissions with high confidence still auto-merge normally."""
        import json

        profile_path = governance_root / "policy" / "default.yaml"
        emissions_dir = tmp_path / "emissions"
        emissions_dir.mkdir()

        panels = [
            "code-review", "security-review", "threat-modeling",
            "cost-analysis", "documentation-review", "data-governance-review",
        ]
        for panel in panels:
            emission = make_emission(
                panel_name=panel,
                confidence_score=0.95,
                risk_level="low",
                execution_status="success",
            )
            with open(emissions_dir / f"{panel}.json", "w") as f:
                json.dump(emission, f)

        manifest, exit_code = policy_engine.evaluate(
            emissions_dir=str(emissions_dir),
            profile_path=str(profile_path),
            ci_passed=True,
            log_stream=io.StringIO(),
        )

        assert exit_code == 0
        assert manifest["decision"]["action"] == "auto_merge"
