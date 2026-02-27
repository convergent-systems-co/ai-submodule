"""Azure DevOps REST API client."""

from __future__ import annotations

from typing import Any

import requests

from governance.integrations.ado._exceptions import (
    AdoAuthError,
    AdoError,
    AdoNotFoundError,
    AdoRateLimitError,
    AdoServerError,
    AdoValidationError,
)
from governance.integrations.ado._pagination import paginate
from governance.integrations.ado._patch import PatchOperation, to_json_patch
from governance.integrations.ado._rate_limit import RetryConfig, execute_with_retry
from governance.integrations.ado._types import (
    ClassificationNode,
    Comment,
    FieldDefinition,
    WiqlResult,
    WorkItem,
    WorkItemExpand,
    WorkItemType,
)
from governance.integrations.ado.auth import AuthProvider
from governance.integrations.ado.config import AdoConfig


class AdoClient:
    """Client for Azure DevOps REST API 7.1.

    Usage::

        from governance.integrations.ado import AdoClient, AdoConfig, create_auth_provider

        config = AdoConfig(organization="myorg", default_project="myproject")
        auth = create_auth_provider("pat", pat="my-token")

        with AdoClient(config, auth) as client:
            wi = client.get_work_item(42)
    """

    def __init__(self, config: AdoConfig, auth: AuthProvider) -> None:
        self._config = config
        self._auth = auth
        self._session = requests.Session()
        self._retry_config = RetryConfig(
            max_retries=config.max_retries,
            base_delay=config.base_delay,
            max_delay=config.max_delay,
        )

    def __enter__(self) -> AdoClient:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self._session.close()

    # ── Work Items ──────────────────────────────────────────────────────

    def create_work_item(
        self,
        work_item_type: str,
        operations: list[PatchOperation],
        *,
        project: str | None = None,
    ) -> WorkItem:
        """Create a new work item.

        Args:
            work_item_type: The type name (e.g. "Bug", "Task", "User Story").
            operations: Patch operations defining field values.
            project: Project name (defaults to config.default_project).
        """
        proj = project or self._config.default_project
        url = f"{self._config.base_url}/{proj}/_apis/wit/workitems/${work_item_type}"
        body = to_json_patch(operations)
        resp = self._request(
            "POST", url, json=body, content_type="application/json-patch+json"
        )
        return _parse_work_item(resp.json())

    def get_work_item(
        self,
        work_item_id: int,
        *,
        project: str | None = None,
        expand: WorkItemExpand | None = None,
        fields: list[str] | None = None,
    ) -> WorkItem:
        """Get a single work item by ID."""
        proj = project or self._config.default_project
        url = f"{self._config.base_url}/{proj}/_apis/wit/workitems/{work_item_id}"
        params: dict[str, str] = {}
        if expand:
            params["$expand"] = expand.value
        if fields:
            params["fields"] = ",".join(fields)
        resp = self._request("GET", url, params=params)
        return _parse_work_item(resp.json())

    def update_work_item(
        self,
        work_item_id: int,
        operations: list[PatchOperation],
        *,
        project: str | None = None,
    ) -> WorkItem:
        """Update a work item with patch operations."""
        proj = project or self._config.default_project
        url = f"{self._config.base_url}/{proj}/_apis/wit/workitems/{work_item_id}"
        body = to_json_patch(operations)
        resp = self._request(
            "PATCH", url, json=body, content_type="application/json-patch+json"
        )
        return _parse_work_item(resp.json())

    def delete_work_item(
        self,
        work_item_id: int,
        *,
        project: str | None = None,
        destroy: bool = False,
    ) -> dict[str, Any]:
        """Delete (recycle) or permanently destroy a work item."""
        proj = project or self._config.default_project
        url = f"{self._config.base_url}/{proj}/_apis/wit/workitems/{work_item_id}"
        params: dict[str, str] = {}
        if destroy:
            params["destroy"] = "true"
        resp = self._request("DELETE", url, params=params)
        return resp.json()

    def get_work_items_batch(
        self,
        ids: list[int],
        *,
        project: str | None = None,
        fields: list[str] | None = None,
        expand: WorkItemExpand | None = None,
    ) -> list[WorkItem]:
        """Get multiple work items by ID in a single batch request."""
        proj = project or self._config.default_project
        url = f"{self._config.base_url}/{proj}/_apis/wit/workitemsbatch"
        body: dict[str, Any] = {"ids": ids}
        if fields:
            body["fields"] = fields
        if expand:
            body["$expand"] = expand.value
        resp = self._request("POST", url, json=body)
        return [_parse_work_item(item) for item in resp.json().get("value", [])]

    # ── WIQL ────────────────────────────────────────────────────────────

    def query_wiql(
        self,
        wiql: str,
        *,
        project: str | None = None,
        top: int | None = None,
    ) -> WiqlResult:
        """Execute a WIQL query, returning work item IDs."""
        proj = project or self._config.default_project
        url = f"{self._config.base_url}/{proj}/_apis/wit/wiql"
        params: dict[str, str] = {}
        if top is not None:
            params["$top"] = str(top)
        resp = self._request("POST", url, json={"query": wiql}, params=params)
        data = resp.json()
        return WiqlResult(
            query_type=data.get("queryType", "flat"),
            as_of=data.get("asOf", ""),
            work_item_ids=[wi["id"] for wi in data.get("workItems", [])],
        )

    def query_wiql_with_details(
        self,
        wiql: str,
        *,
        project: str | None = None,
        top: int | None = None,
        fields: list[str] | None = None,
    ) -> list[WorkItem]:
        """Execute a WIQL query and fetch full work item details.

        Two-step: WIQL query to get IDs, then batch fetch for details.
        """
        result = self.query_wiql(wiql, project=project, top=top)
        if not result.work_item_ids:
            return []
        return self.get_work_items_batch(
            result.work_item_ids, project=project, fields=fields
        )

    # ── Classification Nodes ────────────────────────────────────────────

    def list_area_paths(
        self, *, project: str | None = None, depth: int = 5
    ) -> ClassificationNode:
        """List area paths for a project."""
        return self._get_classification_nodes("areas", project=project, depth=depth)

    def list_iteration_paths(
        self, *, project: str | None = None, depth: int = 5
    ) -> ClassificationNode:
        """List iteration paths for a project."""
        return self._get_classification_nodes(
            "iterations", project=project, depth=depth
        )

    def _get_classification_nodes(
        self, structure_group: str, *, project: str | None = None, depth: int = 5
    ) -> ClassificationNode:
        proj = project or self._config.default_project
        url = (
            f"{self._config.base_url}/{proj}"
            f"/_apis/wit/classificationnodes/{structure_group}"
        )
        resp = self._request("GET", url, params={"$depth": str(depth)})
        return _parse_classification_node(resp.json())

    # ── Fields ──────────────────────────────────────────────────────────

    def list_fields(self, *, project: str | None = None) -> list[FieldDefinition]:
        """List all work item field definitions (paginated)."""
        proj = project or self._config.default_project
        url = f"{self._config.base_url}/{proj}/_apis/wit/fields"

        def request_page(continuation_token: str | None = None) -> requests.Response:
            params: dict[str, str] = {"api-version": self._config.api_version}
            if continuation_token:
                params["continuationToken"] = continuation_token
            return self._raw_request("GET", url, params=params)

        items = paginate(request_page, result_key="value")
        return [_parse_field_definition(f) for f in items]

    def create_field(
        self,
        name: str,
        reference_name: str,
        field_type: str,
        *,
        project: str | None = None,
    ) -> FieldDefinition:
        """Create a new work item field definition."""
        proj = project or self._config.default_project
        url = f"{self._config.base_url}/{proj}/_apis/wit/fields"
        body = {
            "name": name,
            "referenceName": reference_name,
            "type": field_type,
        }
        resp = self._request("POST", url, json=body)
        return _parse_field_definition(resp.json())

    # ── Comments ────────────────────────────────────────────────────────

    def get_comments(
        self,
        work_item_id: int,
        *,
        project: str | None = None,
        top: int | None = None,
    ) -> list[Comment]:
        """Get all comments for a work item.

        Note: ADO comments are HTML, not Markdown.
        """
        proj = project or self._config.default_project
        url = (
            f"{self._config.base_url}/{proj}"
            f"/_apis/wit/workitems/{work_item_id}/comments"
        )
        params: dict[str, str] = {}
        if top is not None:
            params["$top"] = str(top)
        resp = self._request("GET", url, params=params)
        return [
            _parse_comment(c, work_item_id)
            for c in resp.json().get("comments", [])
        ]

    def add_comment(
        self,
        work_item_id: int,
        text: str,
        *,
        project: str | None = None,
    ) -> Comment:
        """Add a comment to a work item.

        Args:
            work_item_id: The work item to comment on.
            text: HTML-formatted comment text. ADO does NOT support Markdown
                in comments — use HTML tags (<p>, <ul>, <strong>, etc.).
            project: Project name (defaults to config.default_project).
        """
        proj = project or self._config.default_project
        url = (
            f"{self._config.base_url}/{proj}"
            f"/_apis/wit/workitems/{work_item_id}/comments"
        )
        resp = self._request("POST", url, json={"text": text})
        return _parse_comment(resp.json(), work_item_id)

    # ── Work Item Types ─────────────────────────────────────────────────

    def list_work_item_types(
        self, *, project: str | None = None
    ) -> list[WorkItemType]:
        """List all work item types for a project."""
        proj = project or self._config.default_project
        url = f"{self._config.base_url}/{proj}/_apis/wit/workitemtypes"
        resp = self._request("GET", url)
        return [_parse_work_item_type(t) for t in resp.json().get("value", [])]

    # ── Project Inspection ───────────────────────────────────────────────

    def get_work_item_type_states(
        self,
        work_item_type: str,
        *,
        project: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get the valid states for a work item type in a project.

        ADO projects can have custom processes with different state workflows.
        Use this to discover available states before setting state fields.

        Returns a list of dicts with 'name', 'color', and 'category' keys.
        """
        proj = project or self._config.default_project
        url = (
            f"{self._config.base_url}/{proj}"
            f"/_apis/wit/workitemtypes/{work_item_type}/states"
        )
        resp = self._request("GET", url)
        return resp.json().get("value", [])

    def get_project_properties(
        self, *, project: str | None = None
    ) -> dict[str, Any]:
        """Get project properties (name, description, state, process template).

        Useful for inspecting project configuration and process customization.
        """
        proj = project or self._config.default_project
        url = f"{self._config.base_url}/_apis/projects/{proj}"
        params = {"includeCapabilities": "true"}
        resp = self._request("GET", url, params=params)
        return resp.json()

    # ── Internal request handling ───────────────────────────────────────

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        content_type: str | None = None,
    ) -> requests.Response:
        """Make a request with retry and error mapping."""
        resp = self._raw_request(
            method, url, params=params, json=json, content_type=content_type
        )
        self._raise_for_status(resp)
        return resp

    def _raw_request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        content_type: str | None = None,
    ) -> requests.Response:
        """Make a request with retry but without error mapping.

        Used by pagination which handles its own raise_for_status.
        """
        if params is None:
            params = {}
        params.setdefault("api-version", self._config.api_version)

        headers = {
            "Authorization": self._auth.get_auth_header(),
            "Accept": "application/json",
        }
        if content_type:
            headers["Content-Type"] = content_type

        def do_request() -> requests.Response:
            return self._session.request(
                method,
                url,
                params=params,
                json=json,
                headers=headers,
                timeout=self._config.timeout,
            )

        return execute_with_retry(do_request, self._retry_config)

    @staticmethod
    def _raise_for_status(response: requests.Response) -> None:
        """Map HTTP error codes to ADO exceptions."""
        status = response.status_code
        if 200 <= status < 300:
            return

        try:
            body = response.json()
        except Exception:
            body = response.text

        message = ""
        if isinstance(body, dict):
            message = body.get("message", "") or body.get("value", {}).get(
                "Message", ""
            )
        if not message:
            message = f"HTTP {status}"

        if status in (401, 403):
            raise AdoAuthError(message, status_code=status, response_body=body)
        if status == 404:
            raise AdoNotFoundError(message, status_code=status, response_body=body)
        if status == 429:
            retry_after = response.headers.get("Retry-After")
            retry_secs = None
            if retry_after:
                try:
                    retry_secs = float(retry_after)
                except ValueError:
                    pass
            raise AdoRateLimitError(
                message,
                retry_after_seconds=retry_secs,
                status_code=status,
                response_body=body,
            )
        if status == 400:
            raise AdoValidationError(message, status_code=status, response_body=body)
        if status >= 500:
            raise AdoServerError(message, status_code=status, response_body=body)

        raise AdoError(message, status_code=status, response_body=body)


# ── Response parsers ────────────────────────────────────────────────────


def _parse_work_item(data: dict) -> WorkItem:
    return WorkItem(
        id=data["id"],
        rev=data.get("rev", 0),
        url=data.get("url", ""),
        fields=data.get("fields", {}),
        relations=data.get("relations", []),
    )


def _parse_classification_node(data: dict) -> ClassificationNode:
    children = [
        _parse_classification_node(c) for c in data.get("children", [])
    ]
    return ClassificationNode(
        id=data.get("id", 0),
        name=data.get("name", ""),
        structure_type=data.get("structureType", ""),
        path=data.get("path", ""),
        has_children=data.get("hasChildren", False),
        children=children,
    )


def _parse_field_definition(data: dict) -> FieldDefinition:
    return FieldDefinition(
        name=data.get("name", ""),
        reference_name=data.get("referenceName", ""),
        type=data.get("type", ""),
        description=data.get("description", ""),
        read_only=data.get("readOnly", False),
    )


def _parse_comment(data: dict, work_item_id: int) -> Comment:
    created_by = data.get("createdBy", {})
    if isinstance(created_by, dict):
        created_by = created_by.get("displayName", "")
    return Comment(
        id=data.get("id", 0),
        work_item_id=work_item_id,
        text=data.get("text", ""),
        created_by=created_by,
        created_date=data.get("createdDate", ""),
        modified_date=data.get("modifiedDate", ""),
        version=data.get("version", 1),
    )


def _parse_work_item_type(data: dict) -> WorkItemType:
    return WorkItemType(
        name=data.get("name", ""),
        description=data.get("description", ""),
        icon_url=data.get("icon", {}).get("url", ""),
        fields=data.get("fields", []),
    )
