"""Azure DevOps REST API client library for Dark Factory Governance."""

from governance.integrations.ado._types import (
    AccessMethod,
    AuthMethod,
    ClassificationNode,
    Comment,
    FieldDefinition,
    PatchOperation,
    WiqlResult,
    WorkItem,
    WorkItemExpand,
    WorkItemType,
)
from governance.integrations.ado._exceptions import (
    AdoAuthError,
    AdoConfigError,
    AdoError,
    AdoNotFoundError,
    AdoRateLimitError,
    AdoServerError,
    AdoValidationError,
)
from governance.integrations.ado.auth import (
    AuthProvider,
    ManagedIdentityAuth,
    PatAuth,
    ServicePrincipalAuth,
    create_auth_provider,
)
from governance.integrations.ado.client import AdoClient
from governance.integrations.ado.config import AdoConfig, load_config, validate_config_schema
from governance.integrations.ado.mappers import (
    map_github_fields_to_ado_patch,
    map_github_labels_to_ado_type,
    map_github_priority_to_ado,
    map_github_state_to_ado,
    map_github_user_to_ado,
)
from governance.integrations.ado.sync_engine import SyncEngine, SyncResult
from governance.integrations.ado.reverse_sync import ReverseSyncEngine
from governance.integrations.ado.reverse_mappers import (
    map_ado_fields_to_github,
    map_ado_priority_to_github,
    map_ado_state_to_github,
    map_ado_user_to_github,
)
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

__all__ = [
    # Client
    "AdoClient",
    # Config
    "AdoConfig",
    "load_config",
    "validate_config_schema",
    # Auth
    "AuthProvider",
    "PatAuth",
    "ServicePrincipalAuth",
    "ManagedIdentityAuth",
    "create_auth_provider",
    # Types
    "AccessMethod",
    "AuthMethod",
    "ClassificationNode",
    "Comment",
    "FieldDefinition",
    "PatchOperation",
    "WiqlResult",
    "WorkItem",
    "WorkItemExpand",
    "WorkItemType",
    # Exceptions
    "AdoError",
    "AdoAuthError",
    "AdoNotFoundError",
    "AdoRateLimitError",
    "AdoValidationError",
    "AdoServerError",
    "AdoConfigError",
    # Sync engine
    "SyncEngine",
    "SyncResult",
    # Reverse sync engine
    "ReverseSyncEngine",
    # Mappers (GitHub -> ADO)
    "map_github_state_to_ado",
    "map_github_labels_to_ado_type",
    "map_github_fields_to_ado_patch",
    "map_github_priority_to_ado",
    "map_github_user_to_ado",
    # Reverse mappers (ADO -> GitHub)
    "map_ado_state_to_github",
    "map_ado_fields_to_github",
    "map_ado_priority_to_github",
    "map_ado_user_to_github",
    # Patch builder
    "add_field",
    "add_github_commit_link",
    "add_github_pr_link",
    "add_hyperlink",
    "replace_field",
    "remove_field",
    "remove_relation",
    "add_relation",
    "add_tag",
    "set_area_path",
    "set_iteration_path",
    "to_json_patch",
]
