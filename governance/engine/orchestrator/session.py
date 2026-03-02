"""Persistent session state for the step-based orchestrator.

Sessions are the orchestrator's internal state — written after every step.
Separate from checkpoints, which are user-facing recovery artifacts.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class PersistedSession:
    """Full orchestrator state that survives process death and context resets."""

    session_id: str = ""
    current_phase: int = 0
    completed_phases: list[int] = field(default_factory=list)

    # Capacity signals
    tool_calls: int = 0
    turns: int = 0
    issues_completed: int = 0

    # Work state
    issues_selected: list[str] = field(default_factory=list)
    issues_done: list[str] = field(default_factory=list)
    prs_created: list[str] = field(default_factory=list)
    prs_resolved: list[str] = field(default_factory=list)
    prs_remaining: list[str] = field(default_factory=list)
    plans: dict[str, str] = field(default_factory=dict)

    # Dispatch state
    dispatched_task_ids: list[str] = field(default_factory=list)
    dispatch_results: list[dict] = field(default_factory=list)

    # Gate history
    gate_history: list[dict] = field(default_factory=list)

    # Circuit breaker state (correlation_id -> {feedback_cycles, total_eval_cycles, blocked})
    circuit_breaker_state: dict[str, dict] = field(default_factory=dict)

    # Loop tracking
    loop_count: int = 0

    # State machine internals
    state_machine: dict = field(default_factory=dict)

    # Timestamps
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at


class SessionStore:
    """Read/write session state to disk.

    Sessions are stored in .governance/state/sessions/{session_id}.json.
    """

    def __init__(self, session_dir: str | Path):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, session_id: str) -> Path:
        safe_id = session_id.replace("/", "-").replace(" ", "-")
        return self.session_dir / f"{safe_id}.json"

    def save(self, session: PersistedSession) -> Path:
        """Write session state to disk. Returns the file path."""
        session.updated_at = datetime.now(timezone.utc).isoformat()
        path = self._path_for(session.session_id)
        with open(path, "w") as f:
            json.dump(asdict(session), f, indent=2)
        return path

    def load(self, session_id: str) -> PersistedSession | None:
        """Load a session by ID. Returns None if not found."""
        path = self._path_for(session_id)
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        return PersistedSession(**{k: v for k, v in data.items() if k in PersistedSession.__dataclass_fields__})

    def load_latest(self) -> PersistedSession | None:
        """Load the most recently updated session. Returns None if none exist."""
        sessions = sorted(
            self.session_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not sessions:
            return None
        with open(sessions[0]) as f:
            data = json.load(f)
        return PersistedSession(**{k: v for k, v in data.items() if k in PersistedSession.__dataclass_fields__})

    def list_sessions(self) -> list[str]:
        """List all session IDs (most recent first)."""
        sessions = sorted(
            self.session_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return [p.stem for p in sessions]
