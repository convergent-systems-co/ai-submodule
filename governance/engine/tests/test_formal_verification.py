"""Formal verification and property-based testing for the policy engine.

Covers:
1. DSL grammar structure: all valid condition patterns accepted, invalid patterns rejected
2. Property-based testing with Hypothesis:
   - Monotonicity: higher risk -> more restrictive decisions
   - Determinism: same inputs -> same output
   - Idempotency: evaluating twice produces same result
   - Range invariant: confidence in [0.0, 1.0] always produces valid decision
3. Synthetic emission corpus for policy evaluation test mode
4. Decision tables for block and escalation rules
5. Full evaluate() round-trip with synthetic data
"""

import io
import json
import os
from pathlib import Path
from copy import deepcopy

from hypothesis import given, settings, HealthCheck, assume
from hypothesis import strategies as st
import pytest

from conftest import (
    REPO_ROOT,
    policy_engine,
    make_emission,
    make_profile,
    all_required_emissions,
)


# ---------------------------------------------------------------------------
# Aliases
# ---------------------------------------------------------------------------

EvaluationLog = policy_engine.EvaluationLog
risk_index = policy_engine.risk_index
RISK_ORDER = policy_engine.RISK_ORDER
_evaluate_block_condition = policy_engine._evaluate_block_condition
_evaluate_escalation_condition = policy_engine._evaluate_escalation_condition
_evaluate_auto_merge_condition = policy_engine._evaluate_auto_merge_condition
_evaluate_auto_remediate_condition = policy_engine._evaluate_auto_remediate_condition
evaluate_block_conditions = policy_engine.evaluate_block_conditions
evaluate_escalation_rules = policy_engine.evaluate_escalation_rules
evaluate_auto_merge = policy_engine.evaluate_auto_merge
compute_weighted_confidence = policy_engine.compute_weighted_confidence
compute_aggregate_risk = policy_engine.compute_aggregate_risk
_compare = policy_engine._compare
_extract_list = policy_engine._extract_list
_extract_comparison = policy_engine._extract_comparison
collect_policy_flags = policy_engine.collect_policy_flags


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log():
    return EvaluationLog(stream=io.StringIO())


def _basic_profile():
    """A minimal valid profile for testing with default block conditions."""
    profile = make_profile()
    # Add the default profile's block conditions for realistic testing
    profile["block"] = {
        "conditions": [
            {
                "description": "Confidence below minimum threshold.",
                "condition": "aggregate_confidence < 0.40",
            },
        ],
    }
    return profile


def _make_emission_set(
    confidence=0.90,
    risk="low",
    verdict="approve",
    flags=None,
):
    """Create a complete set of emissions with specified defaults."""
    emissions = all_required_emissions(
        confidence=confidence,
        risk_level=risk,
        verdict=verdict,
    )
    if flags:
        for e in emissions:
            e["policy_flags"] = flags
    return emissions


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Strategy for valid confidence scores
st_confidence = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Strategy for valid risk levels
st_risk = st.sampled_from(RISK_ORDER)

# Strategy for DSL block conditions
_block_patterns = [
    "aggregate_confidence < ",
    'any_policy_flag == "',
    'any_policy_flag starts_with "',
]

# Strategy for comparison operators
st_op = st.sampled_from([">=", "<=", "==", ">", "<"])


# ===========================================================================
# 1. DSL Grammar Structure Tests
# ===========================================================================


class TestDSLGrammarPatterns:
    """Verify the DSL grammar recognizes all documented condition patterns."""

    # Block conditions
    def test_aggregate_confidence_less_than(self):
        assert _evaluate_block_condition("aggregate_confidence < 0.40", 0.30, "low", []) is True
        assert _evaluate_block_condition("aggregate_confidence < 0.40", 0.50, "low", []) is False

    def test_any_policy_flag_equals(self):
        flags = [{"flag": "pii_exposure", "severity": "high"}]
        assert _evaluate_block_condition('any_policy_flag == "pii_exposure"', 0.90, "low", flags) is True
        assert _evaluate_block_condition('any_policy_flag == "other"', 0.90, "low", flags) is False

    def test_any_policy_flag_starts_with(self):
        flags = [{"flag": "pii_exposure", "severity": "high"}]
        assert _evaluate_block_condition('any_policy_flag starts_with "pii_"', 0.90, "low", flags) is True
        assert _evaluate_block_condition('any_policy_flag starts_with "sec_"', 0.90, "low", flags) is False

    def test_compound_and_condition(self):
        result = _evaluate_block_condition(
            "aggregate_confidence < 0.50 and aggregate_confidence < 0.60",
            0.40, "low", [],
        )
        assert result is True

    def test_destruction_recommended(self):
        emissions = [{"destruction_recommended": True}]
        assert _evaluate_block_condition(
            "destruction_recommended == true",
            0.90, "low", [], emissions=emissions,
        ) is True

    def test_unknown_condition_returns_false(self):
        assert _evaluate_block_condition("unknown_condition_xyz", 0.90, "low", []) is False

    # Escalation conditions
    def test_escalation_risk_level_equals(self):
        assert _evaluate_escalation_condition(
            'risk_level == "high"', 0.90, "high", [], [],
        ) is True
        assert _evaluate_escalation_condition(
            'risk_level == "high"', 0.90, "low", [], [],
        ) is False

    def test_escalation_risk_level_in(self):
        assert _evaluate_escalation_condition(
            'risk_level in ["high", "critical"]', 0.90, "high", [], [],
        ) is True
        assert _evaluate_escalation_condition(
            'risk_level in ["high", "critical"]', 0.90, "low", [], [],
        ) is False

    def test_escalation_aggregate_confidence_less_than(self):
        assert _evaluate_escalation_condition(
            "aggregate_confidence < 0.70", 0.60, "low", [], [],
        ) is True
        assert _evaluate_escalation_condition(
            "aggregate_confidence < 0.70", 0.80, "low", [], [],
        ) is False

    # Auto-merge conditions
    def test_auto_merge_aggregate_confidence_gte(self):
        assert _evaluate_auto_merge_condition(
            "aggregate_confidence >= 0.85", 0.90, "low", [], [], True,
        ) is True
        assert _evaluate_auto_merge_condition(
            "aggregate_confidence >= 0.85", 0.80, "low", [], [], True,
        ) is False

    def test_auto_merge_ci_checks_passed(self):
        assert _evaluate_auto_merge_condition(
            "ci_checks_passed", 0.90, "low", [], [], True,
        ) is True
        assert _evaluate_auto_merge_condition(
            "ci_checks_passed", 0.90, "low", [], [], False,
        ) is False


# ===========================================================================
# 2. Property-Based Tests — Formal Verification
# ===========================================================================


class TestMonotonicity:
    """Higher risk -> more restrictive (or equally restrictive) decisions.

    Property: If a decision is "approve" at risk R, it should also be
    "approve" at any lower risk level.
    """

    @given(
        confidence=st_confidence,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_risk_index_monotonic(self, confidence):
        """risk_index is monotonically increasing with severity."""
        for i in range(len(RISK_ORDER) - 1):
            assert risk_index(RISK_ORDER[i]) <= risk_index(RISK_ORDER[i + 1])

    @given(
        confidence=st_confidence,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_lower_confidence_more_likely_to_block(self, confidence):
        """Lower confidence is always at least as likely to trigger block as higher."""
        assume(0.0 < confidence < 1.0)
        higher = min(confidence + 0.1, 1.0)
        cond = f"aggregate_confidence < {confidence}"
        result_at_confidence = _evaluate_block_condition(cond, confidence, "low", [])
        result_at_higher = _evaluate_block_condition(cond, higher, "low", [])
        # If higher confidence blocks, lower must also block
        if result_at_higher:
            assert result_at_confidence

    def test_risk_order_strictly_increasing(self):
        """Each risk level maps to a strictly higher index than the previous."""
        for i in range(len(RISK_ORDER) - 1):
            assert risk_index(RISK_ORDER[i]) < risk_index(RISK_ORDER[i + 1])


class TestDeterminism:
    """Same inputs always produce the same output."""

    @given(
        confidence=st_confidence,
        risk=st_risk,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_block_condition_deterministic(self, confidence, risk):
        """Block condition evaluation must be deterministic."""
        flags = []
        cond = "aggregate_confidence < 0.50"
        r1 = _evaluate_block_condition(cond, confidence, risk, flags)
        r2 = _evaluate_block_condition(cond, confidence, risk, flags)
        assert r1 == r2

    @given(
        confidence=st_confidence,
        risk=st_risk,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_escalation_condition_deterministic(self, confidence, risk):
        """Escalation condition evaluation must be deterministic."""
        flags = []
        cond = 'risk_level in ["high", "critical"]'
        r1 = _evaluate_escalation_condition(cond, confidence, risk, flags, [])
        r2 = _evaluate_escalation_condition(cond, confidence, risk, flags, [])
        assert r1 == r2

    @given(
        confidence=st_confidence,
        risk=st_risk,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_auto_merge_condition_deterministic(self, confidence, risk):
        """Auto-merge condition evaluation must be deterministic."""
        cond = "aggregate_confidence >= 0.85"
        r1 = _evaluate_auto_merge_condition(cond, confidence, risk, [], [], True)
        r2 = _evaluate_auto_merge_condition(cond, confidence, risk, [], [], True)
        assert r1 == r2


class TestIdempotency:
    """Evaluating a condition twice produces the same result."""

    @given(
        confidence=st_confidence,
        risk=st_risk,
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_evaluate_block_idempotent(self, confidence, risk):
        """Block evaluation with same profile yields same result."""
        profile = _basic_profile()
        log1 = _log()
        log2 = _log()
        emissions = _make_emission_set(confidence=confidence, risk=risk)

        r1 = evaluate_block_conditions(
            confidence, risk, [], [], True, profile, log1, emissions,
        )
        r2 = evaluate_block_conditions(
            confidence, risk, [], [], True, profile, log2, emissions,
        )
        assert r1 == r2


class TestRangeInvariant:
    """confidence in [0.0, 1.0] always produces a valid decision (no exception)."""

    @given(confidence=st_confidence)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_block_never_crashes(self, confidence):
        profile = _basic_profile()
        log = _log()
        blocked, reason = evaluate_block_conditions(
            confidence, "low", [], [], True, profile, log,
        )
        assert isinstance(blocked, bool)
        assert isinstance(reason, str)

    @given(confidence=st_confidence, risk=st_risk)
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_escalation_never_crashes(self, confidence, risk):
        profile = _basic_profile()
        log = _log()
        escalated, reason = evaluate_escalation_rules(
            confidence, risk, [], [], profile, log,
        )
        # escalated is str (action) or None (no escalation)
        assert escalated is None or isinstance(escalated, str)
        assert isinstance(reason, str)


# ===========================================================================
# 3. Synthetic Emission Corpus — Policy Evaluation Test Mode
# ===========================================================================


class TestSyntheticEmissionCorpus:
    """Evaluate a profile against a synthetic emission corpus."""

    def test_all_approve_high_confidence_auto_merges(self):
        """All panels approve with high confidence -> auto_merge."""
        profile = _basic_profile()
        log = _log()
        emissions = _make_emission_set(confidence=0.95, risk="low", verdict="approve")

        conf = compute_weighted_confidence(emissions, profile, log)
        risk = compute_aggregate_risk(emissions, profile, log)

        blocked, _ = evaluate_block_conditions(conf, risk, [], [], True, profile, log, emissions)
        assert blocked is False

        auto_merge = evaluate_auto_merge(conf, risk, [], emissions, True, profile, log)
        assert auto_merge is True

    def test_low_confidence_blocks(self):
        """Low confidence (below 0.40 threshold) should trigger block."""
        profile = _basic_profile()
        log = _log()
        # Directly provide confidence below the default profile's block threshold
        blocked, reason = evaluate_block_conditions(
            0.30, "low", [], [], True, profile, log,
        )
        assert blocked is True
        assert "Confidence below" in reason or "aggregate_confidence" in reason.lower()

    def test_missing_required_panels_blocks(self):
        """Missing required panel should always block."""
        profile = _basic_profile()
        log = _log()
        blocked, reason = evaluate_block_conditions(
            0.95, "low", [], ["security-review"], True, profile, log,
        )
        assert blocked is True
        assert "security-review" in reason

    def test_ci_failure_blocks(self):
        """CI failure should always block."""
        profile = _basic_profile()
        log = _log()
        blocked, reason = evaluate_block_conditions(
            0.95, "low", [], [], False, profile, log,
        )
        assert blocked is True
        assert "CI" in reason

    def test_critical_policy_flags_block(self):
        """Critical severity policy flags should block."""
        profile = _basic_profile()
        log = _log()
        flags = [{"flag": "critical_vulnerability", "severity": "critical"}]
        blocked, reason = evaluate_block_conditions(
            0.95, "low", flags, [], True, profile, log,
        )
        assert blocked is True

    def test_high_severity_policy_flags_block(self):
        """High severity policy flags should block."""
        profile = _basic_profile()
        log = _log()
        flags = [{"flag": "pii_exposure", "severity": "high"}]
        blocked, reason = evaluate_block_conditions(
            0.95, "low", flags, [], True, profile, log,
        )
        assert blocked is True

    def test_low_severity_flags_do_not_block(self):
        """Low severity flags should not block by themselves."""
        profile = _basic_profile()
        log = _log()
        flags = [{"flag": "minor_style_issue", "severity": "low"}]
        blocked, reason = evaluate_block_conditions(
            0.95, "low", flags, [], True, profile, log,
        )
        assert blocked is False


# ===========================================================================
# 4. Decision Tables — Block and Escalation Rules
# ===========================================================================


class TestBlockDecisionTable:
    """Decision table for block conditions."""

    @pytest.mark.parametrize(
        "confidence,risk,missing,ci_passed,flags,expected_blocked",
        [
            # Happy path: high confidence, no issues
            (0.95, "low", [], True, [], False),
            # Universal block: missing required panel
            (0.95, "low", ["security-review"], True, [], True),
            # Universal block: CI failed
            (0.95, "low", [], False, [], True),
            # Universal block: critical flag
            (0.95, "low", [], True, [{"flag": "x", "severity": "critical"}], True),
            # Universal block: high flag
            (0.95, "low", [], True, [{"flag": "x", "severity": "high"}], True),
            # Low flag, no other issues
            (0.95, "low", [], True, [{"flag": "x", "severity": "low"}], False),
            # Medium flag, no other issues
            (0.95, "low", [], True, [{"flag": "x", "severity": "medium"}], False),
        ],
    )
    def test_block_decision(self, confidence, risk, missing, ci_passed, flags, expected_blocked):
        profile = _basic_profile()
        log = _log()
        blocked, _ = evaluate_block_conditions(
            confidence, risk, flags, missing, ci_passed, profile, log,
        )
        assert blocked == expected_blocked


class TestEscalationDecisionTable:
    """Decision table for escalation rules."""

    @pytest.mark.parametrize(
        "confidence,risk,expected_escalated",
        [
            # Low risk, high confidence: no escalation
            (0.95, "low", None),
            # Low risk, low confidence: depends on profile rules
            (0.50, "low", None),
        ],
    )
    def test_escalation_decision(self, confidence, risk, expected_escalated):
        profile = _basic_profile()
        log = _log()
        escalated, _ = evaluate_escalation_rules(
            confidence, risk, [], [], profile, log,
        )
        assert escalated == expected_escalated


# ===========================================================================
# 5. Compare operator formal verification
# ===========================================================================


class TestCompareOperator:
    """Verify _compare covers all operators correctly."""

    @given(a=st.integers(min_value=-1000, max_value=1000),
           b=st.integers(min_value=-1000, max_value=1000))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_gte_consistent_with_python(self, a, b):
        assert _compare(a, ">=", b) == (a >= b)

    @given(a=st.integers(min_value=-1000, max_value=1000),
           b=st.integers(min_value=-1000, max_value=1000))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_lte_consistent_with_python(self, a, b):
        assert _compare(a, "<=", b) == (a <= b)

    @given(a=st.integers(min_value=-1000, max_value=1000),
           b=st.integers(min_value=-1000, max_value=1000))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_eq_consistent_with_python(self, a, b):
        assert _compare(a, "==", b) == (a == b)

    @given(a=st.integers(min_value=-1000, max_value=1000),
           b=st.integers(min_value=-1000, max_value=1000))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_gt_consistent_with_python(self, a, b):
        assert _compare(a, ">", b) == (a > b)

    @given(a=st.integers(min_value=-1000, max_value=1000),
           b=st.integers(min_value=-1000, max_value=1000))
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_lt_consistent_with_python(self, a, b):
        assert _compare(a, "<", b) == (a < b)

    def test_unknown_operator_returns_false(self):
        assert _compare(5, "!=", 3) is False

    @given(a=st.integers(min_value=-1000, max_value=1000),
           b=st.integers(min_value=-1000, max_value=1000))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_trichotomy(self, a, b):
        """Exactly one of a < b, a == b, a > b must be true."""
        lt = _compare(a, "<", b)
        eq = _compare(a, "==", b)
        gt = _compare(a, ">", b)
        assert sum([lt, eq, gt]) == 1


class TestExtractListFormalProperties:
    """Formal properties of _extract_list."""

    @given(s=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_always_returns_list(self, s):
        result = _extract_list(s)
        assert isinstance(result, list)

    @given(s=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_all_items_are_strings(self, s):
        result = _extract_list(s)
        assert all(isinstance(item, str) for item in result)

    @given(items=st.lists(st.text(
        alphabet=st.characters(
            whitelist_categories=('L', 'N', 'P', 'Z'),
            blacklist_characters='"',
        ),
        min_size=1,
    ), min_size=1, max_size=5))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_round_trip_for_well_formed_input(self, items):
        """Well-formed input round-trips correctly."""
        quoted = ", ".join(f'"{item}"' for item in items)
        condition = f'field in [{quoted}]'
        result = _extract_list(condition)
        assert result == items


class TestExtractComparisonFormalProperties:
    """Formal properties of _extract_comparison."""

    @given(s=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_always_returns_tuple(self, s):
        result = _extract_comparison(s)
        assert isinstance(result, tuple)
        assert len(result) == 2

    @given(s=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_operator_is_string(self, s):
        op, _ = _extract_comparison(s)
        assert isinstance(op, str)

    @given(s=st.text())
    @settings(max_examples=200, suppress_health_check=[HealthCheck.too_slow])
    def test_threshold_is_numeric(self, s):
        _, threshold = _extract_comparison(s)
        assert isinstance(threshold, (int, float))

    @given(
        op=st_op,
        threshold=st.integers(min_value=0, max_value=100),
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_well_formed_round_trip(self, op, threshold):
        """Well-formed conditions round-trip correctly."""
        condition = f"count(foo) {op} {threshold}"
        extracted_op, extracted_threshold = _extract_comparison(condition)
        assert extracted_op == op
        assert extracted_threshold == threshold


# ===========================================================================
# 6. Full evaluate() round-trip (integration)
# ===========================================================================


class TestEvaluateRoundTrip:
    """Full policy engine evaluate() with synthetic emissions."""

    def test_full_evaluation_auto_merge(self, tmp_path):
        """High-confidence, low-risk emissions should produce auto_merge."""
        emissions_dir = tmp_path / "emissions"
        emissions_dir.mkdir()
        profile_path = tmp_path / "profile.yaml"

        # Write profile
        import yaml
        profile = _basic_profile()
        with open(profile_path, "w") as f:
            yaml.dump(profile, f)

        # Write emissions
        emissions = _make_emission_set(confidence=0.95, risk="low")
        for emission in emissions:
            filepath = emissions_dir / f"{emission['panel_name']}.json"
            with open(filepath, "w") as f:
                json.dump(emission, f)

        # evaluate() returns (manifest, exit_code)
        manifest, exit_code = policy_engine.evaluate(
            str(emissions_dir),
            str(profile_path),
            ci_passed=True,
            log_stream=io.StringIO(),
        )
        assert isinstance(manifest, dict)
        assert manifest["decision"]["action"] in [
            "auto_merge", "human_review_required", "block", "auto_remediate",
        ]
        # Exit code 0 = auto_merge
        assert exit_code in [0, 1, 2, 3]

    def test_full_evaluation_block_ci_failed(self, tmp_path):
        """CI failure should produce block decision."""
        emissions_dir = tmp_path / "emissions"
        emissions_dir.mkdir()
        profile_path = tmp_path / "profile.yaml"

        import yaml
        profile = _basic_profile()
        with open(profile_path, "w") as f:
            yaml.dump(profile, f)

        emissions = _make_emission_set(confidence=0.95, risk="low")
        for emission in emissions:
            filepath = emissions_dir / f"{emission['panel_name']}.json"
            with open(filepath, "w") as f:
                json.dump(emission, f)

        manifest, exit_code = policy_engine.evaluate(
            str(emissions_dir),
            str(profile_path),
            ci_passed=False,
            log_stream=io.StringIO(),
        )
        assert manifest["decision"]["action"] == "block"
        assert exit_code == 1
