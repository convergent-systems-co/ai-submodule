"""Deterministic tier classification and gate enforcement.

Extracts the context capacity logic from startup.md into testable Python.
All thresholds are from the startup.md context gate protocol.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Tier(Enum):
    """Four-tier capacity model. Any single Red signal -> Red."""

    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"

    def __ge__(self, other: Tier) -> bool:
        order = {Tier.GREEN: 0, Tier.YELLOW: 1, Tier.ORANGE: 2, Tier.RED: 3}
        return order[self] >= order[other]

    def __gt__(self, other: Tier) -> bool:
        order = {Tier.GREEN: 0, Tier.YELLOW: 1, Tier.ORANGE: 2, Tier.RED: 3}
        return order[self] > order[other]

    def __le__(self, other: Tier) -> bool:
        order = {Tier.GREEN: 0, Tier.YELLOW: 1, Tier.ORANGE: 2, Tier.RED: 3}
        return order[self] <= order[other]

    def __lt__(self, other: Tier) -> bool:
        order = {Tier.GREEN: 0, Tier.YELLOW: 1, Tier.ORANGE: 2, Tier.RED: 3}
        return order[self] < order[other]


class Action(Enum):
    """Gate actions determined by (phase, tier) combination."""

    PROCEED = "proceed"
    SKIP_DISPATCH = "skip-dispatch"
    FINISH_CURRENT = "finish-current"
    CHECKPOINT = "checkpoint"
    EMERGENCY_STOP = "emergency-stop"


# ---------------------------------------------------------------------------
# Thresholds -- extracted from startup.md lines 33-41
# ---------------------------------------------------------------------------

# Tool call thresholds
TOOL_CALLS_GREEN_MAX = 49
TOOL_CALLS_YELLOW_MAX = 64
TOOL_CALLS_ORANGE_MAX = 79
# > 79 = Red

# Turn thresholds
TURNS_GREEN_MAX = 59
TURNS_YELLOW_MAX = 99
TURNS_ORANGE_MAX = 139
# > 139 = Red

# Issues completed thresholds are relative to parallel_coders (N):
#   Green: < N-2
#   Yellow: == N-2
#   Orange: == N-1
#   Red: >= N


@dataclass
class CapacitySignals:
    """Observable signals for tier classification."""

    tool_calls: int = 0
    turns: int = 0
    issues_completed: int = 0
    parallel_coders: int = 5  # -1 = unlimited (disables issue count signal)
    system_warning: bool = False
    degraded_recall: bool = False


def _classify_tool_calls(count: int) -> Tier:
    if count <= TOOL_CALLS_GREEN_MAX:
        return Tier.GREEN
    if count <= TOOL_CALLS_YELLOW_MAX:
        return Tier.YELLOW
    if count <= TOOL_CALLS_ORANGE_MAX:
        return Tier.ORANGE
    return Tier.RED


def _classify_turns(count: int) -> Tier:
    if count <= TURNS_GREEN_MAX:
        return Tier.GREEN
    if count <= TURNS_YELLOW_MAX:
        return Tier.YELLOW
    if count <= TURNS_ORANGE_MAX:
        return Tier.ORANGE
    return Tier.RED


def _classify_issues(completed: int, parallel_coders: int) -> Tier:
    if parallel_coders == -1:
        return Tier.GREEN  # Unlimited mode -- issue count signal disabled
    if parallel_coders <= 2:
        # Edge case: N <= 2 means N-2 <= 0, so any completion triggers Yellow+
        if completed >= parallel_coders:
            return Tier.RED
        if completed >= parallel_coders - 1:
            return Tier.ORANGE
        if completed >= max(parallel_coders - 2, 0):
            return Tier.YELLOW
        return Tier.GREEN
    if completed < parallel_coders - 2:
        return Tier.GREEN
    if completed == parallel_coders - 2:
        return Tier.YELLOW
    if completed == parallel_coders - 1:
        return Tier.ORANGE
    return Tier.RED


def classify_tier(signals: CapacitySignals) -> Tier:
    """Deterministic tier classification.

    Evaluates all signals and returns the highest (most severe) tier.
    Any single Red signal escalates the entire classification to Red.
    """
    # Hard Red signals -- always Red regardless of other signals
    if signals.system_warning:
        return Tier.RED
    if signals.degraded_recall:
        return Tier.RED

    tiers = [
        _classify_tool_calls(signals.tool_calls),
        _classify_turns(signals.turns),
        _classify_issues(signals.issues_completed, signals.parallel_coders),
    ]

    # Return highest tier (most severe)
    return max(tiers)


# ---------------------------------------------------------------------------
# Phase-Tier-Action matrix -- extracted from startup.md lines 117-157
# ---------------------------------------------------------------------------

_GATE_ACTIONS: dict[tuple[int, Tier], Action] = {
    # Phase 0: Checkpoint Recovery
    (0, Tier.GREEN): Action.PROCEED,
    (0, Tier.YELLOW): Action.PROCEED,
    (0, Tier.ORANGE): Action.EMERGENCY_STOP,
    (0, Tier.RED): Action.EMERGENCY_STOP,
    # Phase 1: Pre-flight & Triage
    (1, Tier.GREEN): Action.PROCEED,
    (1, Tier.YELLOW): Action.PROCEED,
    (1, Tier.ORANGE): Action.EMERGENCY_STOP,
    (1, Tier.RED): Action.EMERGENCY_STOP,
    # Phase 2: Parallel Planning
    (2, Tier.GREEN): Action.PROCEED,
    (2, Tier.YELLOW): Action.PROCEED,
    (2, Tier.ORANGE): Action.EMERGENCY_STOP,
    (2, Tier.RED): Action.EMERGENCY_STOP,
    # Phase 3: Parallel Dispatch
    (3, Tier.GREEN): Action.PROCEED,
    (3, Tier.YELLOW): Action.SKIP_DISPATCH,
    (3, Tier.ORANGE): Action.EMERGENCY_STOP,
    (3, Tier.RED): Action.EMERGENCY_STOP,
    # Phase 4: Collect & Review
    (4, Tier.GREEN): Action.PROCEED,
    (4, Tier.YELLOW): Action.FINISH_CURRENT,
    (4, Tier.ORANGE): Action.FINISH_CURRENT,
    (4, Tier.RED): Action.EMERGENCY_STOP,
    # Phase 5: Merge & Loop
    (5, Tier.GREEN): Action.PROCEED,
    (5, Tier.YELLOW): Action.PROCEED,
    (5, Tier.ORANGE): Action.EMERGENCY_STOP,
    (5, Tier.RED): Action.EMERGENCY_STOP,
    # Phase 6: Build & Package (optional deployment)
    (6, Tier.GREEN): Action.PROCEED,
    (6, Tier.YELLOW): Action.PROCEED,
    (6, Tier.ORANGE): Action.CHECKPOINT,
    (6, Tier.RED): Action.EMERGENCY_STOP,
    # Phase 7: Deploy & Verify (optional deployment)
    (7, Tier.GREEN): Action.PROCEED,
    (7, Tier.YELLOW): Action.SKIP_DISPATCH,
    (7, Tier.ORANGE): Action.CHECKPOINT,
    (7, Tier.RED): Action.EMERGENCY_STOP,
}

VALID_PHASES = frozenset(range(8))  # 0-7


def gate_action(phase: int, tier: Tier) -> Action:
    """Deterministic gate action lookup.

    Args:
        phase: Pipeline phase (0-7).
        tier: Current capacity tier.

    Returns:
        The action the orchestrator must take.

    Raises:
        ValueError: If phase is not 0-7.
    """
    if phase not in VALID_PHASES:
        raise ValueError(f"Invalid phase {phase}. Must be 0-7.")
    return _GATE_ACTIONS[(phase, tier)]


def format_gate_block(phase: int, signals: CapacitySignals) -> str:
    """Produce the mandatory context gate output block.

    This generates the structured block that startup.md requires at every
    phase boundary. The orchestrator emits this for audit/observability.
    """
    tier = classify_tier(signals)
    action = gate_action(phase, tier)
    return (
        f"--- CONTEXT GATE ---\n"
        f"Phase: {phase}\n"
        f"Tool calls this session: {signals.tool_calls}\n"
        f"Estimated turns: {signals.turns}\n"
        f"Tier: {tier.value.capitalize()}\n"
        f"Action: {action.value}\n"
        f"---"
    )
