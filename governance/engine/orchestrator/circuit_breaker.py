"""Per-work-unit evaluation cycle tracking with hard limits.

Enforces the circuit breaker rules from agent-protocol.md:
- Max 2 Tester FEEDBACK cycles per work unit (trips on 3rd — Tester
  must emit BLOCK at cycle 3 per protocol)
- Max 5 total evaluation cycles per work unit (includes re-assigns after BLOCK/ESCALATE)
"""

from __future__ import annotations

from dataclasses import dataclass, field


class CircuitBreakerTripped(Exception):
    """Raised when a work unit exceeds its evaluation cycle limit."""

    def __init__(self, correlation_id: str, reason: str, cycles: int, limit: int):
        self.correlation_id = correlation_id
        self.reason = reason
        self.cycles = cycles
        self.limit = limit
        super().__init__(
            f"Circuit breaker tripped for {correlation_id}: "
            f"{reason} ({cycles}/{limit})"
        )


@dataclass
class WorkUnit:
    """Tracks evaluation cycles for a single work item (issue/PR)."""

    correlation_id: str
    feedback_cycles: int = 0
    total_eval_cycles: int = 0
    blocked: bool = False
    block_reason: str | None = None


class CircuitBreaker:
    """Tracks per-work-unit evaluation cycles and enforces hard limits.

    Constants from agent-protocol.md:
        MAX_FEEDBACK_CYCLES = 2 (Tester FEEDBACK only — trips on 3rd per protocol)
        MAX_TOTAL_EVAL_CYCLES = 5 (FEEDBACK + re-ASSIGN after BLOCK/ESCALATE)
    """

    def __init__(
        self,
        max_feedback_cycles: int = 2,
        max_total_eval_cycles: int = 5,
    ):
        self.max_feedback_cycles = max_feedback_cycles
        self.max_total_eval_cycles = max_total_eval_cycles
        self._work_units: dict[str, WorkUnit] = {}

    def _get_or_create(self, correlation_id: str) -> WorkUnit:
        if correlation_id not in self._work_units:
            self._work_units[correlation_id] = WorkUnit(
                correlation_id=correlation_id
            )
        return self._work_units[correlation_id]

    def record_feedback(self, correlation_id: str) -> WorkUnit:
        """Record a Tester FEEDBACK cycle.

        Raises:
            CircuitBreakerTripped: If feedback cycle limit (2, trips on 3rd)
                or total eval cycle limit (5) is exceeded.
        """
        unit = self._get_or_create(correlation_id)
        if unit.blocked:
            raise CircuitBreakerTripped(
                correlation_id, "work_unit_already_blocked",
                unit.total_eval_cycles, self.max_total_eval_cycles,
            )

        unit.feedback_cycles += 1
        unit.total_eval_cycles += 1

        if unit.feedback_cycles > self.max_feedback_cycles:
            unit.blocked = True
            unit.block_reason = "feedback_cycle_limit"
            raise CircuitBreakerTripped(
                correlation_id, "feedback_cycle_limit",
                unit.feedback_cycles, self.max_feedback_cycles,
            )

        if unit.total_eval_cycles >= self.max_total_eval_cycles:
            unit.blocked = True
            unit.block_reason = "total_eval_cycle_limit"
            raise CircuitBreakerTripped(
                correlation_id, "total_eval_cycle_limit",
                unit.total_eval_cycles, self.max_total_eval_cycles,
            )

        return unit

    def record_reassign(self, correlation_id: str) -> WorkUnit:
        """Record a re-ASSIGN after BLOCK or ESCALATE.

        Raises:
            CircuitBreakerTripped: If total eval cycle limit (5) is exceeded.
        """
        unit = self._get_or_create(correlation_id)
        if unit.blocked:
            raise CircuitBreakerTripped(
                correlation_id, "work_unit_already_blocked",
                unit.total_eval_cycles, self.max_total_eval_cycles,
            )

        unit.total_eval_cycles += 1

        if unit.total_eval_cycles >= self.max_total_eval_cycles:
            unit.blocked = True
            unit.block_reason = "total_eval_cycle_limit"
            raise CircuitBreakerTripped(
                correlation_id, "total_eval_cycle_limit",
                unit.total_eval_cycles, self.max_total_eval_cycles,
            )

        return unit

    def can_dispatch(self, correlation_id: str) -> bool:
        """Check if a work unit can accept more evaluation cycles."""
        unit = self._work_units.get(correlation_id)
        if unit is None:
            return True
        return not unit.blocked

    def get_unit(self, correlation_id: str) -> WorkUnit | None:
        """Get work unit state. Returns None if not tracked."""
        return self._work_units.get(correlation_id)

    @property
    def all_units(self) -> dict[str, WorkUnit]:
        """Read-only view of all tracked work units."""
        return dict(self._work_units)
