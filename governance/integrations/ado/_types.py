"""Data types for the Azure DevOps client."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AccessMethod(Enum):
    """How to reach ADO — REST API or az CLI."""

    API = "api"
    AZ_CLI = "az_cli"


class AuthMethod(Enum):
    """Supported authentication methods."""

    PAT = "pat"
    SERVICE_PRINCIPAL = "service_principal"
    MANAGED_IDENTITY = "managed_identity"


class WorkItemExpand(Enum):
    """Work item expansion options for $expand query parameter."""

    NONE = "None"
    RELATIONS = "Relations"
    FIELDS = "Fields"
    LINKS = "Links"
    ALL = "All"


@dataclass(frozen=True)
class PatchOperation:
    """A single JSON Patch operation for work item updates."""

    op: str
    path: str
    value: Any = None
    from_: str | None = None


@dataclass(frozen=True)
class WorkItem:
    """An Azure DevOps work item."""

    id: int
    rev: int
    url: str
    fields: dict[str, Any] = field(default_factory=dict)
    relations: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class WiqlResult:
    """Result of a WIQL query — contains work item IDs only."""

    query_type: str
    as_of: str
    work_item_ids: list[int] = field(default_factory=list)


@dataclass(frozen=True)
class ClassificationNode:
    """An area path or iteration path node."""

    id: int
    name: str
    structure_type: str
    path: str
    has_children: bool = False
    children: list[ClassificationNode] = field(default_factory=list)


@dataclass(frozen=True)
class FieldDefinition:
    """A work item field definition."""

    name: str
    reference_name: str
    type: str
    description: str = ""
    read_only: bool = False


@dataclass(frozen=True)
class Comment:
    """A work item comment. Text is HTML, not Markdown."""

    id: int
    work_item_id: int
    text: str
    created_by: str = ""
    created_date: str = ""
    modified_date: str = ""
    version: int = 1


@dataclass(frozen=True)
class WorkItemType:
    """A work item type definition."""

    name: str
    description: str = ""
    icon_url: str = ""
    fields: list[dict[str, Any]] = field(default_factory=list)
