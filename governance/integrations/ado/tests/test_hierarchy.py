"""Tests for parent-child hierarchy sync."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from governance.integrations.ado._types import WorkItem
from governance.integrations.ado.hierarchy import (
    parse_child_references,
    parse_parent_reference,
    sync_hierarchy_from_ado,
    sync_hierarchy_to_ado,
    validate_type_hierarchy,
)


# ── parse_parent_reference ──────────────────────────────────────────────────


class TestParseParentReference:
    def test_basic_parent(self):
        assert parse_parent_reference("parent: #42") == 42

    def test_parent_in_body(self):
        body = "Some issue description.\n\nparent: #100\n\nMore details."
        assert parse_parent_reference(body) == 100

    def test_no_parent(self):
        assert parse_parent_reference("No parent reference here.") is None

    def test_empty_body(self):
        assert parse_parent_reference("") is None

    def test_none_body(self):
        assert parse_parent_reference(None) is None

    def test_case_insensitive(self):
        assert parse_parent_reference("Parent: #7") == 7
        assert parse_parent_reference("PARENT: #7") == 7

    def test_no_space_after_colon(self):
        # The regex uses \s* so no space is accepted too
        assert parse_parent_reference("parent:#42") == 42

    def test_inline_parent_not_matched(self):
        """parent: must be on its own line."""
        assert parse_parent_reference("See parent: #42 for context") is None


# ── parse_child_references ──────────────────────────────────────────────────


class TestParseChildReferences:
    def test_single_child(self):
        assert parse_child_references("child: #10") == [10]

    def test_multiple_children(self):
        assert parse_child_references("child: #10, #20, #30") == [10, 20, 30]

    def test_children_keyword(self):
        assert parse_child_references("children: #5, #6") == [5, 6]

    def test_no_children(self):
        assert parse_child_references("No children here.") == []

    def test_empty_body(self):
        assert parse_child_references("") == []

    def test_none_body(self):
        assert parse_child_references(None) == []

    def test_child_in_body(self):
        body = "Description text.\n\nchild: #1, #2\n\nEnd."
        assert parse_child_references(body) == [1, 2]

    def test_case_insensitive(self):
        assert parse_child_references("Child: #3") == [3]
        assert parse_child_references("CHILDREN: #3, #4") == [3, 4]


# ── validate_type_hierarchy ─────────────────────────────────────────────────


class TestValidateTypeHierarchy:
    def test_valid_epic_to_feature(self):
        assert validate_type_hierarchy("Epic", "Feature") is True

    def test_valid_feature_to_story(self):
        assert validate_type_hierarchy("Feature", "User Story") is True

    def test_valid_story_to_task(self):
        assert validate_type_hierarchy("User Story", "Task") is True

    def test_valid_epic_to_task(self):
        assert validate_type_hierarchy("Epic", "Task") is True

    def test_invalid_task_to_epic(self):
        assert validate_type_hierarchy("Task", "Epic") is False

    def test_invalid_same_level(self):
        assert validate_type_hierarchy("User Story", "Bug") is False

    def test_unknown_type_returns_true(self):
        assert validate_type_hierarchy("Custom Type", "Task") is True

    def test_both_unknown_returns_true(self):
        assert validate_type_hierarchy("Foo", "Bar") is True

    def test_warns_on_violation(self, caplog):
        with caplog.at_level(logging.WARNING):
            validate_type_hierarchy("Task", "Epic")
        assert "Hierarchy violation" in caplog.text


# ── sync_hierarchy_to_ado ───────────────────────────────────────────────────


class TestSyncHierarchyToAdo:
    def _make_ledger(self, mappings):
        return {"schema_version": "1.0.0", "mappings": mappings}

    def _make_mapping(self, issue_number, ado_id):
        return {
            "github_issue_number": issue_number,
            "github_repo": "owner/repo",
            "ado_work_item_id": ado_id,
            "ado_project": "TestProject",
            "sync_direction": "github_to_ado",
            "last_synced_at": "2026-01-01T00:00:00+00:00",
            "sync_status": "active",
        }

    def _config(self):
        return {
            "organization": "testorg",
            "project": "TestProject",
        }

    def test_creates_parent_link(self):
        client = MagicMock()
        client.update_work_item.return_value = WorkItem(id=100, rev=2, url="")

        ledger = self._make_ledger([
            self._make_mapping(10, 100),
            self._make_mapping(5, 50),
        ])

        actions = sync_hierarchy_to_ado(
            issue_number=10,
            parent_issue=5,
            children=[],
            ledger=ledger,
            client=client,
            config=self._config(),
        )

        assert len(actions) == 1
        assert "child of ADO #50" in actions[0]
        client.update_work_item.assert_called_once()

        # Verify the relation type
        call_args = client.update_work_item.call_args
        ops = call_args[0][1]
        assert ops[0].path == "/relations/-"
        assert ops[0].value["rel"] == "System.LinkTypes.Hierarchy-Reverse"

    def test_creates_child_links(self):
        client = MagicMock()
        client.update_work_item.return_value = WorkItem(id=100, rev=2, url="")

        ledger = self._make_ledger([
            self._make_mapping(10, 100),
            self._make_mapping(20, 200),
            self._make_mapping(30, 300),
        ])

        actions = sync_hierarchy_to_ado(
            issue_number=10,
            parent_issue=None,
            children=[20, 30],
            ledger=ledger,
            client=client,
            config=self._config(),
        )

        assert len(actions) == 2
        assert client.update_work_item.call_count == 2

    def test_skips_unmapped_parent(self):
        client = MagicMock()
        ledger = self._make_ledger([self._make_mapping(10, 100)])

        actions = sync_hierarchy_to_ado(
            issue_number=10,
            parent_issue=999,
            children=[],
            ledger=ledger,
            client=client,
            config=self._config(),
        )

        assert len(actions) == 0
        client.update_work_item.assert_not_called()

    def test_skips_if_current_issue_not_in_ledger(self):
        client = MagicMock()
        ledger = self._make_ledger([])

        actions = sync_hierarchy_to_ado(
            issue_number=999,
            parent_issue=5,
            children=[],
            ledger=ledger,
            client=client,
            config=self._config(),
        )

        assert len(actions) == 0

    def test_no_parent_no_children(self):
        client = MagicMock()
        ledger = self._make_ledger([self._make_mapping(10, 100)])

        actions = sync_hierarchy_to_ado(
            issue_number=10,
            parent_issue=None,
            children=[],
            ledger=ledger,
            client=client,
            config=self._config(),
        )

        assert len(actions) == 0
        client.update_work_item.assert_not_called()


# ── sync_hierarchy_from_ado ─────────────────────────────────────────────────


class TestSyncHierarchyFromAdo:
    def _make_ledger(self, mappings):
        return {"schema_version": "1.0.0", "mappings": mappings}

    def _make_mapping(self, issue_number, ado_id):
        return {
            "github_issue_number": issue_number,
            "github_repo": "owner/repo",
            "ado_work_item_id": ado_id,
            "ado_project": "TestProject",
            "sync_direction": "github_to_ado",
            "last_synced_at": "2026-01-01T00:00:00+00:00",
            "sync_status": "active",
        }

    def test_extracts_parent_and_children(self):
        ledger = self._make_ledger([
            self._make_mapping(10, 100),
            self._make_mapping(20, 200),
            self._make_mapping(30, 300),
        ])

        ado_item = {
            "id": 100,
            "relations": [
                {
                    "rel": "System.LinkTypes.Hierarchy-Reverse",
                    "url": "https://dev.azure.com/org/proj/_apis/wit/workitems/200",
                },
                {
                    "rel": "System.LinkTypes.Hierarchy-Forward",
                    "url": "https://dev.azure.com/org/proj/_apis/wit/workitems/300",
                },
            ],
        }

        result = sync_hierarchy_from_ado(ado_item, ledger)
        assert result["parent_ref"] == "#20"
        assert result["child_refs"] == ["#30"]

    def test_no_relations(self):
        ledger = self._make_ledger([self._make_mapping(10, 100)])
        result = sync_hierarchy_from_ado({"id": 100, "relations": []}, ledger)
        assert result["parent_ref"] is None
        assert result["child_refs"] == []

    def test_unmapped_relations_ignored(self):
        ledger = self._make_ledger([self._make_mapping(10, 100)])
        ado_item = {
            "id": 100,
            "relations": [
                {
                    "rel": "System.LinkTypes.Hierarchy-Reverse",
                    "url": "https://dev.azure.com/org/proj/_apis/wit/workitems/999",
                },
            ],
        }
        result = sync_hierarchy_from_ado(ado_item, ledger)
        assert result["parent_ref"] is None

    def test_missing_relations_key(self):
        ledger = self._make_ledger([self._make_mapping(10, 100)])
        result = sync_hierarchy_from_ado({"id": 100}, ledger)
        assert result["parent_ref"] is None
        assert result["child_refs"] == []
