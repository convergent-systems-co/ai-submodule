# Azure Dashboard Templates

Importable Azure Portal dashboard JSON files for applications using the Dark Forge framework. These dashboards provide a hub-and-spoke model: one hub dashboard links to per-environment dashboards with detailed metrics.

## Templates

| File | Purpose |
|------|---------|
| `hub-dashboard.json` | Central dashboard with links to all environment dashboards and an application overview |
| `environment-dashboard.json` | Per-environment dashboard with resource group resources, App Insights metrics, and AKS status |

## Placeholders

Before importing, replace these placeholders with your actual values:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{{SUBSCRIPTION_ID}}` | Azure subscription ID | `a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| `{{RESOURCE_GROUP}}` | Full resource group name (environment dashboards) | `rg-myapp-prod` |
| `{{RESOURCE_GROUP_PREFIX}}` | Resource group name prefix (hub dashboard) | `rg-myapp` |
| `{{ENVIRONMENT}}` | Environment name | `dev`, `stg`, `uat`, `prod` |
| `{{APPLICATION_NAME}}` | Application display name | `my-app` |
| `{{APP_INSIGHTS_NAME}}` | Application Insights resource name | `appi-myapp-prod` |
| `{{AKS_CLUSTER_NAME}}` | AKS cluster resource name | `aks-myapp-prod` |
| `{{AZURE_LOCATION}}` | Azure region for the dashboard resource | `eastus2` |

## Quick Start

### 1. Copy and parameterize

Copy the template files into your repository and replace placeholders using `sed` or your preferred tool.

> **Note:** The `sed -i` flag behaves differently on macOS and Linux. macOS (BSD sed) requires an empty string argument: `sed -i '' 's/...'`. Linux (GNU sed) uses `sed -i 's/...'` without the extra argument. The examples below use the macOS syntax. On Linux, remove the `''` after `-i`.

```bash
# Copy templates
cp .ai/governance/templates/dashboards/*.json dashboards/

# Replace placeholders for a production environment dashboard
# macOS (BSD sed):
sed -i '' \
  -e 's/{{SUBSCRIPTION_ID}}/a1b2c3d4-e5f6-7890-abcd-ef1234567890/g' \
  -e 's/{{RESOURCE_GROUP}}/rg-myapp-prod/g' \
  -e 's/{{ENVIRONMENT}}/prod/g' \
  -e 's/{{APPLICATION_NAME}}/my-app/g' \
  -e 's/{{APP_INSIGHTS_NAME}}/appi-myapp-prod/g' \
  -e 's/{{AKS_CLUSTER_NAME}}/aks-myapp-prod/g' \
  -e 's/{{AZURE_LOCATION}}/eastus2/g' \
  dashboards/environment-dashboard.json

# Linux (GNU sed):
# sed -i \
#   -e 's/{{SUBSCRIPTION_ID}}/a1b2c3d4-e5f6-7890-abcd-ef1234567890/g' \
#   ... (same flags) ...
#   dashboards/environment-dashboard.json

# Replace placeholders for the hub dashboard
sed -i '' \
  -e 's/{{SUBSCRIPTION_ID}}/a1b2c3d4-e5f6-7890-abcd-ef1234567890/g' \
  -e 's/{{RESOURCE_GROUP_PREFIX}}/rg-myapp/g' \
  -e 's/{{APPLICATION_NAME}}/my-app/g' \
  -e 's/{{AZURE_LOCATION}}/eastus2/g' \
  dashboards/hub-dashboard.json
```

### 2. Import into Azure Portal

1. Open the [Azure Portal](https://portal.azure.com)
2. Navigate to **Dashboard** (top-left hamburger menu or search "Dashboard")
3. Click **+ New dashboard** then **Import a custom dashboard**
4. Select the parameterized JSON file
5. Click **Save**

### 3. Generate per-environment dashboards

Create one environment dashboard per environment by copying `environment-dashboard.json` and replacing placeholders with environment-specific values:

```bash
# macOS (BSD sed) — on Linux, remove '' after -i
for env in dev stg uat prod; do
  cp .ai/governance/templates/dashboards/environment-dashboard.json \
     dashboards/${env}-dashboard.json

  sed -i '' \
    -e "s/{{SUBSCRIPTION_ID}}/YOUR_SUBSCRIPTION_ID/g" \
    -e "s/{{RESOURCE_GROUP}}/rg-myapp-${env}/g" \
    -e "s/{{ENVIRONMENT}}/${env}/g" \
    -e "s/{{APPLICATION_NAME}}/my-app/g" \
    -e "s/{{APP_INSIGHTS_NAME}}/appi-myapp-${env}/g" \
    -e "s/{{AKS_CLUSTER_NAME}}/aks-myapp-${env}/g" \
    -e "s/{{AZURE_LOCATION}}/eastus2/g" \
    dashboards/${env}-dashboard.json
done
```

## Deploying via Bicep

You can also deploy dashboards as Azure resources using Bicep. Note that `loadTextContent()` requires a file path that is known at compile time — it does not support runtime variable interpolation (e.g., `'dashboards/${environment}-dashboard.json'` will not work). You must declare a separate resource per environment with a hardcoded file path:

```bicep
// Each environment needs its own resource declaration because
// loadTextContent() requires a compile-time constant file path.

resource devDashboard 'Microsoft.Portal/dashboards@2020-09-01-preview' = if (environment == 'dev') {
  name: '${applicationName}-dev-dashboard'
  location: location
  tags: {
    'hidden-title': '${applicationName} — dev Dashboard'
    Application: applicationName
    Environment: 'dev'
    ManagedBy: 'dark-forge'
  }
  properties: json(loadTextContent('dashboards/dev-dashboard.json')).properties
}

resource prodDashboard 'Microsoft.Portal/dashboards@2020-09-01-preview' = if (environment == 'prod') {
  name: '${applicationName}-prod-dashboard'
  location: location
  tags: {
    'hidden-title': '${applicationName} — prod Dashboard'
    Application: applicationName
    Environment: 'prod'
    ManagedBy: 'dark-forge'
  }
  properties: json(loadTextContent('dashboards/prod-dashboard.json')).properties
}

// Repeat for stg, uat as needed.
```

## Removing AKS Tiles

If your environment does not use AKS, remove parts `"6"` (AKS Pod Status) and `"7"` (AKS Container Logs) from the environment dashboard JSON before importing. The dashboard will function correctly without them.

## Configuration

Enable dashboard support in your `project.yaml`:

```yaml
dashboards:
  enabled: true
  environments:
    - dev
    - stg
    - uat
    - prod
```

See the `project.yaml` template for all available dashboard configuration options.
