"""Bidirectional comment sync between GitHub issues and ADO work items.

GitHub comments are Markdown; ADO comments are HTML-only.  This module
handles formatting, prefix-based filtering, and sync tracking via the
``comment_mappings`` field in ledger entries.
"""

from __future__ import annotations

import html
import logging
from datetime import datetime, timezone
from typing import Any

from governance.integrations.ado.client import AdoClient

logger = logging.getLogger(__name__)

# ── Comment filtering ──────────────────────────────────────────────────────


def should_sync_comment(body: str, prefix: str = "[ado-sync]") -> bool:
    """Check whether a comment is tagged for sync.

    Only comments whose body starts with ``prefix`` (case-insensitive)
    are eligible for cross-system sync.  This prevents infinite echo
    loops and limits noise.

    Also handles HTML-wrapped text (e.g. ``<p>[ado-sync] ...</p>``),
    since ADO comments are HTML-only.

    Args:
        body: The comment body text (Markdown or HTML).
        prefix: The sync prefix to check for (default ``[ado-sync]``).

    Returns:
        ``True`` if the comment should be synced.
    """
    if not body:
        return False
    stripped = body.lstrip()
    lowered = stripped.lower()
    prefix_lower = prefix.lower()
    if lowered.startswith(prefix_lower):
        return True
    # Also check after stripping leading HTML tags (e.g. <p>, <div>)
    import re
    text_only = re.sub(r"^(\s*<[^>]+>)+\s*", "", stripped)
    return text_only.lower().startswith(prefix_lower)


# ── Formatting ─────────────────────────────────────────────────────────────


def format_github_to_ado_comment(author: str, body: str) -> str:
    """Format a GitHub comment as HTML for ADO.

    ADO comments are HTML-only.  The result wraps the body in a ``<p>``
    tag with an attribution prefix.

    Args:
        author: GitHub username of the comment author.
        body: The Markdown comment body.

    Returns:
        HTML string suitable for ``client.add_comment()``.
    """
    escaped_body = html.escape(body)
    escaped_author = html.escape(author)
    return f"<p>[From GitHub &mdash; @{escaped_author}]: {escaped_body}</p>"


def format_ado_to_github_comment(author: str, body: str) -> str:
    """Format an ADO comment as Markdown for GitHub.

    Strips HTML from the body for a clean Markdown representation.

    Args:
        author: ADO display name of the comment author.
        body: The HTML comment body.

    Returns:
        Markdown string suitable for a GitHub issue comment.
    """
    # Basic HTML stripping — remove tags, decode entities
    import re

    stripped = re.sub(r"<[^>]+>", "", body)
    stripped = html.unescape(stripped).strip()
    return f"[From ADO — {author}]: {stripped}"


# ── Sync GitHub -> ADO ─────────────────────────────────────────────────────


def sync_comment_to_ado(
    issue_number: int,
    comment: dict,
    ledger: dict,
    client: AdoClient,
    config: dict,
) -> str | None:
    """Sync a single GitHub comment to ADO.

    Args:
        issue_number: The GitHub issue number.
        comment: A dict with at least ``id``, ``body``, and ``user.login`` keys.
        ledger: The sync ledger dict (modified in-place to add comment mapping).
        client: An ``AdoClient`` instance.
        config: The ``ado_integration`` config dict.

    Returns:
        The ADO comment ID (as string) if synced, or ``None`` if skipped.
    """
    sync_config = config.get("sync", {})
    if not sync_config.get("sync_comments", False):
        return None

    prefix = sync_config.get("comment_prefix", "[ado-sync]")
    body = comment.get("body", "")
    if not should_sync_comment(body, prefix):
        return None

    github_comment_id = comment.get("id")
    if github_comment_id is None:
        return None

    # Find the ADO work item for this issue
    mappings = ledger.get("mappings", [])
    entry = None
    for m in mappings:
        if m.get("github_issue_number") == issue_number:
            entry = m
            break

    if entry is None:
        logger.debug("Issue #%d not in ledger, skipping comment sync", issue_number)
        return None

    ado_work_item_id = entry["ado_work_item_id"]

    # Check if already synced
    comment_mappings = entry.get("comment_mappings", [])
    for cm in comment_mappings:
        if cm.get("github_comment_id") == github_comment_id:
            logger.debug(
                "GitHub comment %d already synced to ADO comment %s",
                github_comment_id,
                cm.get("ado_comment_id"),
            )
            return None

    # Format and send
    user = comment.get("user", {})
    author = user.get("login", "unknown") if isinstance(user, dict) else str(user)
    ado_html = format_github_to_ado_comment(author, body)

    project = config.get("project")
    ado_comment = client.add_comment(ado_work_item_id, ado_html, project=project)

    # Record the mapping
    now = datetime.now(timezone.utc).isoformat()
    new_mapping = {
        "github_comment_id": github_comment_id,
        "ado_comment_id": str(ado_comment.id),
        "synced_at": now,
    }
    entry.setdefault("comment_mappings", []).append(new_mapping)

    logger.info(
        "Synced GitHub comment %d to ADO comment %d on work item %d",
        github_comment_id,
        ado_comment.id,
        ado_work_item_id,
    )
    return str(ado_comment.id)


# ── Sync ADO -> GitHub ─────────────────────────────────────────────────────


def sync_comment_from_ado(
    ado_comment: dict,
    ledger: dict,
    config: dict,
) -> dict | None:
    """Prepare a GitHub comment from an ADO comment.

    Only processes comments that contain the sync prefix in their text.

    Args:
        ado_comment: A dict with ``id``, ``text``, and ``createdBy`` keys
                     (as returned by the ADO comments API).
        ledger: The sync ledger dict.
        config: The ``ado_integration`` config dict.

    Returns:
        A dict with ``body`` (Markdown string) suitable for creating a
        GitHub comment via ``gh issue comment``, or ``None`` if the
        comment should not be synced.
    """
    sync_config = config.get("sync", {})
    if not sync_config.get("sync_comments", False):
        return None

    prefix = sync_config.get("comment_prefix", "[ado-sync]")
    text = ado_comment.get("text", "")
    if not should_sync_comment(text, prefix):
        return None

    # Check if already synced (reverse direction)
    ado_comment_id = str(ado_comment.get("id", ""))
    mappings = ledger.get("mappings", [])
    for entry in mappings:
        for cm in entry.get("comment_mappings", []):
            if cm.get("ado_comment_id") == ado_comment_id:
                return None

    created_by = ado_comment.get("createdBy", {})
    if isinstance(created_by, dict):
        author = created_by.get("displayName", "unknown")
    else:
        author = str(created_by)

    body = format_ado_to_github_comment(author, text)
    return {"body": body}
