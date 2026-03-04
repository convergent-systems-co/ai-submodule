"""Unit tests for every evaluation function in the policy engine."""

import io
import os
import pytest
from pathlib import Path

from conftest import policy_engine, make_emission, make_profile, all_required_emissions

EvaluationLog = policy_engine.EvaluationLog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log():
    return EvaluationLog(stream=io.StringIO())


# ===========================================================================
# Utility helpers
# ===========================================================================


class TestRiskIndex:
    def test_all_levels_map_correctly(self):
        assert policy_engine.risk_index("negligible") == 0
        assert policy_engine.risk_index("low") == 1
        assert policy_engine.risk_index("medium") == 2
        assert policy_engine.risk_index("high") == 3
        assert policy_engine.risk_index("critical") == 4

    def test_unknown_returns_zero(self):
        assert policy_engine.risk_index("unknown") == 0
        assert policy_engine.risk_index("") == 0


class TestExtractList:
    def test_parses_list(self):
        result = policy_engine._extract_list('risk_level in ["critical", "high"]')
        assert result == ["critical", "high"]

    def test_single_item(self):
        result = policy_engine._extract_list('risk_level in ["low"]')
        assert result == ["low"]

    def test_no_match(self):
        result = policy_engine._extract_list("no quotes here")
        assert result == []


class TestExtractComparison:
    def test_gte(self):
        op, val = policy_engine._extract_comparison('count(panel_risk == "high") >= 2')
        assert op == ">="
        assert val == 2

    def test_eq(self):
        op, val = policy_engine._extract_comparison('count(panel_risk == "high") == 1')
        assert op == "=="
        assert val == 1

    def test_lt(self):
        op, val = policy_engine._extract_comparison('count(panel_risk == "low") < 3')
        assert op == "<"
        assert val == 3

    def test_no_match_returns_default(self):
        op, val = policy_engine._extract_comparison("no comparison")
        assert op == ">="
        assert val == 0


class TestCompare:
    def test_gte(self):
        assert policy_engine._compare(2, ">=", 2) is True
        assert policy_engine._compare(1, ">=", 2) is False

    def test_lte(self):
        assert policy_engine._compare(2, "<=", 2) is True
        assert policy_engine._compare(3, "<=", 2) is False

    def test_eq(self):
        assert policy_engine._compare(1, "==", 1) is True
        assert policy_engine._compare(1, "==", 2) is False

    def test_gt(self):
        assert policy_engine._compare(3, ">", 2) is True
        assert policy_engine._compare(2, ">", 2) is False

    def test_lt(self):
        assert policy_engine._compare(1, "<", 2) is True
        assert policy_engine._compare(2, "<", 2) is False

    def test_unknown_op(self):
        assert policy_engine._compare(1, "!=", 1) is False


class TestSlugify:
    def test_basic(self):
        assert policy_engine._slugify("Hello World!") == "hello_world"

    def test_special_chars(self):
        assert policy_engine._slugify("foo@bar#baz") == "foo_bar_baz"

    def test_truncation(self):
        long_text = "a" * 100
        result = policy_engine._slugify(long_text)
        assert len(result) <= 50

    def test_strips_leading_trailing_underscores(self):
        assert policy_engine._slugify("  --hello--  ") == "hello"


# ===========================================================================
# Confidence computation
# ===========================================================================


class TestWeightedConfidence:
    def test_single_panel(self):
        log = _log()
        emissions = [make_emission(panel_name="code-review", confidence_score=0.90)]
        profile = make_profile(weights={"code-review": 1.0})
        result = policy_engine.compute_weighted_confidence(emissions, profile, log)
        assert result == pytest.approx(0.90, abs=0.01)

    def test_multiple_panels(self):
        log = _log()
        emissions = [
            make_emission(panel_name="code-review", confidence_score=0.90),
            make_emission(panel_name="security-review", confidence_score=0.80),
        ]
        profile = make_profile(weights={"code-review": 0.50, "security-review": 0.50})
        result = policy_engine.compute_weighted_confidence(emissions, profile, log)
        assert result == pytest.approx(0.85, abs=0.01)

    def test_missing_panel_redistribute(self):
        log = _log()
        # Only code-review present, security-review absent
        emissions = [make_emission(panel_name="code-review", confidence_score=0.90)]
        profile = make_profile(
            weights={"code-review": 0.50, "security-review": 0.50},
            missing_panel_behavior="redistribute",
        )
        result = policy_engine.compute_weighted_confidence(emissions, profile, log)
        # With redistribution, code-review gets weight 0.50/0.50 = 1.0
        assert result == pytest.approx(0.90, abs=0.01)

    def test_all_panels_present_no_redistribution_needed(self):
        log = _log()
        emissions = [
            make_emission(panel_name="code-review", confidence_score=0.90),
            make_emission(panel_name="security-review", confidence_score=0.80),
        ]
        profile = make_profile(
            weights={"code-review": 0.50, "security-review": 0.50},
        )
        result = policy_engine.compute_weighted_confidence(emissions, profile, log)
        assert result == pytest.approx(0.85, abs=0.01)

    def test_empty_emissions(self):
        log = _log()
        profile = make_profile()
        result = policy_engine.compute_weighted_confidence([], profile, log)
        assert result == 0.0


# ===========================================================================
# Risk aggregation
# ===========================================================================


class TestRiskAggregation:
    def test_any_critical(self):
        log = _log()
        emissions = [
            make_emission(panel_name="code-review", risk_level="low"),
            make_emission(panel_name="security-review", risk_level="critical"),
        ]
        profile = make_profile()
        result = policy_engine.compute_aggregate_risk(emissions, profile, log)
        assert result == "critical"

    def test_two_high(self):
        log = _log()
        emissions = [
            make_emission(panel_name="code-review", risk_level="high"),
            make_emission(panel_name="security-review", risk_level="high"),
            make_emission(panel_name="threat-modeling", risk_level="low"),
        ]
        profile = make_profile()
        result = policy_engine.compute_aggregate_risk(emissions, profile, log)
        assert result == "high"

    def test_one_high(self):
        log = _log()
        emissions = [
            make_emission(panel_name="code-review", risk_level="high"),
            make_emission(panel_name="security-review", risk_level="low"),
        ]
        profile = make_profile()
        result = policy_engine.compute_aggregate_risk(emissions, profile, log)
        assert result == "medium"

    def test_all_low(self):
        log = _log()
        emissions = [
            make_emission(panel_name="code-review", risk_level="low"),
            make_emission(panel_name="security-review", risk_level="negligible"),
        ]
        profile = make_profile()
        result = policy_engine.compute_aggregate_risk(emissions, profile, log)
        assert result == "low"

    def test_no_rule_match_falls_back_to_highest(self):
        log = _log()
        emissions = [
            make_emission(panel_name="code-review", risk_level="medium"),
        ]
        # Profile with no matching rules
        profile = make_profile(risk_rules=[
            {
                "description": "Only matches critical",
                "condition": 'any_panel_risk == "critical"',
                "result": "critical",
            },
        ])
        result = policy_engine.compute_aggregate_risk(emissions, profile, log)
        assert result == "medium"  # fallback to highest severity


# ===========================================================================
# Risk condition evaluator
# ===========================================================================


class TestEvaluateRiskCondition:
    def _risk_levels(self, emissions):
        return {e["panel_name"]: e["risk_level"] for e in emissions}

    def _risk_counts(self, emissions):
        counts = {}
        for r in policy_engine.RISK_ORDER:
            counts[r] = sum(1 for e in emissions if e["risk_level"] == r)
        return counts

    def test_any_panel_risk_eq(self):
        emissions = [make_emission(risk_level="critical")]
        assert policy_engine._evaluate_risk_condition(
            'any_panel_risk == "critical"',
            self._risk_levels(emissions),
            self._risk_counts(emissions),
            emissions,
        ) is True

    def test_any_panel_risk_in(self):
        emissions = [make_emission(risk_level="high")]
        assert policy_engine._evaluate_risk_condition(
            'any_panel_risk in ["critical", "high"]',
            self._risk_levels(emissions),
            self._risk_counts(emissions),
            emissions,
        ) is True

    def test_count_panel_risk(self):
        emissions = [
            make_emission(panel_name="a", risk_level="high"),
            make_emission(panel_name="b", risk_level="high"),
        ]
        assert policy_engine._evaluate_risk_condition(
            'count(panel_risk == "high") >= 2',
            self._risk_levels(emissions),
            self._risk_counts(emissions),
            emissions,
        ) is True

    def test_all_panels_risk_in(self):
        emissions = [
            make_emission(panel_name="a", risk_level="low"),
            make_emission(panel_name="b", risk_level="negligible"),
        ]
        assert policy_engine._evaluate_risk_condition(
            'all_panels_risk in ["low", "negligible"]',
            self._risk_levels(emissions),
            self._risk_counts(emissions),
            emissions,
        ) is True

    def test_panel_risk_named(self):
        emissions = [
            make_emission(panel_name="security-review", risk_level="critical"),
        ]
        assert policy_engine._evaluate_risk_condition(
            'panel_risk("security-review") == "critical"',
            self._risk_levels(emissions),
            self._risk_counts(emissions),
            emissions,
        ) is True


# ===========================================================================
# Required panels
# ===========================================================================


class TestRequiredPanels:
    def test_all_present(self):
        log = _log()
        emissions = all_required_emissions()
        profile = make_profile()
        missing = policy_engine.check_required_panels(emissions, profile, log)
        assert missing == []

    def test_missing_panel(self):
        log = _log()
        emissions = all_required_emissions()
        # Remove the last emission (copilot-review)
        emissions = emissions[:-1]
        profile = make_profile()
        missing = policy_engine.check_required_panels(emissions, profile, log)
        assert len(missing) == 1
        assert "copilot-review" in missing


# ===========================================================================
# Block conditions
# ===========================================================================


class TestBlockConditions:
    def test_block_missing_required(self):
        log = _log()
        blocked, reason = policy_engine.evaluate_block_conditions(
            0.90, "low", [], ["security-review"], True, make_profile(), log
        )
        assert blocked is True
        assert "missing" in reason.lower()

    def test_block_ci_failed(self):
        log = _log()
        blocked, reason = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], False, make_profile(), log
        )
        assert blocked is True
        assert "CI" in reason

    def test_block_low_confidence_threshold(self):
        log = _log()
        profile = make_profile(block_conditions=[
            {"description": "Low confidence", "condition": "aggregate_confidence < 0.40"}
        ])
        blocked, reason = policy_engine.evaluate_block_conditions(
            0.30, "low", [], [], True, profile, log
        )
        assert blocked is True

    def test_block_critical_policy_flag(self):
        log = _log()
        flags = [{"flag": "pii_exposure", "severity": "critical", "description": "PII found"}]
        blocked, reason = policy_engine.evaluate_block_conditions(
            0.90, "low", flags, [], True, make_profile(), log
        )
        assert blocked is True
        assert "policy flags" in reason.lower()

    def test_no_block_happy_path(self):
        log = _log()
        blocked, _ = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], True, make_profile(), log
        )
        assert blocked is False


# ===========================================================================
# Compound block conditions
# ===========================================================================


class TestCompoundBlockConditions:
    """Tests for compound 'and' block conditions (issue #230)."""

    def test_critical_and_not_auto_remediable_blocks(self):
        """Critical flag + not auto_remediable should block."""
        log = _log()
        flags = [
            {"flag": "vuln_found", "severity": "critical", "description": "CVE", "auto_remediable": False},
        ]
        profile = make_profile(block_conditions=[
            {"description": "Critical non-remediable", "condition": 'any_policy_flag_severity == "critical" and not auto_remediable'}
        ])
        blocked, reason = policy_engine.evaluate_block_conditions(
            0.90, "low", flags, [], True, profile, log
        )
        assert blocked is True
        assert "non-remediable" in reason.lower()

    def test_critical_and_auto_remediable_does_not_trigger_compound(self):
        """Critical flag + auto_remediable=True — compound condition evaluates False.

        Note: evaluate_block_conditions has a universal critical/high flag block
        that catches this separately. This test verifies the compound evaluator
        correctly returns False when all flags are auto-remediable.
        """
        flags = [
            {"flag": "vuln_found", "severity": "critical", "description": "CVE", "auto_remediable": True},
        ]
        result = policy_engine._evaluate_block_condition(
            'any_policy_flag_severity == "critical" and not auto_remediable',
            0.90, "low", flags,
        )
        assert result is False

    def test_non_critical_and_not_auto_remediable_does_not_block(self):
        """Non-critical flag + not auto_remediable should NOT block (first sub-condition false)."""
        log = _log()
        flags = [
            {"flag": "style_issue", "severity": "low", "description": "Lint", "auto_remediable": False},
        ]
        profile = make_profile(block_conditions=[
            {"description": "Critical non-remediable", "condition": 'any_policy_flag_severity == "critical" and not auto_remediable'}
        ])
        blocked, _ = policy_engine.evaluate_block_conditions(
            0.90, "low", flags, [], True, profile, log
        )
        assert blocked is False

    def test_no_flags_does_not_block(self):
        """No flags at all should NOT block on compound condition."""
        log = _log()
        profile = make_profile(block_conditions=[
            {"description": "Critical non-remediable", "condition": 'any_policy_flag_severity == "critical" and not auto_remediable'}
        ])
        blocked, _ = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], True, profile, log
        )
        assert blocked is False

    def test_context_dependent_compound_does_not_block(self):
        """Compound with context-dependent sub-condition returns False (cannot evaluate)."""
        log = _log()
        profile = make_profile(block_conditions=[
            {"description": "Missing data panel", "condition": 'panel_missing("data-design-review") and data_files_changed'}
        ])
        blocked, _ = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], True, profile, log
        )
        assert blocked is False

    def test_multiple_critical_flags_mixed_remediable(self):
        """Multiple flags — one critical non-remediable should block."""
        log = _log()
        flags = [
            {"flag": "style_issue", "severity": "low", "description": "Lint", "auto_remediable": True},
            {"flag": "vuln_found", "severity": "critical", "description": "CVE", "auto_remediable": False},
        ]
        profile = make_profile(block_conditions=[
            {"description": "Critical non-remediable", "condition": 'any_policy_flag_severity == "critical" and not auto_remediable'}
        ])
        blocked, _ = policy_engine.evaluate_block_conditions(
            0.90, "low", flags, [], True, profile, log
        )
        assert blocked is True

    def test_all_flags_auto_remediable_compound_returns_false(self):
        """All critical flags are auto-remediable — compound condition evaluates False."""
        flags = [
            {"flag": "vuln_a", "severity": "critical", "description": "A", "auto_remediable": True},
            {"flag": "vuln_b", "severity": "critical", "description": "B", "auto_remediable": True},
        ]
        result = policy_engine._evaluate_block_condition(
            'any_policy_flag_severity == "critical" and not auto_remediable',
            0.90, "low", flags,
        )
        assert result is False

    def test_compound_both_true_blocks(self):
        """Compound condition where both sub-conditions are true returns True (block)."""
        flags = [
            {"flag": "vuln_critical", "severity": "critical", "description": "Critical CVE", "auto_remediable": False},
        ]
        result = policy_engine._evaluate_block_condition(
            'any_policy_flag_severity == "critical" and not auto_remediable',
            0.90, "low", flags,
        )
        assert result is True

    def test_compound_first_false_no_block(self):
        """First sub-condition false (no critical flag) returns False."""
        flags = [
            {"flag": "style_issue", "severity": "low", "description": "Lint", "auto_remediable": False},
        ]
        result = policy_engine._evaluate_block_condition(
            'any_policy_flag_severity == "critical" and not auto_remediable',
            0.90, "low", flags,
        )
        assert result is False

    def test_compound_second_false_no_block(self):
        """Second sub-condition false (all flags auto-remediable) returns False."""
        flags = [
            {"flag": "vuln_critical", "severity": "critical", "description": "Critical CVE", "auto_remediable": True},
        ]
        result = policy_engine._evaluate_block_condition(
            'any_policy_flag_severity == "critical" and not auto_remediable',
            0.90, "low", flags,
        )
        assert result is False

    def test_compound_with_not_negation(self):
        """Compound with 'not' prefix negates the sub-condition correctly.

        Tests: 'any_policy_flag_severity == "critical" and not auto_remediable'
        When flags are critical AND not auto-remediable, block should trigger.
        When flags are critical AND auto-remediable, 'not auto_remediable' is False → no block.
        """
        # Case 1: not auto_remediable is True (flags are NOT auto-remediable) → blocks
        flags_not_remediable = [
            {"flag": "vuln", "severity": "critical", "description": "CVE", "auto_remediable": False},
        ]
        result = policy_engine._evaluate_block_condition(
            'any_policy_flag_severity == "critical" and not auto_remediable',
            0.90, "low", flags_not_remediable,
        )
        assert result is True

        # Case 2: not auto_remediable is False (flags ARE auto-remediable) → no block
        flags_remediable = [
            {"flag": "vuln", "severity": "critical", "description": "CVE", "auto_remediable": True},
        ]
        result = policy_engine._evaluate_block_condition(
            'any_policy_flag_severity == "critical" and not auto_remediable',
            0.90, "low", flags_remediable,
        )
        assert result is False

    def test_compound_context_dependent_returns_false(self):
        """Compound with a context-dependent sub-condition returns False (fail-closed)."""
        result = policy_engine._evaluate_block_condition(
            'panel_missing("data-design-review") and data_files_changed',
            0.90, "low", [],
        )
        assert result is False


class TestCompoundBlockSubCondition:
    """Unit tests for _evaluate_block_sub_condition."""

    def test_any_policy_flag_severity(self):
        flags = [{"flag": "x", "severity": "critical", "description": "t"}]
        result = policy_engine._evaluate_block_sub_condition(
            'any_policy_flag_severity == "critical"', 0.9, "low", flags
        )
        assert result is True

    def test_any_policy_flag_severity_no_match(self):
        flags = [{"flag": "x", "severity": "low", "description": "t"}]
        result = policy_engine._evaluate_block_sub_condition(
            'any_policy_flag_severity == "critical"', 0.9, "low", flags
        )
        assert result is False

    def test_auto_remediable_true(self):
        flags = [{"flag": "x", "severity": "critical", "description": "t", "auto_remediable": True}]
        result = policy_engine._evaluate_block_sub_condition(
            "auto_remediable", 0.9, "low", flags
        )
        assert result is True

    def test_auto_remediable_false(self):
        flags = [{"flag": "x", "severity": "critical", "description": "t", "auto_remediable": False}]
        result = policy_engine._evaluate_block_sub_condition(
            "auto_remediable", 0.9, "low", flags
        )
        assert result is False

    def test_auto_remediable_no_flags(self):
        result = policy_engine._evaluate_block_sub_condition(
            "auto_remediable", 0.9, "low", []
        )
        assert result is True

    def test_context_dependent_returns_none(self):
        result = policy_engine._evaluate_block_sub_condition(
            "data_files_changed", 0.9, "low", []
        )
        assert result is None

    def test_panel_missing_returns_none(self):
        result = policy_engine._evaluate_block_sub_condition(
            'panel_missing("data-design-review")', 0.9, "low", []
        )
        assert result is None

    def test_unknown_returns_none(self):
        result = policy_engine._evaluate_block_sub_condition(
            "some_unknown_pattern", 0.9, "low", []
        )
        assert result is None

    def test_aggregate_confidence_lt(self):
        result = policy_engine._evaluate_block_sub_condition(
            "aggregate_confidence < 0.40", 0.30, "low", []
        )
        assert result is True

    def test_aggregate_confidence_gte(self):
        result = policy_engine._evaluate_block_sub_condition(
            "aggregate_confidence >= 0.85", 0.90, "low", []
        )
        assert result is True


class TestCompoundEscalationConditions:
    """Tests for compound 'and' escalation conditions."""

    def test_context_dependent_compound_does_not_escalate(self):
        """Compound with context-dependent sub-condition returns False."""
        log = _log()
        profile = make_profile(escalation_rules=[
            {"name": "sec_dismiss", "condition": 'dismissed_finding_severity in ["critical", "high"] and dismissed_finding_panel == "security-review"', "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], [], profile, log)
        assert result is None

    def test_evaluable_compound_escalation(self):
        """Compound escalation with evaluable sub-conditions."""
        log = _log()
        flags = [{"flag": "issue", "severity": "critical", "description": "t"}]
        profile = make_profile(escalation_rules=[
            {"name": "compound", "condition": 'risk_level == "high" and any_policy_flag_severity in ["critical"]', "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "high", flags, [], profile, log)
        assert result == "human_review_required"

    def test_evaluable_compound_escalation_partial_false(self):
        """One sub-condition false → no escalation."""
        log = _log()
        flags = [{"flag": "issue", "severity": "low", "description": "t"}]
        profile = make_profile(escalation_rules=[
            {"name": "compound", "condition": 'risk_level == "high" and any_policy_flag_severity in ["critical"]', "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "high", flags, [], profile, log)
        assert result is None


# ===========================================================================
# Escalation rules
# ===========================================================================


class TestEscalationRules:
    def test_escalation_low_confidence(self):
        log = _log()
        profile = make_profile(escalation_rules=[
            {"name": "low_conf", "condition": "aggregate_confidence < 0.70", "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.60, "low", [], [], profile, log)
        assert result == "human_review_required"

    def test_escalation_critical_risk(self):
        log = _log()
        profile = make_profile(escalation_rules=[
            {"name": "crit", "condition": 'risk_level == "critical"', "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "critical", [], [], profile, log)
        assert result == "human_review_required"

    def test_escalation_policy_violation(self):
        log = _log()
        flags = [{"flag": "pii_leak", "severity": "critical", "description": "PII"}]
        profile = make_profile(escalation_rules=[
            {"name": "policy", "condition": 'any_policy_flag_severity in ["critical", "high"]', "action": "block"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", flags, [], profile, log)
        assert result == "block"

    def test_escalation_panel_disagreement(self):
        log = _log()
        emissions = [
            make_emission(panel_name="a", aggregate_verdict="approve"),
            make_emission(panel_name="b", aggregate_verdict="request_changes"),
        ]
        profile = make_profile(escalation_rules=[
            {"name": "disagree", "condition": "panel_disagreement_detected == true", "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], emissions, profile, log)
        assert result == "human_review_required"

    def test_escalation_requires_human_review(self):
        """Panel with requires_human_review=True and non-approve verdict should escalate."""
        log = _log()
        emissions = [make_emission(requires_human_review=True, aggregate_verdict="request_changes")]
        profile = make_profile()
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], emissions, profile, log)
        assert result == "human_review_required"

    def test_no_escalation_when_requires_human_review_but_verdict_approve(self):
        """Issue #693: Panel with requires_human_review=True but approve verdict should NOT escalate."""
        log = _log()
        emissions = [make_emission(requires_human_review=True, aggregate_verdict="approve")]
        profile = make_profile()
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], emissions, profile, log)
        assert result is None

    def test_no_escalation_happy_path(self):
        log = _log()
        emissions = [make_emission()]
        profile = make_profile()
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], emissions, profile, log)
        assert result is None


# ===========================================================================
# Auto-merge conditions
# ===========================================================================


class TestFailClosedDefaults:
    """Issue #236: context-dependent conditions must fail-closed."""

    def test_auto_merge_context_dependent_returns_false(self):
        result = policy_engine._evaluate_auto_merge_condition(
            'not files_changed_in ["deploy/", "k8s/"]',
            0.95, "low", [], [], True
        )
        assert result is False

    def test_auto_merge_unrecognized_returns_false(self):
        result = policy_engine._evaluate_auto_merge_condition(
            'some_future_condition == true',
            0.95, "low", [], [], True
        )
        assert result is False

    def test_auto_remediate_context_dependent_returns_false(self):
        result = policy_engine._evaluate_auto_remediate_condition(
            'files_changed_in ["src/"]',
            0.95, "low", [], []
        )
        assert result is False

    def test_auto_remediate_unrecognized_returns_false(self):
        result = policy_engine._evaluate_auto_remediate_condition(
            'some_future_condition == true',
            0.95, "low", [], []
        )
        assert result is False


# ===========================================================================
# Emission semantic consistency (issue #234)
# ===========================================================================


class TestEmissionConsistency:
    """Tests for validate_emission_consistency()."""

    def test_consistent_emission_no_warnings(self):
        log = _log()
        emission = make_emission(aggregate_verdict="approve")
        warnings = policy_engine.validate_emission_consistency(emission, log)
        assert warnings == []

    def test_block_finding_with_approve_verdict_warns(self):
        """Block finding + aggregate_verdict=approve is inconsistent."""
        log = _log()
        emission = make_emission(
            aggregate_verdict="approve",
            findings=[
                {"persona": "security/reviewer", "verdict": "block", "confidence": 0.95, "rationale": "Critical vuln"},
            ],
        )
        warnings = policy_engine.validate_emission_consistency(emission, log)
        assert len(warnings) == 1
        assert "block" in warnings[0].lower()
        assert "approve" in warnings[0].lower()

    def test_block_finding_with_block_verdict_no_warning(self):
        """Block finding + aggregate_verdict=block is consistent."""
        log = _log()
        emission = make_emission(
            aggregate_verdict="block",
            findings=[
                {"persona": "security/reviewer", "verdict": "block", "confidence": 0.95, "rationale": "Critical vuln"},
            ],
        )
        warnings = policy_engine.validate_emission_consistency(emission, log)
        assert warnings == []

    def test_critical_flag_with_negligible_risk_warns(self):
        """Critical policy flag + risk_level=negligible is inconsistent."""
        log = _log()
        emission = make_emission(
            risk_level="negligible",
            policy_flags=[{"flag": "pii_exposure", "severity": "critical", "description": "PII found"}],
        )
        warnings = policy_engine.validate_emission_consistency(emission, log)
        assert len(warnings) == 1
        assert "negligible" in warnings[0].lower()

    def test_critical_flag_with_high_risk_no_warning(self):
        """Critical policy flag + risk_level=high is consistent."""
        log = _log()
        emission = make_emission(
            risk_level="high",
            policy_flags=[{"flag": "pii_exposure", "severity": "critical", "description": "PII found"}],
        )
        warnings = policy_engine.validate_emission_consistency(emission, log)
        assert warnings == []

    def test_low_flag_with_negligible_risk_no_warning(self):
        """Low severity flag + negligible risk is fine."""
        log = _log()
        emission = make_emission(
            risk_level="negligible",
            policy_flags=[{"flag": "style_issue", "severity": "low", "description": "Minor style"}],
        )
        warnings = policy_engine.validate_emission_consistency(emission, log)
        assert warnings == []

    def test_multiple_inconsistencies(self):
        """Emission with both inconsistencies returns multiple warnings."""
        log = _log()
        emission = make_emission(
            aggregate_verdict="approve",
            risk_level="negligible",
            findings=[
                {"persona": "security/reviewer", "verdict": "block", "confidence": 0.95, "rationale": "Vuln"},
            ],
            policy_flags=[{"flag": "pii_exposure", "severity": "critical", "description": "PII"}],
        )
        warnings = policy_engine.validate_emission_consistency(emission, log)
        assert len(warnings) == 2


# ===========================================================================
# Phase 4b transition (issue #233)
# ===========================================================================


class TestPhase4bTransition:
    """Phase 4b: missing panels downgraded when all present panels approve with high confidence."""

    def test_phase_4b_clears_missing_panels(self):
        """Missing required panel + all approve + high confidence → no block."""
        log = _log()
        emissions = [
            make_emission(panel_name="code-review", confidence_score=0.90),
            make_emission(panel_name="security-review", confidence_score=0.90),
            make_emission(panel_name="threat-modeling", confidence_score=0.90),
            make_emission(panel_name="cost-analysis", confidence_score=0.90),
            make_emission(panel_name="finops-review", confidence_score=0.90),
            make_emission(panel_name="documentation-review", confidence_score=0.90),
            make_emission(panel_name="copilot-review", confidence_score=0.90),
            # data-governance-review missing
        ]
        profile = make_profile()
        # Compute confidence with redistribution
        aggregate_confidence = policy_engine.compute_weighted_confidence(emissions, profile, log)

        # Simulate missing panel check
        missing_required = policy_engine.check_required_panels(emissions, profile, log)
        assert missing_required == ["data-governance-review"]

        # Phase 4b: all present panels approve + high confidence → clear missing
        all_approve = all(e.get("aggregate_verdict") == "approve" for e in emissions)
        assert all_approve is True
        assert aggregate_confidence >= 0.70

    def test_phase_4b_not_triggered_low_confidence(self):
        """Missing panel + low confidence → still blocks."""
        log = _log()
        emissions = [
            make_emission(panel_name="code-review", confidence_score=0.50),
            make_emission(panel_name="security-review", confidence_score=0.50),
            make_emission(panel_name="threat-modeling", confidence_score=0.50),
            make_emission(panel_name="cost-analysis", confidence_score=0.50),
            make_emission(panel_name="documentation-review", confidence_score=0.50),
        ]
        profile = make_profile()
        aggregate_confidence = policy_engine.compute_weighted_confidence(emissions, profile, log)
        assert aggregate_confidence < 0.70  # Too low for Phase 4b

    def test_phase_4b_not_triggered_non_approve_verdict(self):
        """Missing panel + one panel request_changes → still blocks."""
        log = _log()
        emissions = [
            make_emission(panel_name="code-review", confidence_score=0.90, aggregate_verdict="request_changes"),
            make_emission(panel_name="security-review", confidence_score=0.90),
            make_emission(panel_name="threat-modeling", confidence_score=0.90),
            make_emission(panel_name="cost-analysis", confidence_score=0.90),
            make_emission(panel_name="documentation-review", confidence_score=0.90),
        ]
        all_approve = all(e.get("aggregate_verdict") == "approve" for e in emissions)
        assert all_approve is False  # Phase 4b should not trigger


class TestAutoMerge:
    def test_all_pass(self):
        log = _log()
        emissions = [make_emission()]
        profile = make_profile()
        result = policy_engine.evaluate_auto_merge(0.90, "low", [], emissions, True, profile, log)
        assert result is True

    def test_disabled_profile(self):
        log = _log()
        profile = make_profile(auto_merge_enabled=False)
        result = policy_engine.evaluate_auto_merge(0.90, "low", [], [], True, profile, log)
        assert result is False

    def test_fail_low_confidence(self):
        log = _log()
        emissions = [make_emission()]
        profile = make_profile()
        result = policy_engine.evaluate_auto_merge(0.70, "low", [], emissions, True, profile, log)
        assert result is False

    def test_fail_high_risk(self):
        log = _log()
        emissions = [make_emission()]
        profile = make_profile()
        result = policy_engine.evaluate_auto_merge(0.90, "high", [], emissions, True, profile, log)
        assert result is False

    def test_fail_policy_flag(self):
        log = _log()
        flags = [{"flag": "breaking_change", "severity": "high", "description": "API break"}]
        emissions = [make_emission()]
        profile = make_profile()
        result = policy_engine.evaluate_auto_merge(0.90, "low", flags, emissions, True, profile, log)
        assert result is False

    def test_fail_ci_failed(self):
        log = _log()
        emissions = [make_emission()]
        profile = make_profile()
        result = policy_engine.evaluate_auto_merge(0.90, "low", [], emissions, False, profile, log)
        assert result is False

    def test_auto_merge_passes_when_requires_human_review_but_verdict_approve(self):
        """Issue #680/#693: auto-merge should pass when panels have requires_human_review=True but aggregate_verdict=approve."""
        log = _log()
        emissions = [make_emission(requires_human_review=True, aggregate_verdict="approve")]
        profile = make_profile()
        result = policy_engine.evaluate_auto_merge(0.90, "low", [], emissions, True, profile, log)
        assert result is True

    def test_auto_merge_fails_when_requires_human_review_and_verdict_not_approve(self):
        """Issue #680/#693: auto-merge should fail when panels have requires_human_review=True and non-approve verdict."""
        log = _log()
        emissions = [make_emission(requires_human_review=True, aggregate_verdict="request_changes")]
        profile = make_profile()
        result = policy_engine.evaluate_auto_merge(0.90, "low", [], emissions, True, profile, log)
        assert result is False


# ===========================================================================
# Auto-remediate conditions
# ===========================================================================


class TestAutoRemediate:
    def test_all_pass(self):
        log = _log()
        emissions = [make_emission()]
        profile = make_profile()
        result = policy_engine.evaluate_auto_remediate(0.90, "low", [], emissions, profile, log)
        assert result is True

    def test_disabled(self):
        log = _log()
        profile = make_profile(auto_remediate_enabled=False)
        result = policy_engine.evaluate_auto_remediate(0.90, "low", [], [], profile, log)
        assert result is False

    def test_fail_risk(self):
        log = _log()
        emissions = [make_emission()]
        profile = make_profile(auto_remediate_conditions=[
            'risk_level == "low"',
        ])
        result = policy_engine.evaluate_auto_remediate(0.90, "high", [], emissions, profile, log)
        assert result is False

    def test_fail_not_remediable(self):
        log = _log()
        flags = [{"flag": "issue", "severity": "medium", "description": "test", "auto_remediable": False}]
        profile = make_profile(auto_remediate_conditions=[
            "all_policy_flags.auto_remediable == true",
        ])
        result = policy_engine.evaluate_auto_remediate(0.90, "low", flags, [], profile, log)
        assert result is False


# ===========================================================================
# Manifest generation
# ===========================================================================


class TestManifest:
    def test_structure(self):
        log = _log()
        emissions = [make_emission()]
        profile = make_profile()
        manifest = policy_engine.generate_manifest(
            emissions, profile, 0.90, "low", "auto_merge",
            "All conditions met", log, commit_sha="a" * 40,
        )
        assert "manifest_version" in manifest
        assert "manifest_id" in manifest
        assert "timestamp" in manifest
        assert "decision" in manifest
        assert manifest["decision"]["action"] == "auto_merge"
        assert manifest["aggregate_confidence"] == 0.90
        assert manifest["risk_level"] == "low"

    def test_panels_listed(self):
        log = _log()
        emissions = all_required_emissions()
        profile = make_profile()
        manifest = policy_engine.generate_manifest(
            emissions, profile, 0.90, "low", "auto_merge",
            "OK", log,
        )
        panel_names = [p["panel_name"] for p in manifest["panels_executed"]]
        assert "code-review" in panel_names
        assert "security-review" in panel_names
        assert len(panel_names) == 8

    def test_repository_context(self):
        log = _log()
        emissions = [make_emission()]
        profile = make_profile()
        manifest = policy_engine.generate_manifest(
            emissions, profile, 0.90, "low", "auto_merge", "OK", log,
            commit_sha="a" * 40, pr_number=42, repo="owner/repo-name",
        )
        assert manifest["repository"]["owner"] == "owner"
        assert manifest["repository"]["name"] == "repo-name"
        assert manifest["repository"]["commit_sha"] == "a" * 40
        assert manifest["repository"]["pr_number"] == 42


# ===========================================================================
# Emission loading exception handling (issue #237)
# ===========================================================================


class TestEmissionLoadingExceptions:
    """Issue #237: narrow exception handling in load_emissions."""

    def test_permission_error_produces_clear_message(self, tmp_path):
        """PermissionError should report file access error, not generic validation failure."""
        log = _log()
        schema = policy_engine.load_schema("panel-output.schema.json")
        # Create a file that can't be read
        bad_file = tmp_path / "unreadable.json"
        bad_file.write_text('{"valid": true}')
        bad_file.chmod(0o000)
        try:
            emissions, valid, failed = policy_engine.load_emissions(str(tmp_path), schema, log)
            assert valid is False
            assert "unreadable" in failed
            # Check that the error message mentions file access
            entries = log.entries
            fail_entries = [e for e in entries if e["result"] == "fail"]
            assert any("file access error" in e["detail"] for e in fail_entries)
        finally:
            bad_file.chmod(0o644)  # cleanup

    def test_json_decode_error_still_caught(self, tmp_path):
        """JSONDecodeError should still be caught and reported."""
        log = _log()
        schema = policy_engine.load_schema("panel-output.schema.json")
        bad_file = tmp_path / "bad.json"
        bad_file.write_text('not json')
        emissions, valid, failed = policy_engine.load_emissions(str(tmp_path), schema, log)
        assert valid is False
        assert "bad" in failed

    def test_validation_error_still_caught(self, tmp_path):
        """ValidationError should still be caught and reported."""
        log = _log()
        schema = policy_engine.load_schema("panel-output.schema.json")
        bad_file = tmp_path / "invalid.json"
        bad_file.write_text('{"panel_name": 123}')  # panel_name should be string
        emissions, valid, failed = policy_engine.load_emissions(str(tmp_path), schema, log)
        assert valid is False
        assert "invalid" in failed


# ===========================================================================
# Emission freshness and replay protection (issue #240)
# ===========================================================================


class TestEmissionFreshness:
    """Issue #240: emission freshness and replay protection."""

    def test_matching_commit_sha_no_warning(self):
        log = _log()
        emission = make_emission()
        emission["execution_context"] = {"commit_sha": "a" * 40}
        warnings = policy_engine.validate_emission_freshness(emission, "a" * 40, log)
        assert warnings == []

    def test_mismatched_commit_sha_warns(self):
        log = _log()
        emission = make_emission()
        emission["execution_context"] = {"commit_sha": "a" * 40}
        warnings = policy_engine.validate_emission_freshness(emission, "b" * 40, log)
        assert len(warnings) == 1
        assert "does not match" in warnings[0]

    def test_no_commit_sha_no_warning(self):
        """Missing commit_sha in either emission or expected should not warn."""
        log = _log()
        emission = make_emission()
        warnings = policy_engine.validate_emission_freshness(emission, "", log)
        assert warnings == []

    def test_stale_emission_warns(self):
        log = _log()
        emission = make_emission()
        from datetime import datetime, timezone, timedelta
        old_time = datetime.now(timezone.utc) - timedelta(hours=48)
        emission["timestamp"] = old_time.isoformat()
        warnings = policy_engine.validate_emission_freshness(emission, "", log)
        assert len(warnings) == 1
        assert "old" in warnings[0]

    def test_fresh_emission_no_warning(self):
        log = _log()
        emission = make_emission()
        from datetime import datetime, timezone
        emission["timestamp"] = datetime.now(timezone.utc).isoformat()
        warnings = policy_engine.validate_emission_freshness(emission, "", log)
        assert warnings == []


# ===========================================================================
# Reduced touchpoint escalation conditions (issue #242)
# ===========================================================================


class TestReducedTouchpointEscalation:
    """Tests for policy_override_requested and dismissed_finding_* escalation handlers."""

    def test_policy_override_triggers_escalation(self):
        """Emission with execution_context.policy_override_requested: true triggers escalation."""
        log = _log()
        emission = make_emission(panel_name="code-review")
        emission["execution_context"] = {"policy_override_requested": True}
        profile = make_profile(escalation_rules=[
            {"name": "policy_override", "condition": "policy_override_requested == true", "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], [emission], profile, log)
        assert result == "human_review_required"

    def test_dismissed_critical_finding_triggers_escalation(self):
        """Emission with a dismissed critical policy flag triggers escalation."""
        log = _log()
        emission = make_emission(
            panel_name="security-review",
            policy_flags=[
                {"flag": "vuln_found", "severity": "critical", "description": "CVE", "dismissed": True},
            ],
        )
        profile = make_profile(escalation_rules=[
            {"name": "dismissed_critical", "condition": 'dismissed_finding_severity in ["critical", "high"]', "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], [emission], profile, log)
        assert result == "human_review_required"

    def test_dismissed_finding_panel_match(self):
        """Dismissed finding on security-review panel triggers escalation."""
        log = _log()
        emission = make_emission(
            panel_name="security-review",
            policy_flags=[
                {"flag": "vuln_found", "severity": "high", "description": "CVE", "dismissed": True},
            ],
        )
        profile = make_profile(escalation_rules=[
            {"name": "dismissed_panel", "condition": 'dismissed_finding_panel == "security-review"', "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], [emission], profile, log)
        assert result == "human_review_required"

    def test_compound_dismissed_finding_condition(self):
        """Compound condition: dismissed_finding_severity in [...] and dismissed_finding_panel == 'security-review'."""
        log = _log()
        emission = make_emission(
            panel_name="security-review",
            policy_flags=[
                {"flag": "vuln_found", "severity": "critical", "description": "CVE", "dismissed": True},
            ],
        )
        profile = make_profile(escalation_rules=[
            {"name": "sec_dismiss", "condition": 'dismissed_finding_severity in ["critical", "high"] and dismissed_finding_panel == "security-review"', "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], [emission], profile, log)
        assert result == "human_review_required"

    def test_no_dismissed_findings_no_escalation(self):
        """No dismissed findings means no escalation trigger."""
        log = _log()
        emission = make_emission(
            panel_name="security-review",
            policy_flags=[
                {"flag": "vuln_found", "severity": "critical", "description": "CVE"},
            ],
        )
        profile = make_profile(escalation_rules=[
            {"name": "dismissed_critical", "condition": 'dismissed_finding_severity in ["critical", "high"]', "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], [emission], profile, log)
        assert result is None


# ===========================================================================
# Optional emission validation (issue #244)
# ===========================================================================


class TestOptionalEmissionValidation:
    """Issue #244: invalid optional panel emission should not block merge."""

    def _write_emission(self, directory, panel_name, content):
        """Helper to write a JSON emission file."""
        import json as _json
        fpath = directory / f"{panel_name}.json"
        fpath.write_text(_json.dumps(content))

    def _valid_emission(self, panel_name):
        """Return a valid emission dict for the given panel."""
        return make_emission(panel_name=panel_name)

    def test_invalid_optional_emission_does_not_block(self, tmp_path):
        """Malformed JSON for an optional panel should not block when all
        required panel emissions are valid."""
        import json as _json
        import os

        # Write valid emissions for all 6 required panels
        for panel in [
            "code-review", "security-review", "threat-modeling",
            "cost-analysis", "documentation-review", "data-governance-review",
        ]:
            self._write_emission(tmp_path, panel, self._valid_emission(panel))

        # Write an INVALID emission for an optional panel (not in required_panels)
        bad_file = tmp_path / "optional-panel.json"
        bad_file.write_text("not valid json at all")

        # Build a minimal profile on disk
        profile_path = tmp_path / "profile.yaml"
        import yaml as _yaml
        profile_path.write_text(_yaml.dump(make_profile()))

        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path),
            str(profile_path),
            ci_passed=True,
            log_stream=io.StringIO(),
        )

        # Should NOT block — exit_code 0 = auto_merge, 2 = human_review, 3 = remediate
        assert exit_code != 1, (
            f"Expected non-block exit code but got 1. "
            f"Decision: {manifest.get('decision', {}).get('rationale', 'unknown')}"
        )

    def test_invalid_required_emission_still_blocks(self, tmp_path):
        """Malformed JSON for a required panel must still block."""
        import json as _json
        import yaml as _yaml

        # Write valid emissions for 5 of 6 required panels
        for panel in [
            "code-review", "threat-modeling",
            "cost-analysis", "documentation-review", "data-governance-review",
        ]:
            self._write_emission(tmp_path, panel, self._valid_emission(panel))

        # Write INVALID emission for required panel security-review
        bad_file = tmp_path / "security-review.json"
        bad_file.write_text("not valid json")

        profile_path = tmp_path / "profile.yaml"
        profile_path.write_text(_yaml.dump(make_profile()))

        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path),
            str(profile_path),
            ci_passed=True,
            log_stream=io.StringIO(),
        )

        assert exit_code == 1, (
            f"Expected block (exit code 1) but got {exit_code}. "
            f"Decision: {manifest.get('decision', {}).get('rationale', 'unknown')}"
        )
        assert "security-review" in manifest["decision"]["rationale"]

    def test_load_emissions_returns_failed_panels(self, tmp_path):
        """load_emissions should return the list of panel names that failed."""
        import json as _json
        log = _log()
        schema = policy_engine.load_schema("panel-output.schema.json")

        # Write one valid emission
        self._write_emission(tmp_path, "code-review", self._valid_emission("code-review"))

        # Write two invalid emissions
        (tmp_path / "bad-panel-a.json").write_text("bad json")
        (tmp_path / "bad-panel-b.json").write_text('{"panel_name": 123}')

        emissions, all_valid, failed_panels = policy_engine.load_emissions(
            str(tmp_path), schema, log
        )

        assert all_valid is False
        assert len(emissions) == 1
        assert emissions[0]["panel_name"] == "code-review"
        assert sorted(failed_panels) == ["bad-panel-a", "bad-panel-b"]


# ===========================================================================
# find_schema_dir / load_schema
# ===========================================================================


class TestFindSchemaDir:
    def test_find_schema_dir_returns_path(self):
        result = policy_engine.find_schema_dir()
        assert result is not None
        assert isinstance(result, Path)
        assert result.is_dir()

    def test_find_schema_dir_works_from_different_cwd(self, monkeypatch):
        monkeypatch.chdir("/tmp")
        result = policy_engine.find_schema_dir()
        assert result is not None
        assert isinstance(result, Path)
        assert result.is_dir()

    def test_load_schema_loads_panel_output_schema(self):
        schema = policy_engine.load_schema("panel-output.schema.json")
        assert isinstance(schema, dict)
        assert "$schema" in schema or "type" in schema
        assert "properties" in schema


# ===========================================================================
# Dry-run mode (issue #253)
# ===========================================================================


class TestDryRun:
    """Issue #253: --dry-run flag should preview decision without side-effects."""

    def _write_emission(self, directory, panel_name, content):
        """Helper to write a JSON emission file."""
        import json as _json
        fpath = directory / f"{panel_name}.json"
        fpath.write_text(_json.dumps(content))

    def _valid_emission(self, panel_name):
        """Return a valid emission dict for the given panel."""
        return make_emission(panel_name=panel_name)

    def _setup_emissions_and_profile(self, tmp_path):
        """Write all required emissions and a default profile; return profile path."""
        import yaml as _yaml
        for panel in [
            "code-review", "security-review", "threat-modeling",
            "cost-analysis", "documentation-review", "data-governance-review",
        ]:
            self._write_emission(tmp_path, panel, self._valid_emission(panel))
        profile_path = tmp_path / "profile.yaml"
        profile_path.write_text(_yaml.dump(make_profile()))
        return str(profile_path)

    def test_dry_run_returns_exit_code_zero(self, tmp_path):
        """Dry-run must always return exit code 0."""
        profile_path = self._setup_emissions_and_profile(tmp_path)

        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path),
            profile_path,
            ci_passed=True,
            log_stream=io.StringIO(),
            dry_run=True,
        )

        assert exit_code == 0

    def test_dry_run_decision_action_is_dry_run(self, tmp_path):
        """The manifest decision action should be 'dry_run'."""
        profile_path = self._setup_emissions_and_profile(tmp_path)

        manifest, _ = policy_engine.evaluate(
            str(tmp_path),
            profile_path,
            ci_passed=True,
            log_stream=io.StringIO(),
            dry_run=True,
        )

        assert manifest["decision"]["action"] == "dry_run"
        assert "dry-run" in manifest["decision"]["rationale"].lower() or \
               "dry_run" in manifest["decision"]["rationale"].lower()

    def test_dry_run_still_computes_confidence_and_risk(self, tmp_path):
        """Dry-run should compute aggregate confidence and risk normally."""
        profile_path = self._setup_emissions_and_profile(tmp_path)

        manifest, _ = policy_engine.evaluate(
            str(tmp_path),
            profile_path,
            ci_passed=True,
            log_stream=io.StringIO(),
            dry_run=True,
        )

        assert manifest["aggregate_confidence"] > 0
        assert manifest["risk_level"] in ("negligible", "low", "medium", "high", "critical")

    def test_dry_run_prints_summary(self, tmp_path):
        """Dry-run should write a DRY RUN SUMMARY to the log stream."""
        profile_path = self._setup_emissions_and_profile(tmp_path)
        log_stream = io.StringIO()

        policy_engine.evaluate(
            str(tmp_path),
            profile_path,
            ci_passed=True,
            log_stream=log_stream,
            dry_run=True,
        )

        output = log_stream.getvalue()
        assert "DRY RUN SUMMARY" in output
        assert "Confidence:" in output
        assert "Risk:" in output

    def test_dry_run_exits_zero_even_when_would_block(self, tmp_path):
        """Even if the normal evaluation would block, dry-run returns 0."""
        import yaml as _yaml
        # Write emissions with critical risk — would normally block
        for panel in [
            "code-review", "security-review", "threat-modeling",
            "cost-analysis", "documentation-review", "data-governance-review",
        ]:
            self._write_emission(
                tmp_path, panel,
                make_emission(panel_name=panel, risk_level="critical", confidence_score=0.30),
            )
        profile_path = tmp_path / "profile.yaml"
        profile_path.write_text(_yaml.dump(make_profile()))

        manifest, exit_code = policy_engine.evaluate(
            str(tmp_path),
            str(profile_path),
            ci_passed=False,
            log_stream=io.StringIO(),
            dry_run=True,
        )

        assert exit_code == 0
        assert manifest["decision"]["action"] == "dry_run"

    def test_dry_run_includes_panel_names_in_summary(self, tmp_path):
        """The dry-run summary should list which panels were loaded."""
        profile_path = self._setup_emissions_and_profile(tmp_path)
        log_stream = io.StringIO()

        policy_engine.evaluate(
            str(tmp_path),
            profile_path,
            ci_passed=True,
            log_stream=log_stream,
            dry_run=True,
        )

        output = log_stream.getvalue()
        assert "code-review" in output
        assert "security-review" in output


# ===========================================================================
# Boundary confidence values (issue #263)
# ===========================================================================


class TestBoundaryConfidenceValues:
    """Test confidence exactly at 0.0 and 1.0 against thresholds."""

    def test_confidence_zero_fails_auto_merge(self):
        """Confidence exactly 0.0 should fail auto-merge threshold (>= 0.85)."""
        log = _log()
        emissions = [make_emission()]
        profile = make_profile()
        result = policy_engine.evaluate_auto_merge(0.0, "low", [], emissions, True, profile, log)
        assert result is False

    def test_confidence_one_passes_auto_merge(self):
        """Confidence exactly 1.0 should pass auto-merge threshold (>= 0.85)."""
        log = _log()
        emissions = [make_emission()]
        profile = make_profile()
        result = policy_engine.evaluate_auto_merge(1.0, "low", [], emissions, True, profile, log)
        assert result is True

    def test_confidence_zero_fails_auto_remediate(self):
        """Confidence exactly 0.0 should fail auto-remediate threshold (>= 0.60)."""
        log = _log()
        profile = make_profile()
        result = policy_engine.evaluate_auto_remediate(0.0, "low", [], [], profile, log)
        assert result is False

    def test_confidence_one_passes_auto_remediate(self):
        """Confidence exactly 1.0 should pass auto-remediate threshold (>= 0.60)."""
        log = _log()
        profile = make_profile()
        result = policy_engine.evaluate_auto_remediate(1.0, "low", [], [], profile, log)
        assert result is True

    def test_confidence_zero_triggers_escalation(self):
        """Confidence 0.0 should trigger escalation when threshold is < 0.70."""
        log = _log()
        profile = make_profile(escalation_rules=[
            {"name": "low_conf", "condition": "aggregate_confidence < 0.70", "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(0.0, "low", [], [], profile, log)
        assert result == "human_review_required"

    def test_confidence_one_no_escalation(self):
        """Confidence 1.0 should not trigger escalation when threshold is < 0.70."""
        log = _log()
        profile = make_profile(escalation_rules=[
            {"name": "low_conf", "condition": "aggregate_confidence < 0.70", "action": "human_review_required"}
        ])
        result, _ = policy_engine.evaluate_escalation_rules(1.0, "low", [], [], profile, log)
        assert result is None


# ===========================================================================
# Malformed YAML profile (issue #263)
# ===========================================================================


class TestMalformedYamlProfile:
    """Test that loading invalid YAML (bad syntax) is handled gracefully."""

    def test_malformed_yaml_produces_block(self, tmp_path):
        """Invalid YAML syntax in profile file should produce a block decision."""
        emissions = all_required_emissions(confidence=0.92, risk_level="low")
        emissions_dir = tmp_path / "emissions"
        emissions_dir.mkdir()
        for e in emissions:
            with open(str(emissions_dir / f"{e['panel_name']}.json"), "w") as f:
                import json
                json.dump(e, f)

        # Write invalid YAML
        profile_path = tmp_path / "bad-profile.yaml"
        profile_path.write_text(":\n  invalid: yaml: [unclosed\n  - bad: {syntax")

        manifest, exit_code = policy_engine.evaluate(
            str(emissions_dir),
            str(profile_path),
            ci_passed=True,
            log_stream=io.StringIO(),
        )
        assert exit_code == 1
        assert manifest["decision"]["action"] == "block"


# ===========================================================================
# Timestamp parsing exception (issue #263)
# ===========================================================================


class TestTimestampParsingException:
    """Test validate_emission_freshness() with malformed timestamps."""

    def test_malformed_timestamp_no_crash(self):
        """Non-parseable timestamp string should not crash, should pass freshness."""
        log = _log()
        emission = make_emission()
        emission["timestamp"] = "not-a-real-timestamp"
        warnings = policy_engine.validate_emission_freshness(emission, "", log)
        # Malformed timestamps are silently ignored (not a freshness issue)
        # Only commit_sha mismatch or stale timestamps produce warnings
        assert warnings == []

    def test_empty_timestamp_no_crash(self):
        """Empty timestamp string should not crash."""
        log = _log()
        emission = make_emission()
        emission["timestamp"] = ""
        warnings = policy_engine.validate_emission_freshness(emission, "", log)
        assert warnings == []

    def test_partial_timestamp_no_crash(self):
        """Partial timestamp (e.g. just a date) should not crash."""
        log = _log()
        emission = make_emission()
        emission["timestamp"] = "2026-02-25"
        # fromisoformat can parse date-only, but it may produce a naive datetime
        # which would fail subtraction with aware datetime. Should be caught by except.
        warnings = policy_engine.validate_emission_freshness(emission, "", log)
        # Should not crash — may or may not produce a warning depending on parse result
        assert isinstance(warnings, list)


# ===========================================================================
# Fast-track profile and change-type panel overrides
# ===========================================================================


class TestFastTrackProfileLoads:
    """Verify the fast-track.yaml profile loads and has the expected structure."""

    def test_fast_track_profile_loads(self, fast_track_profile):
        """Fast-track profile can be loaded via YAML and has required keys."""
        assert fast_track_profile["profile_name"] == "fast-track"
        assert fast_track_profile["profile_version"] == "1.0.0"

    def test_fast_track_required_panels(self, fast_track_profile):
        """Fast-track profile requires only code-review and security-review."""
        required = fast_track_profile["required_panels"]
        assert "code-review" in required
        assert "security-review" in required
        assert len(required) == 2

    def test_fast_track_security_review_always_required(self, fast_track_profile):
        """Security-review is non-negotiable in fast-track."""
        assert "security-review" in fast_track_profile["required_panels"]

    def test_fast_track_auto_merge_enabled(self, fast_track_profile):
        """Fast-track enables auto-merge with a lower confidence threshold."""
        auto_merge = fast_track_profile["auto_merge"]
        assert auto_merge["enabled"] is True
        # Confidence threshold should be 0.75 (lower than default 0.85)
        conditions = auto_merge["conditions"]
        confidence_cond = [c for c in conditions if "aggregate_confidence" in c]
        assert len(confidence_cond) == 1
        assert "0.75" in confidence_cond[0]

    def test_fast_track_trigger_conditions(self, fast_track_profile):
        """Fast-track defines trigger conditions for change type classification."""
        triggers = fast_track_profile["trigger_conditions"]["change_types"]
        assert "docs_only" in triggers
        assert "chore" in triggers
        assert "typo_fix" in triggers
        assert "test_only" in triggers

    def test_fast_track_plan_skip_condition(self, fast_track_profile):
        """Fast-track allows skipping plans for small changes (< 3 files)."""
        plan_req = fast_track_profile["plan_required"]
        assert plan_req["default"] is True
        assert plan_req["skip_when"]["files_changed_lt"] == 3

    def test_fast_track_weighting(self, fast_track_profile):
        """Fast-track weighting only covers code-review and security-review."""
        weights = fast_track_profile["weighting"]["weights"]
        assert set(weights.keys()) == {"code-review", "security-review"}

    def test_fast_track_block_rules_match_default(self, fast_track_profile, default_profile):
        """Fast-track block rules are the same as default — safety is never relaxed."""
        ft_conditions = fast_track_profile["block"]["conditions"]
        dp_conditions = default_profile["block"]["conditions"]
        assert len(ft_conditions) == len(dp_conditions)

    def test_fast_track_risk_aggregation_matches_default(self, fast_track_profile, default_profile):
        """Fast-track risk aggregation is identical to default."""
        assert fast_track_profile["risk_aggregation"] == default_profile["risk_aggregation"]


class TestFastTrackRequiredPanelCheck:
    """Verify the policy engine correctly validates emissions against fast-track panels."""

    def test_fast_track_all_required_present(self, fast_track_profile):
        """When both code-review and security-review are present, no panels are missing."""
        log = _log()
        emissions = [
            make_emission(panel_name="code-review"),
            make_emission(panel_name="security-review"),
        ]
        missing = policy_engine.check_required_panels(emissions, fast_track_profile, log)
        assert missing == []

    def test_fast_track_missing_security_review(self, fast_track_profile):
        """Missing security-review is detected even in fast-track."""
        log = _log()
        emissions = [make_emission(panel_name="code-review")]
        missing = policy_engine.check_required_panels(emissions, fast_track_profile, log)
        assert "security-review" in missing

    def test_fast_track_missing_code_review(self, fast_track_profile):
        """Missing code-review is detected in fast-track."""
        log = _log()
        emissions = [make_emission(panel_name="security-review")]
        missing = policy_engine.check_required_panels(emissions, fast_track_profile, log)
        assert "code-review" in missing


class TestPanelOverridesByChangeType:
    """Tests for panel_overrides_by_change_type in default.yaml and the engine function."""

    def test_docs_only_reduces_required_panels(self, default_profile):
        """docs_only change type reduces required panels to documentation-review + security-review."""
        log = _log()
        effective = policy_engine.get_required_panels_for_change_type(default_profile, "docs_only", log)
        assert "documentation-review" in effective
        assert "security-review" in effective
        # Should NOT require threat-modeling, cost-analysis, etc.
        assert "threat-modeling" not in effective
        assert "cost-analysis" not in effective

    def test_chore_reduces_required_panels(self, default_profile):
        """chore change type reduces required panels to code-review + security-review."""
        log = _log()
        effective = policy_engine.get_required_panels_for_change_type(default_profile, "chore", log)
        assert "code-review" in effective
        assert "security-review" in effective
        assert "threat-modeling" not in effective

    def test_test_only_requires_testing_review(self, default_profile):
        """test_only change type includes testing-review, code-review, and security-review."""
        log = _log()
        effective = policy_engine.get_required_panels_for_change_type(default_profile, "test_only", log)
        assert "testing-review" in effective
        assert "code-review" in effective
        assert "security-review" in effective

    def test_unknown_change_type_returns_base_required(self, default_profile):
        """Unknown change type falls back to the full required_panels list."""
        log = _log()
        effective = policy_engine.get_required_panels_for_change_type(default_profile, "unknown_type", log)
        assert effective == default_profile["required_panels"]

    def test_no_change_type_returns_base_required(self, default_profile):
        """None change type returns the full required_panels list."""
        log = _log()
        effective = policy_engine.get_required_panels_for_change_type(default_profile, None, log)
        assert effective == default_profile["required_panels"]

    def test_empty_change_type_returns_base_required(self, default_profile):
        """Empty string change type returns the full required_panels list."""
        log = _log()
        effective = policy_engine.get_required_panels_for_change_type(default_profile, "", log)
        assert effective == default_profile["required_panels"]

    def test_security_review_always_enforced(self):
        """If an override omits security-review, the function adds it automatically."""
        log = _log()
        profile = make_profile()
        # Add an override that deliberately omits security-review
        profile["panel_overrides_by_change_type"] = {
            "docs_only": {
                "required_panels": ["documentation-review"],
                "optional_panels": [],
            }
        }
        effective = policy_engine.get_required_panels_for_change_type(profile, "docs_only", log)
        assert "security-review" in effective
        assert "documentation-review" in effective

    def test_security_review_not_duplicated(self, default_profile):
        """If the override already includes security-review, it is not duplicated."""
        log = _log()
        effective = policy_engine.get_required_panels_for_change_type(default_profile, "docs_only", log)
        assert effective.count("security-review") == 1

    def test_profile_without_overrides_section(self):
        """Profile without panel_overrides_by_change_type returns base required panels."""
        log = _log()
        profile = make_profile()
        # make_profile does not include panel_overrides_by_change_type
        effective = policy_engine.get_required_panels_for_change_type(profile, "docs_only", log)
        assert effective == profile["required_panels"]

    def test_override_log_entries(self, default_profile):
        """The function records log entries when applying overrides."""
        log = _log()
        policy_engine.get_required_panels_for_change_type(default_profile, "docs_only", log)
        rule_ids = [e["rule_id"] for e in log.entries]
        assert "change_type_override" in rule_ids

    def test_docs_only_check_required_with_override(self, default_profile):
        """End-to-end: docs_only override + check_required_panels passes with reduced panels."""
        log = _log()
        effective_panels = policy_engine.get_required_panels_for_change_type(default_profile, "docs_only", log)
        # Build a profile with the overridden required panels
        overridden_profile = dict(default_profile)
        overridden_profile["required_panels"] = effective_panels
        # Provide emissions for only the overridden required panels
        emissions = [make_emission(panel_name=p) for p in effective_panels]
        missing = policy_engine.check_required_panels(emissions, overridden_profile, log)
        assert missing == []


# ===========================================================================
# FinOps review panel (issue #455)
# ===========================================================================


class TestFinOpsPanel:
    """Test FinOps review panel integration with policy engine."""

    def test_finops_review_in_default_required_panels(self, default_profile):
        """finops-review must be in the default profile's required_panels."""
        required = default_profile.get("required_panels", [])
        assert "finops-review" in required

    def test_finops_review_in_fin_pii_high_required_panels(self, fin_pii_high_profile):
        """finops-review must be in the fin_pii_high profile's required_panels."""
        required = fin_pii_high_profile.get("required_panels", [])
        assert "finops-review" in required

    def test_finops_review_in_infrastructure_critical_required_panels(self, infrastructure_profile):
        """finops-review must be in the infrastructure_critical profile's required_panels."""
        required = infrastructure_profile.get("required_panels", [])
        assert "finops-review" in required

    def test_finops_review_in_reduced_touchpoint_required_panels(self, reduced_touchpoint_profile):
        """finops-review must be in the reduced_touchpoint profile's required_panels."""
        required = reduced_touchpoint_profile.get("required_panels", [])
        assert "finops-review" in required

    def test_finops_review_weight_in_default_profile(self, default_profile):
        """finops-review must have a weight in the default profile's weighting."""
        weights = default_profile.get("weighting", {}).get("weights", {})
        assert "finops-review" in weights
        assert weights["finops-review"] == 0.02

    def test_destruction_recommended_blocks_auto_merge(self):
        """An emission with destruction_recommended=true must block via block conditions."""
        log = _log()
        emissions = [
            make_emission(
                panel_name="finops-review",
                destruction_recommended=True,
                requires_human_approval=True,
            )
        ]
        profile = make_profile(
            block_conditions=[
                {
                    "description": "Destruction recommended by FinOps review requires human approval.",
                    "condition": "destruction_recommended == true",
                }
            ]
        )
        blocked, reason = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], True, profile, log, emissions=emissions
        )
        assert blocked is True
        assert "destruction" in reason.lower() or "Destruction" in reason

    def test_no_destruction_does_not_block(self):
        """An emission without destruction_recommended should not trigger destruction block."""
        log = _log()
        emissions = [
            make_emission(
                panel_name="finops-review",
                destruction_recommended=False,
                requires_human_approval=False,
            )
        ]
        profile = make_profile(
            block_conditions=[
                {
                    "description": "Destruction recommended by FinOps review requires human approval.",
                    "condition": "destruction_recommended == true",
                }
            ]
        )
        blocked, _ = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], True, profile, log, emissions=emissions
        )
        assert blocked is False

    def test_requires_human_approval_triggers_human_review(self):
        """An emission with requires_human_review=true and non-approve verdict should trigger escalation."""
        log = _log()
        emissions = [
            make_emission(
                panel_name="finops-review",
                requires_human_review=True,
                aggregate_verdict="request_changes",
            )
        ]
        profile = make_profile()
        result, reason = policy_engine.evaluate_escalation_rules(
            0.90, "low", [], emissions, profile, log
        )
        assert result == "human_review_required"
        assert "finops-review" in reason

    def test_destruction_block_condition_in_default_profile(self, default_profile):
        """Default profile must contain a block condition for destruction_recommended."""
        block_conditions = default_profile.get("block", {}).get("conditions", [])
        destruction_conditions = [
            c for c in block_conditions
            if "destruction_recommended" in c.get("condition", "")
        ]
        assert len(destruction_conditions) >= 1

    def test_finops_emission_baseline_exists(self, emissions_dir):
        """Baseline emission file for finops-review must exist."""
        emission_path = emissions_dir / "finops-review.json"
        assert emission_path.exists(), f"Missing baseline emission: {emission_path}"

    def test_finops_emission_baseline_valid(self, emissions_dir, panel_schema):
        """Baseline emission for finops-review must validate against schema."""
        import json as _json
        from jsonschema import validate as _validate
        emission_path = emissions_dir / "finops-review.json"
        with open(emission_path) as f:
            emission = _json.load(f)
        _validate(instance=emission, schema=panel_schema)

    def test_finops_emission_baseline_destruction_fields(self, emissions_dir):
        """Baseline emission must include destruction_recommended and requires_human_approval."""
        import json as _json
        emission_path = emissions_dir / "finops-review.json"
        with open(emission_path) as f:
            emission = _json.load(f)
        assert "destruction_recommended" in emission
        assert "requires_human_approval" in emission
        assert emission["destruction_recommended"] is False
        assert emission["requires_human_approval"] is False


# ===========================================================================
# Copilot findings block condition
# ===========================================================================


class TestCopilotFindingsBlock:
    """Tests for copilot_findings_unresolved == true block condition."""

    def test_copilot_unresolved_findings_blocks(self):
        """Unresolved medium+ Copilot findings must trigger block."""
        log = _log()
        emissions = [
            make_emission(
                panel_name="copilot-review",
                findings=[{
                    "persona": "copilot-review/ci-precheck",
                    "verdict": "request_changes",
                    "confidence": 0.85,
                    "rationale": "3 unresolved findings",
                    "findings_count": {"critical": 0, "high": 1, "medium": 2, "low": 5},
                }],
            )
        ]
        profile = make_profile(
            block_conditions=[{
                "description": "Unresolved Copilot findings (medium+) block auto-merge.",
                "condition": "copilot_findings_unresolved == true",
            }]
        )
        blocked, reason = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], True, profile, log, emissions=emissions
        )
        assert blocked is True
        assert "copilot" in reason.lower() or "Copilot" in reason

    def test_copilot_zero_findings_does_not_block(self):
        """Zero medium+ Copilot findings should not trigger block."""
        log = _log()
        emissions = [
            make_emission(
                panel_name="copilot-review",
                findings=[{
                    "persona": "copilot-review/ci-precheck",
                    "verdict": "approve",
                    "confidence": 0.85,
                    "rationale": "No findings",
                    "findings_count": {"critical": 0, "high": 0, "medium": 0, "low": 3},
                }],
            )
        ]
        profile = make_profile(
            block_conditions=[{
                "description": "Unresolved Copilot findings (medium+) block auto-merge.",
                "condition": "copilot_findings_unresolved == true",
            }]
        )
        blocked, _ = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], True, profile, log, emissions=emissions
        )
        assert blocked is False

    def test_copilot_no_emission_does_not_block(self):
        """Missing copilot-review emission should not trigger copilot block condition."""
        log = _log()
        emissions = [make_emission(panel_name="code-review")]
        profile = make_profile(
            block_conditions=[{
                "description": "Unresolved Copilot findings (medium+) block auto-merge.",
                "condition": "copilot_findings_unresolved == true",
            }]
        )
        blocked, _ = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], True, profile, log, emissions=emissions
        )
        assert blocked is False

    def test_copilot_critical_only_blocks(self):
        """Critical-only Copilot findings must trigger block."""
        log = _log()
        emissions = [
            make_emission(
                panel_name="copilot-review",
                findings=[{
                    "persona": "copilot-review/ci-precheck",
                    "verdict": "request_changes",
                    "confidence": 0.85,
                    "rationale": "1 critical finding",
                    "findings_count": {"critical": 1, "high": 0, "medium": 0, "low": 0},
                }],
            )
        ]
        profile = make_profile(
            block_conditions=[{
                "description": "Unresolved Copilot findings (medium+) block auto-merge.",
                "condition": "copilot_findings_unresolved == true",
            }]
        )
        blocked, _ = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], True, profile, log, emissions=emissions
        )
        assert blocked is True

    def test_copilot_block_condition_in_default_profile(self, default_profile):
        """Default profile must contain a block condition for copilot_findings_unresolved."""
        block_conditions = default_profile.get("block", {}).get("conditions", [])
        copilot_conditions = [
            c for c in block_conditions
            if "copilot_findings_unresolved" in c.get("condition", "")
        ]
        assert len(copilot_conditions) >= 1

    def test_copilot_is_required_panel_in_default_profile(self, default_profile):
        """copilot-review must be in the default profile required_panels."""
        assert "copilot-review" in default_profile.get("required_panels", [])

    def test_evaluate_block_condition_directly(self):
        """Direct _evaluate_block_condition call for copilot findings."""
        emissions = [
            make_emission(
                panel_name="copilot-review",
                findings=[{
                    "persona": "copilot-review/ci-precheck",
                    "verdict": "request_changes",
                    "confidence": 0.85,
                    "rationale": "findings present",
                    "findings_count": {"critical": 0, "high": 2, "medium": 1, "low": 0},
                }],
            )
        ]
        result = policy_engine._evaluate_block_condition(
            "copilot_findings_unresolved == true",
            0.90, "low", [],
            emissions=emissions,
        )
        assert result is True

    def test_evaluate_block_sub_condition_directly(self):
        """Direct _evaluate_block_sub_condition call for copilot findings."""
        emissions = [
            make_emission(
                panel_name="copilot-review",
                findings=[{
                    "persona": "copilot-review/ci-precheck",
                    "verdict": "request_changes",
                    "confidence": 0.85,
                    "rationale": "findings present",
                    "findings_count": {"critical": 0, "high": 0, "medium": 3, "low": 0},
                }],
            )
        ]
        result = policy_engine._evaluate_block_sub_condition(
            "copilot_findings_unresolved == true",
            0.90, "low", [],
            emissions=emissions,
        )
        assert result is True


# ===========================================================================
# Dependabot alerts block condition
# ===========================================================================


class TestDependabotAlertsBlock:
    """Tests for dependabot_alerts_open == true block condition."""

    def test_dependabot_open_alerts_blocks(self):
        """Open critical/high Dependabot alerts must trigger block."""
        log = _log()
        emissions = [
            make_emission(
                panel_name="dependabot-review",
                findings=[{
                    "persona": "dependabot-review/ci-precheck",
                    "verdict": "request_changes",
                    "confidence": 0.90,
                    "rationale": "2 open alerts",
                    "findings_count": {"critical": 1, "high": 1},
                }],
            )
        ]
        profile = make_profile(
            block_conditions=[{
                "description": "Open Dependabot alerts (critical/high) block auto-merge.",
                "condition": "dependabot_alerts_open == true",
            }]
        )
        blocked, reason = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], True, profile, log, emissions=emissions
        )
        assert blocked is True
        assert "dependabot" in reason.lower() or "Dependabot" in reason

    def test_dependabot_zero_alerts_does_not_block(self):
        """Zero critical/high Dependabot alerts should not trigger block."""
        log = _log()
        emissions = [
            make_emission(
                panel_name="dependabot-review",
                findings=[{
                    "persona": "dependabot-review/ci-precheck",
                    "verdict": "approve",
                    "confidence": 0.90,
                    "rationale": "No open alerts",
                    "findings_count": {"critical": 0, "high": 0},
                }],
            )
        ]
        profile = make_profile(
            block_conditions=[{
                "description": "Open Dependabot alerts (critical/high) block auto-merge.",
                "condition": "dependabot_alerts_open == true",
            }]
        )
        blocked, _ = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], True, profile, log, emissions=emissions
        )
        assert blocked is False

    def test_dependabot_no_emission_does_not_block(self):
        """Missing dependabot-review emission should not trigger dependabot block."""
        log = _log()
        emissions = [make_emission(panel_name="code-review")]
        profile = make_profile(
            block_conditions=[{
                "description": "Open Dependabot alerts (critical/high) block auto-merge.",
                "condition": "dependabot_alerts_open == true",
            }]
        )
        blocked, _ = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], True, profile, log, emissions=emissions
        )
        assert blocked is False

    def test_dependabot_critical_only_blocks(self):
        """Critical-only Dependabot alerts must trigger block."""
        log = _log()
        emissions = [
            make_emission(
                panel_name="dependabot-review",
                findings=[{
                    "persona": "dependabot-review/ci-precheck",
                    "verdict": "request_changes",
                    "confidence": 0.90,
                    "rationale": "1 critical alert",
                    "findings_count": {"critical": 1, "high": 0},
                }],
            )
        ]
        profile = make_profile(
            block_conditions=[{
                "description": "Open Dependabot alerts (critical/high) block auto-merge.",
                "condition": "dependabot_alerts_open == true",
            }]
        )
        blocked, _ = policy_engine.evaluate_block_conditions(
            0.90, "low", [], [], True, profile, log, emissions=emissions
        )
        assert blocked is True

    def test_dependabot_block_condition_in_default_profile(self, default_profile):
        """Default profile must contain a block condition for dependabot_alerts_open."""
        block_conditions = default_profile.get("block", {}).get("conditions", [])
        dependabot_conditions = [
            c for c in block_conditions
            if "dependabot_alerts_open" in c.get("condition", "")
        ]
        assert len(dependabot_conditions) >= 1

    def test_evaluate_block_condition_directly(self):
        """Direct _evaluate_block_condition call for dependabot alerts."""
        emissions = [
            make_emission(
                panel_name="dependabot-review",
                findings=[{
                    "persona": "dependabot-review/ci-precheck",
                    "verdict": "request_changes",
                    "confidence": 0.90,
                    "rationale": "alerts present",
                    "findings_count": {"critical": 0, "high": 3},
                }],
            )
        ]
        result = policy_engine._evaluate_block_condition(
            "dependabot_alerts_open == true",
            0.90, "low", [],
            emissions=emissions,
        )
        assert result is True

    def test_evaluate_block_sub_condition_directly(self):
        """Direct _evaluate_block_sub_condition call for dependabot alerts."""
        emissions = [
            make_emission(
                panel_name="dependabot-review",
                findings=[{
                    "persona": "dependabot-review/ci-precheck",
                    "verdict": "request_changes",
                    "confidence": 0.90,
                    "rationale": "alerts present",
                    "findings_count": {"critical": 2, "high": 0},
                }],
            )
        ]
        result = policy_engine._evaluate_block_sub_condition(
            "dependabot_alerts_open == true",
            0.90, "low", [],
            emissions=emissions,
        )
        assert result is True
