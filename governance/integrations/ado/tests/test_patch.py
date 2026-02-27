"""Tests for JSON Patch builder."""

from governance.integrations.ado._patch import (
    add_field,
    add_github_commit_link,
    add_github_pr_link,
    add_hyperlink,
    add_relation,
    add_tag,
    remove_field,
    remove_relation,
    replace_field,
    set_area_path,
    set_iteration_path,
    to_json_patch,
)
from governance.integrations.ado._types import PatchOperation


class TestPatchBuilders:
    def test_add_field(self):
        op = add_field("/fields/System.Title", "My Title")
        assert op.op == "add"
        assert op.path == "/fields/System.Title"
        assert op.value == "My Title"

    def test_replace_field(self):
        op = replace_field("/fields/System.State", "Active")
        assert op.op == "replace"
        assert op.value == "Active"

    def test_remove_field(self):
        op = remove_field("/fields/Custom.Field")
        assert op.op == "remove"
        assert op.value is None

    def test_add_relation(self):
        op = add_relation(
            "System.LinkTypes.Hierarchy-Forward",
            "https://dev.azure.com/org/proj/_apis/wit/workitems/99",
        )
        assert op.op == "add"
        assert op.path == "/relations/-"
        assert op.value["rel"] == "System.LinkTypes.Hierarchy-Forward"

    def test_add_relation_with_attributes(self):
        op = add_relation("Related", "http://example.com", attributes={"comment": "x"})
        assert op.value["attributes"] == {"comment": "x"}

    def test_add_tag(self):
        op = add_tag("governance")
        assert op.path == "/fields/System.Tags"
        assert op.value == "governance"

    def test_set_area_path(self):
        op = set_area_path("Project\\Team")
        assert op.path == "/fields/System.AreaPath"
        assert op.value == "Project\\Team"

    def test_set_iteration_path(self):
        op = set_iteration_path("Project\\Sprint 1")
        assert op.path == "/fields/System.IterationPath"


class TestArtifactLinks:
    def test_github_pr_link(self):
        op = add_github_pr_link("abc-123-def", 42)
        assert op.op == "add"
        assert op.path == "/relations/-"
        assert "vstfs:///GitHub/PullRequest/abc-123-def%2F42" == op.value["url"]
        assert op.value["attributes"]["name"] == "GitHub Pull Request"

    def test_github_commit_link(self):
        sha = "a" * 40
        op = add_github_commit_link("conn-id", sha)
        assert f"vstfs:///GitHub/Commit/conn-id%2F{sha}" == op.value["url"]
        assert op.value["attributes"]["name"] == "GitHub Commit"

    def test_hyperlink_with_comment(self):
        op = add_hyperlink("https://github.com/org/repo/tree/main", "Branch: main")
        assert op.value["rel"] == "Hyperlink"
        assert op.value["url"] == "https://github.com/org/repo/tree/main"
        assert op.value["attributes"]["comment"] == "Branch: main"

    def test_hyperlink_without_comment(self):
        op = add_hyperlink("https://example.com")
        assert "attributes" not in op.value or op.value.get("attributes") is None

    def test_remove_relation_by_index(self):
        op = remove_relation(3)
        assert op.op == "remove"
        assert op.path == "/relations/3"


class TestToJsonPatch:
    def test_converts_operations(self):
        ops = [
            add_field("/fields/System.Title", "Hello"),
            replace_field("/fields/System.State", "Active"),
        ]
        result = to_json_patch(ops)
        assert len(result) == 2
        assert result[0] == {"op": "add", "path": "/fields/System.Title", "value": "Hello"}
        assert result[1] == {"op": "replace", "path": "/fields/System.State", "value": "Active"}

    def test_remove_excludes_value(self):
        ops = [remove_field("/fields/Custom.X")]
        result = to_json_patch(ops)
        assert result == [{"op": "remove", "path": "/fields/Custom.X"}]

    def test_from_field_included(self):
        op = PatchOperation(op="move", path="/fields/A", from_="/fields/B")
        result = to_json_patch([op])
        assert result[0]["from"] == "/fields/B"

    def test_empty_list(self):
        assert to_json_patch([]) == []
