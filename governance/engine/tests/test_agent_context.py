"""Tests for governance.engine.orchestrator.agent_context — sub-agent context monitoring."""

from __future__ import annotations

import pytest

from governance.engine.orchestrator.agent_context import (
    DEFAULT_CONTEXT_WINDOW,
    TIER_ORANGE_THRESHOLD,
    TIER_RED_THRESHOLD,
    TIER_YELLOW_THRESHOLD,
    AgentHealthEntry,
    HealthSummary,
    SubAgentContextMonitor,
    _format_tier_counts,
)
from governance.engine.orchestrator.dispatcher import AgentResult


# ---------------------------------------------------------------------------
# Helper to build AgentResult with context fields
# ---------------------------------------------------------------------------


def _make_result(
    correlation_id: str = "issue-1",
    success: bool = True,
    tokens_consumed: int | None = None,
    tool_uses: int | None = None,
    context_tier: str | None = None,
    task_id: str | None = None,
) -> AgentResult:
    return AgentResult(
        correlation_id=correlation_id,
        success=success,
        tokens_consumed=tokens_consumed,
        tool_uses=tool_uses,
        context_tier=context_tier,
        task_id=task_id,
    )


# ---------------------------------------------------------------------------
# SubAgentContextMonitor.classify
# ---------------------------------------------------------------------------


class TestClassify:
    """Test tier classification from token counts."""

    def test_none_tokens_returns_unknown(self):
        monitor = SubAgentContextMonitor()
        tier, util = monitor.classify(None)
        assert tier == "unknown"
        assert util is None

    def test_zero_tokens_is_green(self):
        monitor = SubAgentContextMonitor()
        tier, util = monitor.classify(0)
        assert tier == "green"
        assert util == 0.0

    def test_below_yellow_is_green(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        # 59% utilization
        tier, util = monitor.classify(118_000)
        assert tier == "green"
        assert util == pytest.approx(0.59, abs=0.01)

    def test_at_yellow_boundary(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        # Exactly 60% = yellow
        tier, util = monitor.classify(120_000)
        assert tier == "yellow"
        assert util == pytest.approx(TIER_YELLOW_THRESHOLD)

    def test_yellow_range(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        # 65% utilization
        tier, util = monitor.classify(130_000)
        assert tier == "yellow"

    def test_at_orange_boundary(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        # Exactly 70% = orange
        tier, util = monitor.classify(140_000)
        assert tier == "orange"
        assert util == pytest.approx(TIER_ORANGE_THRESHOLD)

    def test_orange_range(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        # 75% utilization
        tier, util = monitor.classify(150_000)
        assert tier == "orange"

    def test_at_red_boundary(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        # Exactly 80% = red
        tier, util = monitor.classify(160_000)
        assert tier == "red"
        assert util == pytest.approx(TIER_RED_THRESHOLD)

    def test_above_red_boundary(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        # 95% utilization
        tier, util = monitor.classify(190_000)
        assert tier == "red"

    def test_over_100_percent(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        # 120% — exceeds window
        tier, util = monitor.classify(240_000)
        assert tier == "red"
        assert util == pytest.approx(1.2)

    def test_custom_context_window(self):
        monitor = SubAgentContextMonitor(context_window=100_000)
        # 50_000 / 100_000 = 50% → green
        tier, _ = monitor.classify(50_000)
        assert tier == "green"
        # 65_000 / 100_000 = 65% → yellow
        tier, _ = monitor.classify(65_000)
        assert tier == "yellow"


class TestClassifyEdgeCases:
    def test_one_token(self):
        monitor = SubAgentContextMonitor()
        tier, util = monitor.classify(1)
        assert tier == "green"
        assert util > 0.0

    def test_exactly_at_each_boundary(self):
        """Verify boundaries are inclusive for the higher tier."""
        window = 1000
        monitor = SubAgentContextMonitor(context_window=window)

        # Just below yellow
        tier, _ = monitor.classify(599)
        assert tier == "green"

        # At yellow
        tier, _ = monitor.classify(600)
        assert tier == "yellow"

        # Just below orange
        tier, _ = monitor.classify(699)
        assert tier == "yellow"

        # At orange
        tier, _ = monitor.classify(700)
        assert tier == "orange"

        # Just below red
        tier, _ = monitor.classify(799)
        assert tier == "orange"

        # At red
        tier, _ = monitor.classify(800)
        assert tier == "red"


# ---------------------------------------------------------------------------
# SubAgentContextMonitor.evaluate
# ---------------------------------------------------------------------------


class TestEvaluate:
    def test_empty_results(self):
        monitor = SubAgentContextMonitor()
        summary = monitor.evaluate([])
        assert summary.total_agents == 0
        assert summary.entries == []
        assert summary.agents_at_risk == []
        assert not summary.has_risk

    def test_all_green(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        results = [
            _make_result("issue-1", tokens_consumed=50_000),
            _make_result("issue-2", tokens_consumed=80_000),
            _make_result("issue-3", tokens_consumed=100_000),
        ]
        summary = monitor.evaluate(results)
        assert summary.total_agents == 3
        assert summary.tier_counts["green"] == 3
        assert not summary.has_risk
        assert len(summary.agents_at_risk) == 0

    def test_mixed_tiers(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        results = [
            _make_result("issue-1", tokens_consumed=50_000),   # green (25%)
            _make_result("issue-2", tokens_consumed=130_000),  # yellow (65%)
            _make_result("issue-3", tokens_consumed=150_000),  # orange (75%)
            _make_result("issue-4", tokens_consumed=170_000),  # red (85%)
        ]
        summary = monitor.evaluate(results)
        assert summary.total_agents == 4
        assert summary.tier_counts["green"] == 1
        assert summary.tier_counts["yellow"] == 1
        assert summary.tier_counts["orange"] == 1
        assert summary.tier_counts["red"] == 1
        assert summary.has_risk
        assert len(summary.agents_at_risk) == 2

    def test_all_unknown(self):
        monitor = SubAgentContextMonitor()
        results = [
            _make_result("issue-1", tokens_consumed=None),
            _make_result("issue-2", tokens_consumed=None),
        ]
        summary = monitor.evaluate(results)
        assert summary.total_agents == 2
        assert summary.tier_counts["unknown"] == 2
        assert not summary.has_risk

    def test_agents_at_risk_are_orange_and_red(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        results = [
            _make_result("issue-1", tokens_consumed=50_000),   # green
            _make_result("issue-2", tokens_consumed=145_000),  # orange
            _make_result("issue-3", tokens_consumed=175_000),  # red
        ]
        summary = monitor.evaluate(results)
        risk_ids = {e.correlation_id for e in summary.agents_at_risk}
        assert risk_ids == {"issue-2", "issue-3"}

    def test_tool_uses_passed_through(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        results = [
            _make_result("issue-1", tokens_consumed=50_000, tool_uses=42),
        ]
        summary = monitor.evaluate(results)
        assert summary.entries[0].tool_uses == 42

    def test_task_id_passed_through(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        results = [
            _make_result("issue-1", tokens_consumed=50_000, task_id="task-abc"),
        ]
        summary = monitor.evaluate(results)
        assert summary.entries[0].task_id == "task-abc"

    def test_needs_attention_flag(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        results = [
            _make_result("green", tokens_consumed=50_000),
            _make_result("yellow", tokens_consumed=125_000),
            _make_result("orange", tokens_consumed=145_000),
            _make_result("red", tokens_consumed=175_000),
            _make_result("unknown", tokens_consumed=None),
        ]
        summary = monitor.evaluate(results)
        attention_map = {e.correlation_id: e.needs_attention for e in summary.entries}
        assert attention_map["green"] is False
        assert attention_map["yellow"] is False
        assert attention_map["orange"] is True
        assert attention_map["red"] is True
        assert attention_map["unknown"] is False


# ---------------------------------------------------------------------------
# HealthSummary.has_risk property
# ---------------------------------------------------------------------------


class TestHealthSummary:
    def test_has_risk_true_when_agents_at_risk(self):
        entry = AgentHealthEntry(
            correlation_id="x", task_id=None, tier="red",
            tokens_consumed=180_000, tool_uses=50,
            utilization=0.9, needs_attention=True,
        )
        summary = HealthSummary(total_agents=1, agents_at_risk=[entry])
        assert summary.has_risk is True

    def test_has_risk_false_when_no_risk(self):
        summary = HealthSummary(total_agents=2, agents_at_risk=[])
        assert summary.has_risk is False


# ---------------------------------------------------------------------------
# SubAgentContextMonitor.format_report
# ---------------------------------------------------------------------------


class TestFormatReport:
    def test_report_contains_header(self):
        monitor = SubAgentContextMonitor()
        summary = monitor.evaluate([])
        report = monitor.format_report(summary)
        assert "SUB-AGENT CONTEXT HEALTH" in report

    def test_report_shows_total_agents(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        results = [_make_result("issue-1", tokens_consumed=50_000)]
        summary = monitor.evaluate(results)
        report = monitor.format_report(summary)
        assert "Total agents: 1" in report

    def test_report_shows_risk_agents(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        results = [
            _make_result("issue-1", tokens_consumed=170_000),  # red (85%)
        ]
        summary = monitor.evaluate(results)
        report = monitor.format_report(summary)
        assert "Agents at risk: 1" in report
        assert "issue-1" in report
        assert "RED" in report

    def test_report_shows_tier_distribution(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        results = [
            _make_result("a", tokens_consumed=50_000),   # green
            _make_result("b", tokens_consumed=130_000),  # yellow
        ]
        summary = monitor.evaluate(results)
        report = monitor.format_report(summary)
        assert "green=1" in report
        assert "yellow=1" in report

    def test_report_no_risk_message(self):
        monitor = SubAgentContextMonitor(context_window=200_000)
        results = [_make_result("a", tokens_consumed=50_000)]
        summary = monitor.evaluate(results)
        report = monitor.format_report(summary)
        assert "Agents at risk: 0" in report


# ---------------------------------------------------------------------------
# Initialization validation
# ---------------------------------------------------------------------------


class TestMonitorInit:
    def test_default_context_window(self):
        monitor = SubAgentContextMonitor()
        assert monitor.context_window == DEFAULT_CONTEXT_WINDOW

    def test_custom_context_window(self):
        monitor = SubAgentContextMonitor(context_window=100_000)
        assert monitor.context_window == 100_000

    def test_zero_context_window_raises(self):
        with pytest.raises(ValueError, match="positive integer"):
            SubAgentContextMonitor(context_window=0)

    def test_negative_context_window_raises(self):
        with pytest.raises(ValueError, match="positive integer"):
            SubAgentContextMonitor(context_window=-1)


# ---------------------------------------------------------------------------
# AgentResult extended fields
# ---------------------------------------------------------------------------


class TestAgentResultExtendedFields:
    """Verify the extended fields on AgentResult work correctly."""

    def test_default_values_are_none(self):
        result = AgentResult(correlation_id="x", success=True)
        assert result.tokens_consumed is None
        assert result.tool_uses is None
        assert result.context_tier is None

    def test_fields_can_be_set(self):
        result = AgentResult(
            correlation_id="x",
            success=True,
            tokens_consumed=150_000,
            tool_uses=42,
            context_tier="yellow",
        )
        assert result.tokens_consumed == 150_000
        assert result.tool_uses == 42
        assert result.context_tier == "yellow"

    def test_backward_compatible_construction(self):
        """Existing code that doesn't pass new fields still works."""
        result = AgentResult(
            correlation_id="x",
            success=True,
            branch="feat/test",
            summary="all good",
            files_changed=["a.py"],
            error=None,
            task_id="t-1",
        )
        assert result.tokens_consumed is None
        assert result.tool_uses is None
        assert result.context_tier is None


# ---------------------------------------------------------------------------
# _format_tier_counts helper
# ---------------------------------------------------------------------------


class TestFormatTierCounts:
    def test_all_zero(self):
        result = _format_tier_counts({"green": 0, "yellow": 0, "orange": 0, "red": 0, "unknown": 0})
        assert result == "none"

    def test_empty_dict(self):
        result = _format_tier_counts({})
        assert result == "none"

    def test_single_tier(self):
        result = _format_tier_counts({"green": 3})
        assert result == "green=3"

    def test_multiple_tiers(self):
        result = _format_tier_counts({"green": 2, "red": 1})
        assert "green=2" in result
        assert "red=1" in result

    def test_tier_ordering(self):
        """Tiers are output in severity order: green, yellow, orange, red, unknown."""
        result = _format_tier_counts({"red": 1, "green": 2, "unknown": 1})
        parts = result.split(", ")
        tier_order = [p.split("=")[0] for p in parts]
        assert tier_order == ["green", "red", "unknown"]
