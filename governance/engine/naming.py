"""Core naming logic — pattern assembly, length enforcement, validation.

Produces predictable, Azure-compliant resource names following JM naming
conventions. Three patterns (standard, mini, small) handle different Azure
resource constraints.

Deterministic shortening guarantees:
- prefix, lob, stage, and appId are NEVER reduced
- appName is truncated from the right first, then role
- The shortened form is always derivable from the original components
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from governance.engine.naming_data import (
    RESOURCE_TYPES,
    VALID_LOBS,
    VALID_STAGES,
    ResourceTypeInfo,
)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class NamingError(Exception):
    """Raised when a resource name cannot be generated or validated."""


# ---------------------------------------------------------------------------
# Input container
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NamingInput:
    """Validated input for name generation."""

    resource_type: str
    lob: str
    stage: str
    app_name: str
    app_id: str
    role: str = ""
    location: str = ""

    def __post_init__(self) -> None:
        errors: list[str] = []
        if self.resource_type not in RESOURCE_TYPES:
            errors.append(
                f"Unsupported resource type: {self.resource_type}. "
                f"Use list_resource_types() to see supported types."
            )
        if self.lob.lower() not in VALID_LOBS:
            errors.append(
                f"Invalid LOB '{self.lob}'. Must be one of: {sorted(VALID_LOBS)}"
            )
        if self.stage.lower() not in VALID_STAGES:
            errors.append(
                f"Invalid stage '{self.stage}'. Must be one of: {sorted(VALID_STAGES)}"
            )
        if not _validate_app_id(self.app_id):
            errors.append(
                f"Invalid app_id '{self.app_id}'. Must be a single letter (a-z), "
                "optionally followed by '-si' for shared infrastructure."
            )
        if not self.app_name:
            errors.append("app_name is required and cannot be empty.")

        # Role is required for standard pattern
        if self.resource_type in RESOURCE_TYPES:
            info = RESOURCE_TYPES[self.resource_type]
            if info.pattern == "standard" and not self.role:
                errors.append(
                    f"role is required for standard-pattern resource type "
                    f"{self.resource_type}."
                )

        if errors:
            raise NamingError("; ".join(errors))


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_APP_ID_RE = re.compile(r"^[a-z](-si)?$")


def _validate_app_id(app_id: str) -> bool:
    """Return True if app_id is a single lowercase letter, optionally with -si."""
    return bool(_APP_ID_RE.match(app_id.lower()))


# ---------------------------------------------------------------------------
# Name generation
# ---------------------------------------------------------------------------


def generate_name(inp: NamingInput) -> str:
    """Generate an Azure-compliant resource name from validated input.

    Returns the shortest compliant name, applying deterministic truncation
    when the full name exceeds the resource type's max length.
    """
    info = RESOURCE_TYPES[inp.resource_type]

    if info.pattern == "mini":
        return _generate_mini(inp, info)
    elif info.pattern == "small":
        return _generate_small(inp, info)
    else:
        return _generate_standard(inp, info)


def _generate_standard(inp: NamingInput, info: ResourceTypeInfo) -> str:
    """Standard pattern: {prefix}-{lob}-{stage}-{appName}-{role}-{appId}

    With optional location: {prefix}-{lob}-{stage}-{appName}-{role}-{location}-{appId}
    """
    prefix = info.prefix
    lob = inp.lob.lower()
    stage = inp.stage.lower()
    app_name = inp.app_name.lower()
    role = inp.role.lower()
    app_id = inp.app_id.lower()
    location = inp.location.lower() if inp.location else ""

    # Fixed parts that are never truncated
    if location:
        fixed = f"{prefix}-{lob}-{stage}-{{appName}}-{{role}}-{location}-{app_id}"
    else:
        fixed = f"{prefix}-{lob}-{stage}-{{appName}}-{{role}}-{app_id}"

    # Calculate budget for variable parts
    # Replace placeholders with empty to measure fixed overhead
    fixed_len = len(fixed.replace("{appName}", "").replace("{role}", ""))
    budget = info.max_length - fixed_len

    if budget <= 0:
        raise NamingError(
            f"Cannot fit name within {info.max_length} chars for "
            f"{info.resource_type}. Fixed parts alone exceed the limit."
        )

    # Deterministic shortening: truncate appName first, then role
    truncated_app, truncated_role = _shorten_pair(app_name, role, budget)

    if location:
        name = f"{prefix}-{lob}-{stage}-{truncated_app}-{truncated_role}-{location}-{app_id}"
    else:
        name = f"{prefix}-{lob}-{stage}-{truncated_app}-{truncated_role}-{app_id}"

    return name


def _generate_mini(inp: NamingInput, info: ResourceTypeInfo) -> str:
    """Mini pattern: {prefix}{lob}{stage}{shortName} — no hyphens, typically <=24 chars."""
    prefix = info.prefix
    lob = inp.lob.lower()
    stage = inp.stage.lower()
    app_name = inp.app_name.lower()

    # Remove any hyphens/underscores from app_name for mini pattern
    clean_name = re.sub(r"[-_]", "", app_name)

    fixed_len = len(prefix) + len(lob) + len(stage)
    budget = info.max_length - fixed_len

    if budget <= 0:
        raise NamingError(
            f"Cannot fit name within {info.max_length} chars for "
            f"{info.resource_type}. Fixed parts alone exceed the limit."
        )

    truncated = clean_name[:budget]
    return f"{prefix}{lob}{stage}{truncated}"


def _generate_small(inp: NamingInput, info: ResourceTypeInfo) -> str:
    """Small pattern: {prefix}-{lob}-{stage}-{shortName} — hyphens allowed, <=60 chars."""
    prefix = info.prefix
    lob = inp.lob.lower()
    stage = inp.stage.lower()
    app_name = inp.app_name.lower()

    fixed_len = len(prefix) + 1 + len(lob) + 1 + len(stage) + 1  # hyphens
    budget = info.max_length - fixed_len

    if budget <= 0:
        raise NamingError(
            f"Cannot fit name within {info.max_length} chars for "
            f"{info.resource_type}. Fixed parts alone exceed the limit."
        )

    truncated = app_name[:budget]
    return f"{prefix}-{lob}-{stage}-{truncated}"


# ---------------------------------------------------------------------------
# Deterministic shortening
# ---------------------------------------------------------------------------


def _shorten_pair(app_name: str, role: str, budget: int) -> tuple[str, str]:
    """Shorten appName and role to fit within *budget* total characters.

    Strategy (deterministic):
    1. If both fit, return as-is.
    2. Truncate appName from the right until it fits (min 1 char).
    3. If still too long, truncate role from the right (min 1 char).
    4. If even 1+1 doesn't fit, raise NamingError.
    """
    total = len(app_name) + len(role)
    if total <= budget:
        return app_name, role

    # Phase 1: truncate appName first
    min_app = 1
    min_role = 1

    if min_app + len(role) <= budget:
        # Role fits, shorten appName to fill remaining budget
        new_app_len = budget - len(role)
        return app_name[:new_app_len], role

    if min_app + min_role > budget:
        raise NamingError(
            f"Cannot fit appName and role within {budget} chars. "
            f"Need at least 2 characters but have budget of {budget}."
        )

    # Phase 2: appName at minimum, shorten role
    new_role_len = budget - min_app
    return app_name[:min_app], role[:new_role_len]


# ---------------------------------------------------------------------------
# Name validation
# ---------------------------------------------------------------------------


def validate_name(name: str, resource_type: str) -> dict[str, Any]:
    """Validate a given name against the rules for a resource type.

    Returns a dict with:
    - valid: bool
    - errors: list[str] (empty if valid)
    - resource_type: str
    - max_length: int
    - actual_length: int
    """
    errors: list[str] = []

    if resource_type not in RESOURCE_TYPES:
        return {
            "valid": False,
            "errors": [f"Unsupported resource type: {resource_type}"],
            "resource_type": resource_type,
            "max_length": 0,
            "actual_length": len(name),
        }

    info = RESOURCE_TYPES[resource_type]

    if len(name) > info.max_length:
        errors.append(
            f"Name length {len(name)} exceeds maximum {info.max_length} "
            f"for {resource_type}."
        )

    if not info.allows_hyphens and "-" in name:
        errors.append(
            f"Hyphens are not allowed for {resource_type} (pattern: {info.pattern})."
        )

    if not name:
        errors.append("Name cannot be empty.")

    # Check starts with expected prefix
    expected_prefix = info.prefix
    if info.pattern == "mini":
        if not name.startswith(expected_prefix):
            errors.append(
                f"Name should start with prefix '{expected_prefix}' "
                f"for {resource_type}."
            )
    else:
        if not name.startswith(f"{expected_prefix}-"):
            errors.append(
                f"Name should start with '{expected_prefix}-' "
                f"for {resource_type}."
            )

    # Azure general: alphanumeric, hyphens (if allowed), no leading/trailing hyphen
    if name.startswith("-") or name.endswith("-"):
        errors.append("Name must not start or end with a hyphen.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "resource_type": resource_type,
        "max_length": info.max_length,
        "actual_length": len(name),
    }


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------


def list_resource_types() -> list[dict[str, Any]]:
    """Return a list of all supported resource types with their metadata."""
    return [
        {
            "resource_type": info.resource_type,
            "prefix": info.prefix,
            "max_length": info.max_length,
            "pattern": info.pattern,
            "allows_hyphens": info.allows_hyphens,
        }
        for info in sorted(RESOURCE_TYPES.values(), key=lambda x: x.resource_type)
    ]
