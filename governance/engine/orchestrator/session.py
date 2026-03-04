"""Persistent session state for the step-based orchestrator.

Sessions are the orchestrator's internal state — written after every step.
Separate from checkpoints, which are user-facing recovery artifacts.

Supports two storage modes:
- Direct file I/O to a session directory (default, backward compatible)
- Storage adapter for externalized state (via ``from_adapter()`` factory)
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from governance.engine.storage import StorageAdapter


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
    dispatch_state: dict[str, dict] = field(default_factory=dict)  # task_id -> DispatchRecord.to_dict()

    # Gate history
    gate_history: list[dict] = field(default_factory=list)

    # Circuit breaker state (correlation_id -> {feedback_cycles, total_eval_cycles, blocked})
    circuit_breaker_state: dict[str, dict] = field(default_factory=dict)

    # Deployment state (phases 6-7)
    build_artifact_id: str = ""
    build_artifact_digest: str = ""
    security_scan_passed: bool = False
    deployment_environment: str = ""
    deployment_status: str = ""
    verification_passed: bool = False

    # Loop tracking
    loop_count: int = 0

    # Agent registry state (task_id -> {persona, task_id, correlation_id, status, ...})
    agent_registry: dict[str, dict] = field(default_factory=dict)

    # DevOps Engineer lifecycle (PM mode heartbeat tracking)
    devops_task_id: str = ""
    devops_last_heartbeat: str = ""

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

    Sessions are stored in .artifacts/state/sessions/{session_id}.json.

    Supports two modes:
    - Direct file I/O (default): pass ``session_dir`` to the constructor.
    - Storage adapter: use ``SessionStore.from_adapter()`` factory method
      to route I/O through a ``StorageAdapter`` instance.

    In typical deployments, a storage adapter can be selected by higher-level
    orchestration/config code (for example, based on a ``governance.storage``
    configuration such as ``governance.storage.state: "local"`` in
    project.yaml) to route transient state to an XDG state directory instead
    of the repo's ``.artifacts/`` tree.
    """

    def __init__(self, session_dir: str | Path):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self._adapter: StorageAdapter | None = None
        self._namespace: str = ""

    @classmethod
    def from_adapter(
        cls,
        adapter: StorageAdapter,
        namespace: str = "sessions",
    ) -> SessionStore:
        """Create a SessionStore backed by a StorageAdapter.

        Args:
            adapter: Storage adapter instance (LocalAdapter, RepoAdapter, etc.).
            namespace: Key prefix within the adapter (default: ``"sessions"``).

        Returns:
            A SessionStore that routes all I/O through the adapter.

        Raises:
            ValueError: If the namespace contains path traversal sequences or
                        is an absolute path.
        """
        # Validate namespace to prevent directory traversal
        clean_namespace = namespace.rstrip("/")
        if ".." in clean_namespace.split("/") or clean_namespace.startswith("/"):
            raise ValueError(
                f"Invalid namespace: {namespace!r} — "
                "must not contain '..' segments or start with '/'"
            )

        # Derive a session_dir from the adapter's base directory for
        # compatibility with code that reads store.session_dir.
        base = getattr(
            adapter, "base_dir",
            Path(tempfile.gettempdir()) / "governance-sessions",
        )
        session_dir = Path(base) / clean_namespace

        # Use the real constructor so any __init__ logic is consistently applied.
        store = cls(session_dir)
        store._adapter = adapter
        store._namespace = clean_namespace
        return store

    def _safe_id(self, session_id: str) -> str:
        """Sanitize a session ID for use as a filename/key."""
        return session_id.replace("\\", "-").replace("/", "-").replace(" ", "-")

    def _adapter_key(self, session_id: str) -> str:
        """Build a storage adapter key for a session."""
        safe = self._safe_id(session_id)
        return f"{self._namespace}/{safe}.json"

    def _path_for(self, session_id: str) -> Path:
        safe_id = self._safe_id(session_id)
        return self.session_dir / f"{safe_id}.json"

    def save(self, session: PersistedSession) -> Path:
        """Write session state to disk. Returns the file path."""
        session.updated_at = datetime.now(timezone.utc).isoformat()

        if self._adapter is not None:
            key = self._adapter_key(session.session_id)
            data = json.dumps(asdict(session), indent=2).encode("utf-8")
            self._adapter.put(key, data, metadata={
                "session_id": session.session_id,
                "updated_at": session.updated_at,
            })
            # Also return a Path for compatibility
            return self._path_for(session.session_id)

        path = self._path_for(session.session_id)
        with open(path, "w") as f:
            json.dump(asdict(session), f, indent=2)
        return path

    def load(self, session_id: str) -> PersistedSession | None:
        """Load a session by ID. Returns None if not found."""
        if self._adapter is not None:
            from governance.engine.storage import KeyNotFoundError

            key = self._adapter_key(session_id)
            try:
                raw, _meta = self._adapter.get(key)
            except (KeyError, KeyNotFoundError):
                # Adapter reports missing key: treat as "not found"
                return None
            data = json.loads(raw)
            return PersistedSession(**{
                k: v for k, v in data.items()
                if k in PersistedSession.__dataclass_fields__
            })

        path = self._path_for(session_id)
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        return PersistedSession(**{k: v for k, v in data.items() if k in PersistedSession.__dataclass_fields__})

    def load_latest(self) -> PersistedSession | None:
        """Load the most recently updated session. Returns None if none exist."""
        if self._adapter is not None:
            from governance.engine.storage import KeyNotFoundError

            keys = self._adapter.list(f"{self._namespace}/")
            if not keys:
                return None
            # Load all sessions and find the one with the latest updated_at
            latest: PersistedSession | None = None
            for key in keys:
                try:
                    raw, _meta = self._adapter.get(key)
                    data = json.loads(raw)
                    session = PersistedSession(**{
                        k: v for k, v in data.items()
                        if k in PersistedSession.__dataclass_fields__
                    })
                    if latest is None or session.updated_at > latest.updated_at:
                        latest = session
                except (KeyError, KeyNotFoundError, json.JSONDecodeError):
                    continue
            return latest

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
        if self._adapter is not None:
            from governance.engine.storage import KeyNotFoundError

            keys = self._adapter.list(f"{self._namespace}/")
            # Extract session IDs from keys: "sessions/name.json" -> "name"
            ids = []
            for key in keys:
                name = key.rsplit("/", 1)[-1]
                if name.endswith(".json"):
                    ids.append(name[:-5])
            # Use metadata sidecars for sorting to avoid N+1 full reads.
            # Fall back to loading the full session only if metadata is unavailable.
            sessions_with_time: list[tuple[str, str]] = []
            for sid in ids:
                updated = ""
                try:
                    _data, meta = self._adapter.get(self._adapter_key(sid))
                    updated = meta.get("updated_at", "")
                    if not updated:
                        # Metadata sidecar missing updated_at; parse from payload
                        data = json.loads(_data)
                        updated = data.get("updated_at", "")
                except (KeyError, KeyNotFoundError):
                    pass
                except Exception:
                    pass
                sessions_with_time.append((sid, updated))
            sessions_with_time.sort(key=lambda x: x[1], reverse=True)
            return [s[0] for s in sessions_with_time]

        sessions = sorted(
            self.session_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        return [p.stem for p in sessions]
