"""Bulk initial sync for onboarding — syncs all open issues in one pass.

Supports both GitHub-to-ADO and ADO-to-GitHub directions, with dry-run
mode, rate limiting, progress output, and date filtering.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.integrations.ado._exceptions import AdoError, AdoRateLimitError
from governance.integrations.ado._patch import add_field, add_hyperlink
from governance.integrations.ado.client import AdoClient
from governance.integrations.ado.mappers import (
    map_github_fields_to_ado_patch,
    map_github_labels_to_ado_type,
)
from governance.integrations.ado.sync_engine import SyncResult

logger = logging.getLogger(__name__)


# ── Rate limiting ──────────────────────────────────────────────────────────

_MAX_BACKOFF_RETRIES = 5
_BASE_DELAY = 2.0


def _retry_with_backoff(fn, *args, **kwargs):
    """Execute ``fn`` with exponential backoff on rate limit errors."""
    for attempt in range(_MAX_BACKOFF_RETRIES):
        try:
            return fn(*args, **kwargs)
        except AdoRateLimitError as exc:
            if attempt == _MAX_BACKOFF_RETRIES - 1:
                raise
            wait = exc.retry_after_seconds or (_BASE_DELAY * (2 ** attempt))
            logger.info("Rate limited, waiting %.1f seconds (attempt %d)", wait, attempt + 1)
            time.sleep(wait)
    # Should not reach here, but satisfy type checker
    return fn(*args, **kwargs)  # pragma: no cover


# ── Ledger helpers ─────────────────────────────────────────────────────────


def _load_ledger(ledger_path: Path) -> dict:
    """Load ledger from disk, creating a default if missing."""
    if not ledger_path.exists():
        return {"schema_version": "1.0.0", "mappings": []}
    try:
        text = ledger_path.read_text(encoding="utf-8")
        if not text.strip():
            return {"schema_version": "1.0.0", "mappings": []}
        return json.loads(text)
    except (json.JSONDecodeError, OSError):
        return {"schema_version": "1.0.0", "mappings": []}


def _save_ledger(ledger: dict, ledger_path: Path) -> None:
    """Write ledger to disk."""
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(ledger, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_error_log(error_log_path: Path) -> dict:
    """Load error log from disk."""
    if not error_log_path.exists():
        return {"schema_version": "1.0.0", "errors": []}
    try:
        text = error_log_path.read_text(encoding="utf-8")
        if not text.strip():
            return {"schema_version": "1.0.0", "errors": []}
        return json.loads(text)
    except (json.JSONDecodeError, OSError):
        return {"schema_version": "1.0.0", "errors": []}


def _save_error_log(error_log: dict, error_log_path: Path) -> None:
    """Write error log to disk."""
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    error_log_path.write_text(
        json.dumps(error_log, indent=2) + "\n",
        encoding="utf-8",
    )


def _is_in_ledger(ledger: dict, issue_number: int, repo: str) -> bool:
    """Check if a GitHub issue is already tracked in the ledger."""
    for m in ledger.get("mappings", []):
        if m.get("github_issue_number") == issue_number and m.get("github_repo") == repo:
            return True
    return False


def _is_ado_in_ledger(ledger: dict, ado_work_item_id: int) -> bool:
    """Check if an ADO work item is already tracked in the ledger."""
    for m in ledger.get("mappings", []):
        if m.get("ado_work_item_id") == ado_work_item_id:
            return True
    return False


# ── GitHub CLI helpers ─────────────────────────────────────────────────────


def _gh_list_issues(
    repo: str = "",
    since: str | None = None,
    limit: int | None = None,
) -> list[dict]:
    """List open GitHub issues using the ``gh`` CLI.

    Args:
        repo: Repository in ``owner/repo`` format.  Empty uses the current repo.
        since: ISO date string (``YYYY-MM-DD``).  Only issues created after
               this date are returned.
        limit: Maximum number of issues to return.

    Returns:
        List of issue dicts with ``number``, ``title``, ``body``, ``state``,
        ``labels``, ``createdAt`` keys.
    """
    cmd = [
        "gh", "issue", "list",
        "--state", "open",
        "--json", "number,title,body,state,labels,createdAt",
        "--limit", str(limit or 500),
    ]
    if repo:
        cmd.extend(["--repo", repo])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("gh issue list failed: %s", result.stderr)
        return []

    issues = json.loads(result.stdout)

    # Filter by since date if provided
    if since:
        try:
            since_dt = datetime.fromisoformat(since)
            if since_dt.tzinfo is None:
                since_dt = since_dt.replace(tzinfo=timezone.utc)
            filtered = []
            for issue in issues:
                created = issue.get("createdAt", "")
                if created:
                    created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if created_dt >= since_dt:
                        filtered.append(issue)
            issues = filtered
        except ValueError:
            logger.warning("Invalid --since date '%s', ignoring filter", since)

    return issues


# ── Main sync function ─────────────────────────────────────────────────────


def initial_sync(
    config: dict,
    client: AdoClient,
    ledger_path: Path,
    error_log_path: Path,
    *,
    direction: str = "github_to_ado",
    dry_run: bool = False,
    limit: int | None = None,
    since: str | None = None,
    github_repo: str = "",
) -> list[SyncResult]:
    """Perform a bulk initial sync of all open issues.

    Args:
        config: The ``ado_integration`` config dict.
        client: An ``AdoClient`` instance.
        ledger_path: Path to the sync ledger JSON file.
        error_log_path: Path to the error log JSON file.
        direction: ``"github_to_ado"`` or ``"ado_to_github"``.
        dry_run: If ``True``, list what would be synced without changes.
        limit: Maximum number of items to process.
        since: ISO date string (``YYYY-MM-DD``).  Only items created after
               this date are processed.
        github_repo: Repository in ``owner/repo`` format for GitHub operations.

    Returns:
        A list of ``SyncResult`` objects describing each operation.
    """
    if direction == "github_to_ado":
        return _sync_github_to_ado(
            config, client, ledger_path, error_log_path,
            dry_run=dry_run, limit=limit, since=since, github_repo=github_repo,
        )
    elif direction == "ado_to_github":
        return _sync_ado_to_github(
            config, client, ledger_path, error_log_path,
            dry_run=dry_run, limit=limit, since=since, github_repo=github_repo,
        )
    else:
        logger.error("Unknown direction: %s", direction)
        return [SyncResult(status="error", operation="noop", error=f"Unknown direction: {direction}")]


# ── GitHub -> ADO ──────────────────────────────────────────────────────────


def _sync_github_to_ado(
    config: dict,
    client: AdoClient,
    ledger_path: Path,
    error_log_path: Path,
    *,
    dry_run: bool = False,
    limit: int | None = None,
    since: str | None = None,
    github_repo: str = "",
) -> list[SyncResult]:
    """Sync all open GitHub issues to ADO."""
    results: list[SyncResult] = []
    ledger = _load_ledger(ledger_path)
    error_log = _load_error_log(error_log_path)

    issues = _gh_list_issues(repo=github_repo, since=since, limit=limit)
    total = len(issues)

    if limit and total > limit:
        issues = issues[:limit]
        total = limit

    project = config.get("project", "")

    for i, issue in enumerate(issues, 1):
        issue_number = issue.get("number")
        title = issue.get("title", "")
        repo = github_repo or ""

        if _is_in_ledger(ledger, issue_number, repo):
            _progress(i, total, f"Skipped GitHub #{issue_number} (already in ledger)")
            results.append(SyncResult(
                status="skipped",
                operation="noop",
            ))
            continue

        if dry_run:
            labels = _extract_labels(issue)
            wi_type = map_github_labels_to_ado_type(labels, config)
            _progress(i, total, f"[dry-run] Would create ADO {wi_type} for GitHub #{issue_number}: {title}")
            results.append(SyncResult(
                status="skipped",
                operation="noop",
            ))
            continue

        # Create ADO work item
        try:
            labels = _extract_labels(issue)
            wi_type = map_github_labels_to_ado_type(labels, config)
            ops = map_github_fields_to_ado_patch(issue, config)

            # Add hyperlink back to the GitHub issue
            html_url = issue.get("html_url", "")
            if not html_url and github_repo:
                html_url = f"https://github.com/{github_repo}/issues/{issue_number}"
            if html_url:
                ops.append(add_hyperlink(html_url, f"GitHub Issue #{issue_number}"))

            wi = _retry_with_backoff(
                client.create_work_item, wi_type, ops, project=project
            )

            # Update ledger
            now = datetime.now(timezone.utc).isoformat()
            ledger.setdefault("mappings", []).append({
                "github_issue_number": issue_number,
                "github_repo": repo,
                "ado_work_item_id": wi.id,
                "ado_project": project,
                "ado_work_item_type": wi_type,
                "sync_direction": "github_to_ado",
                "last_synced_at": now,
                "last_sync_source": "github",
                "created_at": now,
                "sync_status": "active",
            })
            _save_ledger(ledger, ledger_path)

            _progress(i, total, f"Created ADO {wi_type} #{wi.id} for GitHub #{issue_number}")
            results.append(SyncResult(
                status="created",
                operation="create",
                ado_work_item_id=wi.id,
            ))

        except AdoError as exc:
            _progress(i, total, f"Error syncing GitHub #{issue_number}: {exc}")
            _log_error(error_log, error_log_path, "create", issue_number, None, exc)
            results.append(SyncResult(
                status="error",
                operation="create",
                error=str(exc),
            ))

    return results


# ── ADO -> GitHub ──────────────────────────────────────────────────────────


def _sync_ado_to_github(
    config: dict,
    client: AdoClient,
    ledger_path: Path,
    error_log_path: Path,
    *,
    dry_run: bool = False,
    limit: int | None = None,
    since: str | None = None,
    github_repo: str = "",
) -> list[SyncResult]:
    """Sync active ADO work items to GitHub issues."""
    results: list[SyncResult] = []
    ledger = _load_ledger(ledger_path)
    error_log = _load_error_log(error_log_path)

    project = config.get("project", "")

    # Build WIQL query
    wiql = (
        "SELECT [System.Id], [System.Title], [System.Description], "
        "[System.State], [System.WorkItemType] "
        "FROM WorkItems "
        "WHERE [System.State] <> 'Closed' AND [System.State] <> 'Removed'"
    )

    # Area path filter
    area_filter = config.get("filters", {}).get("ado_area_path_filter", "")
    if area_filter:
        wiql += f" AND [System.AreaPath] UNDER '{area_filter}'"

    if since:
        wiql += f" AND [System.CreatedDate] >= '{since}'"

    wiql += " ORDER BY [System.CreatedDate] ASC"

    try:
        work_items = _retry_with_backoff(
            client.query_wiql_with_details, wiql, project=project, top=limit or 500
        )
    except AdoError as exc:
        logger.error("WIQL query failed: %s", exc)
        return [SyncResult(status="error", operation="noop", error=str(exc))]

    total = len(work_items)
    if limit and total > limit:
        work_items = work_items[:limit]
        total = limit

    for i, wi in enumerate(work_items, 1):
        ado_id = wi.id
        title = wi.fields.get("System.Title", "")
        wi_type = wi.fields.get("System.WorkItemType", "")

        if _is_ado_in_ledger(ledger, ado_id):
            _progress(i, total, f"Skipped ADO #{ado_id} (already in ledger)")
            results.append(SyncResult(
                status="skipped",
                operation="noop",
                ado_work_item_id=ado_id,
            ))
            continue

        if dry_run:
            _progress(i, total, f"[dry-run] Would create GitHub issue for ADO {wi_type} #{ado_id}: {title}")
            results.append(SyncResult(
                status="skipped",
                operation="noop",
                ado_work_item_id=ado_id,
            ))
            continue

        # Create GitHub issue via gh CLI
        try:
            description = wi.fields.get("System.Description", "") or ""
            gh_result = _gh_create_issue(
                title=title,
                body=description,
                repo=github_repo,
            )

            if gh_result is None:
                _progress(i, total, f"Error creating GitHub issue for ADO #{ado_id}")
                results.append(SyncResult(
                    status="error",
                    operation="create",
                    ado_work_item_id=ado_id,
                    error="gh issue create failed",
                ))
                continue

            issue_number = gh_result

            # Update ledger
            now = datetime.now(timezone.utc).isoformat()
            ledger.setdefault("mappings", []).append({
                "github_issue_number": issue_number,
                "github_repo": github_repo,
                "ado_work_item_id": ado_id,
                "ado_project": project,
                "ado_work_item_type": wi_type,
                "sync_direction": "ado_to_github",
                "last_synced_at": now,
                "last_sync_source": "ado",
                "created_at": now,
                "sync_status": "active",
            })
            _save_ledger(ledger, ledger_path)

            _progress(i, total, f"Created GitHub #{issue_number} for ADO {wi_type} #{ado_id}")
            results.append(SyncResult(
                status="created",
                operation="create",
                ado_work_item_id=ado_id,
            ))

        except Exception as exc:
            _progress(i, total, f"Error creating GitHub issue for ADO #{ado_id}: {exc}")
            _log_error(error_log, error_log_path, "create", None, ado_id, exc)
            results.append(SyncResult(
                status="error",
                operation="create",
                ado_work_item_id=ado_id,
                error=str(exc),
            ))

    return results


def _gh_create_issue(
    title: str,
    body: str,
    repo: str = "",
) -> int | None:
    """Create a GitHub issue using the ``gh`` CLI.

    Returns the issue number, or ``None`` on failure.
    """
    cmd = [
        "gh", "issue", "create",
        "--title", title,
        "--body", body or "(synced from Azure DevOps)",
    ]
    if repo:
        cmd.extend(["--repo", repo])

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("gh issue create failed: %s", result.stderr)
        return None

    # gh issue create prints the URL; extract issue number from it
    url = result.stdout.strip()
    try:
        return int(url.rstrip("/").split("/")[-1])
    except (ValueError, IndexError):
        logger.error("Cannot parse issue number from gh output: %s", url)
        return None


# ── Helpers ────────────────────────────────────────────────────────────────


def _extract_labels(issue: dict) -> list[str]:
    """Extract label names from a GitHub issue dict."""
    raw = issue.get("labels", [])
    names: list[str] = []
    for lbl in raw:
        if isinstance(lbl, dict):
            name = lbl.get("name", "")
        else:
            name = str(lbl)
        if name:
            names.append(name)
    return names


def _progress(current: int, total: int, message: str) -> None:
    """Print progress to stderr."""
    print(f"[{current}/{total}] {message}", file=sys.stderr)


def _log_error(
    error_log: dict,
    error_log_path: Path,
    operation: str,
    issue_number: int | None,
    ado_work_item_id: int | None,
    exc: Exception,
) -> None:
    """Append an error to the sync error log and save."""
    import uuid

    error_record = {
        "error_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "operation": operation,
        "source": "bulk_sync",
        "github_issue_number": issue_number,
        "ado_work_item_id": ado_work_item_id,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "retry_count": 0,
        "resolved": False,
    }
    error_log.setdefault("errors", []).append(error_record)
    _save_error_log(error_log, error_log_path)
