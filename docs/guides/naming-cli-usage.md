# Azure Resource Naming CLI

Generate predictable, Azure-compliant resource names following JM naming conventions (v2 scheme).

## Quick Start

```bash
# Generate a SQL Server name (standard pattern)
python bin/generate-name.py \
    --resource-type Microsoft.Sql/servers \
    --lob set --stage dev \
    --app-name payments --app-id a --role db

# Output: sql-set-dev-payments-db-a

# Generate a Key Vault name (mini pattern with LOB/stage codes)
python bin/generate-name.py \
    --resource-type Microsoft.KeyVault/vaults \
    --lob set --stage dev \
    --app-name myapp --app-id a

# Output: kvsdmyappa
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
| `--app-id` | Yes | Application ID — single lowercase letter (a-z) |
| `--role` | Standard pattern | Component role (web, db, api, etc.). Included in mini/small when provided. |
| `--location` | No | Azure region short name (e.g., eastus) |
| `--json` | No | Output as structured JSON |
| `--validate-only` | No | Validate a given name instead of generating |
| `--list-types` | No | List all supported resource types |

## Naming Patterns (v2)

The v2 naming scheme uses 1-character LOB and stage codes in the mini pattern, and always includes `role` and `appId` in all patterns to prevent name collisions.

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
```

### Mini Pattern (v2)

`{prefix}{lobCode}{stageCode}{appName}{role}{appId}` (no hyphens)

Used for resources with strict character limits (Key Vault, Storage Account, Container Registry). Uses 1-character LOB codes and stage codes for maximum compactness. Always includes role (when provided) and appId.

```bash
# Key Vault (max 24 chars, no hyphens)
python bin/generate-name.py \
    --resource-type Microsoft.KeyVault/vaults \
    --lob set --stage dev --app-name myapp --app-id a
# Output: kvsdmyappa

# Storage Account with role (collision-safe)
python bin/generate-name.py \
    --resource-type Microsoft.Storage/storageAccounts \
    --lob set --stage dev --app-name acctach --role chk --app-id a
# Output: stsdacctachchka

# Same app, different role → different name
python bin/generate-name.py \
    --resource-type Microsoft.Storage/storageAccounts \
    --lob set --stage dev --app-name acctach --role rpt --app-id a
# Output: stsdacctachrpta
```

### Small Pattern (v2)

`{prefix}-{lob}-{stage}-{appName}-{role}-{appId}`

Used for resources with moderate length limits. Now includes role (when provided) and appId.

```bash
# App Configuration (max 50 chars)
python bin/generate-name.py \
    --resource-type Microsoft.AppConfiguration/configurationStores \
    --lob set --stage dev --app-name platform --app-id a
# Output: appcs-set-dev-platform-a

# App Insights with role
python bin/generate-name.py \
    --resource-type Microsoft.Insights/components \
    --lob set --stage dev --app-name myapp --app-id a --role web
# Output: appi-set-dev-myapp-web-a
```

## LOB Codes (Mini Pattern)

| LOB | Code |
|-----|------|
| set | s |
| setf | v |
| jma | j |
| jmf | f |
| jmfe | e |
| to | t |
| ocio | i |
| octo | c |
| lexus | l |

## Stage Codes (Mini Pattern)

| Stage | Code |
|-------|------|
| dev | d |
| stg | s |
| qa | q |
| uat | u |
| prod | p |
| nonprod | n |

## Deterministic Shortening

When a generated name exceeds the resource type's maximum length, the CLI applies deterministic truncation:

1. `appName` is truncated from the right first
2. If still too long, `role` is truncated from the right
3. `prefix`, `lob`/`lobCode`, `stage`/`stageCode`, and `appId` are **never** reduced

This ensures the shortened form is always derivable from the original components.

## Valid Values

**Lines of Business (LOB):** jma, jmf, jmfe, set, setf, to, ocio, octo, lexus

**Deployment Stages:** dev, stg, qa, uat, prod, nonprod

**Application ID:** Single lowercase letter (a-z)

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

## IaC Integration

### Bicep

Use the naming module for v2-compliant names in Bicep deployments:

```bicep
// Import the naming module
module naming 'modules/naming.bicep' = {
  name: 'naming'
  params: {
    lob: 'set'
    stage: 'dev'
    appName: 'myapp'
    appId: 'a'
    role: 'web'
  }
}

// Use generated names
resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: naming.outputs.keyVaultName    // kvsdmyappweba
  location: location
  // ...
}

resource st 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: naming.outputs.storageAccountName  // stsdmyappweba
  location: location
  // ...
}
```

When using the SET-Apps Bicep registry (`br/acr-prod:modules/util:v0`), the registry's `getResourceNames()` function handles naming. The local naming module is for projects that need standalone v2-compliant naming without the registry dependency.

### Terraform

```hcl
module "naming" {
  source   = "./modules/naming"
  lob      = "set"
  stage    = "dev"
  app_name = "myapp"
  app_id   = "a"
  role     = "web"
}

resource "azurerm_key_vault" "main" {
  name = module.naming.key_vault_name  # kvsdmyappweba
  # ...
}
```

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
