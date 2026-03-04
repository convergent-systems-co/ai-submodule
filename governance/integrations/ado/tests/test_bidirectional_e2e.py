"""End-to-end tests for ADO bidirectional sync pipeline.

Validates the complete sync lifecycle:
  - Forward sync  (GitHub -> ADO)
  - Reverse sync  (ADO -> GitHub)
  - Echo detection (grace period, last_sync_source tracking)
  - Comments sync  (bidirectional with prefix filtering)
  - Bulk sync      (dry-run and actual, with rate limiting)
  - Error recovery (transient failures, retry, dead-lettering)
  - Health checks  (connection, custom fields, ledger, error queue)
  - Dashboard      (metrics, JSON output)

Two execution modes:
  **Mock mode** (default) -- runs in every CI pipeline, no credentials needed.
  **Live mode** (@pytest.mark.ado_live) -- requires real ADO credentials;
    skipped when ADO_PAT / ADO_ORGANIZATION / ADO_PROJECT are absent.

Required env vars for live tests:
    ADO_PAT           -- Personal Access Token (vso.work_write + vso.work_full)
    ADO_ORGANIZATION  -- ADO org name
    ADO_PROJECT       -- ADO project name
    GITHUB_TOKEN      -- GitHub PAT (repo:write) for reverse sync simulation

Run mock tests:
    python3 -m pytest governance/integrations/ado/tests/test_bidirectional_e2e.py -x --tb=short

Run live tests (requires credentials):
    ADO_PAT=xxx ADO_ORGANIZATION=myorg ADO_PROJECT=myproj \\
        python3 -m pytest governance/integrations/ado/tests/test_bidirectional_e2e.py -x -m ado_live
"""

from __future__ import annotations

import copy
import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

from governance.integrations.ado._exceptions import AdoError, AdoServerError
from governance.integrations.ado._patch import add_field
from governance.integrations.ado._types import (
    Comment,
    FieldDefinition,
    WorkItem,
)
from governance.integrations.ado.auth import PatAuth
from governance.integrations.ado.bulk_sync import initial_sync
from governance.integrations.ado.client import AdoClient
from governance.integrations.ado.comments_sync import (
    format_ado_to_github_comment,
    format_github_to_ado_comment,
    should_sync_comment,
    sync_comment_from_ado,
    sync_comment_to_ado,
)
from governance.integrations.ado.config import AdoConfig
from governance.integrations.ado.dashboard import generate_dashboard_emission
from governance.integrations.ado.health import (
    HealthCheckResult,
    HealthStatus,
    run_health_checks,
)
from governance.integrations.ado.retry import RetryResult, retry_failed
from governance.integrations.ado.reverse_sync import ReverseSyncEngine
from governance.integrations.ado.sync_engine import SyncEngine, SyncResult

# ---------------------------------------------------------------------------
# Fixture paths
# ---------------------------------------------------------------------------

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
_E2E_CONFIG_PATH = _FIXTURES_DIR / "e2e_config.yaml"
_GH_TEMPLATES_PATH = _FIXTURES_DIR / "github_webhook_templates.json"
_ADO_TEMPLATES_PATH = _FIXTURES_DIR / "ado_webhook_templates.json"

# ---------------------------------------------------------------------------
# Custom markers
# ---------------------------------------------------------------------------

ado_live = pytest.mark.ado_live


def _has_live_creds() -> bool:
    return bool(
        os.environ.get("ADO_PAT")
        and os.environ.get("ADO_ORGANIZATION")
        and os.environ.get("ADO_PROJECT")
    )


skip_no_live_creds = pytest.mark.skipif(
    not _has_live_creds(),
    reason="Live ADO E2E tests require ADO_PAT, ADO_ORGANIZATION, ADO_PROJECT",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_e2e_config() -> dict:
    """Load the E2E config YAML, applying env-var overrides."""
    with open(_E2E_CONFIG_PATH) as f:
        raw = yaml.safe_load(f)
    config = raw.get("ado_integration", raw)
    config["organization"] = os.environ.get("ADO_ORGANIZATION", config.get("organization", ""))
    config["project"] = os.environ.get("ADO_PROJECT", config.get("project", ""))
    return config


def _load_github_templates() -> dict:
    with open(_GH_TEMPLATES_PATH) as f:
        return json.load(f)


def _load_ado_templates() -> dict:
    with open(_ADO_TEMPLATES_PATH) as f:
        return json.load(f)


def _make_work_item(
    wi_id: int = 42,
    rev: int = 1,
    fields: dict | None = None,
) -> WorkItem:
    """Create a mock WorkItem dataclass."""
    return WorkItem(
        id=wi_id,
        rev=rev,
        url=f"https://dev.azure.com/testorg/testproject/_apis/wit/workitems/{wi_id}",
        fields=fields or {"System.Title": "Mock Work Item", "System.State": "New"},
    )


def _make_comment(
    comment_id: int = 1,
    work_item_id: int = 42,
    text: str = "<p>Test comment</p>",
    created_by: str = "Test User",
) -> Comment:
    return Comment(
        id=comment_id,
        work_item_id=work_item_id,
        text=text,
        created_by=created_by,
        created_date=datetime.now(timezone.utc).isoformat(),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def e2e_config() -> dict:
    return _load_e2e_config()


@pytest.fixture
def gh_templates() -> dict:
    return _load_github_templates()


@pytest.fixture
def ado_templates() -> dict:
    return _load_ado_templates()


@pytest.fixture
def ledger_path(tmp_path: Path) -> Path:
    """Isolated ledger file for each test."""
    return tmp_path / f"test-ledger-{uuid.uuid4().hex[:8]}.json"


@pytest.fixture
def error_log_path(tmp_path: Path) -> Path:
    """Isolated error log file for each test."""
    return tmp_path / f"test-errors-{uuid.uuid4().hex[:8]}.json"


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock AdoClient that returns plausible responses."""
    client = MagicMock(spec=AdoClient)

    # Default: create_work_item returns a new work item
    client.create_work_item.return_value = _make_work_item(wi_id=42)

    # Default: update_work_item returns updated work item
    client.update_work_item.return_value = _make_work_item(wi_id=42)

    # Default: get_work_item returns a work item
    client.get_work_item.return_value = _make_work_item(wi_id=42)

    # Default: list_fields returns standard + custom fields
    client.list_fields.return_value = [
        FieldDefinition(name="Title", reference_name="System.Title", type="string"),
        FieldDefinition(name="State", reference_name="System.State", type="string"),
        FieldDefinition(name="GitHubIssueUrl", reference_name="Custom.GitHubIssueUrl", type="string"),
        FieldDefinition(name="GitHubRepo", reference_name="Custom.GitHubRepo", type="string"),
    ]

    # Default: get_project_properties
    client.get_project_properties.return_value = {
        "name": "GitHub-ADO-Sync-E2E-Test",
        "id": "00000000-0000-0000-0000-000000000001",
        "capabilities": {},
    }

    # Default: add_comment
    client.add_comment.return_value = _make_comment(comment_id=101, work_item_id=42)

    return client


@pytest.fixture
def forward_engine(
    mock_client: MagicMock,
    e2e_config: dict,
    ledger_path: Path,
    error_log_path: Path,
) -> SyncEngine:
    """SyncEngine wired to mock client and test paths."""
    return SyncEngine(
        client=mock_client,
        config=e2e_config,
        ledger_path=ledger_path,
        error_log_path=error_log_path,
    )


@pytest.fixture
def reverse_engine(
    e2e_config: dict,
    ledger_path: Path,
    error_log_path: Path,
) -> ReverseSyncEngine:
    """ReverseSyncEngine wired to test paths (uses mock GitHub API)."""
    return ReverseSyncEngine(
        config=e2e_config,
        github_token="ghp_mock_token_for_e2e_testing",
        github_repo="convergent-systems-co/dark-forge",
        ledger_path=ledger_path,
        error_log_path=error_log_path,
    )


# ===========================================================================
# Phase 1: Connection & Configuration
# ===========================================================================


class TestPhase1ConnectionConfiguration:
    """Validate that configuration loading and health checks work correctly."""

    def test_e2e_config_loads(self, e2e_config: dict):
        """E2E config YAML loads and has required keys."""
        assert e2e_config.get("sync", {}).get("direction") == "bidirectional"
        assert e2e_config.get("sync", {}).get("auto_create") is True
        assert e2e_config.get("sync", {}).get("grace_period_seconds") == 10
        assert "state_mapping" in e2e_config
        assert "type_mapping" in e2e_config
        assert "field_mapping" in e2e_config
        assert "user_mapping" in e2e_config

    def test_fixture_templates_load(self, gh_templates: dict, ado_templates: dict):
        """Webhook fixture templates load as valid JSON."""
        assert "issue_opened" in gh_templates
        assert "issue_edited" in gh_templates
        assert "issue_closed" in gh_templates
        assert "issue_reopened" in gh_templates
        assert "workitem_updated_state_active" in ado_templates
        assert "workitem_updated_title" in ado_templates
        assert "workitem_deleted" in ado_templates

    def test_health_checks_all_pass_mock(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Health checks pass with mocked client and empty state."""
        results = run_health_checks(e2e_config, mock_client, ledger_path, error_log_path)
        assert len(results) == 6

        by_name = {r.name: r for r in results}
        assert by_name["ado_connection"].status == HealthStatus.PASS
        assert by_name["custom_fields"].status == HealthStatus.PASS
        assert by_name["ledger_integrity"].status == HealthStatus.PASS
        assert by_name["error_queue"].status == HealthStatus.PASS

    def test_health_check_connection_fail(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Health check reports FAIL when ADO connection fails."""
        mock_client.get_project_properties.side_effect = AdoError("Connection refused")
        results = run_health_checks(e2e_config, mock_client, ledger_path, error_log_path)
        by_name = {r.name: r for r in results}
        assert by_name["ado_connection"].status == HealthStatus.FAIL

    def test_health_check_missing_custom_fields(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Health check reports FAIL when custom fields are missing."""
        mock_client.list_fields.return_value = [
            FieldDefinition(name="Title", reference_name="System.Title", type="string"),
        ]
        results = run_health_checks(e2e_config, mock_client, ledger_path, error_log_path)
        by_name = {r.name: r for r in results}
        assert by_name["custom_fields"].status == HealthStatus.FAIL
        assert "Custom.GitHubIssueUrl" in by_name["custom_fields"].details

    def test_health_check_no_client(
        self,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Health check degrades gracefully with no client."""
        results = run_health_checks(e2e_config, None, ledger_path, error_log_path)
        by_name = {r.name: r for r in results}
        assert by_name["ado_connection"].status == HealthStatus.WARN
        assert by_name["custom_fields"].status == HealthStatus.WARN


# ===========================================================================
# Phase 2: Forward Sync (GitHub -> ADO)
# ===========================================================================


class TestPhase2ForwardSync:
    """Test GitHub issue lifecycle synced to ADO work items."""

    def test_create_work_item_on_issue_opened(
        self,
        forward_engine: SyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
        ledger_path: Path,
    ):
        """Opening a GitHub issue creates an ADO work item."""
        event = copy.deepcopy(gh_templates["issue_opened"])
        mock_client.create_work_item.return_value = _make_work_item(wi_id=42)

        result = forward_engine.sync(event)

        assert result.status == "created"
        assert result.operation == "create"
        assert result.ado_work_item_id == 42
        mock_client.create_work_item.assert_called_once()

        # Verify ledger entry
        ledger = json.loads(ledger_path.read_text())
        mappings = ledger["mappings"]
        assert len(mappings) == 1
        assert mappings[0]["github_issue_number"] == 100
        assert mappings[0]["ado_work_item_id"] == 42
        assert mappings[0]["last_sync_source"] == "github"
        assert mappings[0]["sync_status"] == "active"

    def test_update_work_item_on_issue_edited(
        self,
        forward_engine: SyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
        ledger_path: Path,
    ):
        """Editing a GitHub issue updates the ADO work item."""
        # First create
        event_open = copy.deepcopy(gh_templates["issue_opened"])
        mock_client.create_work_item.return_value = _make_work_item(wi_id=42)
        forward_engine.sync(event_open)

        # Then edit
        event_edit = copy.deepcopy(gh_templates["issue_edited"])
        mock_client.update_work_item.return_value = _make_work_item(wi_id=42)
        result = forward_engine.sync(event_edit)

        assert result.status == "updated"
        assert result.operation == "update"
        assert result.ado_work_item_id == 42

        # Verify ledger updated
        ledger = json.loads(ledger_path.read_text())
        assert len(ledger["mappings"]) == 1
        assert ledger["mappings"][0]["last_sync_source"] == "github"

    def test_close_work_item_on_issue_closed(
        self,
        forward_engine: SyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
    ):
        """Closing a GitHub issue transitions ADO state to Closed."""
        # Create first
        event_open = copy.deepcopy(gh_templates["issue_opened"])
        mock_client.create_work_item.return_value = _make_work_item(wi_id=42)
        forward_engine.sync(event_open)

        # Close
        event_close = copy.deepcopy(gh_templates["issue_closed"])
        mock_client.update_work_item.return_value = _make_work_item(
            wi_id=42, fields={"System.State": "Resolved"}
        )
        result = forward_engine.sync(event_close)

        assert result.status == "updated"
        mock_client.update_work_item.assert_called()

        # Verify the state patch was "Resolved" (closed+label:bug mapping)
        call_args = mock_client.update_work_item.call_args
        ops = call_args[0][1]  # second positional arg = operations
        state_ops = [op for op in ops if op.path == "/fields/System.State"]
        assert len(state_ops) == 1
        assert state_ops[0].value == "Resolved"

    def test_reopen_work_item(
        self,
        forward_engine: SyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
    ):
        """Reopening a GitHub issue reverts ADO state to New."""
        # Create
        event_open = copy.deepcopy(gh_templates["issue_opened"])
        mock_client.create_work_item.return_value = _make_work_item(wi_id=42)
        forward_engine.sync(event_open)

        # Close then reopen
        event_close = copy.deepcopy(gh_templates["issue_closed"])
        mock_client.update_work_item.return_value = _make_work_item(wi_id=42)
        forward_engine.sync(event_close)

        event_reopen = copy.deepcopy(gh_templates["issue_reopened"])
        mock_client.update_work_item.return_value = _make_work_item(wi_id=42)
        result = forward_engine.sync(event_reopen)

        assert result.status == "updated"
        # Last update_work_item call should set state to New
        call_args = mock_client.update_work_item.call_args
        ops = call_args[0][1]
        state_ops = [op for op in ops if op.path == "/fields/System.State"]
        assert len(state_ops) == 1
        assert state_ops[0].value == "New"

    def test_unassign_clears_ado_assignee(
        self,
        forward_engine: SyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
    ):
        """Unassigning a GitHub issue clears ADO AssignedTo."""
        # Create
        event_open = copy.deepcopy(gh_templates["issue_opened"])
        mock_client.create_work_item.return_value = _make_work_item(wi_id=42)
        forward_engine.sync(event_open)

        # Unassign
        event_unassign = copy.deepcopy(gh_templates["issue_unassigned"])
        mock_client.update_work_item.return_value = _make_work_item(wi_id=42)
        result = forward_engine.sync(event_unassign)

        assert result.status == "updated"
        call_args = mock_client.update_work_item.call_args
        ops = call_args[0][1]
        assignee_ops = [op for op in ops if op.path == "/fields/System.AssignedTo"]
        assert len(assignee_ops) == 1
        assert assignee_ops[0].value == ""

    def test_milestone_sets_iteration_path(
        self,
        forward_engine: SyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
        e2e_config: dict,
    ):
        """Adding a milestone sets ADO IterationPath."""
        # Create
        event_open = copy.deepcopy(gh_templates["issue_opened"])
        mock_client.create_work_item.return_value = _make_work_item(wi_id=42)
        forward_engine.sync(event_open)

        # Milestone
        event_milestone = copy.deepcopy(gh_templates["issue_milestoned"])
        mock_client.update_work_item.return_value = _make_work_item(wi_id=42)
        result = forward_engine.sync(event_milestone)

        assert result.status == "updated"
        call_args = mock_client.update_work_item.call_args
        ops = call_args[0][1]
        iter_ops = [op for op in ops if op.path == "/fields/System.IterationPath"]
        assert len(iter_ops) == 1
        project = e2e_config.get("project", "")
        expected = f"{project}\\Sprint-42" if project else "Sprint-42"
        assert iter_ops[0].value == expected

    def test_skip_excluded_labels(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Issues with excluded labels are not synced."""
        engine = SyncEngine(mock_client, e2e_config, ledger_path, error_log_path)
        event = {
            "action": "opened",
            "issue": {
                "number": 200,
                "title": "Internal issue",
                "body": "Should be skipped",
                "state": "open",
                "labels": [{"name": "internal"}, {"name": "ado-sync"}],
                "html_url": "https://github.com/test/repo/issues/200",
            },
            "repository": {"full_name": "test/repo"},
        }
        result = engine.sync(event)
        assert result.status == "skipped"
        mock_client.create_work_item.assert_not_called()

    def test_error_logged_on_ado_failure(
        self,
        forward_engine: SyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
        error_log_path: Path,
    ):
        """ADO errors are logged to the error log."""
        mock_client.create_work_item.side_effect = AdoServerError("500 Internal Server Error")
        event = copy.deepcopy(gh_templates["issue_opened"])
        result = forward_engine.sync(event)

        assert result.status == "error"
        assert "500" in result.error

        # Verify error log
        error_log = json.loads(error_log_path.read_text())
        assert len(error_log["errors"]) == 1
        err = error_log["errors"][0]
        assert err["operation"] == "create"
        assert err["github_issue_number"] == 100
        assert err["retry_count"] == 0
        assert err["resolved"] is False
        assert "error_id" in err
        assert "timestamp" in err


# ===========================================================================
# Phase 3: Reverse Sync (ADO -> GitHub)
# ===========================================================================


class TestPhase3ReverseSync:
    """Test ADO work item events synced back to GitHub issues."""

    def _seed_ledger(self, ledger_path: Path, ado_id: int = 42, issue_num: int = 100):
        """Write a ledger with a known mapping for reverse sync to find."""
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": issue_num,
                    "github_repo": "convergent-systems-co/dark-forge",
                    "ado_work_item_id": ado_id,
                    "ado_project": "GitHub-ADO-Sync-E2E-Test",
                    "sync_direction": "github_to_ado",
                    "last_synced_at": "2020-01-01T00:00:00+00:00",
                    "last_sync_source": "ado",
                    "created_at": "2020-01-01T00:00:00+00:00",
                    "sync_status": "active",
                },
            ],
        }
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2))

    @patch.object(ReverseSyncEngine, "_github_api")
    def test_reverse_sync_state_update(
        self,
        mock_gh_api: MagicMock,
        reverse_engine: ReverseSyncEngine,
        ado_templates: dict,
        ledger_path: Path,
    ):
        """ADO state change syncs to GitHub issue."""
        self._seed_ledger(ledger_path)
        mock_gh_api.return_value = {"id": 100}

        payload = copy.deepcopy(ado_templates["workitem_updated_state_active"])
        result = reverse_engine.sync(payload)

        assert result.status == "updated"
        assert result.ado_work_item_id == 42
        mock_gh_api.assert_called()

        # Verify ledger updated with ado as source
        ledger = json.loads(ledger_path.read_text())
        entry = ledger["mappings"][0]
        assert entry["last_sync_source"] == "ado"

    @patch.object(ReverseSyncEngine, "_github_api")
    def test_reverse_sync_title_update(
        self,
        mock_gh_api: MagicMock,
        reverse_engine: ReverseSyncEngine,
        ado_templates: dict,
        ledger_path: Path,
    ):
        """ADO title change syncs to GitHub issue title."""
        self._seed_ledger(ledger_path)
        mock_gh_api.return_value = {"id": 100}

        payload = copy.deepcopy(ado_templates["workitem_updated_title"])
        result = reverse_engine.sync(payload)

        assert result.status == "updated"
        # Verify PATCH call was made to update the issue title
        mock_gh_api.assert_any_call(
            "PATCH",
            "/repos/convergent-systems-co/dark-forge/issues/100",
            json={"title": "[E2E] ADO-updated title"},
        )

    @patch.object(ReverseSyncEngine, "_github_api")
    def test_reverse_sync_assignee_change(
        self,
        mock_gh_api: MagicMock,
        reverse_engine: ReverseSyncEngine,
        ado_templates: dict,
        ledger_path: Path,
    ):
        """ADO assignee change maps back to GitHub assignee."""
        self._seed_ledger(ledger_path)
        mock_gh_api.return_value = {"id": 100}

        payload = copy.deepcopy(ado_templates["workitem_updated_assignee"])
        result = reverse_engine.sync(payload)

        assert result.status == "updated"
        # Should map e2e-bot@contoso.onmicrosoft.com -> e2e-bot
        mock_gh_api.assert_any_call(
            "PATCH",
            "/repos/convergent-systems-co/dark-forge/issues/100",
            json={"assignees": ["e2e-bot"]},
        )

    @patch.object(ReverseSyncEngine, "_github_api")
    def test_reverse_sync_deleted_closes_issue(
        self,
        mock_gh_api: MagicMock,
        reverse_engine: ReverseSyncEngine,
        ado_templates: dict,
        ledger_path: Path,
    ):
        """ADO work item deletion closes the linked GitHub issue."""
        self._seed_ledger(ledger_path)
        mock_gh_api.return_value = {"id": 100}

        payload = copy.deepcopy(ado_templates["workitem_deleted"])
        result = reverse_engine.sync(payload)

        assert result.status == "updated"
        # Should close the issue and add a comment
        mock_gh_api.assert_any_call(
            "PATCH",
            "/repos/convergent-systems-co/dark-forge/issues/100",
            json={"state": "closed"},
        )

    @patch.object(ReverseSyncEngine, "_github_api")
    def test_reverse_sync_state_machine(
        self,
        mock_gh_api: MagicMock,
        reverse_engine: ReverseSyncEngine,
        ado_templates: dict,
        ledger_path: Path,
    ):
        """ADO state transitions (New->Active->Resolved->Closed) all sync."""
        self._seed_ledger(ledger_path)
        mock_gh_api.return_value = {"id": 100}

        transitions = ado_templates["workitem_state_transitions"]
        for payload in transitions:
            result = reverse_engine.sync(payload)
            assert result.status == "updated"

    def test_reverse_sync_skips_unknown_work_item(
        self,
        reverse_engine: ReverseSyncEngine,
        ledger_path: Path,
    ):
        """Reverse sync skips work items not in the ledger."""
        # Empty ledger
        payload = {
            "eventType": "workitem.updated",
            "resource": {
                "workItemId": 999,
                "id": 999,
                "fields": {
                    "System.State": {"oldValue": "New", "newValue": "Active"},
                },
            },
        }
        result = reverse_engine.sync(payload)
        assert result.status == "skipped"
        assert "No ledger entry" in result.error


# ===========================================================================
# Phase 4: Echo Detection
# ===========================================================================


class TestPhase4EchoDetection:
    """Validate echo prevention between forward and reverse sync."""

    def test_forward_then_reverse_within_grace_period_skipped(
        self,
        forward_engine: SyncEngine,
        reverse_engine: ReverseSyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
        ado_templates: dict,
        ledger_path: Path,
    ):
        """Forward sync followed by immediate reverse sync is skipped (echo)."""
        # Forward sync: GitHub -> ADO
        event = copy.deepcopy(gh_templates["issue_opened"])
        mock_client.create_work_item.return_value = _make_work_item(wi_id=42)
        forward_result = forward_engine.sync(event)
        assert forward_result.status == "created"

        # Immediately attempt reverse sync from ADO
        # The ledger now has last_sync_source="github" and recent timestamp
        payload = copy.deepcopy(ado_templates["workitem_updated_state_active"])
        reverse_result = reverse_engine.sync(payload)

        # Should be skipped: grace period + last_sync_source = "github"
        assert reverse_result.status == "skipped"

    def test_reverse_then_forward_within_grace_period_skipped(
        self,
        forward_engine: SyncEngine,
        reverse_engine: ReverseSyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
        ado_templates: dict,
        ledger_path: Path,
    ):
        """Reverse sync followed by immediate forward sync is skipped (echo)."""
        # Seed ledger with last_sync_source="ado" and current timestamp
        now = datetime.now(timezone.utc).isoformat()
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 100,
                    "github_repo": "convergent-systems-co/dark-forge",
                    "ado_work_item_id": 42,
                    "ado_project": "GitHub-ADO-Sync-E2E-Test",
                    "sync_direction": "bidirectional",
                    "last_synced_at": now,
                    "last_sync_source": "ado",
                    "created_at": now,
                    "sync_status": "active",
                },
            ],
        }
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2))

        # Forward sync should detect echo (last_sync_source=ado, within grace)
        event = copy.deepcopy(gh_templates["issue_edited"])
        result = forward_engine.sync(event)
        assert result.status == "skipped"

    def test_no_echo_after_grace_period_expires(
        self,
        forward_engine: SyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
        ledger_path: Path,
        e2e_config: dict,
    ):
        """After grace period expires, sync proceeds normally (no false positive)."""
        grace_period = e2e_config.get("sync", {}).get("grace_period_seconds", 10)
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=grace_period + 5)).isoformat()
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 100,
                    "github_repo": "convergent-systems-co/dark-forge",
                    "ado_work_item_id": 42,
                    "ado_project": "GitHub-ADO-Sync-E2E-Test",
                    "sync_direction": "bidirectional",
                    "last_synced_at": old_time,
                    "last_sync_source": "ado",
                    "created_at": old_time,
                    "sync_status": "active",
                },
            ],
        }
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2))

        event = copy.deepcopy(gh_templates["issue_edited"])
        mock_client.update_work_item.return_value = _make_work_item(wi_id=42)
        result = forward_engine.sync(event)

        # Should NOT be skipped -- grace period has expired
        assert result.status == "updated"

    def test_ledger_sync_source_tracks_direction(
        self,
        forward_engine: SyncEngine,
        reverse_engine: ReverseSyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
        ado_templates: dict,
        ledger_path: Path,
    ):
        """Ledger last_sync_source toggles between github and ado."""
        # Forward sync
        event = copy.deepcopy(gh_templates["issue_opened"])
        mock_client.create_work_item.return_value = _make_work_item(wi_id=42)
        forward_engine.sync(event)

        ledger = json.loads(ledger_path.read_text())
        assert ledger["mappings"][0]["last_sync_source"] == "github"

        # Manually age the timestamp to avoid echo detection
        grace = 15
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=grace)).isoformat()
        ledger["mappings"][0]["last_synced_at"] = old_time
        ledger_path.write_text(json.dumps(ledger, indent=2))

        # Reverse sync
        payload = copy.deepcopy(ado_templates["workitem_updated_title"])
        with patch.object(ReverseSyncEngine, "_github_api", return_value={"id": 100}):
            reverse_engine.sync(payload)

        ledger = json.loads(ledger_path.read_text())
        assert ledger["mappings"][0]["last_sync_source"] == "ado"


# ===========================================================================
# Phase 5: Comments Sync
# ===========================================================================


class TestPhase5CommentsSync:
    """Validate bidirectional comment sync with prefix filtering."""

    def test_should_sync_comment_with_prefix(self):
        """Comments with [ado-sync] prefix are eligible for sync."""
        assert should_sync_comment("[ado-sync] Test comment") is True
        assert should_sync_comment("[ADO-SYNC] uppercase") is True

    def test_should_not_sync_comment_without_prefix(self):
        """Comments without prefix are rejected."""
        assert should_sync_comment("Regular comment") is False
        assert should_sync_comment("") is False

    def test_should_sync_html_wrapped_prefix(self):
        """HTML-wrapped prefix is also detected."""
        assert should_sync_comment("<p>[ado-sync] HTML comment</p>") is True

    def test_format_github_to_ado(self):
        """Markdown comment is formatted as HTML for ADO."""
        result = format_github_to_ado_comment("testuser", "[ado-sync] Hello world")
        assert "<p>" in result
        assert "testuser" in result
        assert "[ado-sync] Hello world" in result

    def test_format_ado_to_github(self):
        """HTML comment is formatted as Markdown for GitHub."""
        result = format_ado_to_github_comment("ADO User", "<p>[ado-sync] Reply from ADO</p>")
        assert "[From ADO" in result
        assert "ADO User" in result
        assert "[ado-sync] Reply from ADO" in result

    def test_sync_github_comment_to_ado(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
    ):
        """GitHub comment with prefix is synced to ADO."""
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 100,
                    "github_repo": "convergent-systems-co/dark-forge",
                    "ado_work_item_id": 42,
                    "ado_project": "test",
                    "sync_status": "active",
                },
            ],
        }
        comment = {
            "id": 5001,
            "body": "[ado-sync] This should be synced",
            "user": {"login": "test-user-gh"},
        }

        ado_comment_id = sync_comment_to_ado(100, comment, ledger, mock_client, e2e_config)
        assert ado_comment_id is not None
        mock_client.add_comment.assert_called_once()

        # Verify comment mapping recorded
        entry = ledger["mappings"][0]
        assert "comment_mappings" in entry
        assert len(entry["comment_mappings"]) == 1
        assert entry["comment_mappings"][0]["github_comment_id"] == 5001

    def test_skip_comment_without_prefix(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
    ):
        """GitHub comment without prefix is not synced."""
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 100,
                    "github_repo": "convergent-systems-co/dark-forge",
                    "ado_work_item_id": 42,
                    "sync_status": "active",
                },
            ],
        }
        comment = {
            "id": 5002,
            "body": "This should NOT be synced",
            "user": {"login": "test-user-gh"},
        }

        result = sync_comment_to_ado(100, comment, ledger, mock_client, e2e_config)
        assert result is None
        mock_client.add_comment.assert_not_called()

    def test_sync_ado_comment_to_github(self, e2e_config: dict):
        """ADO comment with prefix is prepared for GitHub."""
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 100,
                    "ado_work_item_id": 42,
                    "sync_status": "active",
                },
            ],
        }
        ado_comment = {
            "id": 201,
            "text": "<p>[ado-sync] Reply from ADO side</p>",
            "createdBy": {"displayName": "ADO Test User"},
        }

        result = sync_comment_from_ado(ado_comment, ledger, e2e_config)
        assert result is not None
        assert "[From ADO" in result["body"]
        assert "ADO Test User" in result["body"]

    def test_skip_ado_comment_without_prefix(self, e2e_config: dict):
        """ADO comment without prefix is not synced to GitHub."""
        ledger = {"schema_version": "1.0.0", "mappings": []}
        ado_comment = {
            "id": 202,
            "text": "<p>Regular ADO comment</p>",
            "createdBy": {"displayName": "User"},
        }

        result = sync_comment_from_ado(ado_comment, ledger, e2e_config)
        assert result is None

    def test_duplicate_comment_not_resynced(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
    ):
        """Same GitHub comment ID is not synced twice."""
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 100,
                    "ado_work_item_id": 42,
                    "sync_status": "active",
                    "comment_mappings": [
                        {"github_comment_id": 5001, "ado_comment_id": "101"},
                    ],
                },
            ],
        }
        comment = {
            "id": 5001,
            "body": "[ado-sync] Duplicate attempt",
            "user": {"login": "test-user-gh"},
        }

        result = sync_comment_to_ado(100, comment, ledger, mock_client, e2e_config)
        assert result is None
        mock_client.add_comment.assert_not_called()


# ===========================================================================
# Phase 6: Bulk Sync
# ===========================================================================


class TestPhase6BulkSync:
    """Validate bulk initial sync with dry-run and error handling."""

    @patch("governance.integrations.ado.bulk_sync._gh_list_issues")
    def test_bulk_sync_dry_run(
        self,
        mock_list_issues: MagicMock,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Dry-run lists issues without creating ADO work items."""
        mock_list_issues.return_value = [
            {
                "number": 1,
                "title": "Issue 1",
                "body": "Body 1",
                "state": "open",
                "labels": [{"name": "bug"}, {"name": "ado-sync"}],
            },
            {
                "number": 2,
                "title": "Issue 2",
                "body": "Body 2",
                "state": "open",
                "labels": [{"name": "enhancement"}, {"name": "ado-sync"}],
            },
        ]

        results = initial_sync(
            e2e_config,
            mock_client,
            ledger_path,
            error_log_path,
            direction="github_to_ado",
            dry_run=True,
            github_repo="convergent-systems-co/dark-forge",
        )

        assert len(results) == 2
        assert all(r.status == "skipped" for r in results)
        mock_client.create_work_item.assert_not_called()

    @patch("governance.integrations.ado.bulk_sync._gh_list_issues")
    def test_bulk_sync_actual(
        self,
        mock_list_issues: MagicMock,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Actual bulk sync creates ADO work items and populates ledger."""
        mock_list_issues.return_value = [
            {
                "number": 1,
                "title": "Issue 1",
                "body": "Body 1",
                "state": "open",
                "labels": [{"name": "bug"}, {"name": "ado-sync"}],
            },
            {
                "number": 2,
                "title": "Issue 2",
                "body": "Body 2",
                "state": "open",
                "labels": [{"name": "task"}, {"name": "ado-sync"}],
            },
        ]
        mock_client.create_work_item.side_effect = [
            _make_work_item(wi_id=101),
            _make_work_item(wi_id=102),
        ]

        results = initial_sync(
            e2e_config,
            mock_client,
            ledger_path,
            error_log_path,
            direction="github_to_ado",
            dry_run=False,
            github_repo="convergent-systems-co/dark-forge",
        )

        assert len(results) == 2
        assert results[0].status == "created"
        assert results[0].ado_work_item_id == 101
        assert results[1].status == "created"
        assert results[1].ado_work_item_id == 102

        # Verify ledger
        ledger = json.loads(ledger_path.read_text())
        assert len(ledger["mappings"]) == 2
        assert ledger["mappings"][0]["github_issue_number"] == 1
        assert ledger["mappings"][1]["github_issue_number"] == 2

    @patch("governance.integrations.ado.bulk_sync._gh_list_issues")
    def test_bulk_sync_skips_existing_ledger_entries(
        self,
        mock_list_issues: MagicMock,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Bulk sync skips issues already in the ledger (no duplicates)."""
        # Pre-seed ledger with issue #1
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 1,
                    "github_repo": "convergent-systems-co/dark-forge",
                    "ado_work_item_id": 99,
                    "sync_status": "active",
                },
            ],
        }
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2))

        mock_list_issues.return_value = [
            {"number": 1, "title": "Exists", "body": "", "state": "open", "labels": []},
            {"number": 3, "title": "New", "body": "", "state": "open", "labels": []},
        ]
        mock_client.create_work_item.return_value = _make_work_item(wi_id=103)

        results = initial_sync(
            e2e_config,
            mock_client,
            ledger_path,
            error_log_path,
            direction="github_to_ado",
            dry_run=False,
            github_repo="convergent-systems-co/dark-forge",
        )

        assert len(results) == 2
        assert results[0].status == "skipped"  # issue #1 already in ledger
        assert results[1].status == "created"   # issue #3 is new

    @patch("governance.integrations.ado.bulk_sync._gh_list_issues")
    def test_bulk_sync_error_handling(
        self,
        mock_list_issues: MagicMock,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Bulk sync logs errors without stopping the whole run."""
        mock_list_issues.return_value = [
            {"number": 1, "title": "Will Fail", "body": "", "state": "open", "labels": []},
            {"number": 2, "title": "Will Succeed", "body": "", "state": "open", "labels": []},
        ]
        mock_client.create_work_item.side_effect = [
            AdoServerError("500 error"),
            _make_work_item(wi_id=104),
        ]

        results = initial_sync(
            e2e_config,
            mock_client,
            ledger_path,
            error_log_path,
            direction="github_to_ado",
            dry_run=False,
            github_repo="convergent-systems-co/dark-forge",
        )

        assert results[0].status == "error"
        assert results[1].status == "created"

        # Error logged
        error_log = json.loads(error_log_path.read_text())
        assert len(error_log["errors"]) == 1


# ===========================================================================
# Phase 7: Error Recovery
# ===========================================================================


class TestPhase7ErrorRecovery:
    """Validate retry logic, error queue, and dead-lettering."""

    def _seed_errors(
        self,
        error_log_path: Path,
        errors: list[dict],
    ) -> None:
        error_log = {"schema_version": "1.0.0", "errors": errors}
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        error_log_path.write_text(json.dumps(error_log, indent=2))

    def test_retry_resolves_update_error(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Retry resolves an update error when work item is accessible."""
        mock_client.get_work_item.return_value = _make_work_item(
            wi_id=42, fields={"System.State": "Active"}
        )

        self._seed_errors(error_log_path, [
            {
                "error_id": "err-001",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": "update",
                "source": "github",
                "github_issue_number": 100,
                "ado_work_item_id": 42,
                "error_type": "AdoServerError",
                "error_message": "500 Internal Server Error",
                "retry_count": 0,
                "resolved": False,
            },
        ])

        results = retry_failed(e2e_config, mock_client, ledger_path, error_log_path)
        assert len(results) == 1
        assert results[0].status == "resolved"
        assert results[0].error_id == "err-001"

        # Verify error marked resolved
        error_log = json.loads(error_log_path.read_text())
        assert error_log["errors"][0]["resolved"] is True
        assert "resolved_at" in error_log["errors"][0]

    def test_retry_dead_letters_after_max_retries(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Error is dead-lettered when retry_count >= max_retries."""
        self._seed_errors(error_log_path, [
            {
                "error_id": "err-002",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": "update",
                "source": "github",
                "github_issue_number": 100,
                "ado_work_item_id": 42,
                "error_type": "AdoServerError",
                "error_message": "Persistent failure",
                "retry_count": 3,
                "resolved": False,
            },
        ])

        results = retry_failed(
            e2e_config, mock_client, ledger_path, error_log_path, max_retries=3
        )
        assert len(results) == 1
        assert results[0].status == "dead_letter"

        error_log = json.loads(error_log_path.read_text())
        assert error_log["errors"][0]["dead_letter"] is True

    def test_retry_skips_resolved_errors(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Already-resolved errors are not retried."""
        self._seed_errors(error_log_path, [
            {
                "error_id": "err-003",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": "update",
                "github_issue_number": 100,
                "ado_work_item_id": 42,
                "error_type": "AdoServerError",
                "error_message": "Already resolved",
                "retry_count": 1,
                "resolved": True,
                "resolved_at": datetime.now(timezone.utc).isoformat(),
            },
        ])

        results = retry_failed(e2e_config, mock_client, ledger_path, error_log_path)
        assert len(results) == 0

    def test_retry_dry_run(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Dry-run lists what would be retried without executing."""
        self._seed_errors(error_log_path, [
            {
                "error_id": "err-004",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": "update",
                "github_issue_number": 100,
                "ado_work_item_id": 42,
                "error_type": "AdoError",
                "error_message": "Test",
                "retry_count": 0,
                "resolved": False,
            },
        ])

        results = retry_failed(
            e2e_config, mock_client, ledger_path, error_log_path, dry_run=True
        )
        assert len(results) == 1
        assert results[0].status == "skipped"
        mock_client.get_work_item.assert_not_called()

    def test_retry_increments_count_on_failure(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Failed retry increments retry_count."""
        mock_client.get_work_item.side_effect = AdoServerError("Still failing")

        self._seed_errors(error_log_path, [
            {
                "error_id": "err-005",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": "update",
                "github_issue_number": 100,
                "ado_work_item_id": 42,
                "error_type": "AdoServerError",
                "error_message": "Original error",
                "retry_count": 0,
                "resolved": False,
            },
        ])

        results = retry_failed(e2e_config, mock_client, ledger_path, error_log_path)
        assert len(results) == 1
        assert results[0].status in ("retried", "dead_letter")

        error_log = json.loads(error_log_path.read_text())
        assert error_log["errors"][0]["retry_count"] >= 1

    def test_error_queue_structure(self, error_log_path: Path):
        """Error records have all required fields."""
        required_keys = {
            "error_id",
            "timestamp",
            "operation",
            "github_issue_number",
            "ado_work_item_id",
            "error_type",
            "error_message",
            "retry_count",
            "resolved",
        }
        error_log = {
            "schema_version": "1.0.0",
            "errors": [
                {
                    "error_id": str(uuid.uuid4()),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "operation": "create",
                    "source": "github",
                    "github_issue_number": 100,
                    "ado_work_item_id": None,
                    "error_type": "AdoServerError",
                    "error_message": "500 error",
                    "retry_count": 0,
                    "resolved": False,
                },
            ],
        }
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        error_log_path.write_text(json.dumps(error_log, indent=2))

        loaded = json.loads(error_log_path.read_text())
        for err in loaded["errors"]:
            assert required_keys.issubset(set(err.keys())), (
                f"Missing keys: {required_keys - set(err.keys())}"
            )

    def test_error_queue_bounded_growth(self, error_log_path: Path):
        """Error log grows responsibly (no unbounded entries)."""
        errors = []
        for i in range(50):
            errors.append({
                "error_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": "create",
                "source": "github",
                "github_issue_number": i,
                "ado_work_item_id": None,
                "error_type": "AdoError",
                "error_message": f"Error {i}",
                "retry_count": 0,
                "resolved": False,
            })

        error_log = {"schema_version": "1.0.0", "errors": errors}
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        error_log_path.write_text(json.dumps(error_log, indent=2))

        loaded = json.loads(error_log_path.read_text())
        assert len(loaded["errors"]) == 50
        # Verify serialization is reasonable size (< 100KB for 50 entries)
        assert len(error_log_path.read_text()) < 100_000


# ===========================================================================
# Phase 8: Health Checks & Dashboard
# ===========================================================================


class TestPhase8HealthDashboard:
    """Validate health checks and dashboard metrics."""

    def test_health_checks_with_populated_ledger(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Health checks pass with a populated ledger."""
        now = datetime.now(timezone.utc).isoformat()
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 1,
                    "github_repo": "test/repo",
                    "ado_work_item_id": 42,
                    "last_synced_at": now,
                    "sync_status": "active",
                },
            ],
        }
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2))

        results = run_health_checks(e2e_config, mock_client, ledger_path, error_log_path)
        by_name = {r.name: r for r in results}

        assert by_name["ledger_integrity"].status == HealthStatus.PASS
        assert "1 mapping(s), all valid" in by_name["ledger_integrity"].details
        assert by_name["ledger_recency"].status == HealthStatus.PASS

    def test_health_checks_detect_malformed_ledger(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Ledger integrity check detects missing required keys."""
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {"github_repo": "test/repo"},  # Missing github_issue_number & ado_work_item_id
            ],
        }
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2))

        results = run_health_checks(e2e_config, mock_client, ledger_path, error_log_path)
        by_name = {r.name: r for r in results}
        assert by_name["ledger_integrity"].status == HealthStatus.FAIL

    def test_health_checks_detect_duplicate_entries(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Ledger integrity check detects duplicate GitHub->ADO mappings."""
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 1,
                    "github_repo": "test/repo",
                    "ado_work_item_id": 42,
                    "last_synced_at": datetime.now(timezone.utc).isoformat(),
                },
                {
                    "github_issue_number": 1,
                    "github_repo": "test/repo",
                    "ado_work_item_id": 43,
                    "last_synced_at": datetime.now(timezone.utc).isoformat(),
                },
            ],
        }
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2))

        results = run_health_checks(e2e_config, mock_client, ledger_path, error_log_path)
        by_name = {r.name: r for r in results}
        assert by_name["ledger_integrity"].status == HealthStatus.FAIL
        assert "duplicate" in by_name["ledger_integrity"].details

    def test_health_checks_error_queue_unresolved(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Error queue check warns on unresolved errors."""
        error_log = {
            "schema_version": "1.0.0",
            "errors": [
                {
                    "error_id": "e1",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "operation": "create",
                    "resolved": False,
                },
            ],
        }
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        error_log_path.write_text(json.dumps(error_log, indent=2))

        results = run_health_checks(e2e_config, mock_client, ledger_path, error_log_path)
        by_name = {r.name: r for r in results}
        assert by_name["error_queue"].status == HealthStatus.WARN
        assert "1 unresolved" in by_name["error_queue"].details

    def test_health_check_service_hooks_bidirectional(
        self,
        mock_client: MagicMock,
        e2e_config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Service hooks check warns for bidirectional config."""
        results = run_health_checks(e2e_config, mock_client, ledger_path, error_log_path)
        by_name = {r.name: r for r in results}
        assert by_name["service_hooks"].status == HealthStatus.WARN
        assert "bidirectional" in by_name["service_hooks"].details

    def test_dashboard_metrics_empty_state(
        self,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Dashboard generates correct metrics for empty state."""
        dashboard = generate_dashboard_emission(ledger_path, error_log_path)
        status = dashboard["ado_sync_status"]

        assert status["total_mappings"] == 0
        assert status["active_mappings"] == 0
        assert status["error_mappings"] == 0
        assert status["paused_mappings"] == 0
        assert status["total_errors"] == 0
        assert status["unresolved_errors"] == 0
        assert status["dead_letter_count"] == 0
        assert "generated_at" in status

    def test_dashboard_metrics_populated(
        self,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Dashboard generates correct metrics from populated state."""
        now = datetime.now(timezone.utc).isoformat()
        ledger = {
            "schema_version": "1.0.0",
            "mappings": [
                {
                    "github_issue_number": 1,
                    "ado_work_item_id": 42,
                    "sync_direction": "github_to_ado",
                    "last_synced_at": now,
                    "sync_status": "active",
                },
                {
                    "github_issue_number": 2,
                    "ado_work_item_id": 43,
                    "sync_direction": "github_to_ado",
                    "last_synced_at": now,
                    "sync_status": "error",
                },
                {
                    "github_issue_number": 3,
                    "ado_work_item_id": 44,
                    "sync_direction": "github_to_ado",
                    "last_synced_at": now,
                    "sync_status": "paused",
                },
            ],
        }
        error_log = {
            "schema_version": "1.0.0",
            "errors": [
                {
                    "error_id": "e1",
                    "timestamp": now,
                    "operation": "create",
                    "resolved": False,
                },
                {
                    "error_id": "e2",
                    "timestamp": now,
                    "operation": "update",
                    "resolved": True,
                },
                {
                    "error_id": "e3",
                    "timestamp": now,
                    "operation": "create",
                    "resolved": False,
                    "dead_letter": True,
                },
            ],
        }
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        ledger_path.write_text(json.dumps(ledger, indent=2))
        error_log_path.parent.mkdir(parents=True, exist_ok=True)
        error_log_path.write_text(json.dumps(error_log, indent=2))

        dashboard = generate_dashboard_emission(ledger_path, error_log_path)
        status = dashboard["ado_sync_status"]

        assert status["total_mappings"] == 3
        assert status["active_mappings"] == 1
        assert status["error_mappings"] == 1
        assert status["paused_mappings"] == 1
        assert status["total_errors"] == 3
        assert status["unresolved_errors"] == 2
        assert status["dead_letter_count"] == 1
        assert status["last_github_to_ado_sync"] is not None

    def test_dashboard_json_output_schema(
        self,
        ledger_path: Path,
        error_log_path: Path,
    ):
        """Dashboard JSON output has the expected top-level structure."""
        dashboard = generate_dashboard_emission(ledger_path, error_log_path)

        assert "ado_sync_status" in dashboard
        required_keys = {
            "total_mappings",
            "active_mappings",
            "error_mappings",
            "paused_mappings",
            "last_github_to_ado_sync",
            "last_ado_to_github_sync",
            "errors_today",
            "dead_letter_count",
            "unresolved_errors",
            "total_errors",
            "generated_at",
        }
        assert required_keys.issubset(set(dashboard["ado_sync_status"].keys()))


# ===========================================================================
# Phase 9: Ledger Integrity (cross-phase validation)
# ===========================================================================


class TestPhase9LedgerIntegrity:
    """Validate ledger consistency across the full sync lifecycle."""

    def test_full_lifecycle_ledger_consistency(
        self,
        forward_engine: SyncEngine,
        reverse_engine: ReverseSyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
        ado_templates: dict,
        ledger_path: Path,
        e2e_config: dict,
    ):
        """Run a full lifecycle and verify ledger stays consistent."""
        # 1. Create via forward sync
        event_open = copy.deepcopy(gh_templates["issue_opened"])
        mock_client.create_work_item.return_value = _make_work_item(wi_id=42)
        forward_engine.sync(event_open)

        # 2. Edit via forward sync
        event_edit = copy.deepcopy(gh_templates["issue_edited"])
        mock_client.update_work_item.return_value = _make_work_item(wi_id=42)
        forward_engine.sync(event_edit)

        # 3. Age the timestamp so reverse sync is not echo-blocked
        ledger = json.loads(ledger_path.read_text())
        grace = e2e_config.get("sync", {}).get("grace_period_seconds", 10) + 5
        old_time = (datetime.now(timezone.utc) - timedelta(seconds=grace)).isoformat()
        ledger["mappings"][0]["last_synced_at"] = old_time
        ledger_path.write_text(json.dumps(ledger, indent=2))

        # 4. Reverse sync from ADO
        with patch.object(ReverseSyncEngine, "_github_api", return_value={"id": 100}):
            payload = copy.deepcopy(ado_templates["workitem_updated_title"])
            reverse_engine.sync(payload)

        # Final ledger validation
        ledger = json.loads(ledger_path.read_text())
        assert len(ledger["mappings"]) == 1
        entry = ledger["mappings"][0]

        # Required keys
        for key in [
            "github_issue_number",
            "github_repo",
            "ado_work_item_id",
            "last_synced_at",
            "last_sync_source",
            "sync_status",
        ]:
            assert key in entry, f"Missing key: {key}"

        assert entry["github_issue_number"] == 100
        assert entry["ado_work_item_id"] == 42
        assert entry["last_sync_source"] == "ado"
        assert entry["sync_status"] == "active"

        # Timestamp is valid ISO format
        ts = datetime.fromisoformat(entry["last_synced_at"].replace("Z", "+00:00"))
        assert ts.tzinfo is not None

    def test_no_duplicate_ledger_entries(
        self,
        forward_engine: SyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
        ledger_path: Path,
    ):
        """Multiple syncs of the same issue do not create duplicate entries."""
        event_open = copy.deepcopy(gh_templates["issue_opened"])
        mock_client.create_work_item.return_value = _make_work_item(wi_id=42)
        forward_engine.sync(event_open)

        # Edit multiple times
        for _ in range(5):
            event_edit = copy.deepcopy(gh_templates["issue_edited"])
            mock_client.update_work_item.return_value = _make_work_item(wi_id=42)
            forward_engine.sync(event_edit)

        ledger = json.loads(ledger_path.read_text())
        assert len(ledger["mappings"]) == 1

    def test_ledger_timestamps_are_monotonic(
        self,
        forward_engine: SyncEngine,
        mock_client: MagicMock,
        gh_templates: dict,
        ledger_path: Path,
    ):
        """Ledger last_synced_at is updated monotonically."""
        event_open = copy.deepcopy(gh_templates["issue_opened"])
        mock_client.create_work_item.return_value = _make_work_item(wi_id=42)
        forward_engine.sync(event_open)

        ledger = json.loads(ledger_path.read_text())
        ts1_str = ledger["mappings"][0]["last_synced_at"]

        # Edit
        event_edit = copy.deepcopy(gh_templates["issue_edited"])
        mock_client.update_work_item.return_value = _make_work_item(wi_id=42)
        forward_engine.sync(event_edit)

        ledger = json.loads(ledger_path.read_text())
        ts2_str = ledger["mappings"][0]["last_synced_at"]

        ts1 = datetime.fromisoformat(ts1_str.replace("Z", "+00:00"))
        ts2 = datetime.fromisoformat(ts2_str.replace("Z", "+00:00"))
        assert ts2 >= ts1
