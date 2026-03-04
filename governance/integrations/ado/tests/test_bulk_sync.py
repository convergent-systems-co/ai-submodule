"""Tests for bulk initial sync."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from governance.integrations.ado._exceptions import AdoError, AdoRateLimitError
from governance.integrations.ado._types import WorkItem
from governance.integrations.ado.bulk_sync import (
    _extract_labels,
    _is_ado_in_ledger,
    _is_in_ledger,
    _retry_with_backoff,
    initial_sync,
)


# ── Helpers ────────────────────────────────────────────────────────────────


def _config(**overrides):
    base = {
        "organization": "https://dev.azure.com/testorg",
        "project": "TestProject",
        "sync": {
            "direction": "github_to_ado",
            "auto_create": True,
        },
        "type_mapping": {
            "default": "User Story",
            "bug": "Bug",
        },
        "field_mapping": {},
        "state_mapping": {"open": "New", "closed": "Closed"},
    }
    base.update(overrides)
    return base


def _work_item(wi_id=100):
    return WorkItem(
        id=wi_id,
        rev=1,
        url=f"https://dev.azure.com/testorg/TestProject/_apis/wit/workitems/{wi_id}",
        fields={"System.Title": "Test", "System.WorkItemType": "User Story"},
    )


def _gh_issue(number=1, title="Issue", body="Body", labels=None):
    return {
        "number": number,
        "title": title,
        "body": body,
        "state": "OPEN",
        "labels": [{"name": lbl} for lbl in (labels or [])],
        "createdAt": "2026-01-15T00:00:00Z",
    }


# ── _extract_labels ───────────────────────────────────────────────────────


class TestExtractLabels:
    def test_dict_labels(self):
        issue = {"labels": [{"name": "bug"}, {"name": "P1"}]}
        assert _extract_labels(issue) == ["bug", "P1"]

    def test_string_labels(self):
        issue = {"labels": ["bug", "P1"]}
        assert _extract_labels(issue) == ["bug", "P1"]

    def test_empty_labels(self):
        assert _extract_labels({"labels": []}) == []

    def test_no_labels_key(self):
        assert _extract_labels({}) == []


# ── _is_in_ledger ─────────────────────────────────────────────────────────


class TestIsInLedger:
    def test_found(self):
        ledger = {
            "mappings": [
                {"github_issue_number": 42, "github_repo": "owner/repo"}
            ]
        }
        assert _is_in_ledger(ledger, 42, "owner/repo") is True

    def test_not_found(self):
        ledger = {
            "mappings": [
                {"github_issue_number": 42, "github_repo": "owner/repo"}
            ]
        }
        assert _is_in_ledger(ledger, 99, "owner/repo") is False

    def test_wrong_repo(self):
        ledger = {
            "mappings": [
                {"github_issue_number": 42, "github_repo": "owner/repo"}
            ]
        }
        assert _is_in_ledger(ledger, 42, "other/repo") is False

    def test_empty_ledger(self):
        assert _is_in_ledger({"mappings": []}, 42, "owner/repo") is False


# ── _is_ado_in_ledger ─────────────────────────────────────────────────────


class TestIsAdoInLedger:
    def test_found(self):
        ledger = {"mappings": [{"ado_work_item_id": 100}]}
        assert _is_ado_in_ledger(ledger, 100) is True

    def test_not_found(self):
        ledger = {"mappings": [{"ado_work_item_id": 100}]}
        assert _is_ado_in_ledger(ledger, 999) is False


# ── _retry_with_backoff ───────────────────────────────────────────────────


class TestRetryWithBackoff:
    def test_success_first_try(self):
        fn = MagicMock(return_value="ok")
        assert _retry_with_backoff(fn) == "ok"
        fn.assert_called_once()

    @patch("governance.integrations.ado.bulk_sync.time.sleep")
    def test_retries_on_rate_limit(self, mock_sleep):
        fn = MagicMock(side_effect=[
            AdoRateLimitError("limit", retry_after_seconds=0.1),
            "ok",
        ])
        assert _retry_with_backoff(fn) == "ok"
        assert fn.call_count == 2

    @patch("governance.integrations.ado.bulk_sync.time.sleep")
    def test_raises_after_max_retries(self, mock_sleep):
        fn = MagicMock(side_effect=AdoRateLimitError("limit", retry_after_seconds=0.1))
        with pytest.raises(AdoRateLimitError):
            _retry_with_backoff(fn)


# ── initial_sync (GitHub -> ADO) ──────────────────────────────────────────


class TestInitialSyncGitHubToAdo:
    @patch("governance.integrations.ado.bulk_sync._gh_list_issues")
    def test_creates_work_items(self, mock_gh, tmp_path):
        mock_gh.return_value = [_gh_issue(1), _gh_issue(2)]

        client = MagicMock()
        client.create_work_item.side_effect = [_work_item(100), _work_item(200)]

        ledger_path = tmp_path / "ledger.json"
        error_path = tmp_path / "errors.json"

        results = initial_sync(
            _config(), client, ledger_path, error_path,
            direction="github_to_ado",
            github_repo="owner/repo",
        )

        assert len(results) == 2
        assert results[0].status == "created"
        assert results[0].ado_work_item_id == 100
        assert results[1].status == "created"
        assert results[1].ado_work_item_id == 200

        # Verify ledger was updated
        ledger = json.loads(ledger_path.read_text())
        assert len(ledger["mappings"]) == 2

    @patch("governance.integrations.ado.bulk_sync._gh_list_issues")
    def test_skips_existing_entries(self, mock_gh, tmp_path):
        mock_gh.return_value = [_gh_issue(1)]

        client = MagicMock()
        ledger_path = tmp_path / "ledger.json"
        error_path = tmp_path / "errors.json"

        # Pre-populate ledger
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [{
                "github_issue_number": 1,
                "github_repo": "owner/repo",
                "ado_work_item_id": 100,
                "ado_project": "TestProject",
                "sync_direction": "github_to_ado",
                "last_synced_at": "2026-01-01T00:00:00+00:00",
                "sync_status": "active",
            }],
        }
        ledger_path.write_text(json.dumps(ledger))

        results = initial_sync(
            _config(), client, ledger_path, error_path,
            direction="github_to_ado",
            github_repo="owner/repo",
        )

        assert len(results) == 1
        assert results[0].status == "skipped"
        client.create_work_item.assert_not_called()

    @patch("governance.integrations.ado.bulk_sync._gh_list_issues")
    def test_dry_run_does_not_create(self, mock_gh, tmp_path):
        mock_gh.return_value = [_gh_issue(1)]

        client = MagicMock()
        ledger_path = tmp_path / "ledger.json"
        error_path = tmp_path / "errors.json"

        results = initial_sync(
            _config(), client, ledger_path, error_path,
            direction="github_to_ado",
            dry_run=True,
            github_repo="owner/repo",
        )

        assert len(results) == 1
        assert results[0].status == "skipped"
        client.create_work_item.assert_not_called()
        assert not ledger_path.exists()

    @patch("governance.integrations.ado.bulk_sync._gh_list_issues")
    def test_handles_ado_error(self, mock_gh, tmp_path):
        mock_gh.return_value = [_gh_issue(1)]

        client = MagicMock()
        client.create_work_item.side_effect = AdoError("Failed", status_code=500)

        ledger_path = tmp_path / "ledger.json"
        error_path = tmp_path / "errors.json"

        results = initial_sync(
            _config(), client, ledger_path, error_path,
            direction="github_to_ado",
            github_repo="owner/repo",
        )

        assert len(results) == 1
        assert results[0].status == "error"

        # Error log should have been created
        assert error_path.exists()
        error_log = json.loads(error_path.read_text())
        assert len(error_log["errors"]) == 1

    @patch("governance.integrations.ado.bulk_sync._gh_list_issues")
    def test_empty_issue_list(self, mock_gh, tmp_path):
        mock_gh.return_value = []

        client = MagicMock()
        ledger_path = tmp_path / "ledger.json"
        error_path = tmp_path / "errors.json"

        results = initial_sync(
            _config(), client, ledger_path, error_path,
            direction="github_to_ado",
        )

        assert len(results) == 0

    @patch("governance.integrations.ado.bulk_sync._gh_list_issues")
    def test_limit_applies(self, mock_gh, tmp_path):
        mock_gh.return_value = [_gh_issue(1), _gh_issue(2), _gh_issue(3)]

        client = MagicMock()
        client.create_work_item.return_value = _work_item(100)

        ledger_path = tmp_path / "ledger.json"
        error_path = tmp_path / "errors.json"

        results = initial_sync(
            _config(), client, ledger_path, error_path,
            direction="github_to_ado",
            limit=2,
            github_repo="owner/repo",
        )

        # Should have processed at most 2
        assert len(results) <= 2


# ── initial_sync (ADO -> GitHub) ──────────────────────────────────────────


class TestInitialSyncAdoToGitHub:
    @patch("governance.integrations.ado.bulk_sync._gh_create_issue")
    def test_creates_github_issues(self, mock_gh_create, tmp_path):
        mock_gh_create.side_effect = [10, 20]

        client = MagicMock()
        client.query_wiql_with_details.return_value = [
            _work_item(100),
            _work_item(200),
        ]

        ledger_path = tmp_path / "ledger.json"
        error_path = tmp_path / "errors.json"

        results = initial_sync(
            _config(), client, ledger_path, error_path,
            direction="ado_to_github",
            github_repo="owner/repo",
        )

        assert len(results) == 2
        assert results[0].status == "created"
        assert results[1].status == "created"

        ledger = json.loads(ledger_path.read_text())
        assert len(ledger["mappings"]) == 2
        assert ledger["mappings"][0]["sync_direction"] == "ado_to_github"

    @patch("governance.integrations.ado.bulk_sync._gh_create_issue")
    def test_skips_existing_ado_entries(self, mock_gh_create, tmp_path):
        client = MagicMock()
        client.query_wiql_with_details.return_value = [_work_item(100)]

        ledger_path = tmp_path / "ledger.json"
        error_path = tmp_path / "errors.json"

        # Pre-populate ledger
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [{
                "github_issue_number": 1,
                "github_repo": "owner/repo",
                "ado_work_item_id": 100,
                "ado_project": "TestProject",
                "sync_direction": "ado_to_github",
                "last_synced_at": "2026-01-01T00:00:00+00:00",
                "sync_status": "active",
            }],
        }
        ledger_path.write_text(json.dumps(ledger))

        results = initial_sync(
            _config(), client, ledger_path, error_path,
            direction="ado_to_github",
            github_repo="owner/repo",
        )

        assert len(results) == 1
        assert results[0].status == "skipped"
        mock_gh_create.assert_not_called()

    @patch("governance.integrations.ado.bulk_sync._gh_create_issue")
    def test_dry_run_no_changes(self, mock_gh_create, tmp_path):
        client = MagicMock()
        client.query_wiql_with_details.return_value = [_work_item(100)]

        ledger_path = tmp_path / "ledger.json"
        error_path = tmp_path / "errors.json"

        results = initial_sync(
            _config(), client, ledger_path, error_path,
            direction="ado_to_github",
            dry_run=True,
            github_repo="owner/repo",
        )

        assert len(results) == 1
        assert results[0].status == "skipped"
        mock_gh_create.assert_not_called()

    @patch("governance.integrations.ado.bulk_sync._gh_create_issue")
    def test_handles_gh_create_failure(self, mock_gh_create, tmp_path):
        mock_gh_create.return_value = None  # failure

        client = MagicMock()
        client.query_wiql_with_details.return_value = [_work_item(100)]

        ledger_path = tmp_path / "ledger.json"
        error_path = tmp_path / "errors.json"

        results = initial_sync(
            _config(), client, ledger_path, error_path,
            direction="ado_to_github",
            github_repo="owner/repo",
        )

        assert len(results) == 1
        assert results[0].status == "error"


# ── Unknown direction ─────────────────────────────────────────────────────


class TestUnknownDirection:
    def test_returns_error(self, tmp_path):
        client = MagicMock()
        ledger_path = tmp_path / "ledger.json"
        error_path = tmp_path / "errors.json"

        results = initial_sync(
            _config(), client, ledger_path, error_path,
            direction="invalid",
        )

        assert len(results) == 1
        assert results[0].status == "error"
        assert "Unknown direction" in (results[0].error or "")
