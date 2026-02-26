"""Azure resource type data — prefixes, max lengths, character constraints.

Each entry maps an Azure resource provider type to its naming metadata:
- prefix: Short prefix used in the generated name
- max_length: Maximum allowed characters for the resource name
- pattern: Which naming pattern to use (standard, mini, small)
- allows_hyphens: Whether hyphens are permitted in the name
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceTypeInfo:
    """Immutable metadata for an Azure resource type."""

    resource_type: str
    prefix: str
    max_length: int
    pattern: str  # "standard" | "mini" | "small"
    allows_hyphens: bool


# ---------------------------------------------------------------------------
# Canonical resource type registry
# ---------------------------------------------------------------------------

RESOURCE_TYPES: dict[str, ResourceTypeInfo] = {
    info.resource_type: info
    for info in [
        # SQL
        ResourceTypeInfo("Microsoft.Sql/servers", "sql", 63, "standard", True),
        ResourceTypeInfo("Microsoft.Sql/servers/databases", "sqldb", 128, "standard", True),
        # Web / App Service
        ResourceTypeInfo("Microsoft.Web/sites", "app", 60, "standard", True),
        ResourceTypeInfo("Microsoft.Web/serverfarms", "plan", 40, "standard", True),
        ResourceTypeInfo("Microsoft.Web/sites/function", "func", 60, "standard", True),
        # API Management
        ResourceTypeInfo("Microsoft.ApiManagement/service", "apim", 50, "standard", True),
        # Cosmos DB
        ResourceTypeInfo("Microsoft.DocumentDB/databaseAccounts", "cosmos", 44, "standard", True),
        # Cache
        ResourceTypeInfo("Microsoft.Cache/Redis", "redis", 63, "standard", True),
        # Messaging
        ResourceTypeInfo("Microsoft.ServiceBus/namespaces", "sb", 50, "standard", True),
        ResourceTypeInfo("Microsoft.EventHub/namespaces", "evh", 50, "standard", True),
        # Monitoring
        ResourceTypeInfo("Microsoft.OperationalInsights/workspaces", "log", 63, "standard", True),
        # Key Vault (mini pattern, no hyphens, 24 max)
        ResourceTypeInfo("Microsoft.KeyVault/vaults", "kv", 24, "mini", False),
        # Storage (mini pattern, no hyphens, 24 max)
        ResourceTypeInfo("Microsoft.Storage/storageAccounts", "st", 24, "mini", False),
        # Container Registry (mini pattern, no hyphens, 50 max)
        ResourceTypeInfo("Microsoft.ContainerRegistry/registries", "cr", 50, "mini", False),
        # App Configuration (small pattern)
        ResourceTypeInfo("Microsoft.AppConfiguration/configurationStores", "appcs", 50, "small", True),
        # Application Insights (small pattern)
        ResourceTypeInfo("Microsoft.Insights/components", "appi", 260, "small", True),
        # Networking
        ResourceTypeInfo("Microsoft.Network/virtualNetworks", "vnet", 64, "standard", True),
        ResourceTypeInfo("Microsoft.Network/networkSecurityGroups", "nsg", 80, "standard", True),
        ResourceTypeInfo("Microsoft.Network/publicIPAddresses", "pip", 80, "standard", True),
        # Identity
        ResourceTypeInfo("Microsoft.ManagedIdentity/userAssignedIdentities", "id", 128, "standard", True),
        # AKS
        ResourceTypeInfo("Microsoft.ContainerService/managedClusters", "aks", 63, "standard", True),
        # Application Gateway
        ResourceTypeInfo("Microsoft.Network/applicationGateways", "agw", 80, "standard", True),
    ]
}


# ---------------------------------------------------------------------------
# Validation constants
# ---------------------------------------------------------------------------

VALID_LOBS: set[str] = {"jma", "jmf", "jmfe", "set", "setf", "to", "ocio", "octo", "lexus"}

VALID_STAGES: set[str] = {"dev", "stg", "qa", "uat", "prod", "nonprod"}

# ---------------------------------------------------------------------------
# v2 mini-pattern code tables — 1-char codes for compact resource names
# ---------------------------------------------------------------------------

LOB_CODES: dict[str, str] = {
    "set": "s",
    "setf": "v",
    "jma": "j",
    "jmf": "f",
    "jmfe": "e",
    "to": "t",
    "ocio": "i",
    "octo": "c",
    "lexus": "l",
}

STAGE_CODES: dict[str, str] = {
    "dev": "d",
    "stg": "s",
    "qa": "q",
    "uat": "u",
    "prod": "p",
    "nonprod": "n",
}
