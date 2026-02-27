"""Tests for AdoClient comment operations."""

from __future__ import annotations

import responses

from governance.integrations.ado.tests.conftest import BASE_URL, TEST_PROJECT


class TestGetComments:
    @responses.activate
    def test_get_comments(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitems/42/comments"
        resp_body = {
            "totalCount": 2,
            "comments": [
                {
                    "id": 1,
                    "text": "<p>First comment</p>",
                    "createdBy": {"displayName": "Alice"},
                    "createdDate": "2026-01-01T00:00:00Z",
                    "modifiedDate": "2026-01-01T00:00:00Z",
                    "version": 1,
                },
                {
                    "id": 2,
                    "text": "<p>Second comment</p>",
                    "createdBy": {"displayName": "Bob"},
                    "createdDate": "2026-01-02T00:00:00Z",
                    "modifiedDate": "2026-01-02T00:00:00Z",
                    "version": 1,
                },
            ],
        }
        responses.add(responses.GET, url, json=resp_body, status=200)

        comments = client.get_comments(42)
        assert len(comments) == 2
        assert comments[0].text == "<p>First comment</p>"
        assert comments[0].created_by == "Alice"
        assert comments[0].work_item_id == 42
        assert comments[1].id == 2

    @responses.activate
    def test_get_comments_empty(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitems/1/comments"
        responses.add(responses.GET, url, json={"totalCount": 0, "comments": []}, status=200)

        comments = client.get_comments(1)
        assert comments == []

    @responses.activate
    def test_get_comments_with_top(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitems/1/comments"
        resp_body = {
            "comments": [
                {"id": 1, "text": "<p>Only one</p>", "createdBy": {"displayName": "X"}, "version": 1}
            ]
        }
        responses.add(responses.GET, url, json=resp_body, status=200)

        comments = client.get_comments(1, top=1)
        assert len(comments) == 1


class TestAddComment:
    @responses.activate
    def test_add_comment(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitems/42/comments"
        resp_body = {
            "id": 5,
            "text": "<p>Status update</p>",
            "createdBy": {"displayName": "Bot"},
            "createdDate": "2026-02-27T00:00:00Z",
            "modifiedDate": "2026-02-27T00:00:00Z",
            "version": 1,
        }
        responses.add(responses.POST, url, json=resp_body, status=200)

        comment = client.add_comment(42, "<p>Status update</p>")
        assert comment.id == 5
        assert comment.text == "<p>Status update</p>"
        assert comment.work_item_id == 42

    @responses.activate
    def test_add_comment_html_formatting(self, client):
        url = f"{BASE_URL}/{TEST_PROJECT}/_apis/wit/workitems/10/comments"
        html = "<h3>Review</h3><ul><li>Passed</li></ul>"
        resp_body = {
            "id": 6,
            "text": html,
            "createdBy": {"displayName": "Bot"},
            "version": 1,
        }
        responses.add(responses.POST, url, json=resp_body, status=200)

        comment = client.add_comment(10, html)
        assert "<h3>" in comment.text
