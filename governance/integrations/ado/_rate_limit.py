"""Retry logic with exponential backoff and jitter for ADO API calls."""

from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable

import requests

from governance.integrations.ado._exceptions import AdoRateLimitError, AdoServerError

# HTTP status codes eligible for retry.
RETRYABLE_STATUS_CODES = {429, 500, 502, 503}


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 30.0


def execute_with_retry(
    request_fn: Callable[[], requests.Response],
    config: RetryConfig | None = None,
) -> requests.Response:
    """Execute a request function with exponential backoff and jitter.

    Retries on 429, 500, 502, 503 status codes. Respects the Retry-After
    header when present on 429 responses.

    Args:
        request_fn: A callable that returns a requests.Response.
        config: Retry configuration. Uses defaults if not provided.

    Returns:
        The successful response.

    Raises:
        AdoRateLimitError: When retries are exhausted on 429.
        AdoServerError: When retries are exhausted on 5xx.
    """
    if config is None:
        config = RetryConfig()

    last_response: requests.Response | None = None

    for attempt in range(config.max_retries + 1):
        response = request_fn()
        last_response = response

        if response.status_code not in RETRYABLE_STATUS_CODES:
            return response

        if attempt == config.max_retries:
            break

        # Determine wait time
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after is not None:
                try:
                    wait = float(retry_after)
                except ValueError:
                    wait = _backoff_delay(attempt, config)
            else:
                wait = _backoff_delay(attempt, config)
        else:
            wait = _backoff_delay(attempt, config)

        time.sleep(wait)

    # Retries exhausted — use 'is not None' because requests.Response.__bool__
    # returns False for 4xx/5xx status codes.
    status = last_response.status_code if last_response is not None else 0
    body = _safe_response_body(last_response)

    if status == 429:
        retry_after = None
        if last_response is not None:
            raw = last_response.headers.get("Retry-After")
            if raw is not None:
                try:
                    retry_after = float(raw)
                except ValueError:
                    pass
        raise AdoRateLimitError(
            f"Rate limit exceeded after {config.max_retries} retries",
            retry_after_seconds=retry_after,
            status_code=status,
            response_body=body,
        )

    raise AdoServerError(
        f"Server error ({status}) after {config.max_retries} retries",
        status_code=status,
        response_body=body,
    )


def _backoff_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate exponential backoff with full jitter."""
    delay = min(config.base_delay * (2**attempt), config.max_delay)
    return random.uniform(0, delay)


def _safe_response_body(response: requests.Response | None):
    """Extract response body safely."""
    if response is None:
        return None
    try:
        return response.json()
    except Exception:
        return response.text
