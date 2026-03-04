"""Health check engine for ADO sync integration.

Runs a battery of checks (connection, custom fields, ledger integrity,
ledger recency, error queue, service hooks) and returns structured
results for CLI display or JSON emission.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from governance.integrations.ado._exceptions import (
    AdoAuthError,
    AdoError,
)

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Possible outcomes for an individual health check."""

    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


@dataclass(frozen=True)
class HealthCheckResult:
    """Result of a single health check."""

    name: str
    status: HealthStatus
    details: str


def run_health_checks(
    config: dict,
    client: Any | None,
    ledger_path: Path,
    error_log_path: Path,
) -> list[HealthCheckResult]:
    """Execute all health checks and return results.

    Args:
        config: The ``ado_integration`` dict from ``project.yaml``.
        client: An optional ``AdoClient`` instance. When ``None``,
            connection and custom-field checks are skipped with WARN.
        ledger_path: Path to the sync ledger JSON file.
        error_log_path: Path to the sync error log JSON file.

    Returns:
        A list of :class:`HealthCheckResult` in execution order.
    """
    results: list[HealthCheckResult] = []

    # 1. ADO connection check
    results.append(_check_connection(client))

    # 2. Custom fields check
    results.append(_check_custom_fields(client))

    # 3. Ledger integrity
    results.append(_check_ledger_integrity(ledger_path))

    # 4. Ledger recency
    results.append(_check_ledger_recency(ledger_path))

    # 5. Error queue
    results.append(_check_error_queue(error_log_path))

    # 6. Service hooks advisory
    results.append(_check_service_hooks(config))

    return results


# ── Individual checks ──────────────────────────────────────────────────────


def _check_connection(client: Any | None) -> HealthCheckResult:
    """Verify ADO connection by calling ``get_project_properties()``."""
    if client is None:
        return HealthCheckResult(
            name="ado_connection",
            status=HealthStatus.WARN,
            details="No ADO client provided; connection check skipped",
        )

    try:
        props = client.get_project_properties()
        project_name = props.get("name", "unknown")
        return HealthCheckResult(
            name="ado_connection",
            status=HealthStatus.PASS,
            details=f"Connected to project '{project_name}'",
        )
    except AdoAuthError as exc:
        return HealthCheckResult(
            name="ado_connection",
            status=HealthStatus.FAIL,
            details=f"Authentication failed: {exc}",
        )
    except AdoError as exc:
        return HealthCheckResult(
            name="ado_connection",
            status=HealthStatus.FAIL,
            details=f"Connection error: {exc}",
        )
    except Exception as exc:
        return HealthCheckResult(
            name="ado_connection",
            status=HealthStatus.FAIL,
            details=f"Unexpected error: {exc}",
        )


def _check_custom_fields(client: Any | None) -> HealthCheckResult:
    """Verify ``Custom.GitHubIssueUrl`` exists via ``list_fields()``."""
    if client is None:
        return HealthCheckResult(
            name="custom_fields",
            status=HealthStatus.WARN,
            details="No ADO client provided; custom field check skipped",
        )

    required_fields = ["Custom.GitHubIssueUrl", "Custom.GitHubRepo"]

    try:
        fields = client.list_fields()
        field_refs = {f.reference_name for f in fields}
        missing = [f for f in required_fields if f not in field_refs]

        if missing:
            return HealthCheckResult(
                name="custom_fields",
                status=HealthStatus.FAIL,
                details=(
                    f"Missing custom fields: {', '.join(missing)}. "
                    "Run: python bin/ado-sync.py setup-custom-fields"
                ),
            )

        return HealthCheckResult(
            name="custom_fields",
            status=HealthStatus.PASS,
            details="All required custom fields present",
        )
    except AdoError as exc:
        return HealthCheckResult(
            name="custom_fields",
            status=HealthStatus.FAIL,
            details=f"Cannot list fields: {exc}",
        )


def _check_ledger_integrity(ledger_path: Path) -> HealthCheckResult:
    """Verify all ledger entries have required keys and no orphans."""
    if not ledger_path.exists():
        return HealthCheckResult(
            name="ledger_integrity",
            status=HealthStatus.PASS,
            details="No ledger file (no syncs performed yet)",
        )

    try:
        text = ledger_path.read_text(encoding="utf-8")
        if not text.strip():
            return HealthCheckResult(
                name="ledger_integrity",
                status=HealthStatus.PASS,
                details="Ledger is empty (no syncs performed yet)",
            )

        ledger = json.loads(text)
    except json.JSONDecodeError as exc:
        return HealthCheckResult(
            name="ledger_integrity",
            status=HealthStatus.FAIL,
            details=f"Ledger JSON is malformed: {exc}",
        )
    except OSError as exc:
        return HealthCheckResult(
            name="ledger_integrity",
            status=HealthStatus.FAIL,
            details=f"Cannot read ledger file: {exc}",
        )

    mappings = ledger.get("mappings", [])
    if not mappings:
        return HealthCheckResult(
            name="ledger_integrity",
            status=HealthStatus.PASS,
            details="Ledger has 0 mappings",
        )

    issues: list[str] = []
    seen_keys: set[tuple[int, str]] = set()

    for i, mapping in enumerate(mappings):
        gh_num = mapping.get("github_issue_number")
        ado_id = mapping.get("ado_work_item_id")
        repo = mapping.get("github_repo", "")

        if gh_num is None:
            issues.append(f"mapping[{i}]: missing github_issue_number")
        if ado_id is None:
            issues.append(f"mapping[{i}]: missing ado_work_item_id")

        if gh_num is not None and repo:
            key = (gh_num, repo)
            if key in seen_keys:
                issues.append(f"mapping[{i}]: duplicate entry for issue #{gh_num} in {repo}")
            seen_keys.add(key)

    if issues:
        detail = f"{len(issues)} issue(s) in {len(mappings)} mapping(s): {issues[0]}"
        if len(issues) > 1:
            detail += f" (and {len(issues) - 1} more)"
        return HealthCheckResult(
            name="ledger_integrity",
            status=HealthStatus.FAIL,
            details=detail,
        )

    return HealthCheckResult(
        name="ledger_integrity",
        status=HealthStatus.PASS,
        details=f"{len(mappings)} mapping(s), all valid",
    )


def _check_ledger_recency(
    ledger_path: Path,
    *,
    stale_threshold_hours: int = 24,
) -> HealthCheckResult:
    """Check that the most recent ``last_synced_at`` is within threshold."""
    if not ledger_path.exists():
        return HealthCheckResult(
            name="ledger_recency",
            status=HealthStatus.PASS,
            details="No ledger file (no syncs performed yet)",
        )

    try:
        text = ledger_path.read_text(encoding="utf-8")
        if not text.strip():
            return HealthCheckResult(
                name="ledger_recency",
                status=HealthStatus.PASS,
                details="Ledger is empty",
            )
        ledger = json.loads(text)
    except (json.JSONDecodeError, OSError):
        return HealthCheckResult(
            name="ledger_recency",
            status=HealthStatus.WARN,
            details="Cannot read ledger to check recency",
        )

    mappings = ledger.get("mappings", [])
    if not mappings:
        return HealthCheckResult(
            name="ledger_recency",
            status=HealthStatus.PASS,
            details="No mappings to check",
        )

    # Find the most recent last_synced_at
    latest: datetime | None = None
    for mapping in mappings:
        ts_str = mapping.get("last_synced_at", "")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if latest is None or ts > latest:
                latest = ts
        except (ValueError, TypeError):
            continue

    if latest is None:
        return HealthCheckResult(
            name="ledger_recency",
            status=HealthStatus.WARN,
            details="No valid timestamps found in ledger mappings",
        )

    age = datetime.now(timezone.utc) - latest
    threshold = timedelta(hours=stale_threshold_hours)

    if age > threshold:
        hours_ago = age.total_seconds() / 3600
        return HealthCheckResult(
            name="ledger_recency",
            status=HealthStatus.WARN,
            details=f"Most recent sync was {hours_ago:.1f}h ago (threshold: {stale_threshold_hours}h)",
        )

    return HealthCheckResult(
        name="ledger_recency",
        status=HealthStatus.PASS,
        details=f"Most recent sync: {latest.isoformat()}",
    )


def _check_error_queue(error_log_path: Path) -> HealthCheckResult:
    """Check error log for unresolved entries."""
    if not error_log_path.exists():
        return HealthCheckResult(
            name="error_queue",
            status=HealthStatus.PASS,
            details="No error log (clean)",
        )

    try:
        text = error_log_path.read_text(encoding="utf-8")
        if not text.strip():
            return HealthCheckResult(
                name="error_queue",
                status=HealthStatus.PASS,
                details="Error log is empty",
            )
        error_log = json.loads(text)
    except json.JSONDecodeError as exc:
        return HealthCheckResult(
            name="error_queue",
            status=HealthStatus.FAIL,
            details=f"Error log JSON is malformed: {exc}",
        )
    except OSError as exc:
        return HealthCheckResult(
            name="error_queue",
            status=HealthStatus.FAIL,
            details=f"Cannot read error log: {exc}",
        )

    errors = error_log.get("errors", [])
    unresolved = [e for e in errors if not e.get("resolved", False)]
    dead_letter = [e for e in unresolved if e.get("dead_letter", False)]

    if not unresolved:
        return HealthCheckResult(
            name="error_queue",
            status=HealthStatus.PASS,
            details=f"{len(errors)} error(s), all resolved",
        )

    detail = f"{len(unresolved)} unresolved of {len(errors)} total"
    if dead_letter:
        detail += f" ({len(dead_letter)} dead-lettered)"
    detail += ". Run: python bin/ado-sync.py retry-failed"

    return HealthCheckResult(
        name="error_queue",
        status=HealthStatus.WARN,
        details=detail,
    )


def _check_service_hooks(config: dict) -> HealthCheckResult:
    """Advisory check for ADO-to-GitHub reverse sync service hooks.

    Service hook verification requires ADO admin access and cannot be
    validated from outside. This check just warns when reverse sync is
    configured so operators remember to verify hooks manually.
    """
    sync_config = config.get("sync", {})
    direction = sync_config.get("direction", "github_to_ado")

    if direction in ("ado_to_github", "bidirectional"):
        return HealthCheckResult(
            name="service_hooks",
            status=HealthStatus.WARN,
            details=(
                f"Sync direction is '{direction}' but service hook "
                "verification requires ADO admin access. Verify hooks "
                "are configured in ADO Project Settings > Service Hooks."
            ),
        )

    return HealthCheckResult(
        name="service_hooks",
        status=HealthStatus.PASS,
        details=f"Sync direction is '{direction}'; no service hooks required",
    )
