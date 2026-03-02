"""Structured event logging for the orchestrator.

Events are written by the orchestrator (deterministic code), not by agents.
This ensures the audit trail is complete regardless of agent behavior.
Format: JSONL (one JSON object per line), append-only.

Hash chaining: Each entry includes a `previous_hash` field containing the
SHA-256 hash of the previous entry, creating a tamper-evident chain. The
first entry's `previous_hash` is a seed derived from the session_id.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def _compute_seed(session_id: str) -> str:
    """Compute the seed hash for the first entry in the chain."""
    return hashlib.sha256(f"audit-chain-seed:{session_id}".encode("utf-8")).hexdigest()


def _hash_entry(entry_json: str) -> str:
    """Compute the SHA-256 hash of a JSONL entry string."""
    return hashlib.sha256(entry_json.encode("utf-8")).hexdigest()


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
    """Append-only JSONL audit log for orchestrator events with hash chaining.

    Each entry includes a `previous_hash` field containing the SHA-256 hash
    of the previous JSONL line. The first entry uses a seed derived from the
    session_id. This creates a tamper-evident chain — any modification to a
    previous entry breaks the chain from that point forward.

    Thread-safety: each write opens, appends, and closes the file.
    This is safe for single-writer scenarios (the orchestrator).
    """

    def __init__(self, log_path: str | Path):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash: str | None = None

    def _get_last_hash(self, session_id: str) -> str:
        """Get the hash to use as previous_hash for the next entry.

        If the log file exists and has entries, returns the hash of the
        last entry. Otherwise returns the seed hash for the session.
        """
        if self._last_hash is not None:
            return self._last_hash

        if self.log_path.exists():
            last_line = None
            with open(self.log_path) as f:
                for line in f:
                    stripped = line.strip()
                    if stripped:
                        last_line = stripped
            if last_line:
                self._last_hash = _hash_entry(last_line)
                return self._last_hash

        return _compute_seed(session_id)

    def record(self, event: AuditEvent) -> None:
        """Append an event to the log file with hash chain link."""
        previous_hash = self._get_last_hash(event.session_id)
        entry = asdict(event)
        entry["previous_hash"] = previous_hash

        entry_json = json.dumps(entry, separators=(",", ":"))
        self._last_hash = _hash_entry(entry_json)

        with open(self.log_path, "a") as f:
            f.write(entry_json + "\n")

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

    def verify_chain(self) -> "ChainVerificationResult":
        """Verify the integrity of the hash chain.

        Returns:
            ChainVerificationResult with verification details.
        """
        if not self.log_path.exists():
            return ChainVerificationResult(
                valid=True, total_entries=0, verified_entries=0
            )

        lines = []
        with open(self.log_path) as f:
            for line in f:
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)

        if not lines:
            return ChainVerificationResult(
                valid=True, total_entries=0, verified_entries=0
            )

        total = len(lines)
        first_entry = json.loads(lines[0])
        session_id = first_entry.get("session_id", "")
        seed = _compute_seed(session_id)

        # Verify first entry's previous_hash matches seed
        if first_entry.get("previous_hash") != seed:
            return ChainVerificationResult(
                valid=False,
                total_entries=total,
                verified_entries=0,
                broken_at_index=0,
                reason="First entry's previous_hash does not match session seed",
            )

        # Verify chain links
        for i in range(1, total):
            entry = json.loads(lines[i])
            expected_hash = _hash_entry(lines[i - 1])
            actual_hash = entry.get("previous_hash", "")

            if actual_hash != expected_hash:
                return ChainVerificationResult(
                    valid=False,
                    total_entries=total,
                    verified_entries=i,
                    broken_at_index=i,
                    reason=f"Hash chain broken at entry {i}: "
                           f"expected {expected_hash[:16]}..., "
                           f"got {actual_hash[:16]}...",
                )

        return ChainVerificationResult(
            valid=True, total_entries=total, verified_entries=total
        )


@dataclass
class ChainVerificationResult:
    """Result of hash chain verification."""

    valid: bool
    total_entries: int
    verified_entries: int
    broken_at_index: int | None = None
    reason: str | None = None

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "total_entries": self.total_entries,
            "verified_entries": self.verified_entries,
            "broken_at_index": self.broken_at_index,
            "reason": self.reason,
        }
