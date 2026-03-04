"""Tests for governance.engine.orchestrator.circuit_breaker — evaluation cycle tracking."""

import pytest

from governance.engine.orchestrator.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerTripped,
    WorkUnit,
)


class TestCircuitBreakerBasics:
    def test_new_work_unit_can_dispatch(self):
        cb = CircuitBreaker()
        assert cb.can_dispatch("issue-42") is True

    def test_get_unit_returns_none_for_unknown(self):
        cb = CircuitBreaker()
        assert cb.get_unit("issue-99") is None

    def test_record_feedback_creates_unit(self):
        cb = CircuitBreaker()
        unit = cb.record_feedback("issue-42")
        assert unit.feedback_cycles == 1
        assert unit.total_eval_cycles == 1
        assert unit.blocked is False

    def test_record_reassign_creates_unit(self):
        cb = CircuitBreaker()
        unit = cb.record_reassign("issue-42")
        assert unit.feedback_cycles == 0
        assert unit.total_eval_cycles == 1


class TestFeedbackCycleLimit:
    def test_two_feedback_cycles_allowed(self):
        cb = CircuitBreaker()
        cb.record_feedback("issue-42")
        cb.record_feedback("issue-42")
        unit = cb.get_unit("issue-42")
        assert unit.feedback_cycles == 2
        assert unit.blocked is False

    def test_third_feedback_trips_breaker(self):
        """Protocol requires Tester to emit BLOCK at cycle 3."""
        cb = CircuitBreaker()
        cb.record_feedback("issue-42")
        cb.record_feedback("issue-42")
        with pytest.raises(CircuitBreakerTripped) as exc_info:
            cb.record_feedback("issue-42")
        assert exc_info.value.reason == "feedback_cycle_limit"
        assert exc_info.value.cycles == 3
        assert exc_info.value.limit == 2

    def test_blocked_after_feedback_limit(self):
        cb = CircuitBreaker()
        for _ in range(2):
            cb.record_feedback("issue-42")
        with pytest.raises(CircuitBreakerTripped):
            cb.record_feedback("issue-42")
        assert cb.can_dispatch("issue-42") is False


class TestTotalEvalCycleLimit:
    def test_five_total_cycles_trips_breaker(self):
        cb = CircuitBreaker()
        cb.record_feedback("issue-42")   # 1
        cb.record_feedback("issue-42")   # 2
        cb.record_reassign("issue-42")   # 3
        cb.record_reassign("issue-42")   # 4
        with pytest.raises(CircuitBreakerTripped) as exc_info:
            cb.record_reassign("issue-42")  # 5 → trips
        assert exc_info.value.reason == "total_eval_cycle_limit"
        assert exc_info.value.cycles == 5

    def test_mixed_feedback_and_reassign(self):
        cb = CircuitBreaker()
        cb.record_feedback("issue-42")   # 1
        cb.record_reassign("issue-42")   # 2
        cb.record_feedback("issue-42")   # 3
        cb.record_reassign("issue-42")   # 4
        with pytest.raises(CircuitBreakerTripped):
            cb.record_reassign("issue-42")  # 5 → trips

    def test_reassign_only_hits_total_limit(self):
        cb = CircuitBreaker()
        cb.record_reassign("issue-42")  # 1
        cb.record_reassign("issue-42")  # 2
        cb.record_reassign("issue-42")  # 3
        cb.record_reassign("issue-42")  # 4
        with pytest.raises(CircuitBreakerTripped):
            cb.record_reassign("issue-42")  # 5 → trips


class TestBlockedUnitRejection:
    def test_blocked_unit_rejects_feedback(self):
        cb = CircuitBreaker()
        for _ in range(2):
            cb.record_feedback("issue-42")
        with pytest.raises(CircuitBreakerTripped):
            cb.record_feedback("issue-42")  # Trips breaker (3rd)
        with pytest.raises(CircuitBreakerTripped) as exc_info:
            cb.record_feedback("issue-42")  # Already blocked
        assert exc_info.value.reason == "work_unit_already_blocked"

    def test_blocked_unit_rejects_reassign(self):
        cb = CircuitBreaker()
        for _ in range(2):
            cb.record_feedback("issue-42")
        with pytest.raises(CircuitBreakerTripped):
            cb.record_feedback("issue-42")  # Trips breaker (3rd)
        with pytest.raises(CircuitBreakerTripped):
            cb.record_reassign("issue-42")


class TestIsolation:
    def test_independent_work_units(self):
        cb = CircuitBreaker()
        cb.record_feedback("issue-42")
        cb.record_feedback("issue-42")
        cb.record_feedback("issue-43")

        unit_42 = cb.get_unit("issue-42")
        unit_43 = cb.get_unit("issue-43")
        assert unit_42.feedback_cycles == 2
        assert unit_43.feedback_cycles == 1

    def test_all_units_property(self):
        cb = CircuitBreaker()
        cb.record_feedback("issue-42")
        cb.record_feedback("issue-43")
        assert len(cb.all_units) == 2
        assert "issue-42" in cb.all_units
        assert "issue-43" in cb.all_units


class TestCustomLimits:
    def test_custom_feedback_limit(self):
        cb = CircuitBreaker(max_feedback_cycles=1)
        cb.record_feedback("issue-42")
        with pytest.raises(CircuitBreakerTripped):
            cb.record_feedback("issue-42")  # 2nd trips at limit 1

    def test_custom_total_limit(self):
        cb = CircuitBreaker(max_total_eval_cycles=3)
        cb.record_feedback("issue-42")
        cb.record_feedback("issue-42")
        with pytest.raises(CircuitBreakerTripped):
            cb.record_reassign("issue-42")  # 3rd trips at limit 3
