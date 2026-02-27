"""Live integration tests against a real Azure DevOps instance.

These tests are SKIPPED unless credentials are provided via environment
variables. They hit the actual ADO REST API and verify real responses.

Required env vars:
    ADO_PAT              — Personal Access Token with work item read/write scope
    ADO_ORGANIZATION     — ADO organization name (e.g., "JM-FAMILY")
    ADO_PROJECT          — ADO project name (e.g., "SET Agile Portfolio")

Optional env vars:
    ADO_WORK_ITEM_ID     — An existing work item ID to test read operations
    ADO_ACCESS_METHOD    — "pat" (default), "az_cli"

Run with:
    ADO_PAT=xxx ADO_ORGANIZATION=myorg ADO_PROJECT=myproj pytest tests/test_live_ado.py -v

Or use az cli token:
    ADO_ACCESS_METHOD=az_cli ADO_ORGANIZATION=myorg ADO_PROJECT=myproj pytest tests/test_live_ado.py -v
"""

from __future__ import annotations

import os
import subprocess

import pytest

from governance.integrations.ado._exceptions import AdoNotFoundError
from governance.integrations.ado._patch import add_field, replace_field
from governance.integrations.ado.auth import PatAuth
from governance.integrations.ado.client import AdoClient
from governance.integrations.ado.config import AdoConfig

# ── Skip conditions ────────────────────────────────────────────────────

_ADO_ORG = os.environ.get("ADO_ORGANIZATION", "")
_ADO_PROJECT = os.environ.get("ADO_PROJECT", "")
_ADO_PAT = os.environ.get("ADO_PAT", "")
_ADO_ACCESS_METHOD = os.environ.get("ADO_ACCESS_METHOD", "pat")
_ADO_WORK_ITEM_ID = os.environ.get("ADO_WORK_ITEM_ID", "")


def _get_az_cli_token() -> str:
    """Get a Bearer token from az cli for ADO scope."""
    try:
        result = subprocess.run(
            [
                "az", "account", "get-access-token",
                "--resource", "499b84ac-1321-427f-aa17-267ca6975798",
                "--query", "accessToken", "-o", "tsv",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ""


def _has_credentials() -> bool:
    if not _ADO_ORG or not _ADO_PROJECT:
        return False
    if _ADO_ACCESS_METHOD == "az_cli":
        return bool(_get_az_cli_token())
    return bool(_ADO_PAT)


skip_no_creds = pytest.mark.skipif(
    not _has_credentials(),
    reason="Live ADO tests require ADO_ORGANIZATION, ADO_PROJECT, and ADO_PAT (or ADO_ACCESS_METHOD=az_cli)",
)

skip_no_work_item = pytest.mark.skipif(
    not _ADO_WORK_ITEM_ID,
    reason="ADO_WORK_ITEM_ID not set — skipping tests that read a specific work item",
)


# ── Auth helper ────────────────────────────────────────────────────────


class _BearerAuth:
    """Simple Bearer token auth for az cli tokens."""

    def __init__(self, token: str):
        self._token = token

    def get_auth_header(self) -> str:
        return f"Bearer {self._token}"


# ── Fixtures ───────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def live_client():
    """Create a client against the real ADO instance."""
    if not _has_credentials():
        pytest.skip("No ADO credentials")

    config = AdoConfig(
        organization=_ADO_ORG,
        default_project=_ADO_PROJECT,
        max_retries=2,
        base_delay=1.0,
        max_delay=10.0,
        timeout=30.0,
    )

    if _ADO_ACCESS_METHOD == "az_cli":
        token = _get_az_cli_token()
        auth = _BearerAuth(token)
    else:
        auth = PatAuth(_ADO_PAT)

    client = AdoClient(config, auth)
    yield client
    client.close()


# ── Read-only tests (safe against any ADO instance) ───────────────────


@skip_no_creds
class TestLiveProjectInspection:
    """Read-only tests that inspect project metadata."""

    def test_get_project_properties(self, live_client):
        props = live_client.get_project_properties()
        assert "name" in props
        assert "capabilities" in props
        assert props["name"] == _ADO_PROJECT

    def test_list_work_item_types(self, live_client):
        types = live_client.list_work_item_types()
        assert len(types) > 0
        type_names = [t.name for t in types]
        # Every ADO project has at least Bug and Task
        assert any("Bug" in n for n in type_names) or any("Task" in n for n in type_names)

    def test_get_bug_states(self, live_client):
        states = live_client.get_work_item_type_states("Bug")
        assert len(states) > 0
        state_names = [s["name"] for s in states]
        # Every process has at least New and Closed
        assert any("New" in n for n in state_names)
        assert any("Closed" in n for n in state_names)

    def test_list_area_paths(self, live_client):
        root = live_client.list_area_paths()
        assert root.name != ""
        assert root.path != ""

    def test_list_iteration_paths(self, live_client):
        root = live_client.list_iteration_paths()
        assert root.name != ""

    def test_list_fields(self, live_client):
        fields = live_client.list_fields()
        assert len(fields) > 0
        ref_names = [f.reference_name for f in fields]
        assert "System.Title" in ref_names
        assert "System.State" in ref_names

    def test_wiql_query(self, live_client):
        result = live_client.query_wiql(
            "SELECT [System.Id] FROM WorkItems WHERE [System.State] <> '' ORDER BY [System.Id] DESC",
            top=5,
        )
        assert result.query_type == "flat"
        # Should find at least some work items in any real project
        assert isinstance(result.work_item_ids, list)


@skip_no_creds
@skip_no_work_item
class TestLiveWorkItemRead:
    """Read a specific work item — requires ADO_WORK_ITEM_ID."""

    def test_get_work_item(self, live_client):
        wi_id = int(_ADO_WORK_ITEM_ID)
        wi = live_client.get_work_item(wi_id)
        assert wi.id == wi_id
        assert "System.Title" in wi.fields
        assert "System.State" in wi.fields

    def test_get_work_item_with_relations(self, live_client):
        wi_id = int(_ADO_WORK_ITEM_ID)
        from governance.integrations.ado._types import WorkItemExpand
        wi = live_client.get_work_item(wi_id, expand=WorkItemExpand.RELATIONS)
        assert wi.id == wi_id
        assert isinstance(wi.relations, list)

    def test_get_work_item_specific_fields(self, live_client):
        wi_id = int(_ADO_WORK_ITEM_ID)
        wi = live_client.get_work_item(wi_id, fields=["System.Title", "System.State"])
        assert wi.id == wi_id
        assert "System.Title" in wi.fields

    def test_get_work_items_batch(self, live_client):
        wi_id = int(_ADO_WORK_ITEM_ID)
        items = live_client.get_work_items_batch([wi_id])
        assert len(items) == 1
        assert items[0].id == wi_id

    def test_get_comments(self, live_client):
        wi_id = int(_ADO_WORK_ITEM_ID)
        comments = live_client.get_comments(wi_id)
        assert isinstance(comments, list)
        # Comments may or may not exist — just verify the call succeeds
        for c in comments:
            assert c.work_item_id == wi_id
            assert isinstance(c.text, str)

    def test_wiql_with_details(self, live_client):
        wi_id = int(_ADO_WORK_ITEM_ID)
        items = live_client.query_wiql_with_details(
            f"SELECT [System.Id] FROM WorkItems WHERE [System.Id] = {wi_id}"
        )
        assert len(items) == 1
        assert items[0].id == wi_id
        assert "System.Title" in items[0].fields


@skip_no_creds
class TestLiveErrorHandling:
    """Verify real ADO error responses map to the correct exceptions."""

    def test_nonexistent_work_item(self, live_client):
        with pytest.raises(AdoNotFoundError):
            live_client.get_work_item(999999999)

    def test_nonexistent_work_item_type_states(self, live_client):
        # ADO returns 404 for unknown work item types
        with pytest.raises(AdoNotFoundError):
            live_client.get_work_item_type_states("CompletelyFakeType12345")


@skip_no_creds
class TestLiveWriteOperations:
    """Write tests — creates a work item, updates it, comments, then deletes.

    These are self-cleaning: the work item is deleted at the end.
    Only run when credentials have write access.
    """

    def test_full_lifecycle(self, live_client):
        """Create → read → update state → comment → delete."""
        # 1. Create
        ops = [
            add_field("/fields/System.Title", "[TEST] ADO Client Integration Test — safe to delete"),
            add_field("/fields/System.Description", "<p>Automated test work item. Will be deleted.</p>"),
        ]
        wi = live_client.create_work_item("Task", ops)
        created_id = wi.id
        assert created_id > 0
        assert wi.fields.get("System.Title", "").startswith("[TEST]")

        try:
            # 2. Read back
            fetched = live_client.get_work_item(created_id)
            assert fetched.id == created_id
            assert fetched.fields["System.Title"] == wi.fields["System.Title"]

            # 3. Discover valid states, then update
            states = live_client.get_work_item_type_states("Task")
            state_names = [s["name"] for s in states]
            # Find an active/in-progress state
            target_state = None
            for candidate in ["Active", "In Progress", "Doing", "In Development"]:
                if candidate in state_names:
                    target_state = candidate
                    break

            if target_state:
                update_ops = [replace_field("/fields/System.State", target_state)]
                updated = live_client.update_work_item(created_id, update_ops)
                assert updated.fields.get("System.State") == target_state

            # 4. Add a comment (HTML)
            comment = live_client.add_comment(
                created_id,
                "<p><strong>Integration test</strong> — verifying comment API works.</p>",
            )
            assert comment.id > 0
            assert comment.work_item_id == created_id
            assert "Integration test" in comment.text

            # 5. Read comments back
            comments = live_client.get_comments(created_id)
            assert len(comments) >= 1
            assert any("Integration test" in c.text for c in comments)

        finally:
            # 6. Delete (recycle bin)
            live_client.delete_work_item(created_id)
