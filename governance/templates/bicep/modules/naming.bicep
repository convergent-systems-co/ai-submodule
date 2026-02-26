// ============================================================================
// JM v2 Azure Resource Naming Module
// ============================================================================
//
// Generates Azure-compliant resource names following the JM v2 naming standard.
//
// Three patterns handle different Azure resource constraints:
//   - standard: {prefix}-{lob}-{stage}-{appName}-{role}-{appId}
//   - mini:     {prefix}{lobCode}{stageCode}{appName}{role}{appId}  (no hyphens)
//   - small:    {prefix}-{lob}-{stage}-{appName}-{role}-{appId}
//
// Mini uses 1-char LOB codes and 1-char stage codes for resources with strict
// length limits (Key Vault <=24, Storage <=24, Container Registry <=50).
//
// Usage:
//   module naming 'modules/naming.bicep' = {
//     name: 'naming'
//     params: {
//       lob: 'set'
//       stage: 'dev'
//       appName: 'myapp'
//       appId: 'a'
//       role: 'web'
//     }
//   }
//
//   resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
//     name: naming.outputs.keyVaultName
//     ...
//   }
//
// When the SET-Apps Bicep registry is available, prefer:
//   import { getResourceNames } from 'br/acr-prod:modules/util:v0'
// The registry module will be updated to use v2 naming. This local module
// provides standalone v2-compliant naming without the registry dependency.
//
// IMPORTANT: Bicep cannot do runtime string truncation. Names that exceed
// Azure limits will fail at ARM deployment time. Use the Python CLI
// (bin/generate-name.py) to pre-validate names before deployment.
// ============================================================================

// ---------------------------------------------------------------------------
// Parameters
// ---------------------------------------------------------------------------

@description('Line of business (set, setf, jma, jmf, jmfe, to, ocio, octo, lexus)')
param lob string

@description('Deployment stage (dev, stg, qa, uat, prod, nonprod)')
param stage string

@description('Application name — used in all patterns')
param appName string

@description('Application ID — single lowercase letter (a-z)')
@minLength(1)
@maxLength(1)
param appId string

@description('Component role (web, db, api, etc.) — required for standard pattern, optional for mini/small')
param role string = ''

@description('Azure region short name (e.g., eastus) — optional, only used in standard pattern')
param location string = ''

// ---------------------------------------------------------------------------
// LOB code map — 1-char codes for mini pattern compactness
// ---------------------------------------------------------------------------

var lobCodes = {
  set: 's'
  setf: 'v'
  jma: 'j'
  jmf: 'f'
  jmfe: 'e'
  to: 't'
  ocio: 'i'
  octo: 'c'
  lexus: 'l'
}

// ---------------------------------------------------------------------------
// Stage code map — 1-char codes for mini pattern compactness
// ---------------------------------------------------------------------------

var stageCodes = {
  dev: 'd'
  stg: 's'
  qa: 'q'
  uat: 'u'
  prod: 'p'
  nonprod: 'n'
}

// ---------------------------------------------------------------------------
// Resource prefix map — maps resource categories to their naming prefixes
// ---------------------------------------------------------------------------

var prefixes = {
  sqlServer: 'sql'
  sqlDatabase: 'sqldb'
  appService: 'app'
  appServicePlan: 'plan'
  functionApp: 'func'
  apiManagement: 'apim'
  cosmosDb: 'cosmos'
  redis: 'redis'
  serviceBus: 'sb'
  eventHub: 'evh'
  logAnalytics: 'log'
  keyVault: 'kv'
  storageAccount: 'st'
  containerRegistry: 'cr'
  appConfiguration: 'appcs'
  appInsights: 'appi'
  virtualNetwork: 'vnet'
  networkSecurityGroup: 'nsg'
  publicIp: 'pip'
  managedIdentity: 'id'
  aks: 'aks'
  applicationGateway: 'agw'
}

// ---------------------------------------------------------------------------
// Derived values
// ---------------------------------------------------------------------------

var lobLower = toLower(lob)
var stageLower = toLower(stage)
var appNameLower = toLower(appName)
var appIdLower = toLower(appId)
var roleLower = toLower(role)
var lobCode = lobCodes[lobLower]
var stageCode = stageCodes[stageLower]

// ---------------------------------------------------------------------------
// Standard pattern: {prefix}-{lob}-{stage}-{appName}-{role}-{appId}
// ---------------------------------------------------------------------------

var standardBase = empty(roleLower)
  ? '${lobLower}-${stageLower}-${appNameLower}-${appIdLower}'
  : empty(location)
    ? '${lobLower}-${stageLower}-${appNameLower}-${roleLower}-${appIdLower}'
    : '${lobLower}-${stageLower}-${appNameLower}-${roleLower}-${toLower(location)}-${appIdLower}'

// ---------------------------------------------------------------------------
// Mini pattern: {prefix}{lobCode}{stageCode}{appName}{role}{appId}
// ---------------------------------------------------------------------------

var miniBase = empty(roleLower)
  ? '${lobCode}${stageCode}${appNameLower}${appIdLower}'
  : '${lobCode}${stageCode}${appNameLower}${roleLower}${appIdLower}'

// ---------------------------------------------------------------------------
// Small pattern: {prefix}-{lob}-{stage}-{appName}-{role}-{appId}
// ---------------------------------------------------------------------------

var smallBase = empty(roleLower)
  ? '${lobLower}-${stageLower}-${appNameLower}-${appIdLower}'
  : '${lobLower}-${stageLower}-${appNameLower}-${roleLower}-${appIdLower}'

// ---------------------------------------------------------------------------
// Outputs — Standard pattern resources
// ---------------------------------------------------------------------------

@description('SQL Server name (standard pattern)')
output sqlServerName string = '${prefixes.sqlServer}-${standardBase}'

@description('SQL Database name (standard pattern)')
output sqlDatabaseName string = '${prefixes.sqlDatabase}-${standardBase}'

@description('App Service name (standard pattern)')
output appServiceName string = '${prefixes.appService}-${standardBase}'

@description('App Service Plan name (standard pattern)')
output appServicePlanName string = '${prefixes.appServicePlan}-${standardBase}'

@description('Function App name (standard pattern)')
output functionAppName string = '${prefixes.functionApp}-${standardBase}'

@description('API Management name (standard pattern)')
output apiManagementName string = '${prefixes.apiManagement}-${standardBase}'

@description('Cosmos DB name (standard pattern)')
output cosmosDbName string = '${prefixes.cosmosDb}-${standardBase}'

@description('Redis Cache name (standard pattern)')
output redisName string = '${prefixes.redis}-${standardBase}'

@description('Service Bus name (standard pattern)')
output serviceBusName string = '${prefixes.serviceBus}-${standardBase}'

@description('Event Hub name (standard pattern)')
output eventHubName string = '${prefixes.eventHub}-${standardBase}'

@description('Log Analytics name (standard pattern)')
output logAnalyticsName string = '${prefixes.logAnalytics}-${standardBase}'

@description('Virtual Network name (standard pattern)')
output virtualNetworkName string = '${prefixes.virtualNetwork}-${standardBase}'

@description('Network Security Group name (standard pattern)')
output networkSecurityGroupName string = '${prefixes.networkSecurityGroup}-${standardBase}'

@description('Public IP name (standard pattern)')
output publicIpName string = '${prefixes.publicIp}-${standardBase}'

@description('Managed Identity name (standard pattern)')
output managedIdentityName string = '${prefixes.managedIdentity}-${standardBase}'

@description('AKS Cluster name (standard pattern)')
output aksName string = '${prefixes.aks}-${standardBase}'

@description('Application Gateway name (standard pattern)')
output applicationGatewayName string = '${prefixes.applicationGateway}-${standardBase}'

// ---------------------------------------------------------------------------
// Outputs — Mini pattern resources (no hyphens, LOB/stage codes)
// ---------------------------------------------------------------------------

@description('Key Vault name (mini pattern, max 24 chars)')
output keyVaultName string = '${prefixes.keyVault}${miniBase}'

@description('Storage Account name (mini pattern, max 24 chars)')
output storageAccountName string = '${prefixes.storageAccount}${miniBase}'

@description('Container Registry name (mini pattern, max 50 chars)')
output containerRegistryName string = '${prefixes.containerRegistry}${miniBase}'

// ---------------------------------------------------------------------------
// Outputs — Small pattern resources
// ---------------------------------------------------------------------------

@description('App Configuration name (small pattern)')
output appConfigurationName string = '${prefixes.appConfiguration}-${smallBase}'

@description('Application Insights name (small pattern)')
output appInsightsName string = '${prefixes.appInsights}-${smallBase}'
