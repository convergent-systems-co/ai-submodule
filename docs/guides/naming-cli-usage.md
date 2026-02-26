# Azure Resource Naming CLI

Generate predictable, Azure-compliant resource names following JM naming conventions.

## Quick Start

```bash
# Generate a SQL Server name
python bin/generate-name.py \
    --resource-type Microsoft.Sql/servers \
    --lob set --stage dev \
    --app-name payments --app-id a --role db

# Output: sql-set-dev-payments-db-a
```

## Installation

No additional dependencies required. The CLI uses only Python standard library plus the `governance.engine.naming` module included in this repository.

Requires Python 3.9+.

## Usage

### Generate a Resource Name

```bash
python bin/generate-name.py \
    --resource-type <AZURE_RESOURCE_TYPE> \
    --lob <LINE_OF_BUSINESS> \
    --stage <DEPLOYMENT_STAGE> \
    --app-name <APPLICATION_NAME> \
    --app-id <APPLICATION_ID> \
    --role <COMPONENT_ROLE>           # required for standard pattern
    [--location <AZURE_REGION>]       # optional
    [--json]                          # optional: structured JSON output
```

### List Supported Resource Types

```bash
python bin/generate-name.py --list-types
python bin/generate-name.py --list-types --json
```

### Validate an Existing Name

```bash
python bin/generate-name.py \
    --validate-only "sql-set-dev-payments-db-a" \
    --resource-type Microsoft.Sql/servers
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--resource-type` | Yes | Azure resource type (e.g., `Microsoft.KeyVault/vaults`) |
| `--lob` | Yes | Line of business |
| `--stage` | Yes | Deployment stage |
| `--app-name` | Yes | Application name |
| `--app-id` | Yes | Application ID (single letter a-z, optionally with `-si`) |
| `--role` | Standard pattern | Component role (web, db, api, etc.) |
| `--location` | No | Azure region short name (e.g., eastus) |
| `--json` | No | Output as structured JSON |
| `--validate-only` | No | Validate a given name instead of generating |
| `--list-types` | No | List all supported resource types |

## Naming Patterns

### Standard Pattern

`{prefix}-{lob}-{stage}-{appName}-{role}-{appId}`

Used for most Azure resources. With optional location: `{prefix}-{lob}-{stage}-{appName}-{role}-{location}-{appId}`

```bash
# SQL Server
python bin/generate-name.py \
    --resource-type Microsoft.Sql/servers \
    --lob set --stage prod --app-name billing --app-id a --role db
# Output: sql-set-prod-billing-db-a

# With location
python bin/generate-name.py \
    --resource-type Microsoft.Sql/servers \
    --lob set --stage prod --app-name billing --app-id a --role db --location eastus
# Output: sql-set-prod-billing-db-eastus-a

# Shared infrastructure
python bin/generate-name.py \
    --resource-type Microsoft.Sql/servers \
    --lob set --stage dev --app-name shared --app-id a-si --role db
# Output: sql-set-dev-shared-db-a-si
```

### Mini Pattern

`{prefix}{lob}{stage}{shortName}` (no hyphens)

Used for resources with strict character limits (Key Vault, Storage Account, Container Registry).

```bash
# Key Vault (max 24 chars, no hyphens)
python bin/generate-name.py \
    --resource-type Microsoft.KeyVault/vaults \
    --lob set --stage dev --app-name myapp --app-id a
# Output: kvsetdevmyapp

# Storage Account (max 24 chars, no hyphens)
python bin/generate-name.py \
    --resource-type Microsoft.Storage/storageAccounts \
    --lob jma --stage prod --app-name datalake --app-id b
# Output: stjmaproddatalake
```

### Small Pattern

`{prefix}-{lob}-{stage}-{shortName}`

Used for resources with moderate length limits that don't need role or appId in the name.

```bash
# App Configuration (max 50 chars)
python bin/generate-name.py \
    --resource-type Microsoft.AppConfiguration/configurationStores \
    --lob set --stage dev --app-name platform --app-id a
# Output: appcs-set-dev-platform
```

## Deterministic Shortening

When a generated name exceeds the resource type's maximum length, the CLI applies deterministic truncation:

1. `appName` is truncated from the right first
2. If still too long, `role` is truncated from the right
3. `prefix`, `lob`, `stage`, and `appId` are **never** reduced

This ensures the shortened form is always derivable from the original components.

## Valid Values

**Lines of Business (LOB):** jma, jmf, jmfe, set, setf, to, ocio, octo, lexus

**Deployment Stages:** dev, stg, uat, prod, nonprod

**Application ID:** Single lowercase letter (a-z), optionally with `-si` suffix for shared infrastructure

## JSON Output

Use `--json` for structured output suitable for scripting:

```bash
python bin/generate-name.py \
    --resource-type Microsoft.Sql/servers \
    --lob set --stage dev \
    --app-name payments --app-id a --role db --json
```

```json
{
  "name": "sql-set-dev-payments-db-a",
  "resource_type": "Microsoft.Sql/servers",
  "length": 25,
  "max_length": 63,
  "pattern": "standard",
  "inputs": {
    "lob": "set",
    "stage": "dev",
    "app_name": "payments",
    "app_id": "a",
    "role": "db",
    "location": null
  }
}
```

## Supported Resource Types

| Resource Type | Prefix | Max Length | Pattern | Hyphens |
|--------------|--------|-----------|---------|---------|
| Microsoft.Sql/servers | sql | 63 | standard | yes |
| Microsoft.Sql/servers/databases | sqldb | 128 | standard | yes |
| Microsoft.Web/sites | app | 60 | standard | yes |
| Microsoft.Web/serverfarms | plan | 40 | standard | yes |
| Microsoft.Web/sites/function | func | 60 | standard | yes |
| Microsoft.ApiManagement/service | apim | 50 | standard | yes |
| Microsoft.DocumentDB/databaseAccounts | cosmos | 44 | standard | yes |
| Microsoft.Cache/Redis | redis | 63 | standard | yes |
| Microsoft.ServiceBus/namespaces | sb | 50 | standard | yes |
| Microsoft.EventHub/namespaces | evh | 50 | standard | yes |
| Microsoft.OperationalInsights/workspaces | log | 63 | standard | yes |
| Microsoft.KeyVault/vaults | kv | 24 | mini | no |
| Microsoft.Storage/storageAccounts | st | 24 | mini | no |
| Microsoft.ContainerRegistry/registries | cr | 50 | mini | no |
| Microsoft.AppConfiguration/configurationStores | appcs | 50 | small | yes |
| Microsoft.Insights/components | appi | 260 | small | yes |
| Microsoft.Network/virtualNetworks | vnet | 64 | standard | yes |
| Microsoft.Network/networkSecurityGroups | nsg | 80 | standard | yes |
| Microsoft.Network/publicIPAddresses | pip | 80 | standard | yes |
| Microsoft.ManagedIdentity/userAssignedIdentities | id | 128 | standard | yes |
| Microsoft.ContainerService/managedClusters | aks | 63 | standard | yes |
| Microsoft.Network/applicationGateways | agw | 80 | standard | yes |

## Programmatic Usage

The naming module can be imported directly:

```python
from governance.engine.naming import NamingInput, generate_name, validate_name, list_resource_types

inp = NamingInput(
    resource_type="Microsoft.Sql/servers",
    lob="set",
    stage="dev",
    app_name="payments",
    app_id="a",
    role="db",
)
name = generate_name(inp)  # "sql-set-dev-payments-db-a"

result = validate_name(name, "Microsoft.Sql/servers")
assert result["valid"] is True
```
