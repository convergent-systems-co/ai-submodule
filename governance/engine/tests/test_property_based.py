"""Property-based tests for policy engine condition parsers.

Uses Hypothesis to fuzz all 5 condition evaluator functions and 2 utility
helpers with random string input.  Any unhandled exception is a test failure.
"""

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from conftest import policy_engine

# ---------------------------------------------------------------------------
# Aliases for the functions under test
# ---------------------------------------------------------------------------
_evaluate_block_sub_condition = policy_engine._evaluate_block_sub_condition
_evaluate_escalation_sub_condition = policy_engine._evaluate_escalation_sub_condition
_evaluate_auto_merge_condition = policy_engine._evaluate_auto_merge_condition
_evaluate_auto_remediate_condition = policy_engine._evaluate_auto_remediate_condition
_evaluate_compound_block_condition = policy_engine._evaluate_compound_block_condition
_extract_list = policy_engine._extract_list
_extract_comparison = policy_engine._extract_comparison

# Also test the top-level dispatchers that may do their own parsing
_evaluate_block_condition = policy_engine._evaluate_block_condition
_evaluate_escalation_condition = policy_engine._evaluate_escalation_condition

# ---------------------------------------------------------------------------
# Shared defaults — safe values for non-condition parameters
# ---------------------------------------------------------------------------
_CONF = 0.85
_RISK = "low"
_FLAGS: list = []
_EMISSIONS: list = []
_CI = True

# Flags with data — forces iteration paths like f["flag"].startswith(...)
_FLAGS_WITH_DATA = [{"flag": "test_flag", "severity": "low", "auto_remediable": True}]

# Emissions with data — forces paths that iterate over emissions
_EMISSIONS_WITH_DATA = [
    {
        "panel_name": "code-review",
        "aggregate_verdict": "approve",
        "requires_human_review": False,
        "policy_flags": [{"flag": "test", "severity": "low", "dismissed": False}],
    }
]

# ---------------------------------------------------------------------------
# Strategies — prefixed strings that force deeper code paths
# ---------------------------------------------------------------------------

# Condition prefixes that trigger specific branches containing split('"')[1]
# or float() conversions.  Appending random text exercises the parser edge.
_block_prefixes = [
    "aggregate_confidence <",
    "aggregate_confidence >=",
    "any_policy_flag ==",
    "any_policy_flag_severity ==",
    'any_policy_flag starts_with',
    "panel_missing(",
    "auto_remediable",
]

_escalation_prefixes = [
    "aggregate_confidence <",
    "aggregate_confidence >=",
    "risk_level ==",
    "risk_level in",
    "any_policy_flag_severity in",
    'any_policy_flag starts_with',
    "panel_disagreement",
    "policy_override_requested",
    "dismissed_finding_severity in",
    "dismissed_finding_panel ==",
]

_auto_merge_prefixes = [
    "aggregate_confidence >=",
    "risk_level in",
    "no_policy_flags_severity in",
    "all_panel_verdicts",
    "requires_human_review",
    "ci_checks_passed",
]

_auto_remediate_prefixes = [
    "risk_level ==",
    "risk_level in",
    "auto_remediable",
    "aggregate_confidence >=",
    "no_policy_flag",
]


def _prefixed_text(prefixes):
    """Strategy: pick a known prefix then append random text."""
    return st.one_of(
        st.sampled_from(prefixes).flatmap(lambda p: st.text().map(lambda t: p + t)),
        st.text(),  # also test fully random input
    )


# ===========================================================================
# Property-based fuzz tests — evaluator functions
# ===========================================================================


class TestFuzzBlockSubCondition:
    """_evaluate_block_sub_condition must not raise on arbitrary text."""

    @given(cond=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_random_text_does_not_crash(self, cond):
        result = _evaluate_block_sub_condition(cond, _CONF, _RISK, _FLAGS)
        assert result is True or result is False or result is None

    @given(cond=_prefixed_text(_block_prefixes))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_prefixed_text_does_not_crash(self, cond):
        result = _evaluate_block_sub_condition(
            cond, _CONF, _RISK, _FLAGS_WITH_DATA,
        )
        assert result is True or result is False or result is None


class TestFuzzEscalationSubCondition:
    """_evaluate_escalation_sub_condition must not raise on arbitrary text."""

    @given(cond=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_random_text_does_not_crash(self, cond):
        result = _evaluate_escalation_sub_condition(
            cond, _CONF, _RISK, _FLAGS, _EMISSIONS,
        )
        assert result is True or result is False or result is None

    @given(cond=_prefixed_text(_escalation_prefixes))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_prefixed_text_does_not_crash(self, cond):
        result = _evaluate_escalation_sub_condition(
            cond, _CONF, _RISK, _FLAGS_WITH_DATA, _EMISSIONS_WITH_DATA,
        )
        assert result is True or result is False or result is None


class TestFuzzAutoMergeCondition:
    """_evaluate_auto_merge_condition must not raise on arbitrary text."""

    @given(cond=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_random_text_does_not_crash(self, cond):
        result = _evaluate_auto_merge_condition(
            cond, _CONF, _RISK, _FLAGS, _EMISSIONS, _CI,
        )
        assert result is True or result is False

    @given(cond=_prefixed_text(_auto_merge_prefixes))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_prefixed_text_does_not_crash(self, cond):
        result = _evaluate_auto_merge_condition(
            cond, _CONF, _RISK, _FLAGS_WITH_DATA, _EMISSIONS_WITH_DATA, _CI,
        )
        assert result is True or result is False


class TestFuzzAutoRemediateCondition:
    """_evaluate_auto_remediate_condition must not raise on arbitrary text."""

    @given(cond=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_random_text_does_not_crash(self, cond):
        result = _evaluate_auto_remediate_condition(
            cond, _CONF, _RISK, _FLAGS, _EMISSIONS,
        )
        assert result is True or result is False

    @given(cond=_prefixed_text(_auto_remediate_prefixes))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_prefixed_text_does_not_crash(self, cond):
        result = _evaluate_auto_remediate_condition(
            cond, _CONF, _RISK, _FLAGS_WITH_DATA, _EMISSIONS_WITH_DATA,
        )
        assert result is True or result is False


class TestFuzzCompoundBlockCondition:
    """_evaluate_compound_block_condition must not raise on arbitrary text."""

    @given(cond=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_random_text_does_not_crash(self, cond):
        result = _evaluate_compound_block_condition(
            cond, _CONF, _RISK, _FLAGS,
        )
        assert result is True or result is False

    @given(cond=_prefixed_text(_block_prefixes))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_prefixed_text_does_not_crash(self, cond):
        result = _evaluate_compound_block_condition(
            cond, _CONF, _RISK, _FLAGS_WITH_DATA,
        )
        assert result is True or result is False


class TestFuzzBlockCondition:
    """Top-level _evaluate_block_condition (dispatches to compound/simple)."""

    @given(cond=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_random_text_does_not_crash(self, cond):
        result = _evaluate_block_condition(cond, _CONF, _RISK, _FLAGS)
        assert result is True or result is False

    @given(cond=_prefixed_text(_block_prefixes))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_prefixed_text_does_not_crash(self, cond):
        result = _evaluate_block_condition(
            cond, _CONF, _RISK, _FLAGS_WITH_DATA,
        )
        assert result is True or result is False


class TestFuzzEscalationCondition:
    """Top-level _evaluate_escalation_condition (dispatches to compound/simple)."""

    @given(cond=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_random_text_does_not_crash(self, cond):
        result = _evaluate_escalation_condition(
            cond, _CONF, _RISK, _FLAGS, _EMISSIONS,
        )
        assert result is True or result is False

    @given(cond=_prefixed_text(_escalation_prefixes))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_prefixed_text_does_not_crash(self, cond):
        result = _evaluate_escalation_condition(
            cond, _CONF, _RISK, _FLAGS_WITH_DATA, _EMISSIONS_WITH_DATA,
        )
        assert result is True or result is False


# ===========================================================================
# Property-based fuzz tests — utility helpers
# ===========================================================================


class TestFuzzExtractList:
    """_extract_list must not raise on arbitrary text."""

    @given(cond=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_random_text_does_not_crash(self, cond):
        result = _extract_list(cond)
        assert isinstance(result, list)


class TestFuzzExtractComparison:
    """_extract_comparison must not raise on arbitrary text."""

    @given(cond=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_random_text_does_not_crash(self, cond):
        op, threshold = _extract_comparison(cond)
        assert isinstance(op, str)
        assert isinstance(threshold, (int, float))


# ===========================================================================
# Deterministic edge-case tests — _extract_list
# ===========================================================================


class TestExtractListEdgeCases:
    """Targeted edge cases that Hypothesis might not generate reliably."""

    def test_empty_string(self):
        assert _extract_list("") == []

    def test_no_brackets(self):
        assert _extract_list("risk_level low") == []

    def test_no_quotes(self):
        assert _extract_list("risk_level in [low, medium]") == []

    def test_unbalanced_quotes(self):
        # Single quote never closes — regex should not match
        result = _extract_list('risk_level in ["low')
        # Acceptable: returns partial or empty — must not crash
        assert isinstance(result, list)

    def test_unicode_values(self):
        result = _extract_list('field in ["\u00e9\u00e0\u00fc", "\u00f1"]')
        assert result == ["\u00e9\u00e0\u00fc", "\u00f1"]

    def test_nested_brackets(self):
        result = _extract_list('field in [["a"], ["b"]]')
        assert isinstance(result, list)

    def test_empty_brackets(self):
        result = _extract_list('field in []')
        assert result == []

    def test_single_quotes_ignored(self):
        # _extract_list only matches double-quoted strings
        result = _extract_list("field in ['a', 'b']")
        assert result == []

    def test_escaped_quotes(self):
        result = _extract_list(r'field in ["a\"b"]')
        assert isinstance(result, list)

    def test_very_long_input(self):
        long_input = 'field in ["' + "x" * 10000 + '"]'
        result = _extract_list(long_input)
        assert isinstance(result, list)
        assert len(result) == 1


# ===========================================================================
# Deterministic edge-case tests — _extract_comparison
# ===========================================================================


class TestExtractComparisonEdgeCases:
    """Targeted edge cases for _extract_comparison."""

    def test_empty_string(self):
        op, threshold = _extract_comparison("")
        assert op == ">="
        assert threshold == 0

    def test_no_operator(self):
        op, threshold = _extract_comparison("count(panel_risk) something")
        assert op == ">="
        assert threshold == 0

    def test_valid_gte(self):
        op, threshold = _extract_comparison('count(panel_risk == "high") >= 2')
        assert op == ">="
        assert threshold == 2

    def test_valid_eq(self):
        op, threshold = _extract_comparison('count(panel_risk == "high") == 1')
        assert op == "=="
        assert threshold == 1

    def test_valid_lt(self):
        op, threshold = _extract_comparison('count(foo) < 5')
        assert op == "<"
        assert threshold == 5

    def test_non_numeric_threshold(self):
        # No numeric value after operator — regex won't match
        op, threshold = _extract_comparison('count(foo) >= abc')
        assert op == ">="
        assert threshold == 0

    def test_multiple_operators(self):
        # Should match the first operator after a closing paren
        op, threshold = _extract_comparison('count(x >= 1) >= 3')
        assert op == ">="
        # The regex looks for ) then op then digits — should match >= 3
        assert threshold == 3

    def test_unicode_input(self):
        op, threshold = _extract_comparison('\u00e9\u00e0\u00fc\u00f1')
        assert op == ">="
        assert threshold == 0

    def test_very_long_input(self):
        long_input = "count(" + "x" * 10000 + ") >= 99"
        op, threshold = _extract_comparison(long_input)
        assert op == ">="
        assert threshold == 99
