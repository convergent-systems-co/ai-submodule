"""Structured event logging for the orchestrator.

Events are written by the orchestrator (deterministic code), not by agents.
This ensures the audit trail is complete regardless of agent behavior.
Format: JSONL (one JSON object per line), append-only.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class AuditEvent:
    """A single orchestrator event for the audit log."""

    event_type: str  # gate_check, phase_transition, dispatch, checkpoint, shutdown, etc.
    phase: int
    session_id: str
    tier: str | None = None
    action: str | None = None
    correlation_id: str | None = None
    detail: dict = field(default_factory=dict)
    timestamp: str = field(default="")

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class AuditLog:
    """Append-only JSONL audit log for orchestrator events.

    Thread-safety: each write opens, appends, and closes the file.
    This is safe for single-writer scenarios (the orchestrator).
    """

    def __init__(self, log_path: str | Path):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: AuditEvent) -> None:
        """Append an event to the log file."""
        entry = asdict(event)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")

    def read_all(self) -> list[dict]:
        """Read all events from the log. Returns empty list if file missing."""
        if not self.log_path.exists():
            return []
        events = []
        with open(self.log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events

    def count(self) -> int:
        """Count events in the log without loading all into memory."""
        if not self.log_path.exists():
            return 0
        count = 0
        with open(self.log_path) as f:
            for line in f:
                if line.strip():
                    count += 1
        return count
