"""Tests for governance.engine.orchestrator.dispatch_state."""

import pytest

from governance.engine.orchestrator.dispatch_state import (
    DispatchRecord,
    DispatchState,
    DispatchTracker,
)


class TestDispatchState:
    def test_enum_values(self):
        assert DispatchState.PENDING.value == "pending"
        assert DispatchState.DISPATCHED.value == "dispatched"
        assert DispatchState.RUNNING.value == "running"
        assert DispatchState.COMPLETED.value == "completed"
        assert DispatchState.FAILED.value == "failed"
        assert DispatchState.CANCELLED.value == "cancelled"

    def test_enum_from_value(self):
        assert DispatchState("pending") == DispatchState.PENDING
        assert DispatchState("completed") == DispatchState.COMPLETED


class TestDispatchRecord:
    def test_defaults(self):
        record = DispatchRecord(
            task_id="cc-abc123",
            correlation_id="issue-42",
            persona="coder",
        )
        assert record.state == DispatchState.PENDING
        assert record.created_at != ""
        assert record.dispatched_at == ""
        assert record.completed_at == ""

    def test_to_dict(self):
        record = DispatchRecord(
            task_id="cc-abc123",
            correlation_id="issue-42",
            persona="coder",
        )
        d = record.to_dict()
        assert d["task_id"] == "cc-abc123"
        assert d["correlation_id"] == "issue-42"
        assert d["persona"] == "coder"
        assert d["state"] == "pending"

    def test_from_dict(self):
        data = {
            "task_id": "cc-abc123",
            "correlation_id": "issue-42",
            "persona": "coder",
            "state": "dispatched",
            "created_at": "2026-01-01T00:00:00+00:00",
            "dispatched_at": "2026-01-01T00:00:01+00:00",
            "completed_at": "",
        }
        record = DispatchRecord.from_dict(data)
        assert record.task_id == "cc-abc123"
        assert record.state == DispatchState.DISPATCHED
        assert record.dispatched_at == "2026-01-01T00:00:01+00:00"

    def test_roundtrip(self):
        original = DispatchRecord(
            task_id="cc-xyz",
            correlation_id="issue-99",
            persona="test-evaluator",
            state=DispatchState.COMPLETED,
            created_at="2026-01-01T00:00:00+00:00",
            dispatched_at="2026-01-01T00:00:01+00:00",
            completed_at="2026-01-01T00:01:00+00:00",
        )
        restored = DispatchRecord.from_dict(original.to_dict())
        assert restored.task_id == original.task_id
        assert restored.state == original.state
        assert restored.completed_at == original.completed_at


class TestDispatchTracker:
    def test_create(self):
        tracker = DispatchTracker()
        record = tracker.create("cc-1", "issue-42", "coder")
        assert record.task_id == "cc-1"
        assert record.state == DispatchState.PENDING

    def test_create_duplicate_raises(self):
        tracker = DispatchTracker()
        tracker.create("cc-1", "issue-42", "coder")
        with pytest.raises(ValueError, match="already exists"):
            tracker.create("cc-1", "issue-42", "coder")

    def test_transition_to_dispatched(self):
        tracker = DispatchTracker()
        tracker.create("cc-1", "issue-42", "coder")
        record = tracker.transition("cc-1", DispatchState.DISPATCHED)
        assert record.state == DispatchState.DISPATCHED
        assert record.dispatched_at != ""

    def test_transition_to_completed(self):
        tracker = DispatchTracker()
        tracker.create("cc-1", "issue-42", "coder")
        tracker.transition("cc-1", DispatchState.DISPATCHED)
        record = tracker.transition("cc-1", DispatchState.COMPLETED)
        assert record.state == DispatchState.COMPLETED
        assert record.completed_at != ""

    def test_transition_to_failed(self):
        tracker = DispatchTracker()
        tracker.create("cc-1", "issue-42", "coder")
        tracker.transition("cc-1", DispatchState.DISPATCHED)
        record = tracker.transition("cc-1", DispatchState.FAILED)
        assert record.state == DispatchState.FAILED
        assert record.completed_at != ""

    def test_transition_to_cancelled(self):
        tracker = DispatchTracker()
        tracker.create("cc-1", "issue-42", "coder")
        record = tracker.transition("cc-1", DispatchState.CANCELLED)
        assert record.state == DispatchState.CANCELLED
        assert record.completed_at != ""

    def test_transition_unknown_task_raises(self):
        tracker = DispatchTracker()
        with pytest.raises(KeyError):
            tracker.transition("nonexistent", DispatchState.COMPLETED)

    def test_get(self):
        tracker = DispatchTracker()
        tracker.create("cc-1", "issue-42", "coder")
        assert tracker.get("cc-1") is not None
        assert tracker.get("nonexistent") is None

    def test_query_by_state(self):
        tracker = DispatchTracker()
        tracker.create("cc-1", "issue-42", "coder")
        tracker.create("cc-2", "issue-43", "coder")
        tracker.transition("cc-1", DispatchState.DISPATCHED)

        pending = tracker.query_by_state(DispatchState.PENDING)
        dispatched = tracker.query_by_state(DispatchState.DISPATCHED)
        assert len(pending) == 1
        assert pending[0].task_id == "cc-2"
        assert len(dispatched) == 1
        assert dispatched[0].task_id == "cc-1"

    def test_all_records(self):
        tracker = DispatchTracker()
        tracker.create("cc-1", "issue-42", "coder")
        tracker.create("cc-2", "issue-43", "test-evaluator")
        records = tracker.all_records()
        assert len(records) == 2
        assert "cc-1" in records
        assert "cc-2" in records

    def test_to_dict(self):
        tracker = DispatchTracker()
        tracker.create("cc-1", "issue-42", "coder")
        tracker.transition("cc-1", DispatchState.DISPATCHED)
        d = tracker.to_dict()
        assert "cc-1" in d
        assert d["cc-1"]["state"] == "dispatched"

    def test_from_dict(self):
        data = {
            "cc-1": {
                "task_id": "cc-1",
                "correlation_id": "issue-42",
                "persona": "coder",
                "state": "completed",
                "created_at": "2026-01-01T00:00:00+00:00",
                "dispatched_at": "2026-01-01T00:00:01+00:00",
                "completed_at": "2026-01-01T00:01:00+00:00",
            },
        }
        tracker = DispatchTracker.from_dict(data)
        record = tracker.get("cc-1")
        assert record is not None
        assert record.state == DispatchState.COMPLETED

    def test_roundtrip(self):
        tracker = DispatchTracker()
        tracker.create("cc-1", "issue-42", "coder")
        tracker.transition("cc-1", DispatchState.DISPATCHED)
        tracker.create("cc-2", "issue-43", "test-evaluator")
        tracker.transition("cc-2", DispatchState.DISPATCHED)
        tracker.transition("cc-2", DispatchState.COMPLETED)

        serialized = tracker.to_dict()
        restored = DispatchTracker.from_dict(serialized)

        assert restored.get("cc-1").state == DispatchState.DISPATCHED
        assert restored.get("cc-2").state == DispatchState.COMPLETED

    def test_empty_tracker_to_dict(self):
        tracker = DispatchTracker()
        assert tracker.to_dict() == {}

    def test_from_empty_dict(self):
        tracker = DispatchTracker.from_dict({})
        assert tracker.all_records() == {}
