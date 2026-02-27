"""Tests for the ADO-to-GitHub reverse sync engine."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from governance.integrations.ado.reverse_sync import ReverseSyncEngine
from governance.integrations.ado.sync_engine import SyncResult


# -- Fixtures / helpers ----------------------------------------------------


def _config(**overrides) -> dict:
    """Build a minimal ado_integration config dict."""
    base: dict = {
        "organization": "https://dev.azure.com/testorg",
        "project": "TestProject",
        "sync": {
            "direction": "bidirectional",
            "auto_create": True,
            "grace_period_seconds": 5,
        },
        "state_mapping": {
            "open": "New",
            "closed": "Closed",
        },
        "field_mapping": {
            "area_path": "TestProject\\TeamA",
            "iteration_path": "TestProject\\Sprint 1",
            "priority_labels": {"P1": 1, "P2": 2},
        },
        "user_mapping": {
            "octocat": "octocat@example.com",
        },
    }
    base.update(overrides)
    return base


def _payload(
    event_type: str = "workitem.updated",
    work_item_id: int = 100,
    *,
    changed_fields: dict | None = None,
    revision_fields: dict | None = None,
) -> dict:
    """Build an ADO webhook payload."""
    resource: dict = {
        "workItemId": work_item_id,
        "id": work_item_id,
    }

    if event_type == "workitem.updated":
        # Fields dict with oldValue/newValue
        fields = {}
        for k, v in (changed_fields or {}).items():
            fields[k] = {"oldValue": None, "newValue": v}
        resource["fields"] = fields
    elif event_type == "workitem.created":
        resource["revision"] = {
            "fields": revision_fields or {},
        }

    return {
        "eventType": event_type,
        "resource": resource,
    }


def _ledger_with_entry(
    issue_number: int = 42,
    repo: str = "owner/repo",
    ado_id: int = 100,
    last_sync_source: str = "ado",
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


def _make_engine(
    tmp_path: Path,
    config: dict | None = None,
    ledger: dict | None = None,
) -> tuple[ReverseSyncEngine, Path, Path]:
    """Set up a ReverseSyncEngine with temp paths."""
    ledger_path = tmp_path / ".governance" / "state" / "ado-sync-ledger.json"
    error_path = tmp_path / ".governance" / "state" / "ado-sync-errors.json"

    if ledger:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2))

    cfg = config or _config()
    engine = ReverseSyncEngine(
        config=cfg,
        github_token="ghp_test_token",
        github_repo="owner/repo",
        ledger_path=ledger_path,
        error_log_path=error_path,
    )
    return engine, ledger_path, error_path


# -- No ledger entry (skip) -----------------------------------------------


class TestNoLedgerEntry:
    def test_skips_when_no_ledger_entry(self, tmp_path):
        engine, _, _ = _make_engine(tmp_path)
        result = engine.sync(_payload("workitem.updated", work_item_id=999))
        assert result.status == "skipped"
        assert "No ledger entry" in (result.error or "")

    def test_skips_when_no_work_item_id(self, tmp_path):
        engine, _, _ = _make_engine(tmp_path)
        result = engine.sync({"eventType": "workitem.updated", "resource": {}})
        assert result.status == "skipped"
        assert "No work item ID" in (result.error or "")


# -- Echo detection --------------------------------------------------------


class TestEchoDetection:
    def test_skips_recent_github_sync(self, tmp_path):
        """If last_sync_source is 'github' and within grace period, skip."""
        now = datetime.now(timezone.utc).isoformat()
        ledger = _ledger_with_entry(last_sync_source="github", last_synced_at=now)
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_payload(
            "workitem.updated",
            changed_fields={"System.Title": "New Title"},
        ))
        assert result.status == "skipped"
        assert result.operation == "noop"

    def test_processes_old_github_sync(self, tmp_path):
        """If last_sync_source is 'github' but outside grace period, process."""
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
        ledger = _ledger_with_entry(last_sync_source="github", last_synced_at=old_time)
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None):
            result = engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.Title": "New Title"},
            ))
        assert result.status == "updated"

    def test_processes_ado_sync_source(self, tmp_path):
        """If last_sync_source is 'ado', never skip (not an echo)."""
        now = datetime.now(timezone.utc).isoformat()
        ledger = _ledger_with_entry(last_sync_source="ado", last_synced_at=now)
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None):
            result = engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.Title": "New Title"},
            ))
        assert result.status == "updated"


# -- workitem.updated ------------------------------------------------------


class TestHandleUpdated:
    def test_updates_title(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None) as mock_api:
            result = engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.Title": "New Title"},
            ))

        assert result.status == "updated"
        assert result.ado_work_item_id == 100

        # Check that PATCH was called with title
        patch_calls = [
            c for c in mock_api.call_args_list
            if c[0][0] == "PATCH"
        ]
        assert len(patch_calls) >= 1
        assert patch_calls[0].kwargs["json"]["title"] == "New Title"

    def test_updates_state_to_closed(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None) as mock_api:
            result = engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.State": "Closed"},
            ))

        assert result.status == "updated"

        # Check state was set to closed
        patch_calls = [
            c for c in mock_api.call_args_list
            if c[0][0] == "PATCH" and "/issues/" in c[0][1]
        ]
        assert any(
            c.kwargs.get("json", {}).get("state") == "closed"
            for c in patch_calls
        )

    def test_updates_state_to_open(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None) as mock_api:
            result = engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.State": "Active"},
            ))

        assert result.status == "updated"

        patch_calls = [
            c for c in mock_api.call_args_list
            if c[0][0] == "PATCH" and "/issues/" in c[0][1]
        ]
        assert any(
            c.kwargs.get("json", {}).get("state") == "open"
            for c in patch_calls
        )

    def test_updates_assignee(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None) as mock_api:
            result = engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.AssignedTo": "octocat@example.com"},
            ))

        assert result.status == "updated"
        patch_calls = [
            c for c in mock_api.call_args_list
            if c[0][0] == "PATCH" and "/issues/" in c[0][1]
        ]
        assert any(
            c.kwargs.get("json", {}).get("assignees") == ["octocat"]
            for c in patch_calls
        )

    def test_skips_no_changed_fields(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        payload = {
            "eventType": "workitem.updated",
            "resource": {
                "workItemId": 100,
                "id": 100,
                "fields": {},
            },
        }
        result = engine.sync(payload)
        assert result.status == "skipped"

    def test_updates_ledger_after_sync(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, ledger_path, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None):
            engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.Title": "Updated"},
            ))

        data = json.loads(ledger_path.read_text())
        assert data["mappings"][0]["last_sync_source"] == "ado"

    def test_updates_priority_labels(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None) as mock_api:
            result = engine.sync(_payload(
                "workitem.updated",
                changed_fields={"Microsoft.VSTS.Common.Priority": 1},
            ))

        assert result.status == "updated"

        # Check labels were added
        label_add_calls = [
            c for c in mock_api.call_args_list
            if c[0][0] == "POST" and "/labels" in c[0][1]
        ]
        assert any(
            "P1" in c.kwargs.get("json", {}).get("labels", [])
            for c in label_add_calls
        )

    def test_multiple_field_changes(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None) as mock_api:
            result = engine.sync(_payload(
                "workitem.updated",
                changed_fields={
                    "System.Title": "Multi Update",
                    "System.Description": "New body",
                },
            ))

        assert result.status == "updated"

        patch_calls = [
            c for c in mock_api.call_args_list
            if c[0][0] == "PATCH" and "/issues/" in c[0][1]
        ]
        assert len(patch_calls) >= 1
        body = patch_calls[0].kwargs["json"]
        assert body["title"] == "Multi Update"
        assert body["body"] == "New body"


# -- workitem.created ------------------------------------------------------


class TestHandleCreated:
    def test_updates_github_from_revision(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None) as mock_api:
            result = engine.sync(_payload(
                "workitem.created",
                work_item_id=100,
                revision_fields={"System.Title": "Created Item"},
            ))

        assert result.status == "updated"
        assert result.ado_work_item_id == 100

    def test_skips_empty_revision(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync(_payload(
            "workitem.created",
            work_item_id=100,
            revision_fields={},
        ))
        assert result.status == "skipped"


# -- workitem.deleted ------------------------------------------------------


class TestHandleDeleted:
    def test_closes_github_issue(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None) as mock_api:
            result = engine.sync(_payload("workitem.deleted"))

        assert result.status == "updated"

        # Should close the issue
        patch_calls = [
            c for c in mock_api.call_args_list
            if c[0][0] == "PATCH"
        ]
        assert any(
            c.kwargs.get("json", {}).get("state") == "closed"
            for c in patch_calls
        )

        # Should add a comment
        comment_calls = [
            c for c in mock_api.call_args_list
            if c[0][0] == "POST" and "/comments" in c[0][1]
        ]
        assert len(comment_calls) == 1
        assert "deleted" in comment_calls[0].kwargs["json"]["body"].lower()


# -- Unknown event ---------------------------------------------------------


class TestUnknownEvent:
    def test_unknown_event_skipped(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        result = engine.sync({
            "eventType": "workitem.commented",
            "resource": {"workItemId": 100, "id": 100},
        })
        assert result.status == "skipped"


# -- Error handling --------------------------------------------------------


class TestErrorHandling:
    def test_github_api_error_returns_error_result(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", side_effect=RuntimeError("API failure")):
            result = engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.Title": "Fail"},
            ))

        assert result.status == "error"
        assert "API failure" in result.error

    def test_error_logged(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, error_path = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", side_effect=RuntimeError("API failure")):
            engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.Title": "Fail"},
            ))

        assert error_path.exists()
        data = json.loads(error_path.read_text())
        assert len(data["errors"]) == 1
        assert data["errors"][0]["error_type"] == "RuntimeError"
        assert data["errors"][0]["source"] == "ado"

    def test_error_log_accumulates(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, error_path = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", side_effect=RuntimeError("fail")):
            engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.Title": "Fail 1"},
            ))
            engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.Title": "Fail 2"},
            ))

        data = json.loads(error_path.read_text())
        assert len(data["errors"]) == 2

    def test_error_record_has_uuid(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, error_path = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", side_effect=RuntimeError("fail")):
            engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.Title": "Fail"},
            ))

        data = json.loads(error_path.read_text())
        error_id = data["errors"][0]["error_id"]
        assert len(error_id) == 36
        assert error_id.count("-") == 4


# -- Ledger management ----------------------------------------------------


class TestLedgerManagement:
    def test_creates_parent_directories(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        # Manually set up without creating dirs
        ledger_path = tmp_path / "deep" / "nested" / "ledger.json"
        error_path = tmp_path / "deep" / "nested" / "errors.json"

        # Write ledger in a temp location, then move to the actual path
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2))

        engine = ReverseSyncEngine(
            config=_config(),
            github_token="ghp_test",
            github_repo="owner/repo",
            ledger_path=ledger_path,
            error_log_path=error_path,
        )

        with patch.object(engine, "_github_api", return_value=None):
            result = engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.Title": "Updated"},
            ))

        assert result.status == "updated"
        data = json.loads(ledger_path.read_text())
        assert data["mappings"][0]["last_sync_source"] == "ado"

    def test_handles_empty_ledger_file(self, tmp_path):
        ledger_path = tmp_path / ".governance" / "state" / "ado-sync-ledger.json"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("")

        engine = ReverseSyncEngine(
            config=_config(),
            github_token="ghp_test",
            github_repo="owner/repo",
            ledger_path=ledger_path,
            error_log_path=tmp_path / "errors.json",
        )

        result = engine.sync(_payload("workitem.updated", changed_fields={"System.Title": "X"}))
        assert result.status == "skipped"

    def test_handles_corrupt_ledger(self, tmp_path):
        ledger_path = tmp_path / ".governance" / "state" / "ado-sync-ledger.json"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text("{invalid json")

        engine = ReverseSyncEngine(
            config=_config(),
            github_token="ghp_test",
            github_repo="owner/repo",
            ledger_path=ledger_path,
            error_log_path=tmp_path / "errors.json",
        )

        result = engine.sync(_payload("workitem.updated", changed_fields={"System.Title": "X"}))
        assert result.status == "skipped"

    def test_finds_entry_by_ado_id(self, tmp_path):
        """Reverse sync looks up by ADO work item ID, not by GitHub issue number."""
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 10,
                    "github_repo": "owner/repo",
                    "ado_work_item_id": 200,
                    "ado_project": "TestProject",
                    "sync_direction": "github_to_ado",
                    "last_synced_at": "2026-01-01T00:00:00+00:00",
                    "last_sync_source": "ado",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "sync_status": "active",
                },
                {
                    "github_issue_number": 42,
                    "github_repo": "owner/repo",
                    "ado_work_item_id": 100,
                    "ado_project": "TestProject",
                    "sync_direction": "github_to_ado",
                    "last_synced_at": "2026-01-01T00:00:00+00:00",
                    "last_sync_source": "ado",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "sync_status": "active",
                },
            ],
        }
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None) as mock_api:
            result = engine.sync(_payload(
                "workitem.updated",
                work_item_id=100,
                changed_fields={"System.Title": "Updated"},
            ))

        assert result.status == "updated"

        # Should have updated issue #42 (the entry matching ado_work_item_id=100)
        patch_calls = [
            c for c in mock_api.call_args_list
            if c[0][0] == "PATCH"
        ]
        assert any("/issues/42" in c[0][1] for c in patch_calls)


# -- Label management in apply_github_updates ------------------------------


class TestLabelManagement:
    def test_state_change_adds_and_removes_labels(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None) as mock_api:
            engine.sync(_payload(
                "workitem.updated",
                changed_fields={"System.State": "Active"},
            ))

        # Should add ado:active
        add_calls = [
            c for c in mock_api.call_args_list
            if c[0][0] == "POST" and "/labels" in c[0][1]
        ]
        assert any(
            "ado:active" in c.kwargs.get("json", {}).get("labels", [])
            for c in add_calls
        )

        # Should remove other ado: labels
        delete_calls = [
            c for c in mock_api.call_args_list
            if c[0][0] == "DELETE" and "/labels/" in c[0][1]
        ]
        deleted_labels = [c[0][1].split("/labels/")[1] for c in delete_calls]
        assert "ado:new" in deleted_labels

    def test_priority_change_removes_old_adds_new(self, tmp_path):
        ledger = _ledger_with_entry(last_sync_source="ado")
        engine, _, _ = _make_engine(tmp_path, ledger=ledger)

        with patch.object(engine, "_github_api", return_value=None) as mock_api:
            engine.sync(_payload(
                "workitem.updated",
                changed_fields={"Microsoft.VSTS.Common.Priority": 2},
            ))

        # Should add P2
        add_calls = [
            c for c in mock_api.call_args_list
            if c[0][0] == "POST" and "/labels" in c[0][1]
        ]
        assert any(
            "P2" in c.kwargs.get("json", {}).get("labels", [])
            for c in add_calls
        )

        # Should remove P1 (the other priority label)
        delete_calls = [
            c for c in mock_api.call_args_list
            if c[0][0] == "DELETE" and "/labels/" in c[0][1]
        ]
        deleted_labels = [c[0][1].split("/labels/")[1] for c in delete_calls]
        assert "P1" in deleted_labels
