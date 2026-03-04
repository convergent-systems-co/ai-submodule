// JM Family Enterprise naming conventions
// Pattern: {type}-{lob}-{stage}-{product}-{role}-{appId}

@description('Line of business')
param lob string

@description('Deployment stage')
@allowed(['dev', 'qa', 'uat', 'prod'])
param stage string

@description('Product name')
param product string

@description('Application role')
param role string

@description('Application identifier')
param appId string

// Resource type prefixes (Azure CAF)
var prefixes = {
  managedIdentity: 'id'
  keyVault: 'kv'
  appConfiguration: 'appcs'
  appInsights: 'appi'
  logAnalytics: 'log'
}

// Standard name: {prefix}-{lob}-{stage}-{product}-{role}-{appId}
output managedIdentityName string = '${prefixes.managedIdentity}-${lob}-${stage}-${product}-${role}-${appId}'
// Key Vault has 24-char limit, no hyphens
output keyVaultName string = '${prefixes.keyVault}${lob}${stage}${take(product, 3)}${role}${appId}'
output appConfigurationName string = '${prefixes.appConfiguration}-${lob}-${stage}-${product}-${role}-${appId}'
output appInsightsName string = '${prefixes.appInsights}-${lob}-${stage}-${product}-${role}-${appId}'
output logAnalyticsName string = '${prefixes.logAnalytics}-${lob}-${stage}-${product}-${role}-${appId}'
