"""Integration tests using a real HTTP server — no request mocking.

These tests spin up a real TCP/HTTP server on localhost and point the
AdoClient at it. This exercises the full stack: requests.Session,
connection pooling, auth header construction, JSON serialization,
retry logic, error mapping, and response parsing over real sockets.
"""

from __future__ import annotations

import base64
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest

from governance.integrations.ado._exceptions import (
    AdoAuthError,
    AdoNotFoundError,
    AdoRateLimitError,
    AdoServerError,
    AdoValidationError,
)
from governance.integrations.ado._patch import add_field, replace_field
from governance.integrations.ado._types import WorkItemExpand
from governance.integrations.ado.auth import PatAuth
from governance.integrations.ado.client import AdoClient
from governance.integrations.ado.config import AdoConfig


# ── Fake ADO server ────────────────────────────────────────────────────

# Shared state so tests can configure responses from the handler.
_server_state: dict[str, Any] = {}


def _reset_server_state():
    _server_state.clear()
    _server_state["requests_log"] = []
    _server_state["responses"] = {}
    _server_state["call_count"] = 0


class FakeAdoHandler(BaseHTTPRequestHandler):
    """Minimal handler that mimics ADO REST API responses."""

    def log_message(self, format, *args):
        pass  # Suppress stderr output during tests

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length > 0 else b""

    def _handle(self):
        body = self._read_body()
        parsed_body = json.loads(body) if body else None

        _server_state["call_count"] += 1
        _server_state["requests_log"].append({
            "method": self.command,
            "path": self.path,
            "headers": dict(self.headers),
            "body": parsed_body,
        })

        path = urlparse(self.path).path

        # Check for a configured response for this path
        for pattern, response_cfg in _server_state.get("responses", {}).items():
            if pattern in path:
                status = response_cfg.get("status", 200)
                resp_body = response_cfg.get("body", {})
                resp_headers = response_cfg.get("headers", {})
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                for k, v in resp_headers.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(json.dumps(resp_body).encode())
                return

        # Default: 404
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"message": "Not found"}).encode())

    do_GET = _handle
    do_POST = _handle
    do_PATCH = _handle
    do_DELETE = _handle


@pytest.fixture(scope="module")
def http_server():
    """Start a real HTTP server on a random port for the module."""
    server = HTTPServer(("127.0.0.1", 0), FakeAdoHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()


@pytest.fixture(autouse=True)
def reset_state():
    """Reset server state before each test."""
    _reset_server_state()


def _make_client(base_url: str, **config_overrides) -> AdoClient:
    """Create a client pointing at the local server."""
    # Parse host from base_url to use as "organization"
    # AdoConfig.base_url is https://dev.azure.com/{org}, so we override it
    config = AdoConfig(
        organization="localtest",
        default_project="testproj",
        max_retries=config_overrides.get("max_retries", 0),
        base_delay=0.01,
        max_delay=0.05,
        timeout=5.0,
    )
    auth = PatAuth("test-integration-pat")

    client = AdoClient(config, auth)
    # Override base_url to point at our local server
    client._config = type(config)(
        organization="localtest",
        default_project="testproj",
        max_retries=config_overrides.get("max_retries", 0),
        base_delay=0.01,
        max_delay=0.05,
        timeout=5.0,
    )
    # Monkey-patch base_url property to use local server
    object.__setattr__(client._config, "__class__", type(
        "AdoConfigLocal", (object,), {
            "base_url": base_url,
            "default_project": "testproj",
            "api_version": "7.1",
            "max_retries": config_overrides.get("max_retries", 0),
            "base_delay": 0.01,
            "max_delay": 0.05,
            "timeout": 5.0,
        }
    ))
    return client


class _LocalAdoConfig:
    """Non-frozen config that lets us point base_url at localhost."""

    def __init__(self, base_url: str, **kwargs):
        self.base_url = base_url
        self.default_project = kwargs.get("default_project", "testproj")
        self.api_version = kwargs.get("api_version", "7.1")
        self.max_retries = kwargs.get("max_retries", 0)
        self.base_delay = kwargs.get("base_delay", 0.01)
        self.max_delay = kwargs.get("max_delay", 0.05)
        self.timeout = kwargs.get("timeout", 5.0)


@pytest.fixture
def local_client(http_server):
    """AdoClient pointed at the local HTTP server."""
    config = _LocalAdoConfig(http_server)
    auth = PatAuth("test-integration-pat")
    client = AdoClient.__new__(AdoClient)
    client._config = config
    client._auth = auth
    import requests as req
    from governance.integrations.ado._rate_limit import RetryConfig
    client._session = req.Session()
    client._retry_config = RetryConfig(
        max_retries=config.max_retries,
        base_delay=config.base_delay,
        max_delay=config.max_delay,
    )
    yield client
    client.close()


@pytest.fixture
def local_client_with_retry(http_server):
    """AdoClient with retry enabled, pointed at local HTTP server."""
    config = _LocalAdoConfig(http_server, max_retries=3)
    auth = PatAuth("test-integration-pat")
    client = AdoClient.__new__(AdoClient)
    client._config = config
    client._auth = auth
    import requests as req
    from governance.integrations.ado._rate_limit import RetryConfig
    client._session = req.Session()
    client._retry_config = RetryConfig(
        max_retries=3,
        base_delay=0.01,
        max_delay=0.05,
    )
    yield client
    client.close()


# ── Tests: Real HTTP round-trips ───────────────────────────────────────


class TestRealHttpGetWorkItem:
    """GET work item over real TCP/HTTP."""

    def test_get_work_item_success(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/42"] = {
            "status": 200,
            "body": {
                "id": 42,
                "rev": 3,
                "url": f"{http_server}/testproj/_apis/wit/workitems/42",
                "fields": {
                    "System.Title": "Real HTTP test",
                    "System.State": "Active",
                },
                "relations": [],
            },
        }

        wi = local_client.get_work_item(42)
        assert wi.id == 42
        assert wi.rev == 3
        assert wi.fields["System.Title"] == "Real HTTP test"
        assert wi.fields["System.State"] == "Active"

    def test_auth_header_sent(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/1"] = {
            "status": 200,
            "body": {"id": 1, "rev": 1, "url": "", "fields": {}},
        }

        local_client.get_work_item(1)

        logged = _server_state["requests_log"]
        assert len(logged) == 1
        auth_header = logged[0]["headers"].get("Authorization", "")
        expected = base64.b64encode(b":test-integration-pat").decode()
        assert auth_header == f"Basic {expected}"

    def test_api_version_query_param(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/1"] = {
            "status": 200,
            "body": {"id": 1, "rev": 1, "url": "", "fields": {}},
        }

        local_client.get_work_item(1)

        logged = _server_state["requests_log"]
        assert "api-version=7.1" in logged[0]["path"]

    def test_expand_query_param(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/1"] = {
            "status": 200,
            "body": {"id": 1, "rev": 1, "url": "", "fields": {}, "relations": []},
        }

        local_client.get_work_item(1, expand=WorkItemExpand.RELATIONS)

        logged = _server_state["requests_log"]
        assert "%24expand=Relations" in logged[0]["path"] or "$expand=Relations" in logged[0]["path"]


class TestRealHttpCreateWorkItem:
    """POST create work item over real TCP/HTTP."""

    def test_create_sends_json_patch(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/$Task"] = {
            "status": 200,
            "body": {
                "id": 100,
                "rev": 1,
                "url": f"{http_server}/testproj/_apis/wit/workitems/100",
                "fields": {"System.Title": "Created via HTTP"},
            },
        }

        ops = [add_field("/fields/System.Title", "Created via HTTP")]
        wi = local_client.create_work_item("Task", ops)

        assert wi.id == 100
        assert wi.fields["System.Title"] == "Created via HTTP"

        logged = _server_state["requests_log"]
        assert logged[0]["method"] == "POST"
        assert logged[0]["body"] == [
            {"op": "add", "path": "/fields/System.Title", "value": "Created via HTTP"}
        ]
        assert "application/json-patch+json" in logged[0]["headers"].get("Content-Type", "")

    def test_create_custom_project(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/$Bug"] = {
            "status": 200,
            "body": {"id": 5, "rev": 1, "url": "", "fields": {}},
        }

        ops = [add_field("/fields/System.Title", "Bug")]
        wi = local_client.create_work_item("Bug", ops, project="otherproj")

        logged = _server_state["requests_log"]
        assert "/otherproj/" in logged[0]["path"]


class TestRealHttpUpdateWorkItem:
    """PATCH update work item over real TCP/HTTP."""

    def test_update_sends_patch_method(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/50"] = {
            "status": 200,
            "body": {
                "id": 50,
                "rev": 2,
                "url": "",
                "fields": {"System.State": "Closed"},
            },
        }

        ops = [replace_field("/fields/System.State", "Closed")]
        wi = local_client.update_work_item(50, ops)

        assert wi.rev == 2
        logged = _server_state["requests_log"]
        assert logged[0]["method"] == "PATCH"


class TestRealHttpDeleteWorkItem:
    def test_delete(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/99"] = {
            "status": 200,
            "body": {"id": 99},
        }

        result = local_client.delete_work_item(99)
        assert result["id"] == 99

        logged = _server_state["requests_log"]
        assert logged[0]["method"] == "DELETE"


class TestRealHttpWiql:
    def test_wiql_query(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/wiql"] = {
            "status": 200,
            "body": {
                "queryType": "flat",
                "asOf": "2026-02-27T00:00:00Z",
                "workItems": [
                    {"id": 1, "url": "http://x"},
                    {"id": 2, "url": "http://x"},
                ],
            },
        }

        result = local_client.query_wiql("SELECT [System.Id] FROM WorkItems")

        assert result.work_item_ids == [1, 2]
        assert result.query_type == "flat"

        logged = _server_state["requests_log"]
        assert logged[0]["body"]["query"] == "SELECT [System.Id] FROM WorkItems"


class TestRealHttpComments:
    def test_get_comments(self, local_client, http_server):
        _server_state["responses"]["/comments"] = {
            "status": 200,
            "body": {
                "totalCount": 1,
                "comments": [{
                    "id": 1,
                    "text": "<p>Hello from real HTTP</p>",
                    "createdBy": {"displayName": "Bot"},
                    "createdDate": "2026-02-27T00:00:00Z",
                    "modifiedDate": "2026-02-27T00:00:00Z",
                    "version": 1,
                }],
            },
        }

        comments = local_client.get_comments(10)
        assert len(comments) == 1
        assert comments[0].text == "<p>Hello from real HTTP</p>"
        assert comments[0].work_item_id == 10

    def test_add_comment_html(self, local_client, http_server):
        html = "<h3>Status</h3><ul><li>Done</li></ul>"
        _server_state["responses"]["/comments"] = {
            "status": 200,
            "body": {
                "id": 5,
                "text": html,
                "createdBy": {"displayName": "Bot"},
                "version": 1,
            },
        }

        comment = local_client.add_comment(10, html)
        assert comment.text == html

        logged = _server_state["requests_log"]
        assert logged[0]["method"] == "POST"
        assert logged[0]["body"]["text"] == html


class TestRealHttpProjectInspection:
    def test_work_item_type_states(self, local_client, http_server):
        _server_state["responses"]["/workitemtypes/Bug/states"] = {
            "status": 200,
            "body": {
                "value": [
                    {"name": "New", "color": "b2b2b2", "category": "Proposed"},
                    {"name": "Active", "color": "007acc", "category": "InProgress"},
                    {"name": "Resolved", "color": "ff9d00", "category": "Resolved"},
                    {"name": "Closed", "color": "339933", "category": "Completed"},
                ],
            },
        }

        states = local_client.get_work_item_type_states("Bug")
        assert len(states) == 4
        state_names = [s["name"] for s in states]
        assert state_names == ["New", "Active", "Resolved", "Closed"]

    def test_project_properties(self, local_client, http_server):
        _server_state["responses"]["/_apis/projects/testproj"] = {
            "status": 200,
            "body": {
                "id": "abc-123",
                "name": "testproj",
                "state": "wellFormed",
                "capabilities": {
                    "processTemplate": {
                        "templateName": "Agile",
                    },
                },
            },
        }

        props = local_client.get_project_properties()
        assert props["name"] == "testproj"
        assert props["capabilities"]["processTemplate"]["templateName"] == "Agile"


class TestRealHttpErrorMapping:
    """Verify HTTP error codes are mapped to correct exceptions over real HTTP."""

    def test_401_raises_auth_error(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/1"] = {
            "status": 401,
            "body": {"message": "Unauthorized"},
        }

        with pytest.raises(AdoAuthError) as exc_info:
            local_client.get_work_item(1)
        assert exc_info.value.status_code == 401

    def test_403_raises_auth_error(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/1"] = {
            "status": 403,
            "body": {"message": "Forbidden"},
        }

        with pytest.raises(AdoAuthError) as exc_info:
            local_client.get_work_item(1)
        assert exc_info.value.status_code == 403

    def test_404_raises_not_found(self, local_client):
        # No response configured → default 404
        with pytest.raises(AdoNotFoundError) as exc_info:
            local_client.get_work_item(99999)
        assert exc_info.value.status_code == 404

    def test_400_raises_validation_error(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/$Bad"] = {
            "status": 400,
            "body": {"message": "Invalid work item type"},
        }

        ops = [add_field("/fields/System.Title", "X")]
        with pytest.raises(AdoValidationError):
            local_client.create_work_item("Bad", ops)

    def test_429_raises_rate_limit(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/1"] = {
            "status": 429,
            "body": {"message": "Too many requests"},
            "headers": {"Retry-After": "60"},
        }

        with pytest.raises(AdoRateLimitError) as exc_info:
            local_client.get_work_item(1)
        assert exc_info.value.retry_after_seconds == 60.0

    def test_500_raises_server_error(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/1"] = {
            "status": 500,
            "body": {"message": "Internal server error"},
        }

        with pytest.raises(AdoServerError) as exc_info:
            local_client.get_work_item(1)
        assert exc_info.value.status_code == 500


class TestRealHttpRetry:
    """Verify retry logic works over real HTTP connections."""

    def test_retry_recovers_from_503(self, local_client_with_retry, http_server):
        """Server returns 503 twice, then 200 — client should succeed."""
        call_count = {"n": 0}
        original_handle = FakeAdoHandler._handle

        def flaky_handle(handler_self):
            call_count["n"] += 1
            # First 2 calls: 503, then success
            if call_count["n"] <= 2:
                handler_self.send_response(503)
                handler_self.send_header("Content-Type", "application/json")
                handler_self.end_headers()
                handler_self.wfile.write(json.dumps({"message": "Unavailable"}).encode())
                # Still log the request
                body = handler_self._read_body()
                _server_state["call_count"] += 1
                return

            _server_state["responses"]["/_apis/wit/workitems/7"] = {
                "status": 200,
                "body": {"id": 7, "rev": 1, "url": "", "fields": {"System.Title": "Recovered"}},
            }
            original_handle(handler_self)

        FakeAdoHandler._handle = flaky_handle
        FakeAdoHandler.do_GET = flaky_handle
        try:
            wi = local_client_with_retry.get_work_item(7)
            assert wi.id == 7
            assert wi.fields["System.Title"] == "Recovered"
            assert call_count["n"] == 3  # 2 failures + 1 success
        finally:
            FakeAdoHandler._handle = original_handle
            FakeAdoHandler.do_GET = original_handle


class TestRealHttpSessionReuse:
    """Verify connection pooling via requests.Session works."""

    def test_multiple_requests_same_session(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitems/1"] = {
            "status": 200,
            "body": {"id": 1, "rev": 1, "url": "", "fields": {}},
        }
        _server_state["responses"]["/_apis/wit/workitems/2"] = {
            "status": 200,
            "body": {"id": 2, "rev": 1, "url": "", "fields": {}},
        }

        wi1 = local_client.get_work_item(1)
        wi2 = local_client.get_work_item(2)

        assert wi1.id == 1
        assert wi2.id == 2
        assert len(_server_state["requests_log"]) == 2

    def test_context_manager(self, http_server):
        config = _LocalAdoConfig(http_server)
        auth = PatAuth("ctx-mgr-pat")

        _server_state["responses"]["/_apis/wit/workitems/1"] = {
            "status": 200,
            "body": {"id": 1, "rev": 1, "url": "", "fields": {}},
        }

        import requests as req
        from governance.integrations.ado._rate_limit import RetryConfig

        client = AdoClient.__new__(AdoClient)
        client._config = config
        client._auth = auth
        client._session = req.Session()
        client._retry_config = RetryConfig(max_retries=0, base_delay=0.01, max_delay=0.05)

        with client:
            wi = client.get_work_item(1)
            assert wi.id == 1
        # Session closed after context manager exit — no assertion needed,
        # we just verify no exception is raised


class TestRealHttpBatchAndPagination:
    def test_batch_request(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitemsbatch"] = {
            "status": 200,
            "body": {
                "count": 2,
                "value": [
                    {"id": 10, "rev": 1, "url": "", "fields": {"System.Title": "A"}},
                    {"id": 20, "rev": 1, "url": "", "fields": {"System.Title": "B"}},
                ],
            },
        }

        items = local_client.get_work_items_batch([10, 20])
        assert len(items) == 2
        assert items[0].fields["System.Title"] == "A"
        assert items[1].fields["System.Title"] == "B"

        logged = _server_state["requests_log"]
        assert logged[0]["body"]["ids"] == [10, 20]

    def test_wiql_with_details_two_step(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/wiql"] = {
            "status": 200,
            "body": {
                "queryType": "flat",
                "asOf": "2026-01-01T00:00:00Z",
                "workItems": [{"id": 5, "url": "x"}, {"id": 6, "url": "x"}],
            },
        }
        _server_state["responses"]["/_apis/wit/workitemsbatch"] = {
            "status": 200,
            "body": {
                "count": 2,
                "value": [
                    {"id": 5, "rev": 1, "url": "", "fields": {"System.Title": "Five"}},
                    {"id": 6, "rev": 1, "url": "", "fields": {"System.Title": "Six"}},
                ],
            },
        }

        items = local_client.query_wiql_with_details("SELECT [System.Id] FROM WorkItems")
        assert len(items) == 2
        assert items[0].id == 5
        assert items[1].id == 6
        # Verify two HTTP calls: WIQL + batch
        assert len(_server_state["requests_log"]) == 2


class TestRealHttpFieldsAndTypes:
    def test_list_work_item_types(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/workitemtypes"] = {
            "status": 200,
            "body": {
                "value": [
                    {"name": "Bug", "description": "A defect", "icon": {"url": ""}, "fields": []},
                    {"name": "Task", "description": "A task", "icon": {"url": ""}, "fields": []},
                    {"name": "User Story", "description": "A story", "icon": {"url": ""}, "fields": []},
                ],
            },
        }

        types = local_client.list_work_item_types()
        assert len(types) == 3
        type_names = [t.name for t in types]
        assert "Bug" in type_names
        assert "User Story" in type_names

    def test_list_fields(self, local_client, http_server):
        _server_state["responses"]["/_apis/wit/fields"] = {
            "status": 200,
            "body": {
                "value": [
                    {"name": "Title", "referenceName": "System.Title", "type": "string", "readOnly": False},
                    {"name": "State", "referenceName": "System.State", "type": "string", "readOnly": False},
                ],
            },
        }

        fields = local_client.list_fields()
        assert len(fields) == 2
        assert fields[0].reference_name == "System.Title"
