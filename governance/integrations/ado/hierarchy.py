"""Parent-child hierarchy sync between GitHub issues and ADO work items.

Parses ``parent: #N`` and ``child: #N, #M`` references from GitHub issue
bodies and synchronises them as ``System.LinkTypes.Hierarchy-Reverse``
(parent) and ``System.LinkTypes.Hierarchy-Forward`` (child) relations on
the corresponding ADO work items.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from governance.integrations.ado._patch import add_relation
from governance.integrations.ado.client import AdoClient

logger = logging.getLogger(__name__)

# ── Parsing helpers ─────────────────────────────────────────────────────────

_PARENT_RE = re.compile(r"(?m)^parent:\s*#(\d+)\s*$", re.IGNORECASE)
_CHILD_RE = re.compile(r"(?m)^child(?:ren)?:\s*(#\d+(?:\s*,\s*#\d+)*)\s*$", re.IGNORECASE)
_ISSUE_NUM_RE = re.compile(r"#(\d+)")


def parse_parent_reference(body: str) -> int | None:
    """Extract a ``parent: #N`` reference from an issue body.

    Returns the parent issue number, or ``None`` if not found.
    """
    if not body:
        return None
    m = _PARENT_RE.search(body)
    if m:
        return int(m.group(1))
    return None


def parse_child_references(body: str) -> list[int]:
    """Extract ``child: #N, #M`` references from an issue body.

    Returns a list of child issue numbers (may be empty).
    """
    if not body:
        return []
    m = _CHILD_RE.search(body)
    if not m:
        return []
    refs = _ISSUE_NUM_RE.findall(m.group(1))
    return [int(r) for r in refs]


# ── Hierarchy validation ────────────────────────────────────────────────────

# Canonical ADO hierarchy: Epic > Feature > User Story > Task
_HIERARCHY_ORDER: dict[str, int] = {
    "Epic": 0,
    "Feature": 1,
    "User Story": 2,
    "Task": 3,
    "Bug": 2,  # same level as User Story
}


def validate_type_hierarchy(parent_type: str, child_type: str) -> bool:
    """Validate that the parent-child type ordering is correct.

    Uses the canonical Epic -> Feature -> User Story -> Task hierarchy.
    Returns ``True`` if the ordering is valid, ``False`` if it violates
    the expected hierarchy.  Logs a warning on violation but does **not**
    block the operation.
    """
    parent_rank = _HIERARCHY_ORDER.get(parent_type)
    child_rank = _HIERARCHY_ORDER.get(child_type)

    if parent_rank is None or child_rank is None:
        # Unknown types — can't validate, assume OK
        logger.debug(
            "Cannot validate hierarchy for types %s -> %s (not in known hierarchy)",
            parent_type,
            child_type,
        )
        return True

    if parent_rank >= child_rank:
        logger.warning(
            "Hierarchy violation: %s (rank %d) should be above %s (rank %d)",
            parent_type,
            parent_rank,
            child_type,
            child_rank,
        )
        return False

    return True


# ── ADO work item URL helpers ───────────────────────────────────────────────

def _work_item_url(organization: str, project: str, work_item_id: int) -> str:
    """Build the ADO REST API URL for a work item (used in relation targets)."""
    org = organization
    if org.startswith("https://"):
        # Already a full URL
        base = org.rstrip("/")
    else:
        base = f"https://dev.azure.com/{org}"
    return f"{base}/{project}/_apis/wit/workitems/{work_item_id}"


# ── Sync to ADO ────────────────────────────────────────────────────────────


def sync_hierarchy_to_ado(
    issue_number: int,
    parent_issue: int | None,
    children: list[int],
    ledger: dict,
    client: AdoClient,
    config: dict,
) -> list[str]:
    """Create ``System.LinkTypes.Hierarchy`` relations on ADO work items.

    Args:
        issue_number: The current GitHub issue number.
        parent_issue: Parent issue number (from ``parent: #N``), or ``None``.
        children: List of child issue numbers (from ``child: #N, #M``).
        ledger: The sync ledger dict (with ``mappings`` list).
        client: An ``AdoClient`` instance.
        config: The ``ado_integration`` config dict.

    Returns:
        A list of human-readable action descriptions.
    """
    actions: list[str] = []

    mappings = ledger.get("mappings", [])
    lookup = {m["github_issue_number"]: m for m in mappings}

    current = lookup.get(issue_number)
    if not current:
        logger.debug("Issue #%d not in ledger, skipping hierarchy sync", issue_number)
        return actions

    current_ado_id = current["ado_work_item_id"]
    organization = config.get("organization", "")
    project = config.get("project", "")

    # ── Parent link ──
    if parent_issue is not None:
        parent_entry = lookup.get(parent_issue)
        if parent_entry:
            parent_ado_id = parent_entry["ado_work_item_id"]
            target_url = _work_item_url(organization, project, parent_ado_id)
            op = add_relation("System.LinkTypes.Hierarchy-Reverse", target_url)
            client.update_work_item(current_ado_id, [op])
            actions.append(
                f"Linked ADO #{current_ado_id} as child of ADO #{parent_ado_id} "
                f"(GitHub #{issue_number} -> #{parent_issue})"
            )
        else:
            logger.warning(
                "Parent issue #%d not in ledger, cannot create hierarchy link",
                parent_issue,
            )

    # ── Child links ──
    for child_issue in children:
        child_entry = lookup.get(child_issue)
        if child_entry:
            child_ado_id = child_entry["ado_work_item_id"]
            target_url = _work_item_url(organization, project, child_ado_id)
            op = add_relation("System.LinkTypes.Hierarchy-Forward", target_url)
            client.update_work_item(current_ado_id, [op])
            actions.append(
                f"Linked ADO #{child_ado_id} as child of ADO #{current_ado_id} "
                f"(GitHub #{child_issue} -> #{issue_number})"
            )
        else:
            logger.warning(
                "Child issue #%d not in ledger, cannot create hierarchy link",
                child_issue,
            )

    return actions


# ── Sync from ADO ──────────────────────────────────────────────────────────


def sync_hierarchy_from_ado(
    ado_work_item: dict,
    ledger: dict,
) -> dict:
    """Read ADO relations and return GitHub issue references.

    Args:
        ado_work_item: A work item dict with ``id`` and ``relations`` keys.
        ledger: The sync ledger dict.

    Returns:
        A dict with ``parent_ref`` (``"#N"`` or ``None``) and ``child_refs``
        (list of ``"#M"`` strings).
    """
    result: dict[str, Any] = {"parent_ref": None, "child_refs": []}

    relations = ado_work_item.get("relations", [])
    if not relations:
        return result

    # Build reverse lookup: ADO work item ID -> GitHub issue number
    mappings = ledger.get("mappings", [])
    ado_to_github = {m["ado_work_item_id"]: m["github_issue_number"] for m in mappings}

    for rel in relations:
        rel_type = rel.get("rel", "")
        url = rel.get("url", "")

        # Extract work item ID from the URL (last path segment)
        try:
            target_ado_id = int(url.rstrip("/").split("/")[-1])
        except (ValueError, IndexError):
            continue

        github_issue = ado_to_github.get(target_ado_id)
        if github_issue is None:
            continue

        if rel_type == "System.LinkTypes.Hierarchy-Reverse":
            # This item's parent
            result["parent_ref"] = f"#{github_issue}"
        elif rel_type == "System.LinkTypes.Hierarchy-Forward":
            # This item's child
            result["child_refs"].append(f"#{github_issue}")

    return result
