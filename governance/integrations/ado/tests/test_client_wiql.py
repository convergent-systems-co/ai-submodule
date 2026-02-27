"""Tests for AdoClient WIQL operations."""

from __future__ import annotations

import responses

from governance.integrations.ado.tests.conftest import (
    BASE_URL,
    TEST_PROJECT,
    make_batch_response,
    make_wiql_response,
    make_work_item_response,
)


class TestQueryWiql:
    @responses.activate
    def test_basic_query(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/wiql"
        resp_body = make_wiql_response(ids=[1, 2, 3])
        responses.add(responses.POST, url, json=resp_body, status=200)

        result = client.query_wiql("SELECT [System.Id] FROM WorkItems")
        assert result.work_item_ids == [1, 2, 3]
        assert result.query_type == "flat"

    @responses.activate
    def test_empty_result(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/wiql"
        resp_body = make_wiql_response(ids=[])
        responses.add(responses.POST, url, json=resp_body, status=200)

        result = client.query_wiql("SELECT [System.Id] FROM WorkItems WHERE 1=0")
        assert result.work_item_ids == []

    @responses.activate
    def test_with_top(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/wiql"
        resp_body = make_wiql_response(ids=[1])
        responses.add(responses.POST, url, json=resp_body, status=200)

        result = client.query_wiql("SELECT [System.Id] FROM WorkItems", top=1)
        assert len(result.work_item_ids) == 1


class TestQueryWiqlWithDetails:
    @responses.activate
    def test_two_step_query(self, client):
        wiql_url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/wiql"
        batch_url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitemsbatch"

        wiql_resp = make_wiql_response(ids=[10, 20])
        responses.add(responses.POST, wiql_url, json=wiql_resp, status=200)

        items = [
            make_work_item_response(10, fields={"System.Title": "A"}),
            make_work_item_response(20, fields={"System.Title": "B"}),
        ]
        responses.add(responses.POST, batch_url, json=make_batch_response(items), status=200)

        result = client.query_wiql_with_details("SELECT [System.Id] FROM WorkItems")
        assert len(result) == 2
        assert result[0].id == 10
        assert result[1].id == 20

    @responses.activate
    def test_empty_wiql_skips_batch(self, client):
        wiql_url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/wiql"
        wiql_resp = make_wiql_response(ids=[])
        responses.add(responses.POST, wiql_url, json=wiql_resp, status=200)

        result = client.query_wiql_with_details("SELECT [System.Id] FROM WorkItems WHERE 1=0")
        assert result == []
        # Only 1 call (WIQL), no batch call
        assert len(responses.calls) == 1
