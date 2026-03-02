"""Tests for governance.engine.orchestrator.capacity — tier classification and gate enforcement."""

import pytest

from governance.engine.orchestrator.capacity import (
    Action,
    CapacitySignals,
    Tier,
    classify_tier,
    format_gate_block,
    gate_action,
    TOOL_CALLS_GREEN_MAX,
    TOOL_CALLS_YELLOW_MAX,
    TOOL_CALLS_ORANGE_MAX,
    TURNS_GREEN_MAX,
    TURNS_YELLOW_MAX,
    TURNS_ORANGE_MAX,
)


# ---------------------------------------------------------------------------
# Tier ordering
# ---------------------------------------------------------------------------


class TestTierOrdering:
    def test_green_lt_yellow(self):
        assert Tier.GREEN < Tier.YELLOW

    def test_yellow_lt_orange(self):
        assert Tier.YELLOW < Tier.ORANGE

    def test_orange_lt_red(self):
        assert Tier.ORANGE < Tier.RED

    def test_red_is_highest(self):
        assert Tier.RED >= Tier.GREEN
        assert Tier.RED >= Tier.YELLOW
        assert Tier.RED >= Tier.ORANGE

    def test_equal_comparison(self):
        assert Tier.GREEN <= Tier.GREEN
        assert Tier.GREEN >= Tier.GREEN


# ---------------------------------------------------------------------------
# Tool call classification
# ---------------------------------------------------------------------------


class TestToolCallTiers:
    def test_zero_is_green(self):
        signals = CapacitySignals(tool_calls=0)
        assert classify_tier(signals) == Tier.GREEN

    def test_green_boundary(self):
        signals = CapacitySignals(tool_calls=TOOL_CALLS_GREEN_MAX)
        assert classify_tier(signals) == Tier.GREEN

    def test_yellow_boundary_low(self):
        signals = CapacitySignals(tool_calls=TOOL_CALLS_GREEN_MAX + 1)
        assert classify_tier(signals) == Tier.YELLOW

    def test_yellow_boundary_high(self):
        signals = CapacitySignals(tool_calls=TOOL_CALLS_YELLOW_MAX)
        assert classify_tier(signals) == Tier.YELLOW

    def test_orange_boundary_low(self):
        signals = CapacitySignals(tool_calls=TOOL_CALLS_YELLOW_MAX + 1)
        assert classify_tier(signals) == Tier.ORANGE

    def test_orange_boundary_high(self):
        signals = CapacitySignals(tool_calls=TOOL_CALLS_ORANGE_MAX)
        assert classify_tier(signals) == Tier.ORANGE

    def test_red_boundary(self):
        signals = CapacitySignals(tool_calls=TOOL_CALLS_ORANGE_MAX + 1)
        assert classify_tier(signals) == Tier.RED

    def test_red_high(self):
        signals = CapacitySignals(tool_calls=200)
        assert classify_tier(signals) == Tier.RED


# ---------------------------------------------------------------------------
# Turn classification
# ---------------------------------------------------------------------------


class TestTurnTiers:
    def test_zero_is_green(self):
        signals = CapacitySignals(turns=0)
        assert classify_tier(signals) == Tier.GREEN

    def test_green_boundary(self):
        signals = CapacitySignals(turns=TURNS_GREEN_MAX)
        assert classify_tier(signals) == Tier.GREEN

    def test_yellow_boundary(self):
        signals = CapacitySignals(turns=TURNS_GREEN_MAX + 1)
        assert classify_tier(signals) == Tier.YELLOW

    def test_orange_boundary(self):
        signals = CapacitySignals(turns=TURNS_YELLOW_MAX + 1)
        assert classify_tier(signals) == Tier.ORANGE

    def test_red_boundary(self):
        signals = CapacitySignals(turns=TURNS_ORANGE_MAX + 1)
        assert classify_tier(signals) == Tier.RED


# ---------------------------------------------------------------------------
# Issue completion classification
# ---------------------------------------------------------------------------


class TestIssueCompletionTiers:
    def test_zero_completed_is_green(self):
        signals = CapacitySignals(issues_completed=0, parallel_coders=5)
        assert classify_tier(signals) == Tier.GREEN

    def test_green_below_n_minus_2(self):
        signals = CapacitySignals(issues_completed=2, parallel_coders=5)
        assert classify_tier(signals) == Tier.GREEN

    def test_yellow_at_n_minus_2(self):
        signals = CapacitySignals(issues_completed=3, parallel_coders=5)
        assert classify_tier(signals) == Tier.YELLOW

    def test_orange_at_n_minus_1(self):
        signals = CapacitySignals(issues_completed=4, parallel_coders=5)
        assert classify_tier(signals) == Tier.ORANGE

    def test_red_at_n(self):
        signals = CapacitySignals(issues_completed=5, parallel_coders=5)
        assert classify_tier(signals) == Tier.RED

    def test_red_above_n(self):
        signals = CapacitySignals(issues_completed=7, parallel_coders=5)
        assert classify_tier(signals) == Tier.RED


class TestUnlimitedMode:
    """When parallel_coders == -1, issue count signal is disabled."""

    def test_unlimited_always_green_for_issues(self):
        signals = CapacitySignals(issues_completed=100, parallel_coders=-1)
        assert classify_tier(signals) == Tier.GREEN

    def test_unlimited_tool_calls_still_work(self):
        signals = CapacitySignals(
            issues_completed=100, parallel_coders=-1,
            tool_calls=TOOL_CALLS_ORANGE_MAX + 1,
        )
        assert classify_tier(signals) == Tier.RED

    def test_unlimited_turns_still_work(self):
        signals = CapacitySignals(
            issues_completed=100, parallel_coders=-1,
            turns=TURNS_ORANGE_MAX + 1,
        )
        assert classify_tier(signals) == Tier.RED


class TestSmallParallelCoders:
    """Edge cases with N <= 2."""

    def test_n_equals_1_zero_completed(self):
        signals = CapacitySignals(issues_completed=0, parallel_coders=1)
        # N=1: 0 == max(N-1, 0) = 0 → Orange (one away from cap)
        assert classify_tier(signals) == Tier.ORANGE

    def test_n_equals_1_one_completed(self):
        signals = CapacitySignals(issues_completed=1, parallel_coders=1)
        assert classify_tier(signals) == Tier.RED

    def test_n_equals_2_zero_completed(self):
        signals = CapacitySignals(issues_completed=0, parallel_coders=2)
        assert classify_tier(signals) == Tier.YELLOW

    def test_n_equals_2_one_completed(self):
        signals = CapacitySignals(issues_completed=1, parallel_coders=2)
        assert classify_tier(signals) == Tier.ORANGE

    def test_n_equals_2_two_completed(self):
        signals = CapacitySignals(issues_completed=2, parallel_coders=2)
        assert classify_tier(signals) == Tier.RED


# ---------------------------------------------------------------------------
# Single Red signal dominance
# ---------------------------------------------------------------------------


class TestRedSignalDominance:
    def test_system_warning_always_red(self):
        signals = CapacitySignals(
            tool_calls=0, turns=0, issues_completed=0, system_warning=True,
        )
        assert classify_tier(signals) == Tier.RED

    def test_degraded_recall_always_red(self):
        signals = CapacitySignals(
            tool_calls=0, turns=0, issues_completed=0, degraded_recall=True,
        )
        assert classify_tier(signals) == Tier.RED

    def test_system_warning_overrides_green_signals(self):
        signals = CapacitySignals(
            tool_calls=5, turns=10, issues_completed=0,
            parallel_coders=5, system_warning=True,
        )
        assert classify_tier(signals) == Tier.RED


class TestHighestTierWins:
    def test_mixed_green_and_yellow(self):
        # tool_calls=Green, turns=Yellow
        signals = CapacitySignals(tool_calls=10, turns=70)
        assert classify_tier(signals) == Tier.YELLOW

    def test_mixed_yellow_and_orange(self):
        signals = CapacitySignals(tool_calls=55, turns=110)
        assert classify_tier(signals) == Tier.ORANGE

    def test_one_red_overrides_all_green(self):
        signals = CapacitySignals(tool_calls=0, turns=0, issues_completed=5, parallel_coders=5)
        assert classify_tier(signals) == Tier.RED


# ---------------------------------------------------------------------------
# Gate action matrix
# ---------------------------------------------------------------------------


class TestGateAction:
    @pytest.mark.parametrize("phase", range(6))
    def test_all_phases_green_proceed(self, phase):
        action = gate_action(phase, Tier.GREEN)
        assert action == Action.PROCEED

    @pytest.mark.parametrize("phase", [0, 1, 2, 5])
    def test_yellow_proceed_most_phases(self, phase):
        assert gate_action(phase, Tier.YELLOW) == Action.PROCEED

    def test_yellow_phase3_skip_dispatch(self):
        assert gate_action(3, Tier.YELLOW) == Action.SKIP_DISPATCH

    def test_yellow_phase4_finish_current(self):
        assert gate_action(4, Tier.YELLOW) == Action.FINISH_CURRENT

    @pytest.mark.parametrize("phase", [0, 1, 2, 3, 5])
    def test_orange_emergency_stop_most_phases(self, phase):
        assert gate_action(phase, Tier.ORANGE) == Action.EMERGENCY_STOP

    def test_orange_phase4_finish_current(self):
        assert gate_action(4, Tier.ORANGE) == Action.FINISH_CURRENT

    @pytest.mark.parametrize("phase", range(6))
    def test_red_always_emergency_stop(self, phase):
        action = gate_action(phase, Tier.RED)
        assert action == Action.EMERGENCY_STOP

    def test_invalid_phase_raises(self):
        with pytest.raises(ValueError, match="Invalid phase"):
            gate_action(6, Tier.GREEN)

    def test_negative_phase_raises(self):
        with pytest.raises(ValueError, match="Invalid phase"):
            gate_action(-1, Tier.GREEN)


# ---------------------------------------------------------------------------
# Gate block formatting
# ---------------------------------------------------------------------------


class TestFormatGateBlock:
    def test_basic_format(self):
        signals = CapacitySignals(tool_calls=25, turns=30)
        block = format_gate_block(0, signals)
        assert "Phase: 0" in block
        assert "Tool calls this session: 25" in block
        assert "Tier: Green" in block
        assert "Action: proceed" in block

    def test_red_format(self):
        signals = CapacitySignals(tool_calls=100, turns=200)
        block = format_gate_block(3, signals)
        assert "Tier: Red" in block
        assert "Action: emergency-stop" in block

    def test_yellow_phase3_format(self):
        signals = CapacitySignals(tool_calls=55, turns=30)
        block = format_gate_block(3, signals)
        assert "Action: skip-dispatch" in block
