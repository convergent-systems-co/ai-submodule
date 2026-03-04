"""Sub-agent context capacity monitoring for parallel dispatch.

Provides visibility into sub-agent context consumption so the parent
orchestrator can detect degradation before agents silently fail.

The SubAgentContextMonitor evaluates AgentResult objects and classifies
each agent into a context tier based on token consumption relative to
a configurable context window size.

Tier thresholds (percentage of context window consumed):
    - green:   < 60%
    - yellow:  60% - 69%
    - orange:  70% - 79%
    - red:     >= 80%
    - unknown: no token data available
"""

from __future__ import annotations

from dataclasses import dataclass, field

from governance.engine.orchestrator.dispatcher import AgentResult


# ---------------------------------------------------------------------------
# Tier thresholds (fraction of context window)
# ---------------------------------------------------------------------------

TIER_YELLOW_THRESHOLD = 0.60
TIER_ORANGE_THRESHOLD = 0.70
TIER_RED_THRESHOLD = 0.80

# Default context window size (tokens). Used when not explicitly configured.
DEFAULT_CONTEXT_WINDOW = 200_000


@dataclass
class AgentHealthEntry:
    """Health classification for a single sub-agent result."""

    correlation_id: str
    task_id: str | None
    tier: str  # green / yellow / orange / red / unknown
    tokens_consumed: int | None
    tool_uses: int | None
    utilization: float | None  # 0.0 - 1.0, None if unknown
    needs_attention: bool  # True if orange or red


@dataclass
class HealthSummary:
    """Aggregated health report across all sub-agent results."""

    total_agents: int
    entries: list[AgentHealthEntry] = field(default_factory=list)
    agents_at_risk: list[AgentHealthEntry] = field(default_factory=list)
    tier_counts: dict[str, int] = field(default_factory=dict)

    @property
    def has_risk(self) -> bool:
        """True if any agent is at orange or red tier."""
        return len(self.agents_at_risk) > 0


class SubAgentContextMonitor:
    """Evaluates sub-agent context health from AgentResult metadata.

    Usage::

        monitor = SubAgentContextMonitor(context_window=200_000)
        summary = monitor.evaluate(agent_results)
        if summary.has_risk:
            for entry in summary.agents_at_risk:
                print(f"Agent {entry.correlation_id} is at {entry.tier} tier")
    """

    def __init__(self, context_window: int = DEFAULT_CONTEXT_WINDOW):
        if context_window <= 0:
            raise ValueError("context_window must be a positive integer")
        self.context_window = context_window

    def classify(self, tokens_consumed: int | None) -> tuple[str, float | None]:
        """Classify a single token count into a context tier.

        Args:
            tokens_consumed: Total tokens used, or None if unavailable.

        Returns:
            Tuple of (tier_name, utilization_fraction).
            If tokens_consumed is None, returns ("unknown", None).
        """
        if tokens_consumed is None:
            return "unknown", None

        utilization = tokens_consumed / self.context_window

        if utilization >= TIER_RED_THRESHOLD:
            return "red", utilization
        if utilization >= TIER_ORANGE_THRESHOLD:
            return "orange", utilization
        if utilization >= TIER_YELLOW_THRESHOLD:
            return "yellow", utilization
        return "green", utilization

    def evaluate(self, results: list[AgentResult]) -> HealthSummary:
        """Evaluate context health for a batch of agent results.

        Args:
            results: List of AgentResult objects from dispatched agents.

        Returns:
            HealthSummary with per-agent classification and risk flags.
        """
        entries: list[AgentHealthEntry] = []
        at_risk: list[AgentHealthEntry] = []
        tier_counts: dict[str, int] = {
            "green": 0,
            "yellow": 0,
            "orange": 0,
            "red": 0,
            "unknown": 0,
        }

        for result in results:
            tier, utilization = self.classify(result.tokens_consumed)
            needs_attention = tier in ("orange", "red")

            entry = AgentHealthEntry(
                correlation_id=result.correlation_id,
                task_id=result.task_id,
                tier=tier,
                tokens_consumed=result.tokens_consumed,
                tool_uses=result.tool_uses,
                utilization=utilization,
                needs_attention=needs_attention,
            )

            entries.append(entry)
            tier_counts[tier] = tier_counts.get(tier, 0) + 1

            if needs_attention:
                at_risk.append(entry)

        return HealthSummary(
            total_agents=len(results),
            entries=entries,
            agents_at_risk=at_risk,
            tier_counts=tier_counts,
        )

    def format_report(self, summary: HealthSummary) -> str:
        """Produce a human-readable health report.

        Args:
            summary: HealthSummary from evaluate().

        Returns:
            Formatted string suitable for logging or audit output.
        """
        lines = [
            "--- SUB-AGENT CONTEXT HEALTH ---",
            f"Total agents: {summary.total_agents}",
            f"Tier distribution: {_format_tier_counts(summary.tier_counts)}",
        ]

        if summary.has_risk:
            lines.append(f"Agents at risk: {len(summary.agents_at_risk)}")
            for entry in summary.agents_at_risk:
                pct = f"{entry.utilization:.0%}" if entry.utilization is not None else "N/A"
                lines.append(
                    f"  - {entry.correlation_id} [{entry.tier.upper()}] "
                    f"utilization={pct} tokens={entry.tokens_consumed}"
                )
        else:
            lines.append("Agents at risk: 0")

        lines.append("---")
        return "\n".join(lines)


def _format_tier_counts(counts: dict[str, int]) -> str:
    """Format tier counts as a compact string."""
    parts = []
    for tier in ("green", "yellow", "orange", "red", "unknown"):
        count = counts.get(tier, 0)
        if count > 0:
            parts.append(f"{tier}={count}")
    return ", ".join(parts) if parts else "none"
