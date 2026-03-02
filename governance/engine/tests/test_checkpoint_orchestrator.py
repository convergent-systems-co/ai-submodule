"""Tests for governance.engine.orchestrator.checkpoint — deterministic checkpoint lifecycle."""

import json
from unittest.mock import patch

import pytest

from governance.engine.orchestrator.checkpoint import (
    CheckpointManager,
    IssueState,
    _extract_issue_number,
)


@pytest.fixture
def checkpoint_dir(tmp_path):
    return tmp_path / "checkpoints"


@pytest.fixture
def mgr(checkpoint_dir):
    return CheckpointManager(checkpoint_dir)


# ---------------------------------------------------------------------------
# Issue number extraction
# ---------------------------------------------------------------------------


class TestExtractIssueNumber:
    def test_hash_prefix(self):
        assert _extract_issue_number("#42") == 42

    def test_issue_prefix(self):
        assert _extract_issue_number("issue-42") == 42

    def test_bare_number(self):
        assert _extract_issue_number("42") == 42

    def test_whitespace(self):
        assert _extract_issue_number("  #42  ") == 42

    def test_invalid_returns_none(self):
        assert _extract_issue_number("not-a-number") is None

    def test_empty_returns_none(self):
        assert _extract_issue_number("") is None

    def test_hash_only_returns_none(self):
        assert _extract_issue_number("#") is None


# ---------------------------------------------------------------------------
# Write and load
# ---------------------------------------------------------------------------


class TestCheckpointWrite:
    def test_write_creates_file(self, mgr, checkpoint_dir):
        path = mgr.write(
            session_id="test-session",
            branch="main",
            issues_completed=["#1"],
            issues_remaining=["#2"],
        )
        assert path.exists()
        assert path.suffix == ".json"

    def test_write_valid_json(self, mgr):
        path = mgr.write(
            session_id="test-session",
            branch="feat/42/test",
            issues_completed=["#1", "#2"],
            issues_remaining=["#3"],
            current_issue="#3",
            current_step="Phase 2 — Planning",
            pending_work="Plan issue #3",
        )
        with open(path) as f:
            data = json.load(f)
        assert data["session_id"] == "test-session"
        assert data["branch"] == "feat/42/test"
        assert data["issues_completed"] == ["#1", "#2"]
        assert data["current_issue"] == "#3"
        assert data["git_state"] == "clean"

    def test_write_includes_capacity(self, mgr):
        path = mgr.write(
            session_id="s1",
            branch="main",
            issues_completed=[],
            issues_remaining=[],
            context_capacity={"tier": "orange", "tool_calls": 72},
            context_gates_passed=[{"phase": 1, "tier": "green", "action": "proceed"}],
        )
        with open(path) as f:
            data = json.load(f)
        assert data["context_capacity"]["tier"] == "orange"
        assert len(data["context_gates_passed"]) == 1

    def test_write_creates_directory(self, tmp_path):
        mgr = CheckpointManager(tmp_path / "new" / "dir")
        path = mgr.write(
            session_id="s1", branch="main",
            issues_completed=[], issues_remaining=[],
        )
        assert path.exists()


class TestCheckpointLoad:
    def test_load_latest_returns_none_when_empty(self, mgr):
        assert mgr.load_latest() is None

    def test_load_latest_returns_most_recent(self, mgr):
        mgr.write(session_id="s1", branch="main",
                   issues_completed=[], issues_remaining=["#1"])
        mgr.write(session_id="s2", branch="main",
                   issues_completed=["#1"], issues_remaining=[])
        latest = mgr.load_latest()
        assert latest["session_id"] == "s2"

    def test_load_specific_file(self, mgr):
        path = mgr.write(session_id="specific", branch="main",
                         issues_completed=[], issues_remaining=[])
        data = mgr.load(path)
        assert data["session_id"] == "specific"


# ---------------------------------------------------------------------------
# Resume phase determination
# ---------------------------------------------------------------------------


class TestDetermineResumePhase:
    def test_no_work_returns_phase1(self, mgr):
        checkpoint = {
            "prs_created": [],
            "prs_remaining": [],
            "issues_remaining": [],
            "current_issue": None,
        }
        assert mgr.determine_resume_phase(checkpoint) == 1

    def test_issues_remaining_no_prs_returns_phase2(self, mgr):
        checkpoint = {
            "prs_created": [],
            "prs_remaining": [],
            "issues_remaining": ["#42"],
            "current_issue": None,
        }
        assert mgr.determine_resume_phase(checkpoint) == 2

    def test_current_issue_no_prs_returns_phase2(self, mgr):
        checkpoint = {
            "prs_created": [],
            "prs_remaining": [],
            "issues_remaining": [],
            "current_issue": "#42",
        }
        assert mgr.determine_resume_phase(checkpoint) == 2

    def test_prs_and_issues_remaining_returns_phase3(self, mgr):
        checkpoint = {
            "prs_created": ["#100"],
            "prs_remaining": [],
            "issues_remaining": ["#43"],
            "current_issue": None,
        }
        assert mgr.determine_resume_phase(checkpoint) == 3

    def test_open_prs_returns_phase4(self, mgr):
        checkpoint = {
            "prs_created": ["#100"],
            "prs_remaining": ["#100"],
            "issues_remaining": [],
            "current_issue": None,
        }
        assert mgr.determine_resume_phase(checkpoint) == 4

    def test_all_prs_resolved_returns_phase5(self, mgr):
        checkpoint = {
            "prs_created": ["#100"],
            "prs_remaining": [],
            "issues_remaining": [],
            "current_issue": None,
        }
        assert mgr.determine_resume_phase(checkpoint) == 5


# ---------------------------------------------------------------------------
# Issue validation
# ---------------------------------------------------------------------------


class TestValidateIssues:
    @patch("governance.engine.orchestrator.checkpoint._is_issue_open")
    def test_removes_closed_current_issue(self, mock_open, mgr):
        mock_open.return_value = IssueState.CLOSED
        checkpoint = {
            "current_issue": "#42",
            "issues_remaining": [],
        }
        result = mgr.validate_issues(checkpoint)
        assert result["current_issue"] is None

    @patch("governance.engine.orchestrator.checkpoint._is_issue_open")
    def test_keeps_open_current_issue(self, mock_open, mgr):
        mock_open.return_value = IssueState.OPEN
        checkpoint = {
            "current_issue": "#42",
            "issues_remaining": [],
        }
        result = mgr.validate_issues(checkpoint)
        assert result["current_issue"] == "#42"

    @patch("governance.engine.orchestrator.checkpoint._is_issue_open")
    def test_keeps_unknown_current_issue(self, mock_open, mgr):
        """Unknown state (API error) should preserve the issue, not drop it."""
        mock_open.return_value = IssueState.UNKNOWN
        checkpoint = {
            "current_issue": "#42",
            "issues_remaining": [],
        }
        result = mgr.validate_issues(checkpoint)
        assert result["current_issue"] == "#42"

    @patch("governance.engine.orchestrator.checkpoint._is_issue_open")
    def test_filters_closed_remaining_issues(self, mock_open, mgr):
        def side_effect(n):
            if n == 43:
                return IssueState.CLOSED
            return IssueState.OPEN
        mock_open.side_effect = side_effect
        checkpoint = {
            "current_issue": None,
            "issues_remaining": ["#42", "#43", "#44"],
        }
        result = mgr.validate_issues(checkpoint)
        assert result["issues_remaining"] == ["#42", "#44"]

    @patch("governance.engine.orchestrator.checkpoint._is_issue_open")
    def test_preserves_unknown_remaining_issues(self, mock_open, mgr):
        """Issues with unknown state should be preserved in the work queue."""
        def side_effect(n):
            if n == 43:
                return IssueState.UNKNOWN
            return IssueState.OPEN
        mock_open.side_effect = side_effect
        checkpoint = {
            "current_issue": None,
            "issues_remaining": ["#42", "#43", "#44"],
        }
        result = mgr.validate_issues(checkpoint)
        assert result["issues_remaining"] == ["#42", "#43", "#44"]


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------


class TestCheckpointCleanup:
    def test_cleanup_keeps_n_most_recent(self, mgr, checkpoint_dir):
        import time
        paths = []
        for i in range(5):
            p = mgr.write(session_id=f"s{i}", branch=f"branch-{i}",
                          issues_completed=[], issues_remaining=[])
            paths.append(p)
            time.sleep(0.05)  # Ensure distinct mtime
        removed = mgr.cleanup(keep=2)
        assert len(removed) == 3
        remaining = list(checkpoint_dir.glob("*.json"))
        assert len(remaining) == 2

    def test_cleanup_no_op_when_under_limit(self, mgr):
        mgr.write(session_id="s1", branch="main",
                   issues_completed=[], issues_remaining=[])
        removed = mgr.cleanup(keep=5)
        assert len(removed) == 0
