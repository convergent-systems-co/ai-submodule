"""Phase state machine with gate enforcement at every boundary.

The state machine is the core of the orchestrator. It enforces:
1. Only valid phase transitions are allowed
2. Every transition passes through a capacity gate check
3. Orange/Red tiers raise ShutdownRequired (cannot be bypassed)
4. All gate decisions are recorded for audit
"""

from __future__ import annotations

from dataclasses import dataclass, field

from governance.engine.orchestrator.capacity import (
    Action,
    CapacitySignals,
    Tier,
    classify_tier,
    gate_action,
)


class InvalidTransition(Exception):
    """Raised when an invalid phase transition is attempted."""

    def __init__(self, from_phase: int, to_phase: int):
        self.from_phase = from_phase
        self.to_phase = to_phase
        super().__init__(
            f"Invalid transition: Phase {from_phase} → Phase {to_phase}"
        )


class ShutdownRequired(Exception):
    """Raised when a gate check requires shutdown.

    Callers must treat this as fatal and must not continue the loop
    after catching it. The only valid response is to execute the
    shutdown protocol (write checkpoint, clean git state, exit).
    """

    def __init__(
        self,
        tier: Tier,
        action: Action,
        gates_passed: list[dict],
        signals: CapacitySignals | None = None,
    ):
        self.tier = tier
        self.action = action
        self.gates_passed = gates_passed
        self.signals = signals
        super().__init__(
            f"Shutdown required: tier={tier.value}, action={action.value}"
        )


# ---------------------------------------------------------------------------
# Valid phase transitions — extracted from startup.md pipeline overview
# ---------------------------------------------------------------------------

VALID_TRANSITIONS: dict[int, frozenset[int]] = {
    0: frozenset({1, 2, 3, 4, 5}),  # Phase 0 (recovery) can resume to any phase
    1: frozenset({2}),                # Pre-flight → Planning
    2: frozenset({3}),                # Planning → Dispatch
    3: frozenset({4}),                # Dispatch → Review
    4: frozenset({3, 5}),             # Review → Re-dispatch (feedback) or Merge
    5: frozenset({1}),                # Merge → Loop back to Pre-flight
}

# Actions that require shutdown
_SHUTDOWN_ACTIONS = frozenset({Action.EMERGENCY_STOP, Action.CHECKPOINT})


@dataclass
class PhaseState:
    """Current pipeline phase."""

    phase: int = 0
    sub_phase: str | None = None


@dataclass
class GateRecord:
    """Record of a gate check for audit trail."""

    phase: int
    tier: str
    action: str
    tool_calls: int
    turns: int
    issues_completed: int


class StateMachine:
    """Deterministic phase state machine with gate enforcement.

    Every transition passes through a capacity gate. If the gate
    determines the tier is Orange or Red (for most phases), it raises
    ShutdownRequired. The caller cannot proceed.
    """

    def __init__(self, parallel_coders: int = 5):
        self.state = PhaseState(phase=0)
        self.signals = CapacitySignals(parallel_coders=parallel_coders)
        self.gates_passed: list[GateRecord] = []
        self._started = False

    @property
    def phase(self) -> int:
        return self.state.phase

    @property
    def tier(self) -> Tier:
        return classify_tier(self.signals)

    def transition(self, target_phase: int) -> Action:
        """Attempt a phase transition with gate enforcement.

        Args:
            target_phase: The phase to transition to (0-5).

        Returns:
            The action the orchestrator should take (PROCEED, SKIP_DISPATCH,
            or FINISH_CURRENT).

        Raises:
            InvalidTransition: If the transition is not valid from current phase.
            ShutdownRequired: If the gate check requires shutdown.
        """
        # First transition from Phase 0 is always valid (startup)
        if not self._started:
            self._started = True
        else:
            if target_phase not in VALID_TRANSITIONS.get(self.state.phase, frozenset()):
                raise InvalidTransition(self.state.phase, target_phase)

        # Gate check
        tier = classify_tier(self.signals)
        action = gate_action(target_phase, tier)

        # Record gate decision
        record = GateRecord(
            phase=target_phase,
            tier=tier.value,
            action=action.value,
            tool_calls=self.signals.tool_calls,
            turns=self.signals.turns,
            issues_completed=self.signals.issues_completed,
        )
        self.gates_passed.append(record)

        # Enforce shutdown
        if action in _SHUTDOWN_ACTIONS:
            raise ShutdownRequired(
                tier=tier,
                action=action,
                gates_passed=[
                    {
                        "phase": g.phase,
                        "tier": g.tier,
                        "action": g.action,
                    }
                    for g in self.gates_passed
                ],
                signals=self.signals,
            )

        # Transition
        self.state = PhaseState(phase=target_phase)
        return action

    def record_tool_call(self) -> Tier:
        """Increment tool call counter and return current tier."""
        self.signals.tool_calls += 1
        return classify_tier(self.signals)

    def record_turn(self) -> Tier:
        """Increment turn counter and return current tier."""
        self.signals.turns += 1
        return classify_tier(self.signals)

    def record_issue_completed(self) -> Tier:
        """Increment issues completed and return current tier."""
        self.signals.issues_completed += 1
        return classify_tier(self.signals)

    def get_gate_history(self) -> list[dict]:
        """Return gate history for checkpoint context_gates_passed field."""
        return [
            {"phase": g.phase, "tier": g.tier, "action": g.action}
            for g in self.gates_passed
        ]
