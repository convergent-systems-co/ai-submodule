"""Tests for the ADO sync health check engine."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from governance.integrations.ado._exceptions import AdoAuthError, AdoError
from governance.integrations.ado._types import FieldDefinition
from governance.integrations.ado.health import (
    HealthCheckResult,
    HealthStatus,
    run_health_checks,
    _check_connection,
    _check_custom_fields,
    _check_error_queue,
    _check_ledger_integrity,
    _check_ledger_recency,
    _check_service_hooks,
)


# ── Fixtures ───────────────────────────────────────────────────────────────


def _config(**overrides) -> dict:
    """Minimal ADO config."""
    base: dict = {
        "organization": "https://dev.azure.com/testorg",
        "project": "TestProject",
        "sync": {"direction": "github_to_ado"},
    }
    base.update(overrides)
    return base


def _mock_client(
    *,
    project_name: str = "TestProject",
    fields: list[FieldDefinition] | None = None,
) -> MagicMock:
    """Build a mock AdoClient with sensible defaults."""
    client = MagicMock()
    client.get_project_properties.return_value = {"name": project_name}
    if fields is None:
        fields = [
            FieldDefinition(
                name="GitHub Issue URL",
                reference_name="Custom.GitHubIssueUrl",
                type="string",
                description="",
                read_only=False,
            ),
            FieldDefinition(
                name="GitHub Repo",
                reference_name="Custom.GitHubRepo",
                type="string",
                description="",
                read_only=False,
            ),
        ]
    client.list_fields.return_value = fields
    return client


def _write_ledger(path: Path, mappings: list[dict]) -> None:
    """Write a ledger file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema_version": "1.0.0",
        "mappings": mappings,
    }, indent=2))


def _write_errors(path: Path, errors: list[dict]) -> None:
    """Write an error log file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema_version": "1.0.0",
        "errors": errors,
    }, indent=2))


# ── Connection check ──────────────────────────────────────────────────────


class TestConnectionCheck:
    def test_pass_on_successful_connection(self):
        client = _mock_client()
        result = _check_connection(client)
        assert result.status == HealthStatus.PASS
        assert "TestProject" in result.details

    def test_warn_when_no_client(self):
        result = _check_connection(None)
        assert result.status == HealthStatus.WARN
        assert "skipped" in result.details

    def test_fail_on_auth_error(self):
        client = MagicMock()
        client.get_project_properties.side_effect = AdoAuthError("401 Unauthorized")
        result = _check_connection(client)
        assert result.status == HealthStatus.FAIL
        assert "Authentication" in result.details

    def test_fail_on_generic_ado_error(self):
        client = MagicMock()
        client.get_project_properties.side_effect = AdoError("Timeout")
        result = _check_connection(client)
        assert result.status == HealthStatus.FAIL
        assert "Connection error" in result.details

    def test_fail_on_unexpected_error(self):
        client = MagicMock()
        client.get_project_properties.side_effect = RuntimeError("boom")
        result = _check_connection(client)
        assert result.status == HealthStatus.FAIL
        assert "Unexpected" in result.details


# ── Custom fields check ──────────────────────────────────────────────────


class TestCustomFieldsCheck:
    def test_pass_when_all_present(self):
        client = _mock_client()
        result = _check_custom_fields(client)
        assert result.status == HealthStatus.PASS

    def test_fail_when_missing_field(self):
        fields = [
            FieldDefinition(
                name="GitHub Repo",
                reference_name="Custom.GitHubRepo",
                type="string",
                description="",
                read_only=False,
            ),
        ]
        client = _mock_client(fields=fields)
        result = _check_custom_fields(client)
        assert result.status == HealthStatus.FAIL
        assert "Custom.GitHubIssueUrl" in result.details

    def test_warn_when_no_client(self):
        result = _check_custom_fields(None)
        assert result.status == HealthStatus.WARN

    def test_fail_on_ado_error(self):
        client = MagicMock()
        client.list_fields.side_effect = AdoError("API Error")
        result = _check_custom_fields(client)
        assert result.status == HealthStatus.FAIL


# ── Ledger integrity ─────────────────────────────────────────────────────


class TestLedgerIntegrity:
    def test_pass_when_no_file(self, tmp_path):
        result = _check_ledger_integrity(tmp_path / "missing.json")
        assert result.status == HealthStatus.PASS

    def test_pass_with_valid_mappings(self, tmp_path):
        ledger_path = tmp_path / "ledger.json"
        _write_ledger(ledger_path, [
            {
                "github_issue_number": 1,
                "github_repo": "owner/repo",
                "ado_work_item_id": 100,
                "ado_project": "Proj",
                "sync_direction": "github_to_ado",
                "last_synced_at": "2026-02-27T10:00:00+00:00",
                "sync_status": "active",
            },
        ])
        result = _check_ledger_integrity(ledger_path)
        assert result.status == HealthStatus.PASS
        assert "1 mapping(s)" in result.details

    def test_fail_on_missing_github_issue_number(self, tmp_path):
        ledger_path = tmp_path / "ledger.json"
        _write_ledger(ledger_path, [
            {
                "github_repo": "owner/repo",
                "ado_work_item_id": 100,
            },
        ])
        result = _check_ledger_integrity(ledger_path)
        assert result.status == HealthStatus.FAIL
        assert "missing github_issue_number" in result.details

    def test_fail_on_missing_ado_work_item_id(self, tmp_path):
        ledger_path = tmp_path / "ledger.json"
        _write_ledger(ledger_path, [
            {
                "github_issue_number": 1,
                "github_repo": "owner/repo",
            },
        ])
        result = _check_ledger_integrity(ledger_path)
        assert result.status == HealthStatus.FAIL
        assert "missing ado_work_item_id" in result.details

    def test_fail_on_duplicate_entries(self, tmp_path):
        ledger_path = tmp_path / "ledger.json"
        _write_ledger(ledger_path, [
            {
                "github_issue_number": 1,
                "github_repo": "owner/repo",
                "ado_work_item_id": 100,
            },
            {
                "github_issue_number": 1,
                "github_repo": "owner/repo",
                "ado_work_item_id": 200,
            },
        ])
        result = _check_ledger_integrity(ledger_path)
        assert result.status == HealthStatus.FAIL
        assert "duplicate" in result.details

    def test_fail_on_malformed_json(self, tmp_path):
        ledger_path = tmp_path / "ledger.json"
        ledger_path.write_text("{invalid json")
        result = _check_ledger_integrity(ledger_path)
        assert result.status == HealthStatus.FAIL
        assert "malformed" in result.details

    def test_pass_on_empty_file(self, tmp_path):
        ledger_path = tmp_path / "ledger.json"
        ledger_path.write_text("")
        result = _check_ledger_integrity(ledger_path)
        assert result.status == HealthStatus.PASS

    def test_pass_on_empty_mappings(self, tmp_path):
        ledger_path = tmp_path / "ledger.json"
        _write_ledger(ledger_path, [])
        result = _check_ledger_integrity(ledger_path)
        assert result.status == HealthStatus.PASS


# ── Ledger recency ───────────────────────────────────────────────────────


class TestLedgerRecency:
    def test_pass_when_no_file(self, tmp_path):
        result = _check_ledger_recency(tmp_path / "missing.json")
        assert result.status == HealthStatus.PASS

    def test_pass_when_recent(self, tmp_path):
        ledger_path = tmp_path / "ledger.json"
        recent = datetime.now(timezone.utc).isoformat()
        _write_ledger(ledger_path, [
            {
                "github_issue_number": 1,
                "github_repo": "owner/repo",
                "ado_work_item_id": 100,
                "last_synced_at": recent,
            },
        ])
        result = _check_ledger_recency(ledger_path)
        assert result.status == HealthStatus.PASS

    def test_warn_when_stale(self, tmp_path):
        ledger_path = tmp_path / "ledger.json"
        old = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
        _write_ledger(ledger_path, [
            {
                "github_issue_number": 1,
                "github_repo": "owner/repo",
                "ado_work_item_id": 100,
                "last_synced_at": old,
            },
        ])
        result = _check_ledger_recency(ledger_path)
        assert result.status == HealthStatus.WARN
        assert "ago" in result.details

    def test_warn_when_no_valid_timestamps(self, tmp_path):
        ledger_path = tmp_path / "ledger.json"
        _write_ledger(ledger_path, [
            {
                "github_issue_number": 1,
                "github_repo": "owner/repo",
                "ado_work_item_id": 100,
            },
        ])
        result = _check_ledger_recency(ledger_path)
        assert result.status == HealthStatus.WARN

    def test_pass_on_empty_mappings(self, tmp_path):
        ledger_path = tmp_path / "ledger.json"
        _write_ledger(ledger_path, [])
        result = _check_ledger_recency(ledger_path)
        assert result.status == HealthStatus.PASS


# ── Error queue ──────────────────────────────────────────────────────────


class TestErrorQueue:
    def test_pass_when_no_file(self, tmp_path):
        result = _check_error_queue(tmp_path / "missing.json")
        assert result.status == HealthStatus.PASS

    def test_pass_when_all_resolved(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            {
                "error_id": "abc-123",
                "resolved": True,
                "timestamp": "2026-02-27T10:00:00+00:00",
                "operation": "create",
                "source": "github",
                "error_type": "AdoError",
                "error_message": "test",
            },
        ])
        result = _check_error_queue(error_path)
        assert result.status == HealthStatus.PASS

    def test_warn_when_unresolved(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            {
                "error_id": "abc-123",
                "resolved": False,
                "timestamp": "2026-02-27T10:00:00+00:00",
                "operation": "create",
                "source": "github",
                "error_type": "AdoError",
                "error_message": "test",
            },
        ])
        result = _check_error_queue(error_path)
        assert result.status == HealthStatus.WARN
        assert "1 unresolved" in result.details

    def test_warn_with_dead_letter_count(self, tmp_path):
        error_path = tmp_path / "errors.json"
        _write_errors(error_path, [
            {
                "error_id": "abc-123",
                "resolved": False,
                "dead_letter": True,
                "timestamp": "2026-02-27T10:00:00+00:00",
                "operation": "create",
                "source": "github",
                "error_type": "AdoError",
                "error_message": "test",
            },
        ])
        result = _check_error_queue(error_path)
        assert result.status == HealthStatus.WARN
        assert "dead-lettered" in result.details

    def test_fail_on_malformed_json(self, tmp_path):
        error_path = tmp_path / "errors.json"
        error_path.write_text("not json")
        result = _check_error_queue(error_path)
        assert result.status == HealthStatus.FAIL


# ── Service hooks ────────────────────────────────────────────────────────


class TestServiceHooks:
    def test_pass_for_github_to_ado(self):
        result = _check_service_hooks(_config())
        assert result.status == HealthStatus.PASS

    def test_warn_for_ado_to_github(self):
        result = _check_service_hooks(
            _config(sync={"direction": "ado_to_github"})
        )
        assert result.status == HealthStatus.WARN
        assert "service hook" in result.details.lower()

    def test_warn_for_bidirectional(self):
        result = _check_service_hooks(
            _config(sync={"direction": "bidirectional"})
        )
        assert result.status == HealthStatus.WARN


# ── Integration: run_health_checks ───────────────────────────────────────


class TestRunHealthChecks:
    def test_all_pass(self, tmp_path):
        """All checks pass with valid client, no ledger, no errors."""
        client = _mock_client()
        results = run_health_checks(
            config=_config(),
            client=client,
            ledger_path=tmp_path / "ledger.json",
            error_log_path=tmp_path / "errors.json",
        )
        assert len(results) == 6
        assert all(r.status in (HealthStatus.PASS,) for r in results)

    def test_returns_all_checks_even_on_failure(self, tmp_path):
        """Even when connection fails, all subsequent checks still run."""
        client = MagicMock()
        client.get_project_properties.side_effect = AdoAuthError("401")
        client.list_fields.side_effect = AdoError("cannot list")

        results = run_health_checks(
            config=_config(),
            client=client,
            ledger_path=tmp_path / "ledger.json",
            error_log_path=tmp_path / "errors.json",
        )
        assert len(results) == 6
        assert results[0].status == HealthStatus.FAIL  # connection
        assert results[1].status == HealthStatus.FAIL  # custom fields

    def test_without_client(self, tmp_path):
        """When no client is provided, connection/field checks are WARN."""
        results = run_health_checks(
            config=_config(),
            client=None,
            ledger_path=tmp_path / "ledger.json",
            error_log_path=tmp_path / "errors.json",
        )
        assert results[0].status == HealthStatus.WARN  # connection
        assert results[1].status == HealthStatus.WARN  # custom fields

    def test_result_is_frozen_dataclass(self, tmp_path):
        results = run_health_checks(
            config=_config(),
            client=None,
            ledger_path=tmp_path / "ledger.json",
            error_log_path=tmp_path / "errors.json",
        )
        result = results[0]
        with pytest.raises(AttributeError):
            result.name = "changed"  # type: ignore[misc]
