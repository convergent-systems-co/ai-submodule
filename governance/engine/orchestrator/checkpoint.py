"""Deterministic checkpoint lifecycle management.

Checkpoints are written on every state transition (not just shutdown).
Every phase boundary produces a recovery point. The checkpoint is always
consistent because the state machine is the single source of truth.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import jsonschema


class CheckpointError(Exception):
    """Raised on checkpoint validation or I/O failures."""


class CheckpointManager:
    """Manages checkpoint read/write/validate and Phase 0 recovery logic."""

    def __init__(self, checkpoint_dir: str | Path, schema_path: str | Path | None = None):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._schema = None
        if schema_path:
            schema_file = Path(schema_path)
            if schema_file.exists():
                with open(schema_file) as f:
                    self._schema = json.load(f)

    def write(
        self,
        *,
        session_id: str,
        branch: str,
        issues_completed: list[str],
        issues_remaining: list[str],
        prs_created: list[str] | None = None,
        prs_resolved: list[str] | None = None,
        prs_remaining: list[str] | None = None,
        current_issue: str | None = None,
        current_step: str = "",
        pending_work: str = "",
        context_capacity: dict | None = None,
        context_gates_passed: list[dict] | None = None,
    ) -> Path:
        """Write a checkpoint file. Returns the file path."""
        timestamp = datetime.now(timezone.utc)
        branch_safe = branch.replace("/", "-")
        filename = f"{timestamp.strftime('%Y%m%d-%H%M%S-%f')}-{branch_safe}.json"
        filepath = self.checkpoint_dir / filename

        checkpoint = {
            "timestamp": timestamp.isoformat(),
            "session_id": session_id,
            "branch": branch,
            "issues_completed": issues_completed,
            "issues_remaining": issues_remaining,
            "prs_created": prs_created or [],
            "prs_resolved": prs_resolved or [],
            "prs_remaining": prs_remaining or [],
            "current_issue": current_issue,
            "current_step": current_step,
            "git_state": "clean",
            "pending_work": pending_work,
            "context_capacity": context_capacity or {},
            "context_gates_passed": context_gates_passed or [],
        }

        with open(filepath, "w") as f:
            json.dump(checkpoint, f, indent=2)

        return filepath

    def load_latest(self) -> dict | None:
        """Load the most recent checkpoint file. Returns None if none exist."""
        checkpoints = sorted(
            self.checkpoint_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not checkpoints:
            return None

        with open(checkpoints[0]) as f:
            return json.load(f)

    def load(self, path: str | Path) -> dict:
        """Load a specific checkpoint file."""
        with open(path) as f:
            return json.load(f)

    def validate(self, checkpoint: dict) -> list[str]:
        """Validate a checkpoint against the schema.

        Returns a list of validation error messages. Empty list = valid.
        """
        if self._schema is None:
            return []

        errors = []
        validator = jsonschema.Draft7Validator(self._schema)
        for error in validator.iter_errors(checkpoint):
            # json_path was added in jsonschema 4.18.0; fall back to
            # absolute_path for compatibility with jsonschema >=4.0.0
            path = (
                error.json_path
                if hasattr(error, "json_path")
                else ".".join(str(p) for p in error.absolute_path) or "$"
            )
            errors.append(f"{path}: {error.message}")
        return errors

    def validate_issues(self, checkpoint: dict) -> dict:
        """Check issue states via gh CLI. Returns updated checkpoint
        with confirmed-closed issues removed.

        Issues are validated by calling `gh issue view` for each.
        Only issues confirmed closed are removed from the work queue
        per startup.md Phase 0b: "Closed issues represent a user decision."
        Issues with unknown state (API errors, timeouts) are preserved
        to avoid silently dropping work.
        """
        updated = dict(checkpoint)

        # Validate current_issue
        if updated.get("current_issue"):
            issue_num = _extract_issue_number(updated["current_issue"])
            if issue_num and _is_issue_open(issue_num) == IssueState.CLOSED:
                updated["current_issue"] = None

        # Validate issues_remaining — only drop confirmed-closed issues
        remaining = []
        for issue_ref in updated.get("issues_remaining", []):
            issue_num = _extract_issue_number(issue_ref)
            if issue_num is None or _is_issue_open(issue_num) != IssueState.CLOSED:
                remaining.append(issue_ref)
        updated["issues_remaining"] = remaining

        return updated

    def determine_resume_phase(self, checkpoint: dict) -> int:
        """Determine which phase to resume from based on checkpoint state.

        Logic from startup.md Phase 0d.
        """
        prs_created = checkpoint.get("prs_created", [])
        prs_remaining = checkpoint.get("prs_remaining", [])
        issues_remaining = checkpoint.get("issues_remaining", [])
        current_issue = checkpoint.get("current_issue")

        # No remaining work at all
        if not prs_created and not issues_remaining and not current_issue:
            return 1  # Fresh scan

        # No PRs created yet but issues remain → start planning
        if not prs_created and (issues_remaining or current_issue):
            return 2

        # PRs created but none merged, issues have plans → dispatch
        if prs_created and issues_remaining:
            return 3

        # PRs created with open PRs → enter review monitoring
        if prs_remaining:
            return 4

        # PRs created, all resolved → merge phase
        if prs_created and not prs_remaining:
            return 5

        return 1  # Default: fresh scan

    def cleanup(self, keep: int = 3) -> list[Path]:
        """Remove old checkpoints, keeping the N most recent. Returns removed paths."""
        checkpoints = sorted(
            self.checkpoint_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        removed = []
        for cp in checkpoints[keep:]:
            cp.unlink()
            removed.append(cp)
        return removed


def _extract_issue_number(ref: str) -> int | None:
    """Extract issue number from references like '#42' or 'issue-42'."""
    ref = ref.strip()
    if ref.startswith("#"):
        try:
            return int(ref[1:])
        except ValueError:
            return None
    if ref.startswith("issue-"):
        try:
            return int(ref[6:])
        except ValueError:
            return None
    try:
        return int(ref)
    except ValueError:
        return None


class IssueState:
    """Three-state result for issue status checks."""

    OPEN = "open"
    CLOSED = "closed"
    UNKNOWN = "unknown"


def _is_issue_open(issue_number: int) -> str:
    """Check if a GitHub issue is open via gh CLI.

    Returns:
        IssueState.OPEN if the issue is confirmed open.
        IssueState.CLOSED if the issue is confirmed closed.
        IssueState.UNKNOWN if the check failed (network error, timeout, etc.).
    """
    try:
        result = subprocess.run(
            ["gh", "issue", "view", str(issue_number), "--json", "state", "--jq", ".state"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        state = result.stdout.strip()
        if state == "OPEN":
            return IssueState.OPEN
        if state in ("CLOSED", "MERGED"):
            return IssueState.CLOSED
        # Unexpected output (e.g. empty on API error) — treat as unknown
        return IssueState.UNKNOWN if not state else IssueState.CLOSED
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return IssueState.UNKNOWN
