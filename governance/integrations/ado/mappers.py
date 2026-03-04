"""Mapping functions for GitHub issue data to Azure DevOps work item fields.

Translates GitHub issue states, labels, fields, priorities, and users
to their ADO equivalents using configuration from project.yaml.
"""

from __future__ import annotations

from typing import Any

from governance.integrations.ado._patch import (
    PatchOperation,
    add_field,
    set_area_path,
    set_iteration_path,
)


def map_github_state_to_ado(
    github_state: str,
    labels: list[str],
    config: dict,
) -> str:
    """Map a GitHub issue state to an ADO work item state.

    Checks compound keys first (e.g. ``"closed+label:bug"``), then falls
    back to the plain state (``"open"`` / ``"closed"``).

    Args:
        github_state: The GitHub issue state (``"open"`` or ``"closed"``).
        labels: Current labels on the GitHub issue.
        config: The ``ado_integration`` config dict from ``project.yaml``.

    Returns:
        The ADO state string.  Falls back to ``"New"`` for open and
        ``"Closed"`` for closed when no mapping is configured.
    """
    state_mapping: dict[str, str] = config.get("state_mapping", {})

    # Check compound keys: "closed+label:<name>"
    for label in labels:
        compound_key = f"{github_state}+label:{label}"
        if compound_key in state_mapping:
            return state_mapping[compound_key]

    # Plain state
    if github_state in state_mapping:
        return state_mapping[github_state]

    # Defaults
    defaults = {"open": "New", "closed": "Closed"}
    return defaults.get(github_state, "New")


def map_github_labels_to_ado_type(
    labels: list[str],
    config: dict,
) -> str:
    """Map GitHub issue labels to an ADO work item type.

    Iterates labels and returns the first match found in
    ``type_mapping``.  Falls back to the ``"default"`` key, then
    ``"User Story"``.

    Args:
        labels: Current labels on the GitHub issue.
        config: The ``ado_integration`` config dict.

    Returns:
        The ADO work item type name.
    """
    type_mapping: dict[str, str] = config.get("type_mapping", {})

    for label in labels:
        if label in type_mapping:
            return type_mapping[label]

    return type_mapping.get("default", "User Story")


def map_github_fields_to_ado_patch(
    issue: dict,
    config: dict,
) -> list[PatchOperation]:
    """Build a list of ``PatchOperation`` objects from GitHub issue data.

    Maps the following fields:
    - Title (``System.Title``)
    - Description / body (``System.Description``)
    - State (``System.State``)
    - Assigned user (``System.AssignedTo``)
    - Priority (``Microsoft.VSTS.Common.Priority``)
    - Area path (``System.AreaPath``)
    - Iteration path (``System.IterationPath``)

    Args:
        issue: The GitHub issue payload (from the webhook event).
        config: The ``ado_integration`` config dict.

    Returns:
        A list of ``PatchOperation`` instances ready for ``AdoClient``.
    """
    ops: list[PatchOperation] = []

    # Title
    title = issue.get("title")
    if title:
        ops.append(add_field("/fields/System.Title", title))

    # Description — include even when None (explicit clear)
    if "body" in issue:
        ops.append(add_field("/fields/System.Description", issue["body"]))

    # State
    state = issue.get("state")
    if state:
        labels = [lbl.get("name", "") if isinstance(lbl, dict) else str(lbl) for lbl in issue.get("labels", [])]
        ado_state = map_github_state_to_ado(state, labels, config)
        ops.append(add_field("/fields/System.State", ado_state))

    # Assignee
    assignee = issue.get("assignee")
    if assignee:
        login = assignee.get("login", "") if isinstance(assignee, dict) else str(assignee)
        ado_user = map_github_user_to_ado(login, config)
        if ado_user:
            ops.append(add_field("/fields/System.AssignedTo", ado_user))

    # Priority
    labels = [lbl.get("name", "") if isinstance(lbl, dict) else str(lbl) for lbl in issue.get("labels", [])]
    priority = map_github_priority_to_ado(labels, config)
    if priority is not None:
        ops.append(add_field("/fields/Microsoft.VSTS.Common.Priority", priority))

    # Area path
    field_mapping = config.get("field_mapping", {})
    area_path = field_mapping.get("area_path", "")
    if area_path:
        ops.append(set_area_path(area_path))

    # Iteration path
    iteration_path = field_mapping.get("iteration_path", "")
    if iteration_path:
        ops.append(set_iteration_path(iteration_path))

    return ops


def map_github_priority_to_ado(
    labels: list[str],
    config: dict,
) -> int | None:
    """Map GitHub labels to an ADO priority value (1-4).

    Uses the ``field_mapping.priority_labels`` mapping from config.

    Args:
        labels: Current labels on the GitHub issue.
        config: The ``ado_integration`` config dict.

    Returns:
        An integer 1-4, or ``None`` if no priority label matches.
    """
    field_mapping = config.get("field_mapping", {})
    priority_labels: dict[str, int] = field_mapping.get("priority_labels", {})

    for label in labels:
        if label in priority_labels:
            return priority_labels[label]

    return None


def map_github_user_to_ado(
    github_login: str,
    config: dict,
) -> str | None:
    """Map a GitHub username to an ADO user email.

    Args:
        github_login: The GitHub username.
        config: The ``ado_integration`` config dict.

    Returns:
        The ADO user email, or ``None`` if no mapping exists.
    """
    user_mapping: dict[str, str] = config.get("user_mapping", {})
    return user_mapping.get(github_login)
