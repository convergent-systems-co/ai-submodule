"""Tests for governance.engine.orchestrator.state_machine — phase transitions and gate enforcement."""

import pytest

from governance.engine.orchestrator.capacity import Action, Tier
from governance.engine.orchestrator.state_machine import (
    InvalidTransition,
    PhaseState,
    ShutdownRequired,
    StateMachine,
    VALID_TRANSITIONS,
)


# ---------------------------------------------------------------------------
# Valid transitions
# ---------------------------------------------------------------------------


class TestValidTransitions:
    def test_phase0_can_go_anywhere(self):
        """Phase 0 (recovery) can resume to any phase."""
        assert VALID_TRANSITIONS[0] == frozenset({1, 2, 3, 4, 5})

    def test_phase1_to_phase2_only(self):
        assert VALID_TRANSITIONS[1] == frozenset({2})

    def test_phase2_to_phase3_only(self):
        assert VALID_TRANSITIONS[2] == frozenset({3})

    def test_phase3_to_phase4_only(self):
        assert VALID_TRANSITIONS[3] == frozenset({4})

    def test_phase4_can_loop_or_merge(self):
        assert VALID_TRANSITIONS[4] == frozenset({3, 5})

    def test_phase5_loops_to_phase1(self):
        assert VALID_TRANSITIONS[5] == frozenset({1})


# ---------------------------------------------------------------------------
# State machine basic operations
# ---------------------------------------------------------------------------


class TestStateMachineBasics:
    def test_initial_state_is_phase0(self):
        sm = StateMachine()
        assert sm.phase == 0

    def test_initial_tier_is_green(self):
        sm = StateMachine()
        assert sm.tier == Tier.GREEN

    def test_transition_updates_phase(self):
        sm = StateMachine()
        sm.transition(1)  # Phase 0 → 1
        assert sm.phase == 1

    def test_sequential_pipeline(self):
        """Walk through the full Phase 0→1→2→3→4→5 pipeline."""
        sm = StateMachine()
        sm.transition(1)
        assert sm.phase == 1
        sm.transition(2)
        assert sm.phase == 2
        sm.transition(3)
        assert sm.phase == 3
        sm.transition(4)
        assert sm.phase == 4
        sm.transition(5)
        assert sm.phase == 5

    def test_loop_phase5_to_phase1(self):
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        sm.transition(3)
        sm.transition(4)
        sm.transition(5)
        sm.transition(1)  # Loop
        assert sm.phase == 1

    def test_phase4_feedback_loop(self):
        """Phase 4 → 3 → 4 (feedback cycle)."""
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        sm.transition(3)
        sm.transition(4)
        sm.transition(3)  # Feedback
        sm.transition(4)  # Re-evaluate
        assert sm.phase == 4


# ---------------------------------------------------------------------------
# Invalid transitions
# ---------------------------------------------------------------------------


class TestInvalidTransitions:
    def test_phase1_to_phase3_invalid(self):
        sm = StateMachine()
        sm.transition(1)
        with pytest.raises(InvalidTransition) as exc_info:
            sm.transition(3)  # Must go through Phase 2
        assert exc_info.value.from_phase == 1
        assert exc_info.value.to_phase == 3

    def test_phase2_to_phase5_invalid(self):
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        with pytest.raises(InvalidTransition):
            sm.transition(5)

    def test_phase3_to_phase5_invalid(self):
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        sm.transition(3)
        with pytest.raises(InvalidTransition):
            sm.transition(5)

    def test_phase5_to_phase3_invalid(self):
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        sm.transition(3)
        sm.transition(4)
        sm.transition(5)
        with pytest.raises(InvalidTransition):
            sm.transition(3)


# ---------------------------------------------------------------------------
# Gate enforcement — shutdown on Orange/Red
# ---------------------------------------------------------------------------


class TestGateEnforcement:
    def test_orange_tool_calls_triggers_shutdown(self):
        sm = StateMachine()
        sm.signals.tool_calls = 70  # Orange
        with pytest.raises(ShutdownRequired) as exc_info:
            sm.transition(1)
        assert exc_info.value.tier == Tier.ORANGE
        assert exc_info.value.action == Action.EMERGENCY_STOP

    def test_red_triggers_shutdown(self):
        sm = StateMachine()
        sm.signals.tool_calls = 100  # Red
        with pytest.raises(ShutdownRequired) as exc_info:
            sm.transition(1)
        assert exc_info.value.tier == Tier.RED

    def test_system_warning_triggers_shutdown(self):
        sm = StateMachine()
        sm.signals.system_warning = True
        with pytest.raises(ShutdownRequired):
            sm.transition(1)

    def test_yellow_phase3_returns_skip_dispatch(self):
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        sm.signals.tool_calls = 55  # Yellow
        action = sm.transition(3)
        assert action == Action.SKIP_DISPATCH

    def test_yellow_phase4_returns_finish_current(self):
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        sm.transition(3)
        sm.signals.tool_calls = 55  # Yellow
        action = sm.transition(4)
        assert action == Action.FINISH_CURRENT

    def test_orange_phase4_returns_finish_current(self):
        """Phase 4 at Orange: finish current PR only."""
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        sm.transition(3)
        sm.signals.tool_calls = 70  # Orange
        action = sm.transition(4)
        assert action == Action.FINISH_CURRENT

    def test_green_returns_proceed(self):
        sm = StateMachine()
        action = sm.transition(1)
        assert action == Action.PROCEED


# ---------------------------------------------------------------------------
# Signal recording
# ---------------------------------------------------------------------------


class TestSignalRecording:
    def test_record_tool_call(self):
        sm = StateMachine()
        tier = sm.record_tool_call()
        assert sm.signals.tool_calls == 1
        assert tier == Tier.GREEN

    def test_record_tool_call_tier_change(self):
        sm = StateMachine()
        sm.signals.tool_calls = 49
        tier = sm.record_tool_call()  # 50 → Yellow
        assert tier == Tier.YELLOW

    def test_record_turn(self):
        sm = StateMachine()
        tier = sm.record_turn()
        assert sm.signals.turns == 1
        assert tier == Tier.GREEN

    def test_record_issue_completed(self):
        sm = StateMachine()
        sm.signals.parallel_coders = 5
        sm.signals.issues_completed = 4
        tier = sm.record_issue_completed()  # 5 → Red
        assert tier == Tier.RED


# ---------------------------------------------------------------------------
# Gate history
# ---------------------------------------------------------------------------


class TestGateHistory:
    def test_gate_history_recorded(self):
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        history = sm.get_gate_history()
        assert len(history) == 2
        assert history[0]["phase"] == 1
        assert history[0]["tier"] == "green"
        assert history[0]["action"] == "proceed"

    def test_shutdown_includes_full_history(self):
        sm = StateMachine()
        sm.transition(1)
        sm.signals.tool_calls = 100
        with pytest.raises(ShutdownRequired) as exc_info:
            sm.transition(2)
        # History includes both the successful Phase 1 and failed Phase 2
        assert len(exc_info.value.gates_passed) == 2

    def test_gate_history_has_signals(self):
        sm = StateMachine()
        sm.signals.tool_calls = 25
        sm.signals.turns = 30
        sm.transition(1)
        record = sm.gates_passed[0]
        assert record.tool_calls == 25
        assert record.turns == 30


# ---------------------------------------------------------------------------
# Serialization (to_dict / from_dict)
# ---------------------------------------------------------------------------


class TestStateMachineSerialization:
    def test_to_dict_initial_state(self):
        sm = StateMachine(parallel_coders=6)
        d = sm.to_dict()
        assert d["phase"] == 0
        assert d["signals"]["parallel_coders"] == 6
        assert d["signals"]["tool_calls"] == 0
        assert d["gates_passed"] == []
        assert d["started"] is False

    def test_to_dict_after_transitions(self):
        sm = StateMachine()
        sm.transition(1)
        sm.signals.tool_calls = 25
        sm.transition(2)
        d = sm.to_dict()
        assert d["phase"] == 2
        assert d["signals"]["tool_calls"] == 25
        assert len(d["gates_passed"]) == 2
        assert d["started"] is True

    def test_round_trip(self):
        original = StateMachine(parallel_coders=8)
        original.transition(1)
        original.signals.tool_calls = 30
        original.signals.turns = 15
        original.signals.issues_completed = 2
        original.transition(2)

        d = original.to_dict()
        restored = StateMachine.from_dict(d)

        assert restored.phase == original.phase
        assert restored.signals.tool_calls == original.signals.tool_calls
        assert restored.signals.turns == original.signals.turns
        assert restored.signals.issues_completed == original.signals.issues_completed
        assert restored.signals.parallel_coders == 8
        assert len(restored.gates_passed) == 2
        assert restored._started is True

    def test_round_trip_preserves_tier(self):
        sm = StateMachine()
        sm.signals.tool_calls = 55  # Yellow
        d = sm.to_dict()
        restored = StateMachine.from_dict(d)
        assert restored.tier == Tier.YELLOW

    def test_round_trip_continues_transitions(self):
        """Restored state machine should allow valid transitions from restored phase."""
        sm = StateMachine()
        sm.transition(1)
        sm.transition(2)
        d = sm.to_dict()

        restored = StateMachine.from_dict(d)
        action = restored.transition(3)  # Phase 2 → 3
        assert action == Action.PROCEED
        assert restored.phase == 3

    def test_from_dict_defaults(self):
        restored = StateMachine.from_dict({})
        assert restored.phase == 0
        assert restored.signals.tool_calls == 0
        assert restored._started is False

    def test_gate_records_preserved(self):
        sm = StateMachine()
        sm.signals.tool_calls = 10
        sm.transition(1)
        d = sm.to_dict()
        restored = StateMachine.from_dict(d)
        assert restored.gates_passed[0].tool_calls == 10
        assert restored.gates_passed[0].tier == "green"

    def test_system_warning_preserved(self):
        sm = StateMachine()
        sm.signals.system_warning = True
        d = sm.to_dict()
        restored = StateMachine.from_dict(d)
        assert restored.signals.system_warning is True
        assert restored.tier == Tier.RED
