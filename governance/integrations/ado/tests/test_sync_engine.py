"""Tests for the GitHub-to-ADO sync engine."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from governance.integrations.ado._exceptions import (
    AdoAuthError,
    AdoError,
    AdoValidationError,
)
from governance.integrations.ado._types import WorkItem
from governance.integrations.ado.sync_engine import SyncEngine, SyncResult


# ── Fixtures / helpers ───────────────────────────────────────────────────


def _config(**overrides) -> dict:
    """Build a minimal ado_integration config dict."""
    base: dict = {
        "organization": "https://dev.azure.com/testorg",
        "project": "TestProject",
        "sync": {
            "direction": "github_to_ado",
            "auto_create": True,
            "auto_close": True,
            "grace_period_seconds": 5,
        },
        "state_mapping": {
            "open": "New",
            "closed": "Closed",
            "closed+label:bug": "Resolved",
        },
        "type_mapping": {
            "default": "User Story",
            "bug": "Bug",
        },
        "field_mapping": {
            "area_path": "TestProject\\TeamA",
            "iteration_path": "TestProject\\Sprint 1",
            "priority_labels": {"P1": 1, "P2": 2},
        },
        "user_mapping": {
            "octocat": "octocat@example.com",
        },
        "filters": {
            "include_labels": [],
            "exclude_labels": ["internal", "governance"],
        },
    }
    base.update(overrides)
    return base


def _event(
    action: str = "opened",
    *,
    issue_number: int = 42,
    title: str = "Test issue",
    body: str = "Issue body",
    state: str = "open",
    labels: list[str] | None = None,
    assignee: str | None = None,
    milestone: str | None = None,
    repo: str = "owner/repo",
) -> dict:
    """Build a GitHub issues webhook event payload."""
    issue: dict = {
        "number": issue_number,
        "title": title,
        "body": body,
        "state": state,
        "labels": [{"name": lbl} for lbl in (labels or [])],
        "html_url": f"https://github.com/{repo}/issues/{issue_number}",
    }
    if assignee:
        issue["assignee"] = {"login": assignee}
    if milestone:
        issue["milestone"] = {"title": milestone}
    return {
        "action": action,
        "issue": issue,
        "repository": {"full_name": repo},
    }


def _work_item(work_item_id: int = 100) -> WorkItem:
    """Build a mock WorkItem return value."""
    return WorkItem(
        id=work_item_id,
        rev=1,
        url=f"https://dev.azure.com/testorg/TestProject/_apis/wit/workitems/{work_item_id}",
        fields={"System.Title": "Test"},
    )


def _make_engine(
    tmp_path: Path,
    config: dict | None = None,
    client: MagicMock | None = None,
    ledger: dict | None = None,
) -> tuple[SyncEngine, MagicMock, Path, Path]:
    """Set up a SyncEngine with mock client and temp paths."""
    mock_client = client or MagicMock()
    mock_client.create_work_item.return_value = _work_item(100)
    mock_client.update_work_item.return_value = _work_item(100)

    ledger_path = tmp_path / ".governance" / "state" / "ado-sync-ledger.json"
    error_path = tmp_path / ".governance" / "state" / "ado-sync-errors.json"

    if ledger:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2))

    cfg = config or _config()
    engine = SyncEngine(mock_client, cfg, ledger_path, error_path)
    return engine, mock_client, ledger_path, error_path


def _ledger_with_entry(
    issue_number: int = 42,
    repo: str = "owner/repo",
    ado_id: int = 100,
    last_sync_source: str = "github",
    last_synced_at: str | None = None,
) -> dict:
    """Build a ledger dict with one existing mapping."""
    return {
        "schema_version": "1.0.0",
        "mappings": [
            {
                "github_issue_number": issue_number,
                "github_repo": repo,
                "ado_work_item_id": ado_id,
                "ado_project": "TestProject",
                "sync_direction": "github_to_ado",
                "last_synced_at": last_synced_at or datetime.now(timezone.utc).isoformat(),
                "last_sync_source": last_sync_source,
                "created_at": "2026-01-01T00:00:00+00:00",
                "sync_status": "active",
            }
        ],
    }


# ── SyncResult dataclass ────────────────────────────────────────────────


class TestSyncResult:
    def test_created(self):
        r = SyncResult(status="created", operation="create", ado_work_item_id=42)
        assert r.status == "created"
        assert r.operation == "create"
        assert r.ado_work_item_id == 42
        assert r.error is None

    def test_error(self):
        r = SyncResult(status="error", operation="create", error="boom")
        assert r.error == "boom"
        assert r.ado_work_item_id is None

    def test_frozen(self):
        r = SyncResult(status="skipped", operation="noop")
        with pytest.raises(AttributeError):
            r.status = "created"  # type: ignore[misc]


# ── issues.opened ────────────────────────────────────────────────────────


class TestHandleOpened:
    def test_creates_work_item(self, tmp_path):
        engine, mock_client, ledger_path, _ = _make_engine(tmp_path)
        result = engine.sync(_event("opened"))

        assert result.status == "created"
        assert result.operation == "create"
        assert result.ado_work_item_id == 100
        mock_client.create_work_item.assert_called_once()

    def test_updates_ledger_after_create(self, tmp_path):
        engine, _, ledger_path, _ = _make_engine(tmp_path)
        engine.sync(_event("opened"))

        assert ledger_path.exists()
        ledger = json.loads(ledger_path.read_text())
        assert len(ledger["mappings"]) == 1
        assert ledger["mappings"][0]["github_issue_number"] == 42
        assert ledger["mappings"][0]["ado_work_item_id"] == 100

    def test_skips_when_auto_create_disabled(self, tmp_path):
        cfg = _config()
        cfg["sync"]["auto_create"] = False
        engine, mock_client, _, _ = _make_engine(tmp_path, config=cfg)

        result = engine.sync(_event("opened"))
        assert result.status == "skipped"
        mock_client.create_work_item.assert_not_called()

    def test_updates_existing_entry_on_reopen(self, tmp_path):
        """If ledger already has entry, opened event updates instead."""
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("opened"))
        assert result.status == "updated"
        mock_client.update_work_item.assert_called_once()

    def test_work_item_type_from_labels(self, tmp_path):
        engine, mock_client, _, _ = _make_engine(tmp_path)
        engine.sync(_event("opened", labels=["bug"]))

        call_args = mock_client.create_work_item.call_args
        assert call_args[0][0] == "Bug"  # first positional arg = type


# ── issues.edited ────────────────────────────────────────────────────────


class TestHandleEdited:
    def test_updates_existing(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("edited"))
        assert result.status == "updated"
        mock_client.update_work_item.assert_called_once()

    def test_skips_without_ledger_entry(self, tmp_path):
        engine, mock_client, _, _ = _make_engine(tmp_path)

        result = engine.sync(_event("edited"))
        assert result.status == "skipped"
        mock_client.update_work_item.assert_not_called()


# ── issues.closed ────────────────────────────────────────────────────────


class TestHandleClosed:
    def test_updates_state_to_closed(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("closed", state="closed"))
        assert result.status == "updated"
        assert result.operation == "update"

        # Verify the state patch
        call_args = mock_client.update_work_item.call_args
        ops = call_args[0][1]
        state_op = next(op for op in ops if op.path == "/fields/System.State")
        assert state_op.value == "Closed"

    def test_compound_state_with_bug_label(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("closed", state="closed", labels=["bug"]))
        call_args = mock_client.update_work_item.call_args
        ops = call_args[0][1]
        state_op = next(op for op in ops if op.path == "/fields/System.State")
        assert state_op.value == "Resolved"

    def test_skips_without_ledger_entry(self, tmp_path):
        engine, mock_client, _, _ = _make_engine(tmp_path)
        result = engine.sync(_event("closed", state="closed"))
        assert result.status == "skipped"


# ── issues.reopened ──────────────────────────────────────────────────────


class TestHandleReopened:
    def test_updates_state_to_new(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("reopened", state="open"))
        assert result.status == "updated"

        call_args = mock_client.update_work_item.call_args
        ops = call_args[0][1]
        state_op = next(op for op in ops if op.path == "/fields/System.State")
        assert state_op.value == "New"


# ── issues.labeled ───────────────────────────────────────────────────────


class TestHandleLabeled:
    def test_updates_with_new_labels(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("labeled", labels=["P1"]))
        assert result.status == "updated"

    def test_skips_without_ledger_entry(self, tmp_path):
        engine, _, _, _ = _make_engine(tmp_path)
        result = engine.sync(_event("labeled", labels=["P1"]))
        assert result.status == "skipped"


# ── issues.unlabeled ─────────────────────────────────────────────────────


class TestHandleUnlabeled:
    def test_re_evaluates_priority_and_state(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("unlabeled", labels=[]))
        assert result.status == "updated"
        mock_client.update_work_item.assert_called_once()

    def test_skips_without_ledger_entry(self, tmp_path):
        engine, _, _, _ = _make_engine(tmp_path)
        result = engine.sync(_event("unlabeled"))
        assert result.status == "skipped"


# ── issues.assigned ──────────────────────────────────────────────────────


class TestHandleAssigned:
    def test_maps_assignee(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("assigned", assignee="octocat"))
        assert result.status == "updated"

        call_args = mock_client.update_work_item.call_args
        ops = call_args[0][1]
        assignee_op = next(op for op in ops if op.path == "/fields/System.AssignedTo")
        assert assignee_op.value == "octocat@example.com"

    def test_skips_unmapped_assignee(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("assigned", assignee="unknown_user"))
        assert result.status == "skipped"
        mock_client.update_work_item.assert_not_called()

    def test_skips_without_assignee(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("assigned"))
        assert result.status == "skipped"


# ── issues.unassigned ────────────────────────────────────────────────────


class TestHandleUnassigned:
    def test_clears_assignee(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("unassigned"))
        assert result.status == "updated"

        call_args = mock_client.update_work_item.call_args
        ops = call_args[0][1]
        assignee_op = next(op for op in ops if op.path == "/fields/System.AssignedTo")
        assert assignee_op.value == ""


# ── issues.milestoned ────────────────────────────────────────────────────


class TestHandleMilestoned:
    def test_sets_iteration_path(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("milestoned", milestone="Sprint 2"))
        assert result.status == "updated"

        call_args = mock_client.update_work_item.call_args
        ops = call_args[0][1]
        iter_op = next(op for op in ops if op.path == "/fields/System.IterationPath")
        assert iter_op.value == "TestProject\\Sprint 2"

    def test_skips_without_milestone(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        event = _event("milestoned")
        event["issue"]["milestone"] = None
        result = engine.sync(event)
        assert result.status == "skipped"


# ── issues.demilestoned ──────────────────────────────────────────────────


class TestHandleDemilestoned:
    def test_resets_iteration_path(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("demilestoned"))
        assert result.status == "updated"

        call_args = mock_client.update_work_item.call_args
        ops = call_args[0][1]
        iter_op = next(op for op in ops if op.path == "/fields/System.IterationPath")
        assert iter_op.value == "TestProject\\Sprint 1"


# ── Echo detection ───────────────────────────────────────────────────────


class TestEchoDetection:
    def test_skips_recent_ado_sync(self, tmp_path):
        """If last_sync_source is 'ado' and within grace period, skip."""
        now = datetime.now(timezone.utc).isoformat()
        ledger = _ledger_with_entry(last_sync_source="ado", last_synced_at=now)
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("edited"))
        assert result.status == "skipped"
        assert result.operation == "noop"
        mock_client.update_work_item.assert_not_called()

    def test_processes_old_ado_sync(self, tmp_path):
        """If last_sync_source is 'ado' but outside grace period, process."""
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
        ledger = _ledger_with_entry(last_sync_source="ado", last_synced_at=old_time)
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("edited"))
        assert result.status == "updated"

    def test_processes_github_sync_source(self, tmp_path):
        """If last_sync_source is 'github', never skip."""
        now = datetime.now(timezone.utc).isoformat()
        ledger = _ledger_with_entry(last_sync_source="github", last_synced_at=now)
        engine, mock_client, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_event("edited"))
        assert result.status == "updated"


# ── Label filters ────────────────────────────────────────────────────────


class TestLabelFilters:
    def test_exclude_label_skips(self, tmp_path):
        engine, mock_client, _, _ = _make_engine(tmp_path)

        result = engine.sync(_event("opened", labels=["internal"]))
        assert result.status == "skipped"
        mock_client.create_work_item.assert_not_called()

    def test_exclude_governance_label(self, tmp_path):
        engine, mock_client, _, _ = _make_engine(tmp_path)

        result = engine.sync(_event("opened", labels=["governance"]))
        assert result.status == "skipped"

    def test_include_filter_allows_matching(self, tmp_path):
        cfg = _config()
        cfg["filters"]["include_labels"] = ["sync-to-ado"]
        cfg["filters"]["exclude_labels"] = []
        engine, mock_client, _, _ = _make_engine(tmp_path, config=cfg)

        result = engine.sync(_event("opened", labels=["sync-to-ado"]))
        assert result.status == "created"

    def test_include_filter_blocks_non_matching(self, tmp_path):
        cfg = _config()
        cfg["filters"]["include_labels"] = ["sync-to-ado"]
        cfg["filters"]["exclude_labels"] = []
        engine, mock_client, _, _ = _make_engine(tmp_path, config=cfg)

        result = engine.sync(_event("opened", labels=["other"]))
        assert result.status == "skipped"

    def test_empty_include_allows_all(self, tmp_path):
        cfg = _config()
        cfg["filters"]["include_labels"] = []
        cfg["filters"]["exclude_labels"] = []
        engine, _, _, _ = _make_engine(tmp_path, config=cfg)

        result = engine.sync(_event("opened"))
        assert result.status == "created"

    def test_exclude_takes_priority_over_include(self, tmp_path):
        cfg = _config()
        cfg["filters"]["include_labels"] = ["internal"]
        cfg["filters"]["exclude_labels"] = ["internal"]
        engine, mock_client, _, _ = _make_engine(tmp_path, config=cfg)

        result = engine.sync(_event("opened", labels=["internal"]))
        assert result.status == "skipped"


# ── Ledger management ────────────────────────────────────────────────────


class TestLedgerManagement:
    def test_creates_ledger_file(self, tmp_path):
        engine, _, ledger_path, _ = _make_engine(tmp_path)
        engine.sync(_event("opened"))

        assert ledger_path.exists()
        data = json.loads(ledger_path.read_text())
        assert data["schema_version"] == "1.0.0"
        assert len(data["mappings"]) == 1

    def test_creates_parent_directories(self, tmp_path):
        """Ledger path's parent dirs should be auto-created."""
        engine, _, ledger_path, _ = _make_engine(tmp_path)
        assert not ledger_path.parent.exists()

        engine.sync(_event("opened"))
        assert ledger_path.parent.exists()

    def test_updates_existing_entry(self, tmp_path):
        ledger = _ledger_with_entry()
        engine, _, ledger_path, _ = _make_engine(tmp_path, ledger=ledger)

        engine.sync(_event("edited"))

        data = json.loads(ledger_path.read_text())
        assert len(data["mappings"]) == 1
        assert data["mappings"][0]["last_sync_source"] == "github"
        assert data["mappings"][0]["sync_status"] == "active"

    def test_multiple_issues_tracked(self, tmp_path):
        engine, mock_client, ledger_path, _ = _make_engine(tmp_path)
        mock_client.create_work_item.side_effect = [_work_item(100), _work_item(200)]

        engine.sync(_event("opened", issue_number=1))
        engine.sync(_event("opened", issue_number=2))

        data = json.loads(ledger_path.read_text())
        assert len(data["mappings"]) == 2

    def test_handles_empty_ledger_file(self, tmp_path):
        """Empty file should be treated as new ledger."""
        ledger_path = tmp_path / ".governance" / "state" / "ado-sync-ledger.json"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("")

        engine, _, _, _ = _make_engine(tmp_path)
        result = engine.sync(_event("opened"))
        assert result.status == "created"

    def test_handles_corrupt_ledger_file(self, tmp_path):
        """Corrupt JSON should be treated as new ledger."""
        ledger_path = tmp_path / ".governance" / "state" / "ado-sync-ledger.json"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("{invalid json")

        engine = SyncEngine(
            MagicMock(create_work_item=MagicMock(return_value=_work_item(100))),
            _config(),
            ledger_path,
            tmp_path / ".governance" / "state" / "ado-sync-errors.json",
        )
        result = engine.sync(_event("opened"))
        assert result.status == "created"


# ── Error handling ───────────────────────────────────────────────────────


class TestErrorHandling:
    def test_ado_error_returns_error_result(self, tmp_path):
        mock_client = MagicMock()
        mock_client.create_work_item.side_effect = AdoError("API failure", status_code=500)
        engine, _, _, _ = _make_engine(tmp_path, client=mock_client)

        result = engine.sync(_event("opened"))
        assert result.status == "error"
        assert result.operation == "create"
        assert "API failure" in result.error

    def test_ado_auth_error_logged(self, tmp_path):
        mock_client = MagicMock()
        mock_client.create_work_item.side_effect = AdoAuthError("Unauthorized", status_code=401)
        engine, _, _, error_path = _make_engine(tmp_path, client=mock_client)

        engine.sync(_event("opened"))

        assert error_path.exists()
        data = json.loads(error_path.read_text())
        assert len(data["errors"]) == 1
        assert data["errors"][0]["error_type"] == "AdoAuthError"
        assert data["errors"][0]["operation"] == "create"

    def test_ado_validation_error_logged(self, tmp_path):
        ledger = _ledger_with_entry()
        mock_client = MagicMock()
        mock_client.update_work_item.side_effect = AdoValidationError("Bad request", status_code=400)
        engine, _, _, error_path = _make_engine(tmp_path, client=mock_client, ledger=ledger)

        result = engine.sync(_event("edited"))
        assert result.status == "error"
        assert result.operation == "update"

        data = json.loads(error_path.read_text())
        assert data["errors"][0]["error_type"] == "AdoValidationError"
        assert data["errors"][0]["github_issue_number"] == 42

    def test_error_log_accumulates(self, tmp_path):
        mock_client = MagicMock()
        mock_client.create_work_item.side_effect = AdoError("fail")
        engine, _, _, error_path = _make_engine(tmp_path, client=mock_client)

        engine.sync(_event("opened", issue_number=1))
        engine.sync(_event("opened", issue_number=2))

        data = json.loads(error_path.read_text())
        assert len(data["errors"]) == 2

    def test_error_record_has_uuid(self, tmp_path):
        mock_client = MagicMock()
        mock_client.create_work_item.side_effect = AdoError("fail")
        engine, _, _, error_path = _make_engine(tmp_path, client=mock_client)

        engine.sync(_event("opened"))

        data = json.loads(error_path.read_text())
        error_id = data["errors"][0]["error_id"]
        # UUID v4 format check
        assert len(error_id) == 36
        assert error_id.count("-") == 4

    def test_no_issue_number_returns_skipped(self, tmp_path):
        engine, _, _, _ = _make_engine(tmp_path)
        event = _event("opened")
        del event["issue"]["number"]

        result = engine.sync(event)
        assert result.status == "skipped"
        assert "No issue number" in (result.error or "")


# ── Unknown action ───────────────────────────────────────────────────────


class TestUnknownAction:
    def test_unknown_action_skipped(self, tmp_path):
        engine, mock_client, _, _ = _make_engine(tmp_path)
        result = engine.sync(_event("transferred"))
        assert result.status == "skipped"
        assert result.operation == "noop"
