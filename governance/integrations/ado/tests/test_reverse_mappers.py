"""Tests for ADO-to-GitHub reverse mapping functions."""

from __future__ import annotations

from governance.integrations.ado.reverse_mappers import (
    map_ado_fields_to_github,
    map_ado_priority_to_github,
    map_ado_state_to_github,
    map_ado_user_to_github,
)


# -- Fixtures / helpers ----------------------------------------------------


def _config(**overrides) -> dict:
    """Build a minimal ado_integration config dict."""
    base: dict = {
        "organization": "https://dev.azure.com/testorg",
        "project": "TestProject",
        "state_mapping": {
            "open": "New",
            "closed": "Closed",
            "closed+label:bug": "Resolved",
        },
        "type_mapping": {
            "default": "User Story",
            "bug": "Bug",
            "task": "Task",
            "enhancement": "Feature",
        },
        "field_mapping": {
            "area_path": "TestProject\\TeamA",
            "iteration_path": "TestProject\\Sprint 1",
            "priority_labels": {
                "P1": 1,
                "P2": 2,
                "P3": 3,
                "P4": 4,
            },
        },
        "user_mapping": {
            "octocat": "octocat@example.com",
            "janedoe": "jane.doe@example.com",
        },
        "sync": {
            "direction": "bidirectional",
            "grace_period_seconds": 5,
        },
    }
    base.update(overrides)
    return base


# -- map_ado_state_to_github -----------------------------------------------


class TestMapAdoStateToGithub:
    def test_new_state_reopens(self):
        result = map_ado_state_to_github("New", _config())
        assert result["action"] == "reopen"
        assert "ado:new" in result["labels_add"]

    def test_active_state_reopens(self):
        result = map_ado_state_to_github("Active", _config())
        assert result["action"] == "reopen"
        assert "ado:active" in result["labels_add"]
        assert "ado:new" in result["labels_remove"]

    def test_resolved_state_noop(self):
        result = map_ado_state_to_github("Resolved", _config())
        assert result["action"] == "noop"
        assert "ado:resolved" in result["labels_add"]

    def test_closed_state_closes(self):
        result = map_ado_state_to_github("Closed", _config())
        assert result["action"] == "close"
        assert "ado:closed" in result["labels_add"]

    def test_removed_state_closes_with_wontfix(self):
        result = map_ado_state_to_github("Removed", _config())
        assert result["action"] == "close"
        assert "wontfix" in result["labels_add"]

    def test_unknown_state_noop(self):
        result = map_ado_state_to_github("CustomState", _config())
        assert result["action"] == "noop"
        assert result["labels_add"] == []
        assert result["labels_remove"] == []

    def test_case_insensitive(self):
        result = map_ado_state_to_github("new", _config())
        assert result["action"] == "reopen"

        result = map_ado_state_to_github("ACTIVE", _config())
        assert result["action"] == "reopen"

    def test_new_removes_other_ado_labels(self):
        result = map_ado_state_to_github("New", _config())
        assert "ado:active" in result["labels_remove"]
        assert "ado:resolved" in result["labels_remove"]
        assert "ado:closed" in result["labels_remove"]
        assert "ado:new" not in result["labels_remove"]

    def test_active_removes_other_ado_labels(self):
        result = map_ado_state_to_github("Active", _config())
        assert "ado:new" in result["labels_remove"]
        assert "ado:resolved" in result["labels_remove"]
        assert "ado:closed" in result["labels_remove"]
        assert "ado:active" not in result["labels_remove"]

    def test_removed_removes_all_ado_labels(self):
        result = map_ado_state_to_github("Removed", _config())
        assert "ado:new" in result["labels_remove"]
        assert "ado:active" in result["labels_remove"]
        assert "ado:resolved" in result["labels_remove"]
        assert "ado:closed" in result["labels_remove"]

    def test_explicit_reverse_state_mapping(self):
        """Custom reverse_state_mapping takes priority over defaults."""
        cfg = _config(reverse_state_mapping={
            "New": {
                "action": "noop",
                "labels_add": ["custom:new"],
                "labels_remove": [],
            },
        })
        result = map_ado_state_to_github("New", cfg)
        assert result["action"] == "noop"
        assert result["labels_add"] == ["custom:new"]

    def test_explicit_mapping_with_missing_keys(self):
        """Explicit mapping with partial keys gets defaults for missing."""
        cfg = _config(reverse_state_mapping={
            "Active": {"action": "reopen"},
        })
        result = map_ado_state_to_github("Active", cfg)
        assert result["action"] == "reopen"
        assert result["labels_add"] == []
        assert result["labels_remove"] == []


# -- map_ado_user_to_github ------------------------------------------------


class TestMapAdoUserToGithub:
    def test_mapped_user(self):
        assert map_ado_user_to_github("octocat@example.com", _config()) == "octocat"

    def test_another_mapped_user(self):
        assert map_ado_user_to_github("jane.doe@example.com", _config()) == "janedoe"

    def test_unmapped_user_returns_none(self):
        assert map_ado_user_to_github("unknown@example.com", _config()) is None

    def test_empty_email_returns_none(self):
        assert map_ado_user_to_github("", _config()) is None

    def test_case_insensitive_lookup(self):
        assert map_ado_user_to_github("Octocat@Example.COM", _config()) == "octocat"

    def test_no_user_mapping(self):
        cfg = _config(user_mapping={})
        assert map_ado_user_to_github("octocat@example.com", cfg) is None

    def test_no_user_mapping_key(self):
        cfg = _config()
        del cfg["user_mapping"]
        assert map_ado_user_to_github("octocat@example.com", cfg) is None


# -- map_ado_priority_to_github --------------------------------------------


class TestMapAdoPriorityToGithub:
    def test_priority_1(self):
        assert map_ado_priority_to_github(1, _config()) == "P1"

    def test_priority_2(self):
        assert map_ado_priority_to_github(2, _config()) == "P2"

    def test_priority_3(self):
        assert map_ado_priority_to_github(3, _config()) == "P3"

    def test_priority_4(self):
        assert map_ado_priority_to_github(4, _config()) == "P4"

    def test_unmapped_priority_returns_none(self):
        assert map_ado_priority_to_github(5, _config()) is None

    def test_no_priority_config(self):
        cfg = _config(field_mapping={})
        assert map_ado_priority_to_github(1, cfg) is None

    def test_no_field_mapping_key(self):
        cfg = _config()
        del cfg["field_mapping"]
        assert map_ado_priority_to_github(1, cfg) is None


# -- map_ado_fields_to_github ----------------------------------------------


class TestMapAdoFieldsToGithub:
    def test_title_mapped(self):
        result = map_ado_fields_to_github(
            {"System.Title": "New Title"}, _config()
        )
        assert result["title"] == "New Title"

    def test_description_mapped(self):
        result = map_ado_fields_to_github(
            {"System.Description": "New body"}, _config()
        )
        assert result["body"] == "New body"

    def test_none_description_clears_body(self):
        result = map_ado_fields_to_github(
            {"System.Description": None}, _config()
        )
        assert result["body"] == ""

    def test_assignee_mapped(self):
        result = map_ado_fields_to_github(
            {"System.AssignedTo": "octocat@example.com"}, _config()
        )
        assert result["assignees"] == ["octocat"]

    def test_assignee_identity_object(self):
        """ADO sometimes returns identity objects instead of plain strings."""
        result = map_ado_fields_to_github(
            {"System.AssignedTo": {"uniqueName": "octocat@example.com", "displayName": "Octocat"}},
            _config(),
        )
        assert result["assignees"] == ["octocat"]

    def test_unmapped_assignee_not_included(self):
        result = map_ado_fields_to_github(
            {"System.AssignedTo": "unknown@example.com"}, _config()
        )
        assert "assignees" not in result

    def test_empty_assignee_clears(self):
        result = map_ado_fields_to_github(
            {"System.AssignedTo": ""}, _config()
        )
        assert result["assignees"] == []

    def test_state_mapped(self):
        result = map_ado_fields_to_github(
            {"System.State": "Active"}, _config()
        )
        assert "state" in result
        assert result["state"]["action"] == "reopen"

    def test_priority_mapped(self):
        result = map_ado_fields_to_github(
            {"Microsoft.VSTS.Common.Priority": 1}, _config()
        )
        assert result["priority_label"] == "P1"

    def test_invalid_priority_not_mapped(self):
        result = map_ado_fields_to_github(
            {"Microsoft.VSTS.Common.Priority": "invalid"}, _config()
        )
        assert "priority_label" not in result

    def test_empty_fields_returns_empty(self):
        result = map_ado_fields_to_github({}, _config())
        assert result == {}

    def test_multiple_fields(self):
        result = map_ado_fields_to_github(
            {
                "System.Title": "Updated",
                "System.Description": "New body",
                "Microsoft.VSTS.Common.Priority": 2,
            },
            _config(),
        )
        assert result["title"] == "Updated"
        assert result["body"] == "New body"
        assert result["priority_label"] == "P2"

    def test_unrecognized_fields_ignored(self):
        result = map_ado_fields_to_github(
            {"Custom.Unknown": "value"}, _config()
        )
        assert result == {}

    def test_none_assignee_identity_clears(self):
        """AssignedTo set to None (ADO unassign)."""
        result = map_ado_fields_to_github(
            {"System.AssignedTo": None}, _config()
        )
        # None assignee means unassign
        assert result["assignees"] == []
