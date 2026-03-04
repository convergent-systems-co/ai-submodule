"""Tests for AdoClient field and work item type operations."""

from __future__ import annotations

import responses

from governance.integrations.ado.tests.conftest import (
    BASE_URL,
    TEST_PROJECT,
    make_field_response,
)


class TestListFields:
    @responses.activate
    def test_single_page(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/fields"
        fields = [
            make_field_response("Title", "System.Title", "string"),
            make_field_response("State", "System.State", "string"),
        ]
        responses.add(responses.GET, url, json={"value": fields}, status=200)

        result = client.list_fields()
        assert len(result) == 2
        assert result[0].name == "Title"
        assert result[1].reference_name == "System.State"

    @responses.activate
    def test_paginated(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/fields"
        page1 = [make_field_response("Field1", "Custom.F1", "string")]
        page2 = [make_field_response("Field2", "Custom.F2", "integer")]

        responses.add(
            responses.GET,
            url,
            json={"value": page1},
            status=200,
            headers={"x-ms-continuationtoken": "page2"},
        )
        responses.add(responses.GET, url, json={"value": page2}, status=200)

        result = client.list_fields()
        assert len(result) == 2
        assert result[0].name == "Field1"
        assert result[1].name == "Field2"


class TestCreateField:
    @responses.activate
    def test_create(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/fields"
        resp = make_field_response("NewField", "Custom.NewField", "string")
        responses.add(responses.POST, url, json=resp, status=200)

        field = client.create_field("NewField", "Custom.NewField", "string")
        assert field.name == "NewField"
        assert field.reference_name == "Custom.NewField"


class TestListWorkItemTypes:
    @responses.activate
    def test_list(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitemtypes"
        resp = {
            "value": [
                {"name": "Bug", "description": "A bug", "icon": {"url": "http://icon"}, "fields": []},
                {"name": "Task", "description": "A task", "icon": {"url": ""}, "fields": []},
            ]
        }
        responses.add(responses.GET, url, json=resp, status=200)

        types = client.list_work_item_types()
        assert len(types) == 2
        assert types[0].name == "Bug"
        assert types[1].name == "Task"
