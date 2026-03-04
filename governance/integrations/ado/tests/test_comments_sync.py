"""Tests for bidirectional comment sync."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from governance.integrations.ado._types import Comment
from governance.integrations.ado.comments_sync import (
    format_ado_to_github_comment,
    format_github_to_ado_comment,
    should_sync_comment,
    sync_comment_from_ado,
    sync_comment_to_ado,
)


# ── should_sync_comment ────────────────────────────────────────────────────


class TestShouldSyncComment:
    def test_tagged_comment(self):
        assert should_sync_comment("[ado-sync] Fix the bug") is True

    def test_tagged_with_leading_whitespace(self):
        assert should_sync_comment("  [ado-sync] Fix the bug") is True

    def test_untagged_comment(self):
        assert should_sync_comment("Just a normal comment") is False

    def test_empty_body(self):
        assert should_sync_comment("") is False

    def test_none_body(self):
        assert should_sync_comment(None) is False

    def test_case_insensitive(self):
        assert should_sync_comment("[ADO-SYNC] Fix it") is True
        assert should_sync_comment("[Ado-Sync] Fix it") is True

    def test_custom_prefix(self):
        assert should_sync_comment("[sync] message", prefix="[sync]") is True
        assert should_sync_comment("[ado-sync] message", prefix="[sync]") is False

    def test_prefix_only(self):
        assert should_sync_comment("[ado-sync]") is True


# ── format_github_to_ado_comment ──────────────────────────────────────────


class TestFormatGitHubToAdoComment:
    def test_basic_format(self):
        result = format_github_to_ado_comment("octocat", "[ado-sync] Fix the issue")
        assert "<p>" in result
        assert "@octocat" in result
        assert "[ado-sync] Fix the issue" in result
        assert result.startswith("<p>")
        assert result.endswith("</p>")

    def test_html_escaping(self):
        result = format_github_to_ado_comment("user<script>", "body with <b>html</b>")
        assert "&lt;script&gt;" in result
        assert "&lt;b&gt;" in result

    def test_empty_body(self):
        result = format_github_to_ado_comment("user", "")
        assert "@user" in result


# ── format_ado_to_github_comment ──────────────────────────────────────────


class TestFormatAdoToGitHubComment:
    def test_basic_format(self):
        result = format_ado_to_github_comment("John Doe", "<p>[ado-sync] Some feedback</p>")
        assert result.startswith("[From ADO")
        assert "John Doe" in result
        assert "[ado-sync] Some feedback" in result

    def test_strips_html_tags(self):
        result = format_ado_to_github_comment("User", "<p>Hello <strong>world</strong></p>")
        assert "<p>" not in result
        assert "<strong>" not in result
        assert "Hello world" in result

    def test_handles_empty_body(self):
        result = format_ado_to_github_comment("User", "")
        assert "[From ADO" in result
        assert "User" in result


# ── sync_comment_to_ado ───────────────────────────────────────────────────


class TestSyncCommentToAdo:
    def _config(self, sync_comments=True, prefix="[ado-sync]"):
        return {
            "project": "TestProject",
            "sync": {
                "sync_comments": sync_comments,
                "comment_prefix": prefix,
            },
        }

    def _ledger(self, issue_number=42, ado_id=100, comment_mappings=None):
        mapping = {
            "github_issue_number": issue_number,
            "github_repo": "owner/repo",
            "ado_work_item_id": ado_id,
            "ado_project": "TestProject",
            "sync_direction": "github_to_ado",
            "last_synced_at": "2026-01-01T00:00:00+00:00",
            "sync_status": "active",
        }
        if comment_mappings:
            mapping["comment_mappings"] = comment_mappings
        return {"schema_version": "1.0.0", "mappings": [mapping]}

    def _comment(self, comment_id=1, body="[ado-sync] test", author="octocat"):
        return {
            "id": comment_id,
            "body": body,
            "user": {"login": author},
        }

    def test_syncs_tagged_comment(self):
        client = MagicMock()
        client.add_comment.return_value = Comment(
            id=500, work_item_id=100, text="test"
        )

        ledger = self._ledger()
        result = sync_comment_to_ado(
            42, self._comment(), ledger, client, self._config()
        )

        assert result == "500"
        client.add_comment.assert_called_once()

        # Verify comment mapping was added to ledger
        entry = ledger["mappings"][0]
        assert len(entry["comment_mappings"]) == 1
        assert entry["comment_mappings"][0]["github_comment_id"] == 1
        assert entry["comment_mappings"][0]["ado_comment_id"] == "500"

    def test_skips_when_sync_disabled(self):
        client = MagicMock()
        result = sync_comment_to_ado(
            42, self._comment(), self._ledger(), client, self._config(sync_comments=False)
        )
        assert result is None
        client.add_comment.assert_not_called()

    def test_skips_untagged_comment(self):
        client = MagicMock()
        comment = self._comment(body="Normal comment without prefix")
        result = sync_comment_to_ado(
            42, comment, self._ledger(), client, self._config()
        )
        assert result is None

    def test_skips_already_synced_comment(self):
        client = MagicMock()
        ledger = self._ledger(comment_mappings=[
            {"github_comment_id": 1, "ado_comment_id": "500", "synced_at": "2026-01-01T00:00:00+00:00"}
        ])
        result = sync_comment_to_ado(
            42, self._comment(comment_id=1), ledger, client, self._config()
        )
        assert result is None
        client.add_comment.assert_not_called()

    def test_skips_issue_not_in_ledger(self):
        client = MagicMock()
        ledger = self._ledger(issue_number=999)
        result = sync_comment_to_ado(
            42, self._comment(), ledger, client, self._config()
        )
        assert result is None

    def test_skips_comment_without_id(self):
        client = MagicMock()
        comment = {"body": "[ado-sync] test", "user": {"login": "user"}}
        result = sync_comment_to_ado(
            42, comment, self._ledger(), client, self._config()
        )
        assert result is None


# ── sync_comment_from_ado ─────────────────────────────────────────────────


class TestSyncCommentFromAdo:
    def _config(self, sync_comments=True, prefix="[ado-sync]"):
        return {
            "project": "TestProject",
            "sync": {
                "sync_comments": sync_comments,
                "comment_prefix": prefix,
            },
        }

    def _ledger(self, comment_mappings=None):
        mapping = {
            "github_issue_number": 42,
            "github_repo": "owner/repo",
            "ado_work_item_id": 100,
            "ado_project": "TestProject",
            "sync_direction": "github_to_ado",
            "last_synced_at": "2026-01-01T00:00:00+00:00",
            "sync_status": "active",
        }
        if comment_mappings:
            mapping["comment_mappings"] = comment_mappings
        return {"schema_version": "1.0.0", "mappings": [mapping]}

    def test_returns_github_comment(self):
        ado_comment = {
            "id": 500,
            "text": "<p>[ado-sync] Check this out</p>",
            "createdBy": {"displayName": "John Doe"},
        }
        result = sync_comment_from_ado(ado_comment, self._ledger(), self._config())
        assert result is not None
        assert "body" in result
        assert "John Doe" in result["body"]
        assert "[ado-sync] Check this out" in result["body"]

    def test_returns_none_when_sync_disabled(self):
        ado_comment = {
            "id": 500,
            "text": "<p>[ado-sync] test</p>",
            "createdBy": {"displayName": "User"},
        }
        result = sync_comment_from_ado(
            ado_comment, self._ledger(), self._config(sync_comments=False)
        )
        assert result is None

    def test_returns_none_for_untagged_comment(self):
        ado_comment = {
            "id": 500,
            "text": "<p>Regular comment</p>",
            "createdBy": {"displayName": "User"},
        }
        result = sync_comment_from_ado(ado_comment, self._ledger(), self._config())
        assert result is None

    def test_returns_none_for_already_synced(self):
        ado_comment = {
            "id": 500,
            "text": "<p>[ado-sync] test</p>",
            "createdBy": {"displayName": "User"},
        }
        ledger = self._ledger(comment_mappings=[
            {"github_comment_id": 1, "ado_comment_id": "500", "synced_at": "2026-01-01T00:00:00+00:00"}
        ])
        result = sync_comment_from_ado(ado_comment, ledger, self._config())
        assert result is None

    def test_handles_string_created_by(self):
        ado_comment = {
            "id": 600,
            "text": "<p>[ado-sync] msg</p>",
            "createdBy": "Plain User",
        }
        result = sync_comment_from_ado(ado_comment, self._ledger(), self._config())
        assert result is not None
        assert "Plain User" in result["body"]
