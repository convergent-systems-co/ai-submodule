"""Mapping functions for Azure DevOps work item data to GitHub issue fields.

Translates ADO work item states, fields, priorities, and users
to their GitHub equivalents using configuration from project.yaml.
This is the reverse direction of mappers.py (GitHub -> ADO).
"""

from __future__ import annotations

from typing import Any


def map_ado_state_to_github(
    ado_state: str,
    config: dict,
) -> dict:
    """Map an ADO work item state to a GitHub issue action and labels.

    Args:
        ado_state: The ADO work item state (e.g. "New", "Active", "Resolved",
            "Closed", "Removed").
        config: The ``ado_integration`` config dict from ``project.yaml``.

    Returns:
        A dict with keys:
        - ``action``: ``"reopen"``, ``"close"``, or ``"noop"``
        - ``labels_add``: list of labels to add
        - ``labels_remove``: list of labels to remove
    """
    reverse_state_mapping: dict[str, dict] = config.get("reverse_state_mapping", {})

    # Check explicit mapping first
    if ado_state in reverse_state_mapping:
        mapping = reverse_state_mapping[ado_state]
        return {
            "action": mapping.get("action", "noop"),
            "labels_add": list(mapping.get("labels_add", [])),
            "labels_remove": list(mapping.get("labels_remove", [])),
        }

    # Built-in defaults
    ado_label_prefix = "ado:"
    all_ado_labels = [
        f"{ado_label_prefix}new",
        f"{ado_label_prefix}active",
        f"{ado_label_prefix}resolved",
        f"{ado_label_prefix}closed",
    ]

    normalized = ado_state.lower()

    if normalized == "new":
        return {
            "action": "reopen",
            "labels_add": [f"{ado_label_prefix}new"],
            "labels_remove": [lbl for lbl in all_ado_labels if lbl != f"{ado_label_prefix}new"],
        }

    if normalized == "active":
        return {
            "action": "reopen",
            "labels_add": [f"{ado_label_prefix}active"],
            "labels_remove": [lbl for lbl in all_ado_labels if lbl != f"{ado_label_prefix}active"],
        }

    if normalized == "resolved":
        return {
            "action": "noop",
            "labels_add": [f"{ado_label_prefix}resolved"],
            "labels_remove": [lbl for lbl in all_ado_labels if lbl != f"{ado_label_prefix}resolved"],
        }

    if normalized == "closed":
        return {
            "action": "close",
            "labels_add": [f"{ado_label_prefix}closed"],
            "labels_remove": [lbl for lbl in all_ado_labels if lbl != f"{ado_label_prefix}closed"],
        }

    if normalized == "removed":
        return {
            "action": "close",
            "labels_add": ["wontfix"],
            "labels_remove": all_ado_labels,
        }

    # Unknown state: no-op
    return {
        "action": "noop",
        "labels_add": [],
        "labels_remove": [],
    }


def map_ado_fields_to_github(
    changed_fields: dict[str, Any],
    config: dict,
) -> dict:
    """Map changed ADO work item fields to GitHub issue update fields.

    Only returns keys for fields that actually changed, so callers can
    apply a partial update.

    Args:
        changed_fields: Dict of ADO field reference names to their new values.
            E.g. ``{"System.Title": "New Title", "System.AssignedTo": "user@example.com"}``.
        config: The ``ado_integration`` config dict from ``project.yaml``.

    Returns:
        A dict with any combination of keys: ``title``, ``body``,
        ``assignees``, ``labels``, ``state``.  Only keys for changed
        fields are present.
    """
    result: dict[str, Any] = {}

    # Title
    if "System.Title" in changed_fields:
        result["title"] = changed_fields["System.Title"]

    # Description -> body
    if "System.Description" in changed_fields:
        result["body"] = changed_fields["System.Description"] or ""

    # Assigned To -> assignees
    if "System.AssignedTo" in changed_fields:
        ado_user = changed_fields["System.AssignedTo"]
        # Handle identity objects (dict with uniqueName or displayName)
        if isinstance(ado_user, dict):
            ado_user = ado_user.get("uniqueName", ado_user.get("displayName", ""))
        github_user = map_ado_user_to_github(str(ado_user) if ado_user else "", config)
        if github_user:
            result["assignees"] = [github_user]
        elif not ado_user:
            # Clearing assignment
            result["assignees"] = []

    # State
    if "System.State" in changed_fields:
        state_result = map_ado_state_to_github(changed_fields["System.State"], config)
        result["state"] = state_result

    # Priority -> labels
    if "Microsoft.VSTS.Common.Priority" in changed_fields:
        priority_val = changed_fields["Microsoft.VSTS.Common.Priority"]
        try:
            priority_int = int(priority_val)
        except (ValueError, TypeError):
            priority_int = None
        if priority_int is not None:
            label = map_ado_priority_to_github(priority_int, config)
            if label:
                result["priority_label"] = label

    return result


def map_ado_user_to_github(
    ado_email: str,
    config: dict,
) -> str | None:
    """Reverse lookup: map an ADO user email to a GitHub username.

    Searches the ``user_mapping`` dict in config for a value matching
    the given email and returns the corresponding key (GitHub login).

    Args:
        ado_email: The ADO user email (e.g. ``"user@example.com"``).
        config: The ``ado_integration`` config dict.

    Returns:
        The GitHub username, or ``None`` if no reverse mapping exists.
    """
    if not ado_email:
        return None

    user_mapping: dict[str, str] = config.get("user_mapping", {})
    # Reverse lookup: values are ADO emails, keys are GitHub logins
    for github_login, mapped_email in user_mapping.items():
        if mapped_email.lower() == ado_email.lower():
            return github_login

    return None


def map_ado_priority_to_github(
    priority_int: int,
    config: dict,
) -> str | None:
    """Reverse lookup: map an ADO priority integer to a GitHub label.

    Searches the ``field_mapping.priority_labels`` dict in config for
    a value matching the given priority and returns the corresponding
    key (GitHub label name).

    Args:
        priority_int: The ADO priority value (1-4).
        config: The ``ado_integration`` config dict.

    Returns:
        The GitHub label string, or ``None`` if no reverse mapping exists.
    """
    field_mapping = config.get("field_mapping", {})
    priority_labels: dict[str, int] = field_mapping.get("priority_labels", {})

    for label, value in priority_labels.items():
        if value == priority_int:
            return label

    return None
