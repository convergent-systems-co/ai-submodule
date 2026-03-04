"""Tests for retry and rate limit logic."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from governance.integrations.ado._exceptions import AdoRateLimitError, AdoServerError
from governance.integrations.ado._rate_limit import RetryConfig, execute_with_retry


def _make_response(status_code: int, headers: dict | None = None, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    resp.json.return_value = json_data or {}
    resp.text = ""
    return resp


class TestExecuteWithRetry:
    def test_success_no_retry(self):
        resp = _make_response(200)
        result = execute_with_retry(lambda: resp)
        assert result.status_code == 200

    def test_retries_on_429(self):
        fail = _make_response(429)
        success = _make_response(200)
        call_count = 0

        def request_fn():
            nonlocal call_count
            call_count += 1
            return fail if call_count < 3 else success

        config = RetryConfig(max_retries=5, base_delay=0.01, max_delay=0.02)
        result = execute_with_retry(request_fn, config)
        assert result.status_code == 200
        assert call_count == 3

    def test_retries_on_503(self):
        fail = _make_response(503)
        success = _make_response(200)
        calls = []

        def request_fn():
            calls.append(1)
            return fail if len(calls) < 2 else success

        config = RetryConfig(max_retries=3, base_delay=0.01, max_delay=0.02)
        result = execute_with_retry(request_fn, config)
        assert result.status_code == 200

    def test_exhausted_429_raises_rate_limit(self):
        resp = _make_response(429, headers={"Retry-After": "10"})
        config = RetryConfig(max_retries=2, base_delay=0.01, max_delay=0.02)
        with pytest.raises(AdoRateLimitError, match="Rate limit exceeded"):
            execute_with_retry(lambda: resp, config)

    def test_exhausted_500_raises_server_error(self):
        resp = _make_response(500)
        config = RetryConfig(max_retries=1, base_delay=0.01, max_delay=0.02)
        with pytest.raises(AdoServerError, match="Server error"):
            execute_with_retry(lambda: resp, config)

    def test_respects_retry_after_header(self):
        resp_429 = _make_response(429, headers={"Retry-After": "0.01"})
        resp_ok = _make_response(200)
        calls = []

        def request_fn():
            calls.append(1)
            return resp_429 if len(calls) == 1 else resp_ok

        config = RetryConfig(max_retries=3, base_delay=0.01, max_delay=0.02)
        result = execute_with_retry(request_fn, config)
        assert result.status_code == 200

    def test_non_retryable_status_returned_immediately(self):
        resp = _make_response(400)
        config = RetryConfig(max_retries=3, base_delay=0.01, max_delay=0.02)
        result = execute_with_retry(lambda: resp, config)
        assert result.status_code == 400

    def test_404_not_retried(self):
        call_count = 0

        def request_fn():
            nonlocal call_count
            call_count += 1
            return _make_response(404)

        config = RetryConfig(max_retries=3, base_delay=0.01, max_delay=0.02)
        result = execute_with_retry(request_fn, config)
        assert result.status_code == 404
        assert call_count == 1

    def test_rate_limit_error_includes_retry_after(self):
        resp = _make_response(429, headers={"Retry-After": "42"})
        config = RetryConfig(max_retries=0, base_delay=0.01, max_delay=0.02)
        with pytest.raises(AdoRateLimitError) as exc_info:
            execute_with_retry(lambda: resp, config)
        assert exc_info.value.retry_after_seconds == 42.0
