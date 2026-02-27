"""JSON Patch builder for Azure DevOps work item updates."""

from __future__ import annotations

from governance.integrations.ado._types import PatchOperation


def add_field(field_path: str, value) -> PatchOperation:
    """Add a field value. field_path should be like '/fields/System.Title'."""
    return PatchOperation(op="add", path=field_path, value=value)


def replace_field(field_path: str, value) -> PatchOperation:
    """Replace an existing field value."""
    return PatchOperation(op="replace", path=field_path, value=value)


def remove_field(field_path: str) -> PatchOperation:
    """Remove a field value."""
    return PatchOperation(op="remove", path=field_path)


def add_relation(
    rel_type: str,
    target_url: str,
    attributes: dict | None = None,
) -> PatchOperation:
    """Add a relation (link) to a work item."""
    value: dict = {"rel": rel_type, "url": target_url}
    if attributes:
        value["attributes"] = attributes
    return PatchOperation(op="add", path="/relations/-", value=value)


def add_tag(tag: str) -> PatchOperation:
    """Add a tag to a work item (appends via add to Tags field)."""
    return PatchOperation(op="add", path="/fields/System.Tags", value=tag)


def set_area_path(area_path: str) -> PatchOperation:
    """Set the area path of a work item."""
    return PatchOperation(op="add", path="/fields/System.AreaPath", value=area_path)


def set_iteration_path(iteration_path: str) -> PatchOperation:
    """Set the iteration path of a work item."""
    return PatchOperation(
        op="add", path="/fields/System.IterationPath", value=iteration_path
    )


def add_github_pr_link(connection_id: str, pr_number: int) -> PatchOperation:
    """Link a GitHub Pull Request to a work item (appears in Development section).

    Args:
        connection_id: The GitHub service connection GUID in the ADO org.
        pr_number: The GitHub PR number.
    """
    url = f"vstfs:///GitHub/PullRequest/{connection_id}%2F{pr_number}"
    return add_relation(
        "ArtifactLink", url, attributes={"name": "GitHub Pull Request"}
    )


def add_github_commit_link(connection_id: str, commit_sha: str) -> PatchOperation:
    """Link a GitHub Commit to a work item (appears in Development section).

    Args:
        connection_id: The GitHub service connection GUID in the ADO org.
        commit_sha: The full 40-character commit SHA. Short SHAs silently fail.
    """
    url = f"vstfs:///GitHub/Commit/{connection_id}%2F{commit_sha}"
    return add_relation(
        "ArtifactLink", url, attributes={"name": "GitHub Commit"}
    )


def add_hyperlink(url: str, comment: str = "") -> PatchOperation:
    """Add a generic hyperlink to a work item (appears in Links tab).

    Use for GitHub branches, issues, and other URLs that don't have
    native artifact link support in ADO.
    """
    attrs = {}
    if comment:
        attrs["comment"] = comment
    return add_relation("Hyperlink", url, attributes=attrs if attrs else None)


def remove_relation(index: int) -> PatchOperation:
    """Remove a relation by its index in the relations array."""
    return PatchOperation(op="remove", path=f"/relations/{index}")


def to_json_patch(operations: list[PatchOperation]) -> list[dict]:
    """Convert a list of PatchOperations to the JSON Patch format expected by ADO.

    Returns a list of dicts suitable for use as a request body.
    """
    result = []
    for op in operations:
        entry: dict = {"op": op.op, "path": op.path}
        if op.value is not None:
            entry["value"] = op.value
        if op.from_ is not None:
            entry["from"] = op.from_
        result.append(entry)
    return result
