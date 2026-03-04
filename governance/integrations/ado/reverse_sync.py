"""ADO-to-GitHub reverse sync engine.

Processes Azure DevOps work item webhook payloads (delivered via
``repository_dispatch``) and synchronises changes back to GitHub
issues.  Manages the same shared ledger and error log as the
forward ``SyncEngine``.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from governance.integrations.ado.reverse_mappers import (
    map_ado_fields_to_github,
    map_ado_state_to_github,
)
from governance.integrations.ado.sync_engine import SyncResult

logger = logging.getLogger(__name__)


class ReverseSyncEngine:
    """Process ADO work item events and sync to GitHub issues.

    Usage::

        from governance.integrations.ado.reverse_sync import ReverseSyncEngine

        engine = ReverseSyncEngine(
            config=ado_config_data,
            github_token="ghp_...",
            github_repo="owner/repo",
            ledger_path=Path(".artifacts/state/ado-sync-ledger.json"),
            error_log_path=Path(".artifacts/state/ado-sync-errors.json"),
        )
        result = engine.sync(ado_webhook_payload)
    """

    def __init__(
        self,
        config: dict,
        github_token: str,
        github_repo: str,
        ledger_path: Path,
        error_log_path: Path,
    ) -> None:
        self._config = config
        self._github_token = github_token
        self._github_repo = github_repo
        self._ledger_path = ledger_path
        self._error_log_path = error_log_path

    # -- Public API --------------------------------------------------------

    def sync(self, payload: dict) -> SyncResult:
        """Process an ADO webhook payload and sync to GitHub.

        The payload is expected to be the ``client_payload`` from a
        GitHub ``repository_dispatch`` event, which wraps an ADO
        Service Hook notification.

        Args:
            payload: The ADO webhook payload.  Expected shape::

                {
                    "eventType": "workitem.updated",
                    "resource": {
                        "id": 42,
                        "workItemId": 42,
                        "revision": { "fields": { ... } },
                        "fields": { "System.State": { "oldValue": "New", "newValue": "Active" } }
                    }
                }

        Returns:
            A ``SyncResult`` describing what happened.
        """
        event_type = payload.get("eventType", "")
        resource = payload.get("resource", {})

        work_item_id = resource.get("workItemId") or resource.get("id")
        if not work_item_id:
            return SyncResult(
                status="skipped",
                operation="noop",
                error="No work item ID in payload",
            )

        # -- Ledger lookup --
        ledger = self._load_ledger()
        entry = self._find_ledger_entry_by_ado_id(ledger, work_item_id)

        if not entry:
            logger.debug(
                "No ledger entry for ADO work item %s, skipping reverse sync",
                work_item_id,
            )
            return SyncResult(
                status="skipped",
                operation="noop",
                ado_work_item_id=work_item_id,
                error="No ledger entry for this ADO work item",
            )

        issue_number = entry["github_issue_number"]
        repo = entry.get("github_repo", self._github_repo)

        # -- Echo detection --
        if self._is_echo(entry):
            logger.debug(
                "Echo detected for ADO work item %s (issue #%s), skipping",
                work_item_id,
                issue_number,
            )
            return SyncResult(
                status="skipped",
                operation="noop",
                ado_work_item_id=work_item_id,
            )

        # -- Dispatch by event type --
        try:
            if event_type == "workitem.created":
                result = self._handle_created(resource, entry, issue_number, repo)
            elif event_type == "workitem.updated":
                result = self._handle_updated(resource, entry, issue_number, repo)
            elif event_type == "workitem.deleted":
                result = self._handle_deleted(resource, entry, issue_number, repo)
            else:
                return SyncResult(
                    status="skipped",
                    operation="noop",
                    ado_work_item_id=work_item_id,
                )
        except Exception as exc:
            self._log_error(
                operation="reverse_sync",
                issue_number=issue_number,
                ado_work_item_id=work_item_id,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            return SyncResult(
                status="error",
                operation="update",
                ado_work_item_id=work_item_id,
                error=str(exc),
            )

        # -- Update ledger --
        if result.status in ("created", "updated"):
            self._upsert_ledger_entry(
                ledger,
                issue_number=issue_number,
                repo_full_name=repo,
                ado_work_item_id=work_item_id,
                operation=result.operation,
            )

        return result

    # -- Event handlers ----------------------------------------------------

    def _handle_created(
        self,
        resource: dict,
        entry: dict,
        issue_number: int,
        repo: str,
    ) -> SyncResult:
        """Handle workitem.created — update the linked GitHub issue with current fields."""
        work_item_id = resource.get("workItemId") or resource.get("id")
        revision = resource.get("revision", {})
        fields = revision.get("fields", {})

        if not fields:
            return SyncResult(
                status="skipped",
                operation="noop",
                ado_work_item_id=work_item_id,
            )

        updates = map_ado_fields_to_github(fields, self._config)
        self._apply_github_updates(issue_number, repo, updates)

        return SyncResult(
            status="updated",
            operation="update",
            ado_work_item_id=work_item_id,
        )

    def _handle_updated(
        self,
        resource: dict,
        entry: dict,
        issue_number: int,
        repo: str,
    ) -> SyncResult:
        """Handle workitem.updated — detect changed fields and sync to GitHub."""
        work_item_id = resource.get("workItemId") or resource.get("id")

        # ADO updated events have a "fields" dict where each key maps to
        # {"oldValue": ..., "newValue": ...}
        changed_fields_raw = resource.get("fields", {})
        if not changed_fields_raw:
            return SyncResult(
                status="skipped",
                operation="noop",
                ado_work_item_id=work_item_id,
            )

        # Extract the new values
        changed_fields: dict[str, Any] = {}
        for field_name, change in changed_fields_raw.items():
            if isinstance(change, dict) and "newValue" in change:
                changed_fields[field_name] = change["newValue"]
            else:
                # Some payloads may include the value directly
                changed_fields[field_name] = change

        if not changed_fields:
            return SyncResult(
                status="skipped",
                operation="noop",
                ado_work_item_id=work_item_id,
            )

        updates = map_ado_fields_to_github(changed_fields, self._config)
        if not updates:
            return SyncResult(
                status="skipped",
                operation="noop",
                ado_work_item_id=work_item_id,
            )

        self._apply_github_updates(issue_number, repo, updates)

        return SyncResult(
            status="updated",
            operation="update",
            ado_work_item_id=work_item_id,
        )

    def _handle_deleted(
        self,
        resource: dict,
        entry: dict,
        issue_number: int,
        repo: str,
    ) -> SyncResult:
        """Handle workitem.deleted — close the linked GitHub issue."""
        work_item_id = resource.get("workItemId") or resource.get("id")

        self._github_api(
            "PATCH",
            f"/repos/{repo}/issues/{issue_number}",
            json={"state": "closed"},
        )

        # Add a comment noting the ADO work item was deleted
        self._github_api(
            "POST",
            f"/repos/{repo}/issues/{issue_number}/comments",
            json={
                "body": (
                    f"ADO work item #{work_item_id} was deleted. "
                    "Closing this issue."
                ),
            },
        )

        return SyncResult(
            status="updated",
            operation="update",
            ado_work_item_id=work_item_id,
        )

    # -- GitHub API --------------------------------------------------------

    def _apply_github_updates(
        self,
        issue_number: int,
        repo: str,
        updates: dict,
    ) -> None:
        """Apply mapped field updates to a GitHub issue."""
        patch_body: dict[str, Any] = {}
        labels_add: list[str] = []
        labels_remove: list[str] = []

        if "title" in updates:
            patch_body["title"] = updates["title"]

        if "body" in updates:
            patch_body["body"] = updates["body"]

        if "assignees" in updates:
            patch_body["assignees"] = updates["assignees"]

        if "state" in updates:
            state_result = updates["state"]
            action = state_result.get("action", "noop")
            if action == "close":
                patch_body["state"] = "closed"
            elif action == "reopen":
                patch_body["state"] = "open"
            labels_add.extend(state_result.get("labels_add", []))
            labels_remove.extend(state_result.get("labels_remove", []))

        if "priority_label" in updates:
            # Remove existing priority labels and add the new one
            field_mapping = self._config.get("field_mapping", {})
            priority_labels = field_mapping.get("priority_labels", {})
            for existing_label in priority_labels:
                if existing_label != updates["priority_label"]:
                    labels_remove.append(existing_label)
            labels_add.append(updates["priority_label"])

        # Apply the issue patch
        if patch_body:
            self._github_api(
                "PATCH",
                f"/repos/{repo}/issues/{issue_number}",
                json=patch_body,
            )

        # Apply label changes
        for label in labels_add:
            self._github_api(
                "POST",
                f"/repos/{repo}/issues/{issue_number}/labels",
                json={"labels": [label]},
            )

        for label in labels_remove:
            # DELETE label — 404 is fine (label not present)
            self._github_api(
                "DELETE",
                f"/repos/{repo}/issues/{issue_number}/labels/{label}",
                ignore_404=True,
            )

    def _github_api(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        ignore_404: bool = False,
    ) -> dict | None:
        """Make a GitHub REST API request.

        Uses ``requests`` if available, otherwise falls back to the
        ``gh`` CLI.
        """
        try:
            return self._github_api_requests(method, path, json=json, ignore_404=ignore_404)
        except ImportError:
            return self._github_api_cli(method, path, json=json, ignore_404=ignore_404)

    def _github_api_requests(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        ignore_404: bool = False,
    ) -> dict | None:
        """GitHub API via requests library."""
        import requests

        url = f"https://api.github.com{path}"
        headers = {
            "Authorization": f"Bearer {self._github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        resp = requests.request(method, url, headers=headers, json=json, timeout=30)

        if ignore_404 and resp.status_code == 404:
            return None

        if resp.status_code >= 400:
            raise RuntimeError(
                f"GitHub API error: {resp.status_code} {resp.text}"
            )

        if resp.status_code == 204 or not resp.content:
            return None

        return resp.json()

    def _github_api_cli(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        ignore_404: bool = False,
    ) -> dict | None:
        """GitHub API via gh CLI (fallback)."""
        import subprocess

        cmd = ["gh", "api", "-X", method, path]
        if json:
            import json as json_module
            cmd.extend(["-H", "Accept: application/vnd.github+json"])
            cmd.extend(["--input", "-"])
            input_data = json_module.dumps(json).encode()
        else:
            input_data = None

        result = subprocess.run(
            cmd,
            capture_output=True,
            input=input_data,
            timeout=30,
        )

        if ignore_404 and result.returncode != 0 and b"404" in result.stderr:
            return None

        if result.returncode != 0:
            raise RuntimeError(
                f"gh CLI error: {result.stderr.decode()}"
            )

        if not result.stdout.strip():
            return None

        import json as json_module
        return json_module.loads(result.stdout)

    # -- Echo detection ----------------------------------------------------

    def _is_echo(self, entry: dict) -> bool:
        """Detect if a change is an echo from a recent GitHub sync.

        If the last sync was from GitHub and occurred within the grace
        period, this ADO event is likely an echo of that sync.
        """
        if entry.get("last_sync_source") != "github":
            return False

        grace_period = self._config.get("sync", {}).get("grace_period_seconds", 5)
        last_synced_at = entry.get("last_synced_at", "")
        if not last_synced_at:
            return False

        try:
            last_sync_time = datetime.fromisoformat(
                last_synced_at.replace("Z", "+00:00")
            )
            elapsed = (datetime.now(timezone.utc) - last_sync_time).total_seconds()
            return elapsed < grace_period
        except (ValueError, TypeError):
            return False

    # -- Ledger management -------------------------------------------------

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

    def _find_ledger_entry_by_ado_id(
        self,
        ledger: dict,
        ado_work_item_id: int,
    ) -> dict | None:
        """Find an existing ledger entry by ADO work item ID."""
        for mapping in ledger.get("mappings", []):
            if mapping.get("ado_work_item_id") == ado_work_item_id:
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
        """Update a ledger mapping with reverse sync metadata and persist."""
        now = datetime.now(timezone.utc).isoformat()

        entry = self._find_ledger_entry_by_ado_id(ledger, ado_work_item_id)
        if entry:
            entry["last_synced_at"] = now
            entry["last_sync_source"] = "ado"
            entry["sync_status"] = "active"
        else:
            project = self._config.get("project", "")
            new_entry = {
                "github_issue_number": issue_number,
                "github_repo": repo_full_name,
                "ado_work_item_id": ado_work_item_id,
                "ado_project": project,
                "sync_direction": "bidirectional",
                "last_synced_at": now,
                "last_sync_source": "ado",
                "created_at": now,
                "sync_status": "active",
            }
            ledger.setdefault("mappings", []).append(new_entry)

        self._save_ledger(ledger)

    # -- Error logging -----------------------------------------------------

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
            "source": "ado",
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
            "Reverse sync error [%s] for ADO work item #%s: %s",
            error_type,
            ado_work_item_id,
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
