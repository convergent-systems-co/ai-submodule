"""Tests for pagination helper."""

from __future__ import annotations

from unittest.mock import MagicMock

from governance.integrations.ado._pagination import paginate


def _make_page_response(items: list, continuation_token: str | None = None):
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"value": items}
    resp.headers = {}
    if continuation_token:
        resp.headers["x-ms-continuationtoken"] = continuation_token
    resp.raise_for_status = MagicMock()
    return resp


class TestPaginate:
    def test_single_page(self):
        page = _make_page_response([{"id": 1}, {"id": 2}])
        result = paginate(lambda token: page)
        assert len(result) == 2

    def test_multiple_pages(self):
        page1 = _make_page_response([{"id": 1}], continuation_token="page2")
        page2 = _make_page_response([{"id": 2}], continuation_token="page3")
        page3 = _make_page_response([{"id": 3}])

        pages = [page1, page2, page3]
        call_idx = 0

        def request_fn(token):
            nonlocal call_idx
            resp = pages[call_idx]
            call_idx += 1
            return resp

        result = paginate(request_fn)
        assert len(result) == 3
        assert [r["id"] for r in result] == [1, 2, 3]

    def test_empty_page(self):
        page = _make_page_response([])
        result = paginate(lambda token: page)
        assert result == []

    def test_max_pages_limit(self):
        """Stops after max_pages even if continuation tokens keep coming."""
        page = _make_page_response([{"id": 1}], continuation_token="next")
        call_count = 0

        def request_fn(token):
            nonlocal call_count
            call_count += 1
            return page

        result = paginate(request_fn, max_pages=3)
        assert call_count == 3
        assert len(result) == 3

    def test_custom_result_key(self):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"items": [{"name": "a"}]}
        resp.headers = {}
        resp.raise_for_status = MagicMock()

        result = paginate(lambda token: resp, result_key="items")
        assert result == [{"name": "a"}]

    def test_continuation_token_passed(self):
        """Verify the continuation token is forwarded to request_fn."""
        page1 = _make_page_response([{"id": 1}], continuation_token="tok123")
        page2 = _make_page_response([{"id": 2}])

        received_tokens = []

        def request_fn(token):
            received_tokens.append(token)
            return page1 if token is None else page2

        paginate(request_fn)
        assert received_tokens == [None, "tok123"]
