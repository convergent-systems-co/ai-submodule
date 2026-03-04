"""Pagination support for Azure DevOps API responses."""

from __future__ import annotations

from typing import Any, Callable

import requests


def paginate(
    request_fn: Callable[[str | None], requests.Response],
    result_key: str = "value",
    max_pages: int = 100,
) -> list[Any]:
    """Follow x-ms-continuationtoken headers to collect all pages.

    Args:
        request_fn: A callable that takes an optional continuation token
            and returns a requests.Response. The caller is responsible for
            including the token as a query parameter.
        result_key: The JSON key containing the result array (default: "value").
        max_pages: Safety limit on the number of pages to fetch.

    Returns:
        A concatenated list of all items across pages.
    """
    all_items: list[Any] = []
    continuation_token: str | None = None

    for _ in range(max_pages):
        response = request_fn(continuation_token)
        response.raise_for_status()

        data = response.json()
        items = data.get(result_key, [])
        all_items.extend(items)

        continuation_token = response.headers.get("x-ms-continuationtoken")
        if not continuation_token:
            break

    return all_items
