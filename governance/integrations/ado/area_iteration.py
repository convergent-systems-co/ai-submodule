"""Area path and iteration path mapping between GitHub and ADO.

Maps GitHub labels to ADO area paths and GitHub milestones to ADO
iteration paths, using configuration from ``project.yaml``.

Labels with the ``area:`` prefix are matched against the
``area_path_mapping`` configuration.  Milestones are matched against
the ``iteration_mapping`` configuration.

The ``@CurrentIteration`` macro is passed through to ADO as-is and
is never reverse-mapped.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# The ADO @CurrentIteration macro — passed through, never reverse-mapped
_CURRENT_ITERATION_MACRO = "@CurrentIteration"


# ── Area path mapping ──────────────────────────────────────────────────────


def map_label_to_area_path(labels: list[str], config: dict) -> str | None:
    """Match ``area:*`` labels to an ADO area path via config mapping.

    Iterates through ``labels`` looking for ones prefixed with ``area:``.
    The suffix (after ``area:``) is looked up in the ``area_path_mapping``
    configuration.

    Args:
        labels: List of GitHub label names.
        config: The ``ado_integration`` config dict.  Expected key:
                ``area_path_mapping`` — a dict mapping label suffixes to
                ADO area paths.

    Returns:
        The mapped ADO area path, or ``None`` if no match.
    """
    mapping: dict[str, str] = config.get("area_path_mapping", {})
    if not mapping:
        return None

    for label in labels:
        if label.lower().startswith("area:"):
            suffix = label[5:].strip()
            if suffix in mapping:
                return mapping[suffix]
            # Try case-insensitive lookup
            for key, value in mapping.items():
                if key.lower() == suffix.lower():
                    return value

    return None


def map_area_path_to_label(area_path: str, config: dict) -> str | None:
    """Reverse-map an ADO area path to a GitHub ``area:*`` label.

    Args:
        area_path: The full ADO area path (e.g., ``"Project\\Team A"``).
        config: The ``ado_integration`` config dict.

    Returns:
        A GitHub label string (e.g., ``"area:Team A"``), or ``None``
        if no reverse mapping exists.
    """
    mapping: dict[str, str] = config.get("area_path_mapping", {})
    if not mapping:
        return None

    # Build reverse lookup: area_path -> label_suffix
    for label_suffix, mapped_path in mapping.items():
        if mapped_path == area_path:
            return f"area:{label_suffix}"

    return None


# ── Iteration path mapping ─────────────────────────────────────────────────


def map_milestone_to_iteration(milestone_title: str, config: dict) -> str | None:
    """Match a GitHub milestone title to an ADO iteration path.

    The ``@CurrentIteration`` macro is a special value that is passed
    through to ADO as-is.

    Args:
        milestone_title: The GitHub milestone title.
        config: The ``ado_integration`` config dict.  Expected key:
                ``iteration_mapping`` — a dict mapping milestone titles
                to ADO iteration paths.

    Returns:
        The mapped ADO iteration path, or ``None`` if no match.
    """
    if not milestone_title:
        return None

    mapping: dict[str, str] = config.get("iteration_mapping", {})
    if not mapping:
        return None

    # Direct lookup
    if milestone_title in mapping:
        value = mapping[milestone_title]
        return value

    # Case-insensitive fallback
    for key, value in mapping.items():
        if key.lower() == milestone_title.lower():
            return value

    return None


def map_iteration_to_milestone(iteration_path: str, config: dict) -> str | None:
    """Reverse-map an ADO iteration path to a GitHub milestone title.

    The ``@CurrentIteration`` macro is **not** reverse-mapped — it
    returns ``None`` since it has no stable milestone equivalent.

    Args:
        iteration_path: The full ADO iteration path.
        config: The ``ado_integration`` config dict.

    Returns:
        A GitHub milestone title, or ``None`` if no reverse mapping
        exists or if the path is the ``@CurrentIteration`` macro.
    """
    if not iteration_path:
        return None

    # Never reverse-map the @CurrentIteration macro
    if iteration_path == _CURRENT_ITERATION_MACRO:
        return None

    mapping: dict[str, str] = config.get("iteration_mapping", {})
    if not mapping:
        return None

    # Build reverse lookup: iteration_path -> milestone_title
    for milestone_title, mapped_path in mapping.items():
        # Skip @CurrentIteration values in the mapping
        if mapped_path == _CURRENT_ITERATION_MACRO:
            continue
        if mapped_path == iteration_path:
            return milestone_title

    return None
