"""Tests for AdoClient project inspection operations."""

from __future__ import annotations

import responses

from governance.integrations.ado.tests.conftest import BASE_URL, TEST_PROJECT


class TestGetWorkItemTypeStates:
    @responses.activate
    def test_get_states(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitemtypes/Bug/states"
        resp_body = {
            "value": [
                {"name": "New", "color": "b2b2b2", "category": "Proposed"},
                {"name": "Active", "color": "007acc", "category": "InProgress"},
                {"name": "Resolved", "color": "ff9d00", "category": "Resolved"},
                {"name": "Closed", "color": "339933", "category": "Completed"},
            ]
        }
        responses.add(responses.GET, url, json=resp_body, status=200)

        states = client.get_work_item_type_states("Bug")
        assert len(states) == 4
        assert states[0]["name"] == "New"
        assert states[1]["category"] == "InProgress"
        assert states[3]["name"] == "Closed"

    @responses.activate
    def test_custom_process_states(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitemtypes/User%20Story/states"
        resp_body = {
            "value": [
                {"name": "New", "color": "b2b2b2", "category": "Proposed"},
                {"name": "Ready", "color": "007acc", "category": "InProgress"},
                {"name": "In Development", "color": "007acc", "category": "InProgress"},
                {"name": "Done", "color": "339933", "category": "Completed"},
            ]
        }
        responses.add(responses.GET, url, json=resp_body, status=200)

        states = client.get_work_item_type_states("User Story")
        state_names = [s["name"] for s in states]
        assert "Ready" in state_names
        assert "In Development" in state_names


class TestGetProjectProperties:
    @responses.activate
    def test_get_properties(self, client):
        url = f"{BASE_URL}/_apis/projects/{TEST_PROJECT}"
        resp_body = {
            "id": "abc-123",
            "name": TEST_PROJECT,
            "description": "Test project",
            "state": "wellFormed",
            "capabilities": {
                "processTemplate": {
                    "templateName": "Agile",
                    "templateTypeId": "adcc42ab-9882-485e-a3ed-7678f01f66bc",
                },
                "versioncontrol": {"sourceControlType": "Git"},
            },
        }
        responses.add(responses.GET, url, json=resp_body, status=200)

        props = client.get_project_properties()
        assert props["name"] == TEST_PROJECT
        assert props["capabilities"]["processTemplate"]["templateName"] == "Agile"
