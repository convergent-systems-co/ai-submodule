// Dark Governance Service — Azure Infrastructure
// Deploys: Managed Identity + Federated Credential, Key Vault, App Configuration, App Insights
//
// Usage:
//   az deployment group create \
//     --resource-group rg-set-dev-governance-api-a \
//     --template-file infra/main.bicep \
//     --parameters stage=dev appId=a

targetScope = 'resourceGroup'

@description('Deployment stage')
@allowed(['dev', 'qa', 'uat', 'prod'])
param stage string

@description('Application identifier')
param appId string

@description('Line of business')
param lob string = 'set'

@description('Product name')
param product string = 'governance'

@description('Application role')
param role string = 'api'

@description('AKS OIDC issuer URL for Workload Identity federation')
param aksOidcIssuerUrl string

@description('Kubernetes namespace for the governance service')
param k8sNamespace string = 'governance-service'

@description('Kubernetes service account name')
param k8sServiceAccountName string = 'governance-service-sa'

@description('Location for all resources')
param location string = resourceGroup().location

// Naming module
module naming 'naming.bicep' = {
  name: 'naming'
  params: {
    lob: lob
    stage: stage
    product: product
    role: role
    appId: appId
  }
}

// --- Managed Identity ---
resource managedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: naming.outputs.managedIdentityName
  location: location
}

// Federated credential for AKS Workload Identity
resource federatedCredential 'Microsoft.ManagedIdentity/userAssignedIdentities/federatedIdentityCredentials@2023-01-31' = {
  parent: managedIdentity
  name: '${k8sNamespace}-${k8sServiceAccountName}'
  properties: {
    issuer: aksOidcIssuerUrl
    subject: 'system:serviceaccount:${k8sNamespace}:${k8sServiceAccountName}'
    audiences: [
      'api://AzureADTokenExchange'
    ]
  }
}

// --- Key Vault ---
resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: naming.outputs.keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enablePurgeProtection: true
  }
}

// Key Vault Secrets User role for managed identity
resource kvSecretsUserRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, managedIdentity.id, '4633458b-17de-408a-b874-0445c86b69e6')
  scope: keyVault
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// --- App Configuration ---
resource appConfig 'Microsoft.AppConfiguration/configurationStores@2023-03-01' = {
  name: naming.outputs.appConfigurationName
  location: location
  sku: {
    name: 'standard'
  }
  properties: {
    disableLocalAuth: true
    enablePurgeProtection: false
  }
}

// App Configuration Data Reader role for managed identity
resource appConfigReaderRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(appConfig.id, managedIdentity.id, '516239f1-63e1-4d78-a4de-a74fb236a071')
  scope: appConfig
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '516239f1-63e1-4d78-a4de-a74fb236a071')
    principalId: managedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

// --- Monitoring ---
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: naming.outputs.logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: naming.outputs.appInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalytics.id
    RetentionInDays: 30
  }
}

// --- Outputs ---
output managedIdentityClientId string = managedIdentity.properties.clientId
output managedIdentityPrincipalId string = managedIdentity.properties.principalId
output keyVaultUri string = keyVault.properties.vaultUri
output keyVaultName string = keyVault.name
output appConfigEndpoint string = appConfig.properties.endpoint
output appInsightsConnectionString string = appInsights.properties.ConnectionString
