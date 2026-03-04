"""Tests for the ADO sync dashboard emission."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from governance.integrations.ado.dashboard import generate_dashboard_emission


# ── Helpers ────────────────────────────────────────────────────────────────


def _write_ledger(path: Path, mappings: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema_version": "1.0.0",
        "mappings": mappings,
    }, indent=2))


def _write_errors(path: Path, errors: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "schema_version": "1.0.0",
        "errors": errors,
    }, indent=2))


def _make_mapping(
    github_issue: int = 1,
    ado_id: int = 100,
    status: str = "active",
    direction: str = "github_to_ado",
    last_synced: str | None = None,
) -> dict:
    return {
        "github_issue_number": github_issue,
        "github_repo": "owner/repo",
        "ado_work_item_id": ado_id,
        "ado_project": "TestProject",
        "sync_direction": direction,
        "last_synced_at": last_synced or datetime.now(timezone.utc).isoformat(),
        "sync_status": status,
    }


def _make_error(
    error_id: str = "err-1",
    resolved: bool = False,
    dead_letter: bool = False,
    timestamp: str | None = None,
) -> dict:
    err: dict = {
        "error_id": error_id,
        "timestamp": timestamp or datetime.now(timezone.utc).isoformat(),
        "operation": "create",
        "source": "github",
        "error_type": "AdoError",
        "error_message": "failed",
        "retry_count": 0,
        "resolved": resolved,
    }
    if dead_letter:
        err["dead_letter"] = True
    return err


# ── Tests ────────────────────────────────────────────────────────────────


class TestDashboardEmission:
    def test_empty_state(self, tmp_path):
        """No ledger or error files produces zero counts."""
        result = generate_dashboard_emission(
            tmp_path / "ledger.json",
            tmp_path / "errors.json",
        )
        status = result["ado_sync_status"]
        assert status["total_mappings"] == 0
        assert status["active_mappings"] == 0
        assert status["error_mappings"] == 0
        assert status["paused_mappings"] == 0
        assert status["last_github_to_ado_sync"] is None
        assert status["last_ado_to_github_sync"] is None
        assert status["errors_today"] == 0
        assert status["dead_letter_count"] == 0
        assert status["unresolved_errors"] == 0
        assert status["total_errors"] == 0
        assert "generated_at" in status

    def test_mapping_counts(self, tmp_path):
        ledger_path = tmp_path / "ledger.json"
        _write_ledger(ledger_path, [
            _make_mapping(github_issue=1, status="active"),
            _make_mapping(github_issue=2, status="active"),
            _make_mapping(github_issue=3, status="error"),
            _make_mapping(github_issue=4, status="paused"),
        ])

        result = generate_dashboard_emission(
            ledger_path,
            tmp_path / "errors.json",
        )
        status = result["ado_sync_status"]
        assert status["total_mappings"] == 4
        assert status["active_mappings"] == 2
        assert status["error_mappings"] == 1
        assert status["paused_mappings"] == 1

    def test_last_sync_timestamps(self, tmp_path):
        ledger_path = tmp_path / "ledger.json"
        gh_to_ado_ts = "2026-02-27T10:00:00+00:00"
        ado_to_gh_ts = "2026-02-27T08:00:00+00:00"

        _write_ledger(ledger_path, [
            _make_mapping(
                github_issue=1,
                direction="github_to_ado",
                last_synced=gh_to_ado_ts,
            ),
            _make_mapping(
                github_issue=2,
                direction="ado_to_github",
                last_synced=ado_to_gh_ts,
            ),
        ])

        result = generate_dashboard_emission(
            ledger_path,
            tmp_path / "errors.json",
        )
        status = result["ado_sync_status"]
        assert status["last_github_to_ado_sync"] is not None
        assert status["last_ado_to_github_sync"] is not None

    def test_error_metrics(self, tmp_path):
        error_path = tmp_path / "errors.json"
        now_ts = datetime.now(timezone.utc).isoformat()
        old_ts = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()

        _write_errors(error_path, [
            _make_error(error_id="e1", resolved=False, timestamp=now_ts),
            _make_error(error_id="e2", resolved=True, timestamp=now_ts),
            _make_error(error_id="e3", resolved=False, dead_letter=True, timestamp=old_ts),
            _make_error(error_id="e4", resolved=False, timestamp=old_ts),
        ])

        result = generate_dashboard_emission(
            tmp_path / "ledger.json",
            error_path,
        )
        status = result["ado_sync_status"]
        assert status["total_errors"] == 4
        assert status["unresolved_errors"] == 3  # e1, e3, e4
        assert status["dead_letter_count"] == 1  # e3
        assert status["errors_today"] >= 1  # at least e1 and e2

    def test_generated_at_is_recent(self, tmp_path):
        result = generate_dashboard_emission(
            tmp_path / "ledger.json",
            tmp_path / "errors.json",
        )
        generated = datetime.fromisoformat(result["ado_sync_status"]["generated_at"])
        now = datetime.now(timezone.utc)
        assert (now - generated).total_seconds() < 5

    def test_complete_scenario(self, tmp_path):
        """Full scenario with multiple mappings and errors."""
        ledger_path = tmp_path / "ledger.json"
        error_path = tmp_path / "errors.json"

        _write_ledger(ledger_path, [
            _make_mapping(github_issue=i, status="active")
            for i in range(1, 11)
        ] + [
            _make_mapping(github_issue=11, status="error"),
            _make_mapping(github_issue=12, status="paused"),
        ])

        now_ts = datetime.now(timezone.utc).isoformat()
        _write_errors(error_path, [
            _make_error(error_id=f"e{i}", resolved=False, timestamp=now_ts)
            for i in range(3)
        ])

        result = generate_dashboard_emission(ledger_path, error_path)
        status = result["ado_sync_status"]

        assert status["total_mappings"] == 12
        assert status["active_mappings"] == 10
        assert status["error_mappings"] == 1
        assert status["paused_mappings"] == 1
        assert status["unresolved_errors"] == 3
        assert status["total_errors"] == 3

    def test_top_level_key(self, tmp_path):
        """Emission is wrapped in ado_sync_status key."""
        result = generate_dashboard_emission(
            tmp_path / "ledger.json",
            tmp_path / "errors.json",
        )
        assert "ado_sync_status" in result
        assert isinstance(result["ado_sync_status"], dict)
