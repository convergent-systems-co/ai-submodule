"""Shared fixtures for ADO client tests."""

from __future__ import annotations

import pytest

from governance.integrations.ado._rate_limit import RetryConfig
from governance.integrations.ado.auth import PatAuth
from governance.integrations.ado.client import AdoClient
from governance.integrations.ado.config import AdoConfig

TEST_ORG = "testorg"
TEST_PROJECT = "testproject"
TEST_PAT = "test-pat-token-value"
BASE_URL = f"https://dev.azure.com/{TEST_ORG}"


@pytest.fixture
def ado_config() -> AdoConfig:
    return AdoConfig(
        organization=TEST_ORG,
        default_project=TEST_PROJECT,
        max_retries=0,
        base_delay=0.01,
        max_delay=0.05,
        timeout=5.0,
    )


@pytest.fixture
def pat_auth() -> PatAuth:
    return PatAuth(TEST_PAT)


@pytest.fixture
def client(ado_config, pat_auth) -> AdoClient:
    c = AdoClient(ado_config, pat_auth)
    yield c
    c.close()


@pytest.fixture
def fast_retry_config() -> RetryConfig:
    return RetryConfig(max_retries=3, base_delay=0.01, max_delay=0.05)


def make_work_item_response(
    work_item_id: int = 1,
    rev: int = 1,
    fields: dict | None = None,
    relations: list | None = None,
) -> dict:
    """Factory for work item API response payloads."""
    return {
        "id": work_item_id,
        "rev": rev,
        "url": f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitems/{work_item_id}",
        "fields": fields or {"System.Title": "Test Work Item"},
        "relations": relations or [],
    }


def make_wiql_response(
    ids: list[int] | None = None,
    query_type: str = "flat",
    as_of: str = "2026-01-01T00:00:00Z",
) -> dict:
    """Factory for WIQL query response payloads."""
    work_items = [{"id": i, "url": f"{BASE_URL}/_apis/wit/workitems/{i}"} for i in (ids or [])]
    return {
        "queryType": query_type,
        "asOf": as_of,
        "workItems": work_items,
    }


def make_batch_response(items: list[dict]) -> dict:
    """Factory for batch work items response."""
    return {"count": len(items), "value": items}


def make_classification_node_response(
    node_id: int = 1,
    name: str = "Root",
    structure_type: str = "area",
    path: str = "\\Root",
    children: list | None = None,
) -> dict:
    """Factory for classification node response."""
    resp = {
        "id": node_id,
        "name": name,
        "structureType": structure_type,
        "path": path,
        "hasChildren": bool(children),
    }
    if children:
        resp["children"] = children
    return resp


def make_field_response(
    name: str = "Custom.Field",
    reference_name: str = "Custom.Field",
    field_type: str = "string",
) -> dict:
    """Factory for field definition response."""
    return {
        "name": name,
        "referenceName": reference_name,
        "type": field_type,
        "description": "",
        "readOnly": False,
    }
