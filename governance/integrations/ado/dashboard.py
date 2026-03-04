"""Sync status dashboard emission for ADO integration.

Reads the sync ledger and error log to produce a structured status
summary suitable for CLI display, JSON output, or dashboard embedding.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def generate_dashboard_emission(
    ledger_path: Path,
    error_log_path: Path,
) -> dict:
    """Generate a sync status dashboard from ledger and error log.

    Args:
        ledger_path: Path to the sync ledger JSON file.
        error_log_path: Path to the sync error log JSON file.

    Returns:
        A dict with an ``ado_sync_status`` key containing the dashboard
        metrics. Example::

            {
              "ado_sync_status": {
                "total_mappings": 128,
                "active_mappings": 120,
                "error_mappings": 3,
                "paused_mappings": 5,
                "last_github_to_ado_sync": "2026-02-27T10:00:00+00:00",
                "last_ado_to_github_sync": null,
                "errors_today": 1,
                "dead_letter_count": 0,
                "unresolved_errors": 1,
                "total_errors": 5,
                "generated_at": "2026-02-27T12:00:00+00:00"
              }
            }
    """
    ledger = _load_json(ledger_path)
    error_log = _load_json(error_log_path)

    mappings = ledger.get("mappings", [])
    errors = error_log.get("errors", [])

    # Mapping counts by sync_status
    active_count = sum(1 for m in mappings if m.get("sync_status") == "active")
    error_count = sum(1 for m in mappings if m.get("sync_status") == "error")
    paused_count = sum(1 for m in mappings if m.get("sync_status") == "paused")

    # Most recent sync timestamps by direction
    last_gh_to_ado = _latest_timestamp(mappings, direction="github_to_ado")
    last_ado_to_gh = _latest_timestamp(mappings, direction="ado_to_github")

    # Error metrics
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    errors_today = 0
    dead_letter_count = 0
    unresolved_count = 0

    for err in errors:
        if not err.get("resolved", False):
            unresolved_count += 1
        if err.get("dead_letter", False):
            dead_letter_count += 1

        ts_str = err.get("timestamp", "")
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                if ts >= today_start:
                    errors_today += 1
            except (ValueError, TypeError):
                pass

    return {
        "ado_sync_status": {
            "total_mappings": len(mappings),
            "active_mappings": active_count,
            "error_mappings": error_count,
            "paused_mappings": paused_count,
            "last_github_to_ado_sync": last_gh_to_ado,
            "last_ado_to_github_sync": last_ado_to_gh,
            "errors_today": errors_today,
            "dead_letter_count": dead_letter_count,
            "unresolved_errors": unresolved_count,
            "total_errors": len(errors),
            "generated_at": now.isoformat(),
        },
    }


# ── Internal helpers ───────────────────────────────────────────────────────


def _load_json(path: Path) -> dict:
    """Load a JSON file, returning an empty dict structure on failure."""
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            return {}
        return json.loads(text)
    except (json.JSONDecodeError, OSError):
        return {}


def _latest_timestamp(
    mappings: list[dict],
    *,
    direction: str,
) -> str | None:
    """Find the most recent ``last_synced_at`` for a given sync direction."""
    latest: datetime | None = None

    for m in mappings:
        if m.get("sync_direction") != direction:
            continue
        ts_str = m.get("last_synced_at", "")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            if latest is None or ts > latest:
                latest = ts
        except (ValueError, TypeError):
            continue

    return latest.isoformat() if latest else None
