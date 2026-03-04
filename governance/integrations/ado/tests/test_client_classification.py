"""Tests for AdoClient classification node operations."""

from __future__ import annotations

import responses

from governance.integrations.ado.tests.conftest import (
    BASE_URL,
    TEST_PROJECT,
    make_classification_node_response,
)


class TestListAreaPaths:
    @responses.activate
    def test_flat(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/classificationnodes/areas"
        resp_body = make_classification_node_response(
            name="TestProject", path="\\TestProject"
        )
        responses.add(responses.GET, url, json=resp_body, status=200)

        node = client.list_area_paths()
        assert node.name == "TestProject"
        assert node.path == "\\TestProject"

    @responses.activate
    def test_with_children(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/classificationnodes/areas"
        child = make_classification_node_response(
            node_id=2, name="Team A", path="\\Root\\Team A"
        )
        resp_body = make_classification_node_response(
            name="Root", path="\\Root", children=[child]
        )
        responses.add(responses.GET, url, json=resp_body, status=200)

        node = client.list_area_paths()
        assert node.has_children is True
        assert len(node.children) == 1
        assert node.children[0].name == "Team A"


class TestListIterationPaths:
    @responses.activate
    def test_iterations(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/classificationnodes/iterations"
        resp_body = make_classification_node_response(
            name="Sprint 1", structure_type="iteration", path="\\Sprint 1"
        )
        responses.add(responses.GET, url, json=resp_body, status=200)

        node = client.list_iteration_paths()
        assert node.name == "Sprint 1"
        assert node.structure_type == "iteration"
