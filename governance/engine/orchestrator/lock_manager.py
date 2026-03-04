"""Cross-session work locking for the orchestrator.

Prevents multiple concurrent orchestrator sessions from claiming the same
GitHub issue.  Uses advisory file locking (``fcntl.flock`` on Unix) to
eliminate TOCTOU races on the lock files themselves.

Lock files live under the XDG state directory (same root as
``governance.engine.storage``):

    ``~/.local/state/dark-governance/locks/issues/issue-{N}.lock.json``

Each lock file records the claiming session, a heartbeat timestamp, and a
TTL.  Stale locks (heartbeat older than TTL) are automatically cleaned up
on the next claim or list operation.

Usage::

    from governance.engine.orchestrator.lock_manager import LockManager

    mgr = LockManager(session_id="session-abc123")
    claimed = mgr.claim(42)          # True if we got the lock
    mgr.heartbeat(42)                # Refresh the heartbeat timestamp
    mgr.release(42)                  # Release the lock

    # Filter a list of issues, removing those claimed by other sessions
    available = mgr.filter_claimed_issues(["#42", "#43", "#44"])
"""

from __future__ import annotations

import fcntl
import json
import os
import platform
import socket
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Default TTL: 1 hour
DEFAULT_TTL_SECONDS = 3600

# Heartbeat interval recommendation (callers should call heartbeat at this rate)
HEARTBEAT_INTERVAL_SECONDS = 60


def _get_locks_dir(base_dir: Path | None = None) -> Path:
    """Resolve the locks directory under the XDG state path.

    Uses the same XDG resolution logic as ``governance.engine.storage``.

    Args:
        base_dir: Override the base directory.  If ``None``, uses the
                  platform-appropriate XDG state directory.

    Returns:
        Path to ``locks/issues/`` under the governance state root.
    """
    if base_dir is not None:
        root = base_dir
    else:
        # Inline XDG resolution (same logic as storage._get_xdg_state_dir)
        xdg_state = os.environ.get("XDG_STATE_HOME")
        if xdg_state:
            root = Path(xdg_state) / "dark-governance"
        else:
            system = platform.system()
            if system == "Darwin":
                root = Path.home() / "Library" / "Application Support" / "dark-governance"
            elif system == "Windows":
                local_app_data = os.environ.get("LOCALAPPDATA")
                if local_app_data:
                    root = Path(local_app_data) / "dark-governance"
                else:
                    root = Path.home() / "AppData" / "Local" / "dark-governance"
            else:
                root = Path.home() / ".local" / "state" / "dark-governance"

    return root / "locks" / "issues"


@dataclass
class LockEntry:
    """Schema for a lock file on disk."""

    issue_number: int
    session_id: str
    claimed_at: str = ""
    hostname: str = ""
    pid: int = 0
    heartbeat: str = ""
    ttl_seconds: int = DEFAULT_TTL_SECONDS

    def __post_init__(self) -> None:
        now_iso = datetime.now(timezone.utc).isoformat()
        if not self.claimed_at:
            self.claimed_at = now_iso
        if not self.heartbeat:
            self.heartbeat = now_iso
        if not self.hostname:
            self.hostname = socket.gethostname()
        if not self.pid:
            self.pid = os.getpid()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LockEntry:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def is_stale(self, now: float | None = None) -> bool:
        """Return ``True`` if the heartbeat is older than the TTL.

        Args:
            now: Current time as a Unix timestamp.  Defaults to ``time.time()``.
        """
        if now is None:
            now = time.time()
        try:
            hb_str = self.heartbeat
            # Parse ISO 8601 timestamp to Unix epoch
            # Handle both with and without timezone info
            if hb_str.endswith("Z"):
                hb_str = hb_str[:-1] + "+00:00"
            hb_dt = datetime.fromisoformat(hb_str)
            if hb_dt.tzinfo is None:
                hb_dt = hb_dt.replace(tzinfo=timezone.utc)
            hb_epoch = hb_dt.timestamp()
        except (ValueError, OSError):
            # Unparseable heartbeat — treat as stale
            return True
        return (now - hb_epoch) > self.ttl_seconds


class LockManager:
    """Advisory file-lock-based work locking for cross-session coordination.

    Each issue is represented by a JSON lock file.  All mutations use
    ``fcntl.flock`` (shared/exclusive) to prevent TOCTOU races between
    concurrent processes.

    Args:
        session_id: The current orchestrator session ID.
        locks_dir: Override the lock file directory (useful for testing).
        ttl_seconds: Default TTL for new locks.
    """

    def __init__(
        self,
        session_id: str,
        locks_dir: Path | str | None = None,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ):
        self.session_id = session_id
        self.ttl_seconds = ttl_seconds

        if locks_dir is not None:
            self._dir = Path(locks_dir)
        else:
            self._dir = _get_locks_dir()

        self._dir.mkdir(parents=True, exist_ok=True)

    @property
    def locks_dir(self) -> Path:
        """The directory containing issue lock files."""
        return self._dir

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _lock_path(self, issue_number: int) -> Path:
        """Return the lock file path for a given issue number."""
        return self._dir / f"issue-{issue_number}.lock.json"

    def _read_lock(self, path: Path) -> LockEntry | None:
        """Read and parse a lock file.  Returns ``None`` if missing/corrupt."""
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return LockEntry.from_dict(data)
        except (json.JSONDecodeError, OSError, TypeError, KeyError):
            return None

    def _write_lock(self, path: Path, entry: LockEntry) -> None:
        """Atomically write a lock entry to disk."""
        path.write_text(
            json.dumps(entry.to_dict(), indent=2) + "\n",
            encoding="utf-8",
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def claim(self, issue_number: int) -> bool:
        """Attempt to claim an issue for this session.

        Uses ``fcntl.flock`` with ``LOCK_EX | LOCK_NB`` (non-blocking
        exclusive lock) to prevent races.  If the lock file already exists
        and belongs to another non-stale session, the claim is denied.

        Args:
            issue_number: The GitHub issue number to claim.

        Returns:
            ``True`` if the lock was acquired, ``False`` if the issue is
            already claimed by another active session.
        """
        path = self._lock_path(issue_number)

        # Open (or create) the lock file for exclusive advisory locking.
        # We use a separate .lck sentinel so the JSON content is never
        # partially written while another process reads it.
        sentinel = path.with_suffix(".lck")
        sentinel.parent.mkdir(parents=True, exist_ok=True)

        fd = os.open(str(sentinel), os.O_CREAT | os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)  # Blocking exclusive lock
            try:
                existing = self._read_lock(path)

                if existing is not None:
                    # Already claimed by us — refresh heartbeat
                    if existing.session_id == self.session_id:
                        existing.heartbeat = datetime.now(timezone.utc).isoformat()
                        self._write_lock(path, existing)
                        return True

                    # Claimed by someone else — check staleness
                    if not existing.is_stale():
                        return False

                    # Stale lock — we can take over

                # Write our lock
                entry = LockEntry(
                    issue_number=issue_number,
                    session_id=self.session_id,
                    ttl_seconds=self.ttl_seconds,
                )
                self._write_lock(path, entry)
                return True
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def release(self, issue_number: int) -> bool:
        """Release a lock previously held by this session.

        Args:
            issue_number: The issue number to release.

        Returns:
            ``True`` if the lock was released, ``False`` if it was not
            held by this session (or didn't exist).
        """
        path = self._lock_path(issue_number)
        sentinel = path.with_suffix(".lck")

        if not path.exists():
            return False

        fd = os.open(str(sentinel), os.O_CREAT | os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            try:
                existing = self._read_lock(path)
                if existing is None:
                    return False
                if existing.session_id != self.session_id:
                    return False

                # Remove the lock file
                path.unlink(missing_ok=True)
                return True
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def release_all(self) -> list[int]:
        """Release all locks held by this session.

        Returns:
            List of issue numbers whose locks were released.
        """
        released: list[int] = []
        for entry in self._list_all_entries():
            if entry.session_id == self.session_id:
                if self.release(entry.issue_number):
                    released.append(entry.issue_number)
        return released

    def heartbeat(self, issue_number: int) -> bool:
        """Update the heartbeat timestamp for a lock held by this session.

        Args:
            issue_number: The issue number to heartbeat.

        Returns:
            ``True`` if the heartbeat was updated, ``False`` if the lock
            is not held by this session.
        """
        path = self._lock_path(issue_number)
        sentinel = path.with_suffix(".lck")

        if not path.exists():
            return False

        fd = os.open(str(sentinel), os.O_CREAT | os.O_RDWR)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX)
            try:
                existing = self._read_lock(path)
                if existing is None or existing.session_id != self.session_id:
                    return False

                existing.heartbeat = datetime.now(timezone.utc).isoformat()
                self._write_lock(path, existing)
                return True
            finally:
                fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)

    def heartbeat_all(self) -> int:
        """Heartbeat all locks held by this session.

        Returns:
            Number of locks heartbeated.
        """
        count = 0
        for entry in self._list_all_entries():
            if entry.session_id == self.session_id:
                if self.heartbeat(entry.issue_number):
                    count += 1
        return count

    def is_claimed(self, issue_number: int) -> bool:
        """Check if an issue is claimed by any active (non-stale) session.

        Args:
            issue_number: The issue number to check.

        Returns:
            ``True`` if the issue is claimed by an active session
            (including this one).
        """
        path = self._lock_path(issue_number)
        entry = self._read_lock(path)
        if entry is None:
            return False
        return not entry.is_stale()

    def is_claimed_by_other(self, issue_number: int) -> bool:
        """Check if an issue is claimed by another active session.

        Args:
            issue_number: The issue number to check.

        Returns:
            ``True`` if the issue is actively claimed by a session other
            than this one.
        """
        path = self._lock_path(issue_number)
        entry = self._read_lock(path)
        if entry is None:
            return False
        if entry.session_id == self.session_id:
            return False
        return not entry.is_stale()

    def get_lock(self, issue_number: int) -> LockEntry | None:
        """Return the lock entry for an issue, or ``None`` if unlocked.

        Stale locks are returned as-is (caller can check ``entry.is_stale()``).
        """
        path = self._lock_path(issue_number)
        return self._read_lock(path)

    def _list_all_entries(self) -> list[LockEntry]:
        """List all lock entries on disk (including stale ones)."""
        entries: list[LockEntry] = []
        if not self._dir.exists():
            return entries
        for path in sorted(self._dir.glob("issue-*.lock.json")):
            entry = self._read_lock(path)
            if entry is not None:
                entries.append(entry)
        return entries

    def list_claimed(self) -> list[LockEntry]:
        """List all active (non-stale) lock entries.

        Returns:
            List of ``LockEntry`` objects for all non-stale locks.
        """
        return [e for e in self._list_all_entries() if not e.is_stale()]

    def list_stale(self) -> list[LockEntry]:
        """List all stale lock entries.

        Returns:
            List of ``LockEntry`` objects for all stale locks.
        """
        return [e for e in self._list_all_entries() if e.is_stale()]

    def cleanup_stale(self) -> list[int]:
        """Remove all stale lock files.

        Returns:
            List of issue numbers whose stale locks were removed.
        """
        removed: list[int] = []
        for entry in self._list_all_entries():
            if entry.is_stale():
                path = self._lock_path(entry.issue_number)
                try:
                    path.unlink(missing_ok=True)
                    removed.append(entry.issue_number)
                except OSError:
                    pass
        return removed

    def force_release(self, issue_number: int) -> bool:
        """Force-release a lock regardless of which session holds it.

        Use with caution — intended for manual override via CLI.

        Args:
            issue_number: The issue number to force-release.

        Returns:
            ``True`` if a lock file was deleted, ``False`` if none existed.
        """
        path = self._lock_path(issue_number)
        if not path.exists():
            return False
        try:
            path.unlink()
            return True
        except OSError:
            return False

    def filter_claimed_issues(
        self,
        issue_refs: list[str],
    ) -> tuple[list[str], list[dict[str, Any]]]:
        """Filter a list of issue references, removing those claimed by other sessions.

        Issue refs are strings like ``"#42"`` or ``"42"``.

        Args:
            issue_refs: List of issue references to filter.

        Returns:
            Tuple of (available_refs, skipped_info) where available_refs are
            the issue refs not claimed by other sessions, and skipped_info
            contains details about which issues were skipped and why.
        """
        available: list[str] = []
        skipped: list[dict[str, Any]] = []

        for ref in issue_refs:
            # Parse issue number from ref (handles "#42" and "42")
            num_str = ref.lstrip("#")
            try:
                issue_num = int(num_str)
            except (ValueError, TypeError):
                # Can't parse — include it (don't filter what we can't understand)
                available.append(ref)
                continue

            if self.is_claimed_by_other(issue_num):
                entry = self.get_lock(issue_num)
                skipped.append({
                    "issue": ref,
                    "claimed_by_session": entry.session_id if entry else "unknown",
                    "claimed_at": entry.claimed_at if entry else "",
                    "heartbeat": entry.heartbeat if entry else "",
                })
            else:
                available.append(ref)

        return available, skipped

    def to_status_dict(self) -> dict[str, Any]:
        """Return a summary dict suitable for JSON output in CLI commands."""
        active = self.list_claimed()
        stale = self.list_stale()

        active_entries = []
        for e in active:
            d = e.to_dict()
            d["owned_by_this_session"] = e.session_id == self.session_id
            active_entries.append(d)

        stale_entries = [e.to_dict() for e in stale]

        return {
            "locks_dir": str(self._dir),
            "session_id": self.session_id,
            "active_locks": active_entries,
            "active_count": len(active_entries),
            "stale_locks": stale_entries,
            "stale_count": len(stale_entries),
        }
