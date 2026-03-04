"""Tests for the ADO sync retry processor."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from governance.integrations.ado._exceptions import AdoError
from governance.integrations.ado._types import WorkItem
from governance.integrations.ado.retry import RetryResult, retry_failed


# ── Fixtures / helpers ─────────────────────────────────────────────────────


def _config(**overrides) -> dict:
    """Minimal ADO config."""
    base: dict = {
        "organization": "https://dev.azure.com/testorg",
        "project": "TestProject",
        "type_mapping": {"default": "User Story"},
    }
    base.update(overrides)
    return base


def _work_item(work_item_id: int = 200) -> WorkItem:
    return WorkItem(
        id=work_item_id,
        rev=1,
        url=f"https://dev.azure.com/testorg/TestProject/_apis/wit/workitems/{work_item_id}",
        fields={"System.Title": "Test", "System.State": "New"},
    )


def _write_errors(path: Path, errors: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema_version": "1.0.0",
        "errors": errors,
    }, indent=2))


def _read_errors(path: Path) -> list[dict]:
    with open(path) as f:
        return json.load(f).get("errors", [])


def _write_ledger(path: Path, mappings: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema_version": "1.0.0",
        "mappings": mappings,
    }, indent=2))


def _read_ledger(path: Path) -> list[dict]:
    with open(path) as f:
        return json.load(f).get("mappings", [])


def _make_error(
    error_id: str = "err-1",
    operation: str = "create",
    github_issue: int = 42,
    ado_id: int | None = None,
    retry_count: int = 0,
    resolved: bool = False,
    dead_letter: bool = False,
) -> dict:
    err: dict = {
        "error_id": error_id,
        "timestamp": "2026-02-27T10:00:00+00:00",
        "operation": operation,
        "source": "github",
        "github_issue_number": github_issue,
        "ado_work_item_id": ado_id,
        "error_type": "AdoError",
        "error_message": "Something failed",
        "retry_count": retry_count,
        "resolved": resolved,
    }
    if dead_letter:
        err["dead_letter"] = True
    return err


# ── Empty queue ──────────────────────────────────────────────────────────


class TestEmptyQueue:
    def test_no_error_file(self, tmp_path):
        results = retry_failed(
            config=_config(),
            client=MagicMock(),
            ledger_path=tmp_path / "ledger.json",
            error_log_path=tmp_path / "errors.json",
        )
        assert results == []

    def test_all_resolved(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            _make_error(resolved=True),
        ])
        results = retry_failed(
            config=_config(),
            client=MagicMock(),
            ledger_path=tmp_path / "ledger.json",
            error_log_path=error_path,
        )
        assert results == []

    def test_all_dead_lettered(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            _make_error(dead_letter=True),
        ])
        results = retry_failed(
            config=_config(),
            client=MagicMock(),
            ledger_path=tmp_path / "ledger.json",
            error_log_path=error_path,
        )
        assert results == []


# ── Dry run ──────────────────────────────────────────────────────────────


class TestDryRun:
    def test_dry_run_lists_without_executing(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            _make_error(error_id="e1"),
            _make_error(error_id="e2"),
        ])
        client = MagicMock()

        results = retry_failed(
            config=_config(),
            client=client,
            ledger_path=tmp_path / "ledger.json",
            error_log_path=error_path,
            dry_run=True,
        )
        assert len(results) == 2
        assert all(r.status == "skipped" for r in results)
        assert "Would retry" in results[0].message
        client.create_work_item.assert_not_called()

    def test_dry_run_does_not_modify_error_log(self, tmp_path):
        error_path = tmp_path / "errors.json"
        original_error = _make_error(error_id="e1")
        _write_errors(error_path, [original_error])
        original_text = error_path.read_text()

        retry_failed(
            config=_config(),
            client=MagicMock(),
            ledger_path=tmp_path / "ledger.json",
            error_log_path=error_path,
            dry_run=True,
        )
        # File should be unchanged
        assert error_path.read_text() == original_text

    def test_dry_run_dead_letters_without_executing(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            _make_error(error_id="e1", retry_count=5),
        ])
        results = retry_failed(
            config=_config(),
            client=MagicMock(),
            ledger_path=tmp_path / "ledger.json",
            error_log_path=error_path,
            dry_run=True,
            max_retries=3,
        )
        assert len(results) == 1
        assert results[0].status == "dead_letter"


# ── Successful retry ─────────────────────────────────────────────────────


class TestRetrySuccess:
    def test_create_retry_succeeds(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            _make_error(error_id="e1", operation="create", github_issue=42),
        ])

        client = MagicMock()
        client.create_work_item.return_value = _work_item(200)

        results = retry_failed(
            config=_config(),
            client=client,
            ledger_path=tmp_path / "ledger.json",
            error_log_path=error_path,
        )
        assert len(results) == 1
        assert results[0].status == "resolved"
        assert "200" in results[0].message

        # Error should be marked resolved
        errors = _read_errors(error_path)
        assert errors[0]["resolved"] is True

    def test_update_retry_succeeds(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            _make_error(error_id="e1", operation="update", ado_id=100),
        ])

        client = MagicMock()
        client.get_work_item.return_value = _work_item(100)

        results = retry_failed(
            config=_config(),
            client=client,
            ledger_path=tmp_path / "ledger.json",
            error_log_path=error_path,
        )
        assert len(results) == 1
        assert results[0].status == "resolved"

        errors = _read_errors(error_path)
        assert errors[0]["resolved"] is True

    def test_create_retry_updates_ledger(self, tmp_path):
        error_path = tmp_path / "errors.json"
        ledger_path = tmp_path / "ledger.json"
        _write_errors(error_path, [
            _make_error(error_id="e1", operation="create", github_issue=42),
        ])

        client = MagicMock()
        client.create_work_item.return_value = _work_item(200)

        retry_failed(
            config=_config(),
            client=client,
            ledger_path=ledger_path,
            error_log_path=error_path,
        )

        mappings = _read_ledger(ledger_path)
        assert len(mappings) == 1
        assert mappings[0]["github_issue_number"] == 42
        assert mappings[0]["ado_work_item_id"] == 200


# ── Max retries / dead letter ────────────────────────────────────────────


class TestMaxRetries:
    def test_dead_letter_when_max_exceeded(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            _make_error(error_id="e1", retry_count=3),
        ])

        results = retry_failed(
            config=_config(),
            client=MagicMock(),
            ledger_path=tmp_path / "ledger.json",
            error_log_path=error_path,
            max_retries=3,
        )
        assert len(results) == 1
        assert results[0].status == "dead_letter"

        errors = _read_errors(error_path)
        assert errors[0].get("dead_letter") is True

    def test_dead_letter_on_retry_failure_at_max(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            _make_error(error_id="e1", operation="create", github_issue=42, retry_count=2),
        ])

        client = MagicMock()
        client.create_work_item.side_effect = AdoError("Still failing")

        results = retry_failed(
            config=_config(),
            client=client,
            ledger_path=tmp_path / "ledger.json",
            error_log_path=error_path,
            max_retries=3,
        )
        assert len(results) == 1
        assert results[0].status == "dead_letter"

    def test_retry_failure_increments_count(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            _make_error(error_id="e1", operation="create", github_issue=42, retry_count=0),
        ])

        client = MagicMock()
        client.create_work_item.side_effect = AdoError("Transient")

        results = retry_failed(
            config=_config(),
            client=client,
            ledger_path=tmp_path / "ledger.json",
            error_log_path=error_path,
            max_retries=5,
        )
        assert len(results) == 1
        assert results[0].status == "retried"

        errors = _read_errors(error_path)
        assert errors[0]["retry_count"] == 1


# ── Unsupported operations ───────────────────────────────────────────────


class TestSkippedOperations:
    def test_unsupported_operation_skipped(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            _make_error(error_id="e1", operation="delete"),
        ])

        results = retry_failed(
            config=_config(),
            client=MagicMock(),
            ledger_path=tmp_path / "ledger.json",
            error_log_path=error_path,
        )
        assert len(results) == 1
        assert results[0].status == "skipped"


# ── Mixed scenarios ──────────────────────────────────────────────────────


class TestMixedScenarios:
    def test_mix_of_resolved_unresolved_dead_letter(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            _make_error(error_id="resolved", resolved=True),
            _make_error(error_id="dead", dead_letter=True),
            _make_error(error_id="retryable", operation="create", github_issue=10),
        ])

        client = MagicMock()
        client.create_work_item.return_value = _work_item(300)

        results = retry_failed(
            config=_config(),
            client=client,
            ledger_path=tmp_path / "ledger.json",
            error_log_path=error_path,
        )
        # Only the retryable one should appear
        assert len(results) == 1
        assert results[0].error_id == "retryable"
        assert results[0].status == "resolved"

    def test_result_is_frozen_dataclass(self, tmp_path):
        result = RetryResult(error_id="e1", status="resolved", message="ok")
        with pytest.raises(AttributeError):
            result.error_id = "changed"  # type: ignore[misc]
