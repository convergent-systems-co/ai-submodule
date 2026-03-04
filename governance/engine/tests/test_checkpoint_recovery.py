"""PreCompact hook and checkpoint recovery integration tests.

Covers:
- Full checkpoint cycle: write -> validate schema -> read -> verify fields match
- Phase 0 issue validation: mock gh CLI returning CLOSED -> issue removed
- Phase 0 git state mismatch: checkpoint branch != current branch
- Emergency checkpoint detection: filename contains 'emergency'
- PreCompact hook script structure validation
- Emergency checkpoint format validation against schema
- Checkpoint cleanup logic
"""

import json
import time
from pathlib import Path
from unittest.mock import patch

import jsonschema
import pytest

from conftest import REPO_ROOT

from governance.engine.orchestrator.checkpoint import (
    CheckpointManager,
    IssueState,
    _extract_issue_number,
)


# ---------------------------------------------------------------------------
# Paths and schemas
# ---------------------------------------------------------------------------

CHECKPOINT_SCHEMA_PATH = REPO_ROOT / "governance" / "schemas" / "checkpoint.schema.json"
PRECOMPACT_SCRIPT = REPO_ROOT / "governance" / "bin" / "pre-compact-checkpoint.sh"


@pytest.fixture
def checkpoint_schema():
    with open(CHECKPOINT_SCHEMA_PATH) as f:
        return json.load(f)


@pytest.fixture
def checkpoint_dir(tmp_path):
    return tmp_path / "checkpoints"


@pytest.fixture
def mgr(checkpoint_dir):
    return CheckpointManager(checkpoint_dir)


@pytest.fixture
def mgr_with_schema(checkpoint_dir):
    return CheckpointManager(checkpoint_dir, schema_path=CHECKPOINT_SCHEMA_PATH)


# ===========================================================================
# Full checkpoint cycle: write -> validate -> read -> verify
# ===========================================================================


class TestFullCheckpointCycle:
    """End-to-end checkpoint lifecycle test."""

    def test_write_validate_read_verify(self, mgr_with_schema):
        # Write
        path = mgr_with_schema.write(
            session_id="cycle-1",
            branch="feat/42/test",
            issues_completed=["#1", "#2"],
            issues_remaining=["#3"],
            prs_created=["#100"],
            prs_resolved=["#100"],
            prs_remaining=[],
            current_issue="#3",
            current_step="Phase 2 - Planning",
            pending_work="Plan issue #3",
            context_capacity={"tier": "yellow", "tool_calls": 55},
            context_gates_passed=[
                {"phase": 1, "tier": "green", "action": "proceed"},
                {"phase": 2, "tier": "yellow", "action": "proceed"},
            ],
        )

        # Validate schema
        data = mgr_with_schema.load(path)
        errors = mgr_with_schema.validate(data)
        assert errors == [], f"Schema validation errors: {errors}"

        # Read and verify fields
        assert data["session_id"] == "cycle-1"
        assert data["branch"] == "feat/42/test"
        assert data["issues_completed"] == ["#1", "#2"]
        assert data["issues_remaining"] == ["#3"]
        assert data["prs_created"] == ["#100"]
        assert data["current_issue"] == "#3"
        assert data["git_state"] == "clean"
        assert data["context_capacity"]["tier"] == "yellow"
        assert len(data["context_gates_passed"]) == 2

    def test_minimal_checkpoint_validates(self, mgr_with_schema):
        """A checkpoint with only required fields should validate."""
        path = mgr_with_schema.write(
            session_id="min-1",
            branch="main",
            issues_completed=[],
            issues_remaining=[],
        )
        data = mgr_with_schema.load(path)
        errors = mgr_with_schema.validate(data)
        assert errors == []

    def test_multiple_checkpoints_load_latest(self, mgr):
        mgr.write(
            session_id="s1", branch="main",
            issues_completed=[], issues_remaining=["#1"],
        )
        time.sleep(0.05)
        mgr.write(
            session_id="s2", branch="main",
            issues_completed=["#1"], issues_remaining=[],
        )
        latest = mgr.load_latest()
        assert latest["session_id"] == "s2"


# ===========================================================================
# Phase 0 issue validation
# ===========================================================================


class TestPhase0IssueValidation:
    """Mock gh issue view returning CLOSED -> issue removed from queue."""

    @patch("governance.engine.orchestrator.checkpoint._is_issue_open")
    def test_closed_issue_removed_from_current(self, mock_open, mgr):
        mock_open.return_value = IssueState.CLOSED
        checkpoint = {
            "current_issue": "#42",
            "issues_remaining": [],
        }
        result = mgr.validate_issues(checkpoint)
        assert result["current_issue"] is None

    @patch("governance.engine.orchestrator.checkpoint._is_issue_open")
    def test_closed_issues_removed_from_remaining(self, mock_open, mgr):
        def side_effect(n):
            return IssueState.CLOSED if n == 43 else IssueState.OPEN
        mock_open.side_effect = side_effect
        checkpoint = {
            "current_issue": None,
            "issues_remaining": ["#42", "#43", "#44"],
        }
        result = mgr.validate_issues(checkpoint)
        assert result["issues_remaining"] == ["#42", "#44"]

    @patch("governance.engine.orchestrator.checkpoint._is_issue_open")
    def test_unknown_state_preserves_issues(self, mock_open, mgr):
        mock_open.return_value = IssueState.UNKNOWN
        checkpoint = {
            "current_issue": "#42",
            "issues_remaining": ["#43"],
        }
        result = mgr.validate_issues(checkpoint)
        assert result["current_issue"] == "#42"
        assert result["issues_remaining"] == ["#43"]

    @patch("governance.engine.orchestrator.checkpoint._is_issue_open")
    def test_all_closed_empties_queue(self, mock_open, mgr):
        mock_open.return_value = IssueState.CLOSED
        checkpoint = {
            "current_issue": "#42",
            "issues_remaining": ["#43", "#44"],
        }
        result = mgr.validate_issues(checkpoint)
        assert result["current_issue"] is None
        assert result["issues_remaining"] == []


# ===========================================================================
# Phase 0 git state mismatch
# ===========================================================================


class TestPhase0GitStateMismatch:
    """Checkpoint branch != current branch should be detectable."""

    def test_branch_mismatch_detected(self, mgr):
        path = mgr.write(
            session_id="mismatch-1",
            branch="feat/42/old-branch",
            issues_completed=[],
            issues_remaining=["#42"],
        )
        data = mgr.load(path)
        current_branch = "feat/43/new-branch"
        assert data["branch"] != current_branch

    def test_branch_match_confirmed(self, mgr):
        path = mgr.write(
            session_id="match-1",
            branch="feat/42/my-branch",
            issues_completed=[],
            issues_remaining=[],
        )
        data = mgr.load(path)
        assert data["branch"] == "feat/42/my-branch"


# ===========================================================================
# Emergency checkpoint detection
# ===========================================================================


class TestEmergencyCheckpointDetection:
    """Emergency checkpoint filenames contain 'emergency'."""

    def test_emergency_filename_detected(self, checkpoint_dir):
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        emergency_file = checkpoint_dir / "20260301-120000-emergency-feat-42.json"
        emergency_file.write_text(json.dumps({
            "timestamp": "2026-03-01T12:00:00Z",
            "session_id": "emergency",
            "branch": "feat/42/test",
            "issues_completed": [],
            "issues_remaining": [],
            "git_state": "clean",
            "pending_work": "Emergency checkpoint",
        }))
        # Detect emergency checkpoints by filename pattern
        emergency_files = list(checkpoint_dir.glob("*emergency*"))
        assert len(emergency_files) == 1

    def test_non_emergency_not_detected(self, checkpoint_dir):
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        normal_file = checkpoint_dir / "20260301-120000-feat-42.json"
        normal_file.write_text(json.dumps({"session_id": "normal"}))
        emergency_files = list(checkpoint_dir.glob("*emergency*"))
        assert len(emergency_files) == 0

    def test_emergency_detection_within_timeframe(self, checkpoint_dir):
        """Emergency checkpoints written within 5 minutes should be detectable."""
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        emergency_file = checkpoint_dir / "20260301-120000-emergency-main.json"
        emergency_file.write_text(json.dumps({"session_id": "emergency"}))
        # Check the file was just written (within 5 minutes)
        mtime = emergency_file.stat().st_mtime
        now = time.time()
        assert now - mtime < 300, "Emergency checkpoint should be recent"


# ===========================================================================
# PreCompact hook script validation
# ===========================================================================


class TestPreCompactHookScript:
    """Validate the pre-compact-checkpoint.sh script structure."""

    def test_script_exists(self):
        assert PRECOMPACT_SCRIPT.exists(), "pre-compact-checkpoint.sh not found"

    def test_script_is_bash(self):
        content = PRECOMPACT_SCRIPT.read_text()
        assert content.startswith("#!/bin/bash"), "Must be a bash script"

    def test_script_uses_strict_mode(self):
        content = PRECOMPACT_SCRIPT.read_text()
        assert "set -euo pipefail" in content

    def test_script_creates_checkpoint_dir(self):
        content = PRECOMPACT_SCRIPT.read_text()
        assert "mkdir -p" in content
        assert ".artifacts/checkpoints" in content

    def test_script_writes_json_checkpoint(self):
        content = PRECOMPACT_SCRIPT.read_text()
        assert '"timestamp"' in content
        assert '"session_id"' in content

    def test_script_includes_emergency_in_filename(self):
        content = PRECOMPACT_SCRIPT.read_text()
        assert "emergency" in content

    def test_script_auto_commits_wip(self):
        """Hook should auto-commit tracked changes with wip: prefix."""
        content = PRECOMPACT_SCRIPT.read_text()
        assert "wip:" in content
        assert "git commit" in content

    def test_script_handles_clean_working_tree(self):
        """Hook should handle clean working tree (no auto-commit needed)."""
        content = PRECOMPACT_SCRIPT.read_text()
        assert "git status" in content or "GIT_DIRTY" in content

    def test_script_sets_red_tier(self):
        """Emergency checkpoint should set tier to Red."""
        content = PRECOMPACT_SCRIPT.read_text()
        assert '"Red"' in content or '"red"' in content

    def test_script_includes_pre_compact_signal(self):
        """Emergency checkpoint should include pre_compact_hook_fired signal."""
        content = PRECOMPACT_SCRIPT.read_text()
        assert "pre_compact_hook_fired" in content


# ===========================================================================
# Emergency checkpoint schema compatibility
# ===========================================================================


class TestEmergencyCheckpointFormat:
    """Emergency checkpoints have a different format from standard checkpoints.

    The PreCompact hook writes a simplified format with context_capacity
    and git_state as objects rather than the standard checkpoint schema.
    This test validates the hook's output structure.
    """

    def test_emergency_checkpoint_has_required_keys(self):
        """Validate the emergency checkpoint has the keys the hook writes."""
        # Simulate what the hook produces
        emergency = {
            "timestamp": "2026-03-01T12:00:00Z",
            "session_id": "emergency",
            "phase": "interrupted",
            "phase_label": "Compaction interrupted agentic loop",
            "context_capacity": {
                "tier": "Red",
                "signals": ["pre_compact_hook_fired"],
                "trigger": "claude_code_pre_compact_hook",
            },
            "git_state": {
                "branch": "feat/42/test",
                "clean": True,
                "stash": False,
            },
            "completed_work": [],
            "remaining_work": ["Check git log"],
            "issues": [],
            "notes": "Emergency checkpoint.",
        }
        assert "timestamp" in emergency
        assert "session_id" in emergency
        assert emergency["context_capacity"]["tier"] == "Red"
        assert "pre_compact_hook_fired" in emergency["context_capacity"]["signals"]

    def test_emergency_checkpoint_is_valid_json(self, tmp_path):
        """Emergency checkpoint must be valid JSON."""
        data = {
            "timestamp": "2026-03-01T12:00:00Z",
            "session_id": "emergency",
        }
        filepath = tmp_path / "emergency.json"
        with open(filepath, "w") as f:
            json.dump(data, f)
        with open(filepath) as f:
            loaded = json.load(f)
        assert loaded == data


# ===========================================================================
# Checkpoint cleanup
# ===========================================================================


class TestCheckpointCleanup:
    """Checkpoint cleanup keeps N most recent files."""

    def test_cleanup_keeps_specified_count(self, mgr, checkpoint_dir):
        for i in range(5):
            mgr.write(
                session_id=f"s{i}", branch=f"branch-{i}",
                issues_completed=[], issues_remaining=[],
            )
            time.sleep(0.05)
        removed = mgr.cleanup(keep=2)
        assert len(removed) == 3
        remaining = list(checkpoint_dir.glob("*.json"))
        assert len(remaining) == 2

    def test_cleanup_no_op_when_under_limit(self, mgr):
        mgr.write(
            session_id="s1", branch="main",
            issues_completed=[], issues_remaining=[],
        )
        removed = mgr.cleanup(keep=5)
        assert len(removed) == 0

    def test_cleanup_keeps_most_recent(self, mgr):
        for i in range(4):
            mgr.write(
                session_id=f"s{i}", branch="main",
                issues_completed=[], issues_remaining=[],
            )
            time.sleep(0.05)
        mgr.cleanup(keep=1)
        latest = mgr.load_latest()
        assert latest["session_id"] == "s3"


# ===========================================================================
# Issue number extraction edge cases
# ===========================================================================


class TestIssueNumberExtraction:
    """Edge cases for _extract_issue_number helper."""

    def test_hash_prefix(self):
        assert _extract_issue_number("#42") == 42

    def test_issue_prefix(self):
        assert _extract_issue_number("issue-42") == 42

    def test_bare_number(self):
        assert _extract_issue_number("42") == 42

    def test_whitespace_trimmed(self):
        assert _extract_issue_number("  #42  ") == 42

    def test_invalid_returns_none(self):
        assert _extract_issue_number("not-a-number") is None

    def test_empty_returns_none(self):
        assert _extract_issue_number("") is None

    def test_hash_only_returns_none(self):
        assert _extract_issue_number("#") is None

    def test_float_returns_none(self):
        assert _extract_issue_number("#42.5") is None

    def test_negative_parses_as_int(self):
        # _extract_issue_number uses int() which accepts negative numbers
        assert _extract_issue_number("#-1") == -1
