"""GitHub-to-ADO sync engine.

Processes GitHub issue webhook events and synchronises them to Azure
DevOps work items via the ``AdoClient``.  Manages a ledger of
GitHub-to-ADO mappings and an error log for failed operations.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.integrations.ado._exceptions import AdoError
from governance.integrations.ado._patch import (
    add_field,
    add_hyperlink,
    remove_field,
)
from governance.integrations.ado.client import AdoClient
from governance.integrations.ado.mappers import (
    map_github_fields_to_ado_patch,
    map_github_labels_to_ado_type,
    map_github_priority_to_ado,
    map_github_state_to_ado,
    map_github_user_to_ado,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SyncResult:
    """Outcome of a single sync operation."""

    status: str  # "created", "updated", "skipped", "error"
    operation: str  # "create", "update", "noop"
    ado_work_item_id: int | None = None
    error: str | None = None


class SyncEngine:
    """Process GitHub issue events and sync to Azure DevOps.

    Usage::

        from governance.integrations.ado.sync_engine import SyncEngine

        engine = SyncEngine(client, config, ledger_path, error_log_path)
        result = engine.sync(github_event_payload)
    """

    def __init__(
        self,
        client: AdoClient,
        config: dict,
        ledger_path: Path,
        error_log_path: Path,
    ) -> None:
        self._client = client
        self._config = config
        self._ledger_path = ledger_path
        self._error_log_path = error_log_path

    # ── Public API ────────────────────────────────────────────────────

    def sync(self, event: dict) -> SyncResult:
        """Process a GitHub issue event and sync to ADO.

        Args:
            event: The full GitHub webhook payload for an ``issues`` event.

        Returns:
            A ``SyncResult`` describing what happened.
        """
        action = event.get("action", "")
        issue = event.get("issue", {})
        issue_number = issue.get("number")
        repo_full_name = event.get("repository", {}).get("full_name", "")

        if not issue_number:
            return SyncResult(status="skipped", operation="noop", error="No issue number in event")

        labels = _extract_label_names(issue)

        # ---- Label filters ----
        if not self._passes_label_filters(labels):
            return SyncResult(status="skipped", operation="noop")

        # ---- Ledger lookup ----
        ledger = self._load_ledger()
        entry = self._find_ledger_entry(ledger, issue_number, repo_full_name)

        # ---- Echo detection ----
        if entry and self._is_echo(entry):
            logger.debug("Echo detected for issue #%s, skipping", issue_number)
            return SyncResult(
                status="skipped",
                operation="noop",
                ado_work_item_id=entry.get("ado_work_item_id"),
            )

        # ---- Dispatch by action ----
        try:
            result = self._dispatch(action, issue, entry, repo_full_name, labels)
        except AdoError as exc:
            self._log_error(
                operation="update" if entry else "create",
                issue_number=issue_number,
                ado_work_item_id=entry.get("ado_work_item_id") if entry else None,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            return SyncResult(
                status="error",
                operation="update" if entry else "create",
                ado_work_item_id=entry.get("ado_work_item_id") if entry else None,
                error=str(exc),
            )

        # ---- Update ledger ----
        if result.status in ("created", "updated") and result.ado_work_item_id:
            self._upsert_ledger_entry(
                ledger,
                issue_number=issue_number,
                repo_full_name=repo_full_name,
                ado_work_item_id=result.ado_work_item_id,
                operation=result.operation,
            )

        return result

    # ── Dispatch ──────────────────────────────────────────────────────

    def _dispatch(
        self,
        action: str,
        issue: dict,
        entry: dict | None,
        repo_full_name: str,
        labels: list[str],
    ) -> SyncResult:
        """Route to the appropriate handler based on event action."""
        handlers = {
            "opened": self._handle_opened,
            "edited": self._handle_edited,
            "closed": self._handle_closed,
            "reopened": self._handle_reopened,
            "labeled": self._handle_labeled,
            "unlabeled": self._handle_unlabeled,
            "assigned": self._handle_assigned,
            "unassigned": self._handle_unassigned,
            "milestoned": self._handle_milestoned,
            "demilestoned": self._handle_demilestoned,
        }

        handler = handlers.get(action)
        if handler is None:
            return SyncResult(status="skipped", operation="noop")

        return handler(issue, entry, repo_full_name, labels)

    # ── Event handlers ────────────────────────────────────────────────

    def _handle_opened(
        self,
        issue: dict,
        entry: dict | None,
        repo_full_name: str,
        labels: list[str],
    ) -> SyncResult:
        sync_config = self._config.get("sync", {})
        auto_create = sync_config.get("auto_create", True)

        if not auto_create:
            return SyncResult(status="skipped", operation="noop")

        if entry:
            # Already exists, treat as update
            return self._update_work_item(issue, entry, labels)

        return self._create_work_item(issue, repo_full_name, labels)

    def _handle_edited(
        self,
        issue: dict,
        entry: dict | None,
        repo_full_name: str,
        labels: list[str],
    ) -> SyncResult:
        if not entry:
            return SyncResult(status="skipped", operation="noop")
        return self._update_work_item(issue, entry, labels)

    def _handle_closed(
        self,
        issue: dict,
        entry: dict | None,
        repo_full_name: str,
        labels: list[str],
    ) -> SyncResult:
        if not entry:
            return SyncResult(status="skipped", operation="noop")
        return self._update_state(entry, "closed", labels)

    def _handle_reopened(
        self,
        issue: dict,
        entry: dict | None,
        repo_full_name: str,
        labels: list[str],
    ) -> SyncResult:
        if not entry:
            return SyncResult(status="skipped", operation="noop")
        return self._update_state(entry, "open", labels)

    def _handle_labeled(
        self,
        issue: dict,
        entry: dict | None,
        repo_full_name: str,
        labels: list[str],
    ) -> SyncResult:
        if not entry:
            return SyncResult(status="skipped", operation="noop")
        return self._update_work_item(issue, entry, labels)

    def _handle_unlabeled(
        self,
        issue: dict,
        entry: dict | None,
        repo_full_name: str,
        labels: list[str],
    ) -> SyncResult:
        if not entry:
            return SyncResult(status="skipped", operation="noop")

        # Re-evaluate priority — may need to remove it
        ops = []
        priority = map_github_priority_to_ado(labels, self._config)
        if priority is not None:
            ops.append(add_field("/fields/Microsoft.VSTS.Common.Priority", priority))
        # Re-evaluate state based on current labels
        state = issue.get("state", "open")
        ado_state = map_github_state_to_ado(state, labels, self._config)
        ops.append(add_field("/fields/System.State", ado_state))

        if not ops:
            return SyncResult(
                status="skipped",
                operation="noop",
                ado_work_item_id=entry["ado_work_item_id"],
            )

        wi = self._client.update_work_item(entry["ado_work_item_id"], ops)
        return SyncResult(
            status="updated",
            operation="update",
            ado_work_item_id=wi.id,
        )

    def _handle_assigned(
        self,
        issue: dict,
        entry: dict | None,
        repo_full_name: str,
        labels: list[str],
    ) -> SyncResult:
        if not entry:
            return SyncResult(status="skipped", operation="noop")

        assignee = issue.get("assignee")
        if not assignee:
            return SyncResult(status="skipped", operation="noop", ado_work_item_id=entry["ado_work_item_id"])

        login = assignee.get("login", "") if isinstance(assignee, dict) else str(assignee)
        ado_user = map_github_user_to_ado(login, self._config)
        if not ado_user:
            return SyncResult(status="skipped", operation="noop", ado_work_item_id=entry["ado_work_item_id"])

        ops = [add_field("/fields/System.AssignedTo", ado_user)]
        wi = self._client.update_work_item(entry["ado_work_item_id"], ops)
        return SyncResult(status="updated", operation="update", ado_work_item_id=wi.id)

    def _handle_unassigned(
        self,
        issue: dict,
        entry: dict | None,
        repo_full_name: str,
        labels: list[str],
    ) -> SyncResult:
        if not entry:
            return SyncResult(status="skipped", operation="noop")

        ops = [add_field("/fields/System.AssignedTo", "")]
        wi = self._client.update_work_item(entry["ado_work_item_id"], ops)
        return SyncResult(status="updated", operation="update", ado_work_item_id=wi.id)

    def _handle_milestoned(
        self,
        issue: dict,
        entry: dict | None,
        repo_full_name: str,
        labels: list[str],
    ) -> SyncResult:
        if not entry:
            return SyncResult(status="skipped", operation="noop")

        milestone = issue.get("milestone", {})
        milestone_title = milestone.get("title", "") if isinstance(milestone, dict) else ""
        if not milestone_title:
            return SyncResult(status="skipped", operation="noop", ado_work_item_id=entry["ado_work_item_id"])

        # Use milestone title as iteration path suffix
        project = self._config.get("project", "")
        iteration_path = f"{project}\\{milestone_title}" if project else milestone_title
        from governance.integrations.ado._patch import set_iteration_path as _set_iter
        ops = [_set_iter(iteration_path)]
        wi = self._client.update_work_item(entry["ado_work_item_id"], ops)
        return SyncResult(status="updated", operation="update", ado_work_item_id=wi.id)

    def _handle_demilestoned(
        self,
        issue: dict,
        entry: dict | None,
        repo_full_name: str,
        labels: list[str],
    ) -> SyncResult:
        if not entry:
            return SyncResult(status="skipped", operation="noop")

        # Reset to default iteration path from config
        field_mapping = self._config.get("field_mapping", {})
        default_iteration = field_mapping.get("iteration_path", "")
        if default_iteration:
            from governance.integrations.ado._patch import set_iteration_path as _set_iter
            ops = [_set_iter(default_iteration)]
        else:
            ops = [add_field("/fields/System.IterationPath", "")]

        wi = self._client.update_work_item(entry["ado_work_item_id"], ops)
        return SyncResult(status="updated", operation="update", ado_work_item_id=wi.id)

    # ── Core operations ───────────────────────────────────────────────

    def _create_work_item(
        self,
        issue: dict,
        repo_full_name: str,
        labels: list[str],
    ) -> SyncResult:
        """Create a new ADO work item from a GitHub issue."""
        work_item_type = map_github_labels_to_ado_type(labels, self._config)
        ops = map_github_fields_to_ado_patch(issue, self._config)

        # Add hyperlink back to the GitHub issue
        issue_url = issue.get("html_url", "")
        if issue_url:
            ops.append(add_hyperlink(issue_url, f"GitHub Issue #{issue.get('number', '')}"))

        project = self._config.get("project")
        wi = self._client.create_work_item(work_item_type, ops, project=project)
        return SyncResult(status="created", operation="create", ado_work_item_id=wi.id)

    def _update_work_item(
        self,
        issue: dict,
        entry: dict,
        labels: list[str],
    ) -> SyncResult:
        """Update an existing ADO work item from GitHub issue data."""
        ops = map_github_fields_to_ado_patch(issue, self._config)
        if not ops:
            return SyncResult(
                status="skipped",
                operation="noop",
                ado_work_item_id=entry["ado_work_item_id"],
            )

        wi = self._client.update_work_item(entry["ado_work_item_id"], ops)
        return SyncResult(status="updated", operation="update", ado_work_item_id=wi.id)

    def _update_state(
        self,
        entry: dict,
        github_state: str,
        labels: list[str],
    ) -> SyncResult:
        """Update only the state of an ADO work item."""
        ado_state = map_github_state_to_ado(github_state, labels, self._config)
        ops = [add_field("/fields/System.State", ado_state)]
        wi = self._client.update_work_item(entry["ado_work_item_id"], ops)
        return SyncResult(status="updated", operation="update", ado_work_item_id=wi.id)

    # ── Label filters ─────────────────────────────────────────────────

    def _passes_label_filters(self, labels: list[str]) -> bool:
        """Check if labels pass include/exclude filters."""
        filters = self._config.get("filters", {})
        include_labels = filters.get("include_labels", [])
        exclude_labels = filters.get("exclude_labels", [])

        # Exclude takes priority
        if exclude_labels:
            for label in labels:
                if label in exclude_labels:
                    return False

        # If include list is non-empty, at least one label must match
        if include_labels:
            return any(label in include_labels for label in labels)

        return True

    # ── Echo detection ────────────────────────────────────────────────

    def _is_echo(self, entry: dict) -> bool:
        """Detect if a change is an echo from a recent ADO sync."""
        if entry.get("last_sync_source") != "ado":
            return False

        grace_period = self._config.get("sync", {}).get("grace_period_seconds", 5)
        last_synced_at = entry.get("last_synced_at", "")
        if not last_synced_at:
            return False

        try:
            last_sync_time = datetime.fromisoformat(last_synced_at.replace("Z", "+00:00"))
            elapsed = (datetime.now(timezone.utc) - last_sync_time).total_seconds()
            return elapsed < grace_period
        except (ValueError, TypeError):
            return False

    # ── Ledger management ─────────────────────────────────────────────

    def _load_ledger(self) -> dict:
        """Load the sync ledger from disk, creating it if missing."""
        if not self._ledger_path.exists():
            return {"schema_version": "1.0.0", "mappings": []}

        try:
            text = self._ledger_path.read_text(encoding="utf-8")
            if not text.strip():
                return {"schema_version": "1.0.0", "mappings": []}
            return json.loads(text)
        except (json.JSONDecodeError, OSError):
            return {"schema_version": "1.0.0", "mappings": []}

    def _save_ledger(self, ledger: dict) -> None:
        """Write the sync ledger to disk, creating parent dirs if needed."""
        self._ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self._ledger_path.write_text(
            json.dumps(ledger, indent=2) + "\n",
            encoding="utf-8",
        )

    def _find_ledger_entry(
        self,
        ledger: dict,
        issue_number: int,
        repo_full_name: str,
    ) -> dict | None:
        """Find an existing ledger entry for a GitHub issue."""
        for mapping in ledger.get("mappings", []):
            if (
                mapping.get("github_issue_number") == issue_number
                and mapping.get("github_repo") == repo_full_name
            ):
                return mapping
        return None

    def _upsert_ledger_entry(
        self,
        ledger: dict,
        *,
        issue_number: int,
        repo_full_name: str,
        ado_work_item_id: int,
        operation: str,
    ) -> None:
        """Create or update a ledger mapping and persist to disk."""
        now = datetime.now(timezone.utc).isoformat()
        project = self._config.get("project", "")

        entry = self._find_ledger_entry(ledger, issue_number, repo_full_name)
        if entry:
            entry["ado_work_item_id"] = ado_work_item_id
            entry["last_synced_at"] = now
            entry["last_sync_source"] = "github"
            entry["sync_status"] = "active"
        else:
            new_entry = {
                "github_issue_number": issue_number,
                "github_repo": repo_full_name,
                "ado_work_item_id": ado_work_item_id,
                "ado_project": project,
                "sync_direction": "github_to_ado",
                "last_synced_at": now,
                "last_sync_source": "github",
                "created_at": now,
                "sync_status": "active",
            }
            ledger.setdefault("mappings", []).append(new_entry)

        self._save_ledger(ledger)

    # ── Error logging ─────────────────────────────────────────────────

    def _log_error(
        self,
        *,
        operation: str,
        issue_number: int | None = None,
        ado_work_item_id: int | None = None,
        error_type: str = "unknown",
        error_message: str = "",
    ) -> None:
        """Append an error to the sync error log."""
        error_log = self._load_error_log()

        error_record = {
            "error_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "source": "github",
            "github_issue_number": issue_number,
            "ado_work_item_id": ado_work_item_id,
            "error_type": error_type,
            "error_message": error_message,
            "retry_count": 0,
            "resolved": False,
        }
        error_log.setdefault("errors", []).append(error_record)

        self._error_log_path.parent.mkdir(parents=True, exist_ok=True)
        self._error_log_path.write_text(
            json.dumps(error_log, indent=2) + "\n",
            encoding="utf-8",
        )

        logger.warning(
            "Sync error [%s] for issue #%s: %s",
            error_type,
            issue_number,
            error_message,
        )

    def _load_error_log(self) -> dict:
        """Load the error log from disk."""
        if not self._error_log_path.exists():
            return {"schema_version": "1.0.0", "errors": []}

        try:
            text = self._error_log_path.read_text(encoding="utf-8")
            if not text.strip():
                return {"schema_version": "1.0.0", "errors": []}
            return json.loads(text)
        except (json.JSONDecodeError, OSError):
            return {"schema_version": "1.0.0", "errors": []}


# ── Helpers ──────────────────────────────────────────────────────────────


def _extract_label_names(issue: dict) -> list[str]:
    """Extract label name strings from a GitHub issue payload."""
    raw = issue.get("labels", [])
    names: list[str] = []
    for lbl in raw:
        if isinstance(lbl, dict):
            names.append(lbl.get("name", ""))
        else:
            names.append(str(lbl))
    return [n for n in names if n]
