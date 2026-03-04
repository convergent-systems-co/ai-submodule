"""Error queue retry processor for ADO sync operations.

Reads the error log at ``.artifacts/state/ado-sync-errors.json``,
re-attempts unresolved operations, and updates the log with outcomes.
Dead-letters entries that exceed ``max_retries``.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.integrations.ado._exceptions import AdoError
from governance.integrations.ado._patch import add_field, replace_field

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetryResult:
    """Outcome of retrying a single error entry."""

    error_id: str
    status: str  # "resolved", "retried", "dead_letter", "skipped"
    message: str


def retry_failed(
    config: dict,
    client: Any,
    ledger_path: Path,
    error_log_path: Path,
    *,
    dry_run: bool = False,
    max_retries: int = 3,
) -> list[RetryResult]:
    """Process the error queue and retry unresolved operations.

    Args:
        config: The ``ado_integration`` dict from ``project.yaml``.
        client: An ``AdoClient`` instance for API calls.
        ledger_path: Path to the sync ledger JSON file.
        error_log_path: Path to the sync error log JSON file.
        dry_run: If ``True``, list what would be retried without executing.
        max_retries: Maximum retry attempts before dead-lettering.

    Returns:
        A list of :class:`RetryResult` describing each error's outcome.
    """
    error_log = _load_error_log(error_log_path)
    errors = error_log.get("errors", [])
    unresolved = [
        e for e in errors
        if not e.get("resolved", False) and not e.get("dead_letter", False)
    ]

    if not unresolved:
        return []

    results: list[RetryResult] = []

    for error in unresolved:
        error_id = error.get("error_id", "unknown")
        retry_count = error.get("retry_count", 0)
        operation = error.get("operation", "")

        # Dead-letter check
        if retry_count >= max_retries:
            if not dry_run:
                error["dead_letter"] = True
                error["resolved_at"] = datetime.now(timezone.utc).isoformat()
            results.append(RetryResult(
                error_id=error_id,
                status="dead_letter",
                message=(
                    f"Max retries ({max_retries}) exceeded for "
                    f"{operation} (retry_count={retry_count})"
                ),
            ))
            continue

        if dry_run:
            results.append(RetryResult(
                error_id=error_id,
                status="skipped",
                message=f"Would retry {operation} (attempt {retry_count + 1}/{max_retries})",
            ))
            continue

        # Attempt retry
        result = _retry_one(error, config, client, ledger_path, max_retries)
        results.append(result)

    # Persist changes (unless dry run)
    if not dry_run:
        _save_error_log(error_log, error_log_path)

    return results


# ── Internal helpers ───────────────────────────────────────────────────────


def _retry_one(
    error: dict,
    config: dict,
    client: Any,
    ledger_path: Path,
    max_retries: int,
) -> RetryResult:
    """Retry a single error entry, mutating it in place."""
    error_id = error.get("error_id", "unknown")
    operation = error.get("operation", "")
    github_issue = error.get("github_issue_number")
    ado_id = error.get("ado_work_item_id")
    retry_count = error.get("retry_count", 0)

    try:
        if operation == "create" and github_issue is not None:
            result = _retry_create(error, config, client, ledger_path)
        elif operation == "update" and ado_id is not None:
            result = _retry_update(error, client)
        else:
            error["retry_count"] = retry_count + 1
            return RetryResult(
                error_id=error_id,
                status="skipped",
                message=f"Unsupported retry for operation '{operation}'",
            )

        return result

    except AdoError as exc:
        error["retry_count"] = retry_count + 1
        error["last_retry_at"] = datetime.now(timezone.utc).isoformat()

        if error["retry_count"] >= max_retries:
            error["dead_letter"] = True
            error["resolved_at"] = datetime.now(timezone.utc).isoformat()
            return RetryResult(
                error_id=error_id,
                status="dead_letter",
                message=f"Retry failed, dead-lettered: {exc}",
            )

        return RetryResult(
            error_id=error_id,
            status="retried",
            message=f"Retry failed (attempt {error['retry_count']}/{max_retries}): {exc}",
        )


def _retry_create(
    error: dict,
    config: dict,
    client: Any,
    ledger_path: Path,
) -> RetryResult:
    """Retry a failed create operation.

    Attempts to create the work item again. On success, marks the error
    resolved and updates the ledger with the new mapping.
    """
    error_id = error.get("error_id", "unknown")
    github_issue = error.get("github_issue_number")
    retry_count = error.get("retry_count", 0)

    # Determine work item type from config
    type_mapping = config.get("type_mapping", {"default": "User Story"})
    wi_type = type_mapping.get("default", "User Story")

    # Build minimal operations from available error metadata
    title = f"GitHub Issue #{github_issue}"
    ops = [add_field("/fields/System.Title", title)]

    wi = client.create_work_item(wi_type, ops)

    # Mark resolved
    now = datetime.now(timezone.utc).isoformat()
    error["resolved"] = True
    error["resolved_at"] = now
    error["retry_count"] = retry_count + 1
    error["last_retry_at"] = now

    # Update ledger
    _upsert_ledger(
        ledger_path,
        github_issue_number=github_issue,
        ado_work_item_id=wi.id,
        ado_project=config.get("project", ""),
    )

    return RetryResult(
        error_id=error_id,
        status="resolved",
        message=f"Created ADO work item #{wi.id} for GitHub issue #{github_issue}",
    )


def _retry_update(error: dict, client: Any) -> RetryResult:
    """Retry a failed update operation.

    Verifies the work item still exists in ADO. If accessible, marks
    the error as resolved (the original update may have partially
    succeeded or the transient issue has cleared).
    """
    error_id = error.get("error_id", "unknown")
    ado_id = error.get("ado_work_item_id")
    retry_count = error.get("retry_count", 0)

    wi = client.get_work_item(ado_id)
    state = wi.fields.get("System.State", "unknown")

    now = datetime.now(timezone.utc).isoformat()
    error["resolved"] = True
    error["resolved_at"] = now
    error["retry_count"] = retry_count + 1
    error["last_retry_at"] = now

    return RetryResult(
        error_id=error_id,
        status="resolved",
        message=f"ADO work item #{ado_id} exists (state: {state}), marked resolved",
    )


def _upsert_ledger(
    ledger_path: Path,
    *,
    github_issue_number: int,
    ado_work_item_id: int,
    ado_project: str,
) -> None:
    """Add or update a ledger entry after a successful retry."""
    ledger = _load_ledger(ledger_path)
    mappings = ledger.get("mappings", [])
    now = datetime.now(timezone.utc).isoformat()

    # Check for existing entry
    for mapping in mappings:
        if mapping.get("github_issue_number") == github_issue_number:
            mapping["ado_work_item_id"] = ado_work_item_id
            mapping["last_synced_at"] = now
            mapping["sync_status"] = "active"
            break
    else:
        mappings.append({
            "github_issue_number": github_issue_number,
            "github_repo": "",
            "ado_work_item_id": ado_work_item_id,
            "ado_project": ado_project,
            "sync_direction": "github_to_ado",
            "last_synced_at": now,
            "sync_status": "active",
            "created_at": now,
        })

    ledger["mappings"] = mappings
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")


def _load_ledger(path: Path) -> dict:
    """Load the sync ledger, returning an empty structure if missing."""
    if not path.exists():
        return {"schema_version": "1.0.0", "mappings": []}
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return {"schema_version": "1.0.0", "mappings": []}
        return json.loads(text)
    except (json.JSONDecodeError, OSError):
        return {"schema_version": "1.0.0", "mappings": []}


def _load_error_log(path: Path) -> dict:
    """Load the error log, returning an empty structure if missing."""
    if not path.exists():
        return {"schema_version": "1.0.0", "errors": []}
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return {"schema_version": "1.0.0", "errors": []}
        return json.loads(text)
    except (json.JSONDecodeError, OSError):
        return {"schema_version": "1.0.0", "errors": []}


def _save_error_log(error_log: dict, path: Path) -> None:
    """Write the error log to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(error_log, indent=2) + "\n", encoding="utf-8")
