"""Azure DevOps REST API client library for Dark Forge."""

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
from governance.integrations.ado.health import HealthCheckResult, HealthStatus, run_health_checks
from governance.integrations.ado.retry import RetryResult, retry_failed
from governance.integrations.ado.dashboard import generate_dashboard_emission
from governance.integrations.ado.hierarchy import (
    parse_child_references,
    parse_parent_reference,
    sync_hierarchy_from_ado,
    sync_hierarchy_to_ado,
    validate_type_hierarchy,
)
from governance.integrations.ado.comments_sync import (
    format_ado_to_github_comment,
    format_github_to_ado_comment,
    should_sync_comment,
    sync_comment_from_ado,
    sync_comment_to_ado,
)
from governance.integrations.ado.area_iteration import (
    map_area_path_to_label,
    map_iteration_to_milestone,
    map_label_to_area_path,
    map_milestone_to_iteration,
)
from governance.integrations.ado.bulk_sync import initial_sync
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
    # Health checks
    "HealthCheckResult",
    "HealthStatus",
    "run_health_checks",
    # Retry processor
    "RetryResult",
    "retry_failed",
    # Dashboard
    "generate_dashboard_emission",
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
    # Hierarchy sync
    "parse_parent_reference",
    "parse_child_references",
    "sync_hierarchy_to_ado",
    "sync_hierarchy_from_ado",
    "validate_type_hierarchy",
    # Comment sync
    "should_sync_comment",
    "format_github_to_ado_comment",
    "format_ado_to_github_comment",
    "sync_comment_to_ado",
    "sync_comment_from_ado",
    # Area/iteration mapping
    "map_label_to_area_path",
    "map_area_path_to_label",
    "map_milestone_to_iteration",
    "map_iteration_to_milestone",
    # Bulk sync
    "initial_sync",
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
