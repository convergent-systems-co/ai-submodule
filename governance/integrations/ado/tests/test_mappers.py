"""Tests for GitHub-to-ADO mapping functions."""

from __future__ import annotations

from governance.integrations.ado._types import PatchOperation
from governance.integrations.ado.mappers import (
    map_github_fields_to_ado_patch,
    map_github_labels_to_ado_type,
    map_github_priority_to_ado,
    map_github_state_to_ado,
    map_github_user_to_ado,
)


# ── Fixtures / helpers ───────────────────────────────────────────────────


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
    }
    base.update(overrides)
    return base


def _issue(
    *,
    title: str = "Test issue",
    body: str = "Issue body",
    state: str = "open",
    labels: list[str] | None = None,
    assignee: str | None = None,
    milestone: str | None = None,
) -> dict:
    """Build a minimal GitHub issue payload."""
    issue: dict = {
        "number": 42,
        "title": title,
        "body": body,
        "state": state,
        "labels": [{"name": lbl} for lbl in (labels or [])],
        "html_url": "https://github.com/owner/repo/issues/42",
    }
    if assignee:
        issue["assignee"] = {"login": assignee}
    if milestone:
        issue["milestone"] = {"title": milestone}
    return issue


# ── map_github_state_to_ado ─────────────────────────────────────────────


class TestMapGithubStateToAdo:
    def test_open_state(self):
        assert map_github_state_to_ado("open", [], _config()) == "New"

    def test_closed_state(self):
        assert map_github_state_to_ado("closed", [], _config()) == "Closed"

    def test_compound_key_with_label(self):
        """closed+label:bug should map to Resolved."""
        result = map_github_state_to_ado("closed", ["bug"], _config())
        assert result == "Resolved"

    def test_compound_key_not_matched(self):
        """closed without bug label falls to plain 'closed'."""
        result = map_github_state_to_ado("closed", ["enhancement"], _config())
        assert result == "Closed"

    def test_missing_state_mapping_defaults(self):
        cfg = _config(state_mapping={})
        assert map_github_state_to_ado("open", [], cfg) == "New"
        assert map_github_state_to_ado("closed", [], cfg) == "Closed"

    def test_unknown_state_defaults_to_new(self):
        assert map_github_state_to_ado("unknown", [], _config()) == "New"

    def test_empty_labels(self):
        assert map_github_state_to_ado("open", [], _config()) == "New"

    def test_no_state_mapping_key(self):
        cfg = _config()
        del cfg["state_mapping"]
        assert map_github_state_to_ado("open", [], cfg) == "New"


# ── map_github_labels_to_ado_type ────────────────────────────────────────


class TestMapGithubLabelsToAdoType:
    def test_bug_label(self):
        assert map_github_labels_to_ado_type(["bug"], _config()) == "Bug"

    def test_task_label(self):
        assert map_github_labels_to_ado_type(["task"], _config()) == "Task"

    def test_enhancement_label(self):
        assert map_github_labels_to_ado_type(["enhancement"], _config()) == "Feature"

    def test_first_match_wins(self):
        """When multiple labels match, the first one wins."""
        result = map_github_labels_to_ado_type(["bug", "task"], _config())
        assert result == "Bug"

    def test_no_matching_label_uses_default(self):
        result = map_github_labels_to_ado_type(["documentation"], _config())
        assert result == "User Story"

    def test_empty_labels_uses_default(self):
        assert map_github_labels_to_ado_type([], _config()) == "User Story"

    def test_no_type_mapping_falls_back(self):
        cfg = _config(type_mapping={})
        assert map_github_labels_to_ado_type(["bug"], cfg) == "User Story"

    def test_no_type_mapping_key(self):
        cfg = _config()
        del cfg["type_mapping"]
        assert map_github_labels_to_ado_type([], cfg) == "User Story"


# ── map_github_fields_to_ado_patch ───────────────────────────────────────


class TestMapGithubFieldsToAdoPatch:
    def test_basic_fields(self):
        ops = map_github_fields_to_ado_patch(_issue(), _config())
        paths = [op.path for op in ops]

        assert "/fields/System.Title" in paths
        assert "/fields/System.Description" in paths
        assert "/fields/System.State" in paths
        assert "/fields/System.AreaPath" in paths
        assert "/fields/System.IterationPath" in paths

    def test_title_value(self):
        ops = map_github_fields_to_ado_patch(
            _issue(title="My Title"), _config()
        )
        title_op = next(op for op in ops if op.path == "/fields/System.Title")
        assert title_op.value == "My Title"

    def test_body_value(self):
        ops = map_github_fields_to_ado_patch(
            _issue(body="The body"), _config()
        )
        desc_op = next(op for op in ops if op.path == "/fields/System.Description")
        assert desc_op.value == "The body"

    def test_state_mapping(self):
        ops = map_github_fields_to_ado_patch(
            _issue(state="closed", labels=["bug"]), _config()
        )
        state_op = next(op for op in ops if op.path == "/fields/System.State")
        assert state_op.value == "Resolved"

    def test_assignee_mapped(self):
        ops = map_github_fields_to_ado_patch(
            _issue(assignee="octocat"), _config()
        )
        assignee_op = next(
            (op for op in ops if op.path == "/fields/System.AssignedTo"), None
        )
        assert assignee_op is not None
        assert assignee_op.value == "octocat@example.com"

    def test_unmapped_assignee_skipped(self):
        ops = map_github_fields_to_ado_patch(
            _issue(assignee="unknown_user"), _config()
        )
        assignee_ops = [op for op in ops if op.path == "/fields/System.AssignedTo"]
        assert len(assignee_ops) == 0

    def test_priority_from_label(self):
        ops = map_github_fields_to_ado_patch(
            _issue(labels=["P1"]), _config()
        )
        priority_op = next(
            (op for op in ops if op.path == "/fields/Microsoft.VSTS.Common.Priority"), None
        )
        assert priority_op is not None
        assert priority_op.value == 1

    def test_no_priority_label(self):
        ops = map_github_fields_to_ado_patch(
            _issue(labels=["enhancement"]), _config()
        )
        priority_ops = [op for op in ops if op.path == "/fields/Microsoft.VSTS.Common.Priority"]
        assert len(priority_ops) == 0

    def test_area_path_from_config(self):
        ops = map_github_fields_to_ado_patch(_issue(), _config())
        area_op = next(op for op in ops if op.path == "/fields/System.AreaPath")
        assert area_op.value == "TestProject\\TeamA"

    def test_iteration_path_from_config(self):
        ops = map_github_fields_to_ado_patch(_issue(), _config())
        iter_op = next(op for op in ops if op.path == "/fields/System.IterationPath")
        assert iter_op.value == "TestProject\\Sprint 1"

    def test_empty_area_path_not_included(self):
        cfg = _config(field_mapping={"area_path": "", "iteration_path": ""})
        ops = map_github_fields_to_ado_patch(_issue(), cfg)
        area_ops = [op for op in ops if op.path == "/fields/System.AreaPath"]
        assert len(area_ops) == 0

    def test_all_ops_are_patch_operations(self):
        ops = map_github_fields_to_ado_patch(_issue(), _config())
        for op in ops:
            assert isinstance(op, PatchOperation)

    def test_empty_issue(self):
        """Issue with no data produces no ops."""
        ops = map_github_fields_to_ado_patch({}, _config(field_mapping={}))
        assert ops == []

    def test_none_body_included_as_none(self):
        """body=None should still produce a description op (explicit clear)."""
        issue = _issue()
        issue["body"] = None
        ops = map_github_fields_to_ado_patch(issue, _config())
        desc_ops = [op for op in ops if op.path == "/fields/System.Description"]
        # body is explicitly None, which means the description was cleared
        assert len(desc_ops) == 1
        assert desc_ops[0].value is None


# ── map_github_priority_to_ado ───────────────────────────────────────────


class TestMapGithubPriorityToAdo:
    def test_p1(self):
        assert map_github_priority_to_ado(["P1"], _config()) == 1

    def test_p2(self):
        assert map_github_priority_to_ado(["P2"], _config()) == 2

    def test_p3(self):
        assert map_github_priority_to_ado(["P3"], _config()) == 3

    def test_p4(self):
        assert map_github_priority_to_ado(["P4"], _config()) == 4

    def test_first_match_wins(self):
        assert map_github_priority_to_ado(["P2", "P1"], _config()) == 2

    def test_no_match_returns_none(self):
        assert map_github_priority_to_ado(["enhancement"], _config()) is None

    def test_empty_labels_returns_none(self):
        assert map_github_priority_to_ado([], _config()) is None

    def test_no_priority_labels_config(self):
        cfg = _config(field_mapping={})
        assert map_github_priority_to_ado(["P1"], cfg) is None


# ── map_github_user_to_ado ───────────────────────────────────────────────


class TestMapGithubUserToAdo:
    def test_mapped_user(self):
        assert map_github_user_to_ado("octocat", _config()) == "octocat@example.com"

    def test_another_mapped_user(self):
        assert map_github_user_to_ado("janedoe", _config()) == "jane.doe@example.com"

    def test_unmapped_user_returns_none(self):
        assert map_github_user_to_ado("unknown", _config()) is None

    def test_empty_login_returns_none(self):
        assert map_github_user_to_ado("", _config()) is None

    def test_no_user_mapping(self):
        cfg = _config(user_mapping={})
        assert map_github_user_to_ado("octocat", cfg) is None

    def test_no_user_mapping_key(self):
        cfg = _config()
        del cfg["user_mapping"]
        assert map_github_user_to_ado("octocat", cfg) is None
