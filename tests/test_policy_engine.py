"""Unit tests for every evaluation function in the policy engine."""

import io
import pytest

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
        # Remove the last emission
        emissions = emissions[:-1]
        profile = make_profile()
        missing = policy_engine.check_required_panels(emissions, profile, log)
        assert len(missing) == 1
        assert "data-governance-review" in missing


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
        log = _log()
        emissions = [make_emission(requires_human_review=True)]
        profile = make_profile()
        result, _ = policy_engine.evaluate_escalation_rules(0.90, "low", [], emissions, profile, log)
        assert result == "human_review_required"

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
            make_emission(panel_name="documentation-review", confidence_score=0.90),
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
        assert len(panel_names) == 6

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
            emissions, valid = policy_engine.load_emissions(str(tmp_path), schema, log)
            assert valid is False
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
        emissions, valid = policy_engine.load_emissions(str(tmp_path), schema, log)
        assert valid is False

    def test_validation_error_still_caught(self, tmp_path):
        """ValidationError should still be caught and reported."""
        log = _log()
        schema = policy_engine.load_schema("panel-output.schema.json")
        bad_file = tmp_path / "invalid.json"
        bad_file.write_text('{"panel_name": 123}')  # panel_name should be string
        emissions, valid = policy_engine.load_emissions(str(tmp_path), schema, log)
        assert valid is False
