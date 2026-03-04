"""Dispatch state tracking for agent tasks.

Tracks the lifecycle of each dispatched task from PENDING through
COMPLETED/FAILED/CANCELLED. State is serializable for session persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class DispatchState(Enum):
    """Lifecycle states for a dispatched task."""

    PENDING = "pending"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DispatchRecord:
    """State record for a single dispatched task.

    Attributes:
        task_id: Platform-specific task identifier (e.g. ``cc-abc12345``).
        correlation_id: Issue or PR reference (e.g. ``issue-42``).
        persona: Agent persona name (e.g. ``coder``).
        state: Current lifecycle state.
        created_at: ISO timestamp when the record was created.
        dispatched_at: ISO timestamp when the task was dispatched.
        completed_at: ISO timestamp when the task completed/failed/was cancelled.
    """

    task_id: str
    correlation_id: str
    persona: str
    state: DispatchState = DispatchState.PENDING
    created_at: str = ""
    dispatched_at: str = ""
    completed_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        return {
            "task_id": self.task_id,
            "correlation_id": self.correlation_id,
            "persona": self.persona,
            "state": self.state.value,
            "created_at": self.created_at,
            "dispatched_at": self.dispatched_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DispatchRecord:
        """Deserialize from a dict."""
        return cls(
            task_id=data["task_id"],
            correlation_id=data["correlation_id"],
            persona=data["persona"],
            state=DispatchState(data.get("state", "pending")),
            created_at=data.get("created_at", ""),
            dispatched_at=data.get("dispatched_at", ""),
            completed_at=data.get("completed_at", ""),
        )


class DispatchTracker:
    """Tracks dispatch state for all tasks in a session.

    Provides methods to transition states, query by state, and
    serialize/deserialize for session persistence.
    """

    def __init__(self):
        self._records: dict[str, DispatchRecord] = {}

    def create(self, task_id: str, correlation_id: str, persona: str) -> DispatchRecord:
        """Create a new dispatch record in PENDING state.

        Args:
            task_id: Platform-specific task identifier.
            correlation_id: Issue or PR reference.
            persona: Agent persona name.

        Returns:
            The newly created DispatchRecord.

        Raises:
            ValueError: If task_id already exists.
        """
        if task_id in self._records:
            raise ValueError(f"Dispatch record already exists for task_id '{task_id}'.")
        record = DispatchRecord(
            task_id=task_id,
            correlation_id=correlation_id,
            persona=persona,
        )
        self._records[task_id] = record
        return record

    def transition(self, task_id: str, new_state: DispatchState) -> DispatchRecord:
        """Transition a task to a new state.

        Automatically sets the appropriate timestamp:
        - DISPATCHED: sets ``dispatched_at``
        - COMPLETED/FAILED/CANCELLED: sets ``completed_at``

        Args:
            task_id: The task to transition.
            new_state: The target state.

        Returns:
            The updated DispatchRecord.

        Raises:
            KeyError: If task_id is not found.
        """
        record = self._records[task_id]
        now = datetime.now(timezone.utc).isoformat()

        record.state = new_state

        if new_state == DispatchState.DISPATCHED:
            record.dispatched_at = now
        elif new_state in (
            DispatchState.COMPLETED,
            DispatchState.FAILED,
            DispatchState.CANCELLED,
        ):
            record.completed_at = now

        return record

    def get(self, task_id: str) -> DispatchRecord | None:
        """Get a dispatch record by task_id."""
        return self._records.get(task_id)

    def query_by_state(self, state: DispatchState) -> list[DispatchRecord]:
        """Return all records in the given state."""
        return [r for r in self._records.values() if r.state == state]

    def all_records(self) -> dict[str, DispatchRecord]:
        """Return a copy of all records."""
        return dict(self._records)

    def to_dict(self) -> dict[str, dict]:
        """Serialize all records to a JSON-compatible dict."""
        return {tid: record.to_dict() for tid, record in self._records.items()}

    @classmethod
    def from_dict(cls, data: dict[str, dict]) -> DispatchTracker:
        """Deserialize from a dict of record dicts."""
        tracker = cls()
        for tid, record_data in data.items():
            tracker._records[tid] = DispatchRecord.from_dict(record_data)
        return tracker
