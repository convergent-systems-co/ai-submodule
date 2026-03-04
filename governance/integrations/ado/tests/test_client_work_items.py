"""Tests for AdoClient work item operations."""

from __future__ import annotations

import responses

from governance.integrations.ado._patch import add_field
from governance.integrations.ado._types import WorkItemExpand
from governance.integrations.ado.tests.conftest import (
    BASE_URL,
    TEST_PROJECT,
    make_batch_response,
    make_work_item_response,
)


class TestCreateWorkItem:
    @responses.activate
    def test_create(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitems/$Task"
        resp_body = make_work_item_response(42, fields={"System.Title": "New Task"})
        responses.add(responses.POST, url, json=resp_body, status=200)

        ops = [add_field("/fields/System.Title", "New Task")]
        wi = client.create_work_item("Task", ops)
        assert wi.id == 42
        assert wi.fields["System.Title"] == "New Task"

    @responses.activate
    def test_create_custom_project(self, client):
        url = f"{BASE_URL}/otherproj/_apis/wit/workitems/$Bug"
        resp_body = make_work_item_response(10)
        responses.add(responses.POST, url, json=resp_body, status=200)

        ops = [add_field("/fields/System.Title", "Bug")]
        wi = client.create_work_item("Bug", ops, project="otherproj")
        assert wi.id == 10


class TestGetWorkItem:
    @responses.activate
    def test_get_by_id(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitems/1"
        resp_body = make_work_item_response(1)
        responses.add(responses.GET, url, json=resp_body, status=200)

        wi = client.get_work_item(1)
        assert wi.id == 1
        assert wi.fields["System.Title"] == "Test Work Item"

    @responses.activate
    def test_get_with_expand(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitems/1"
        resp_body = make_work_item_response(1, relations=[{"rel": "Parent", "url": "http://x"}])
        responses.add(responses.GET, url, json=resp_body, status=200)

        wi = client.get_work_item(1, expand=WorkItemExpand.RELATIONS)
        assert len(wi.relations) == 1

    @responses.activate
    def test_get_with_fields_filter(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitems/1"
        resp_body = make_work_item_response(1, fields={"System.Title": "T"})
        responses.add(responses.GET, url, json=resp_body, status=200)

        wi = client.get_work_item(1, fields=["System.Title"])
        assert wi.fields == {"System.Title": "T"}


class TestUpdateWorkItem:
    @responses.activate
    def test_update(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitems/5"
        resp_body = make_work_item_response(5, rev=2, fields={"System.State": "Active"})
        responses.add(responses.PATCH, url, json=resp_body, status=200)

        ops = [add_field("/fields/System.State", "Active")]
        wi = client.update_work_item(5, ops)
        assert wi.rev == 2


class TestDeleteWorkItem:
    @responses.activate
    def test_delete(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitems/3"
        responses.add(responses.DELETE, url, json={"id": 3}, status=200)

        result = client.delete_work_item(3)
        assert result["id"] == 3

    @responses.activate
    def test_destroy(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitems/3"
        responses.add(responses.DELETE, url, json={"id": 3}, status=200)

        result = client.delete_work_item(3, destroy=True)
        assert result["id"] == 3


class TestGetWorkItemsBatch:
    @responses.activate
    def test_batch(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitemsbatch"
        items = [make_work_item_response(i) for i in [1, 2, 3]]
        responses.add(responses.POST, url, json=make_batch_response(items), status=200)

        result = client.get_work_items_batch([1, 2, 3])
        assert len(result) == 3
        assert [wi.id for wi in result] == [1, 2, 3]

    @responses.activate
    def test_batch_empty(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitemsbatch"
        responses.add(responses.POST, url, json=make_batch_response([]), status=200)

        result = client.get_work_items_batch([])
        assert result == []
