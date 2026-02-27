# Azure Resource Naming v2 — Comprehensive Test Matrix

> Generated: 2026-02-26  
> Naming scheme: v2 (compressed mini, standard/small with full LOB/stage)  
> Test cases: 20 apps x 2 appId variants x 22 resource types = **880 names**  
> Note: `-si` suffix applies only to resource groups; individual resource appId is always a single letter (a-z)

## Executive Summary

| Metric | Value |
|--------|-------|
| Total names generated | 880 |
| Length violations | **0** |
| Truncations required | **0** |
| Collisions detected | **0** |
| Resource types tested | 22 |
| App names tested | 20 |
| AppId variants | 2 (a, b) |

## Naming Patterns Applied

| Pattern | Resources | Format | Example |
|---------|-----------|--------|---------|
| **mini** | Storage, Key Vault, Container Registry | `{prefix}{lobCode}{stageCode}{appName}{role}{appId}` | `stsdacctachacha` |
| **standard** | SQL, App Service, Cosmos, Redis, etc. | `{prefix}-{lob}-{stage}-{appName}-{role}-{appId}` | `sql-set-dev-acctach-ach-a` |
| **small** | App Configuration, App Insights | `{prefix}-{lob}-{stage}-{appName}-{role}-{appId}` | `appcs-set-dev-acctach-ach-a` |

## Reference: Encoding Tables (Mini Pattern Only)

### LOB Codes
| LOB | Code | Mnemonic |
|-----|------|----------|
| set | `s` | SET |
| setf | `v` | SET Financial (Value) |
| jma | `j` | JMA |
| jmf | `f` | JM Financial |
| jmfe | `e` | JMF Enterprise |
| to | `t` | TO |
| ocio | `i` | OCIO |
| octo | `c` | OCTO |
| lexus | `l` | LEXUS |

### Stage Codes
| Stage | Code |
|-------|------|
| dev | `d` |
| stg | `s` |
| qa | `q` |
| uat | `u` |
| prod | `p` |
| nonprod | `n` |

### AppId

Single letter (a-z). The `-si` (shared infrastructure) suffix applies only to resource group naming.
Individual resources within a resource group use only the letter portion.

### Character Budget (Mini Pattern, 24-char resources)

| Component | Width | Example |
|-----------|-------|---------|
| prefix | 2 | `st`, `kv`, `cr` |
| lobCode | 1 | `s`, `j`, `l` |
| stageCode | 1 | `d`, `p`, `n` |
| appId | 1 | `a`, `b` |
| **Fixed total** | **5** | |
| **Budget (appName+role)** | **19** | |
| **Min appName (role=4)** | **15** | |

## Test Input Assignments

| # | AppName | LOB (code) | Stage (code) | Role | AppName Len |
|---|---------|------------|--------------|------|-------------|
| 1 | acctach | set (s) | dev (d) | ach | 7 |
| 2 | payments | setf (v) | stg (s) | web | 8 |
| 3 | ledger | jma (j) | qa (q) | db | 6 |
| 4 | hris | jmf (f) | uat (u) | api | 4 |
| 5 | okta | jmfe (e) | prod (p) | fe | 4 |
| 6 | snowflk | to (t) | nonprod (n) | rpt | 7 |
| 7 | datamart | ocio (i) | dev (d) | wkr | 8 |
| 8 | claimshub | octo (c) | stg (s) | msg | 9 |
| 9 | billing | lexus (l) | qa (q) | que | 7 |
| 10 | taxengine | set (s) | uat (u) | sch | 9 |
| 11 | portfolio | setf (v) | prod (p) | log | 9 |
| 12 | riskmodel | jma (j) | nonprod (n) | cfg | 9 |
| 13 | custportal | jmf (f) | dev (d) | be | 10 |
| 14 | supplychain | jmfe (e) | stg (s) | chk | 11 |
| 15 | chatbot | to (t) | qa (q) | cch | 7 |
| 16 | auditlog | ocio (i) | uat (u) | api | 8 |
| 17 | docmgmt | octo (c) | prod (p) | web | 7 |
| 18 | policyeng | lexus (l) | nonprod (n) | rpt | 9 |
| 19 | identmgr | set (s) | dev (d) | db | 8 |
| 20 | wealthplat | setf (v) | stg (s) | wkr | 10 |

## Test Case 1: `acctach` — LOB=set, Stage=dev, Role=ach

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stsdacctachacha` | 15 | 24 | YES | No |
| Key Vault | mini | a | `kvsdacctachacha` | 15 | 24 | YES | No |
| Container Registry | mini | a | `crsdacctachacha` | 15 | 50 | YES | No |
| SQL Server | standard | a | `sql-set-dev-acctach-ach-a` | 25 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-set-dev-acctach-ach-a` | 27 | 128 | YES | No |
| App Service | standard | a | `app-set-dev-acctach-ach-a` | 25 | 60 | YES | No |
| App Service Plan | standard | a | `plan-set-dev-acctach-ach-a` | 26 | 40 | YES | No |
| Function App | standard | a | `func-set-dev-acctach-ach-a` | 26 | 60 | YES | No |
| API Management | standard | a | `apim-set-dev-acctach-ach-a` | 26 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-set-dev-acctach-ach-a` | 28 | 44 | YES | No |
| Redis Cache | standard | a | `redis-set-dev-acctach-ach-a` | 27 | 63 | YES | No |
| Service Bus | standard | a | `sb-set-dev-acctach-ach-a` | 24 | 50 | YES | No |
| Event Hub | standard | a | `evh-set-dev-acctach-ach-a` | 25 | 50 | YES | No |
| Log Analytics | standard | a | `log-set-dev-acctach-ach-a` | 25 | 63 | YES | No |
| App Configuration | small | a | `appcs-set-dev-acctach-ach-a` | 27 | 50 | YES | No |
| App Insights | small | a | `appi-set-dev-acctach-ach-a` | 26 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-set-dev-acctach-ach-a` | 26 | 64 | YES | No |
| NSG | standard | a | `nsg-set-dev-acctach-ach-a` | 25 | 80 | YES | No |
| Public IP | standard | a | `pip-set-dev-acctach-ach-a` | 25 | 80 | YES | No |
| Managed Identity | standard | a | `id-set-dev-acctach-ach-a` | 24 | 128 | YES | No |
| AKS | standard | a | `aks-set-dev-acctach-ach-a` | 25 | 63 | YES | No |
| App Gateway | standard | a | `agw-set-dev-acctach-ach-a` | 25 | 80 | YES | No |
| Storage Account | mini | b | `stsdacctachachb` | 15 | 24 | YES | No |
| Key Vault | mini | b | `kvsdacctachachb` | 15 | 24 | YES | No |
| Container Registry | mini | b | `crsdacctachachb` | 15 | 50 | YES | No |
| SQL Server | standard | b | `sql-set-dev-acctach-ach-b` | 25 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-set-dev-acctach-ach-b` | 27 | 128 | YES | No |
| App Service | standard | b | `app-set-dev-acctach-ach-b` | 25 | 60 | YES | No |
| App Service Plan | standard | b | `plan-set-dev-acctach-ach-b` | 26 | 40 | YES | No |
| Function App | standard | b | `func-set-dev-acctach-ach-b` | 26 | 60 | YES | No |
| API Management | standard | b | `apim-set-dev-acctach-ach-b` | 26 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-set-dev-acctach-ach-b` | 28 | 44 | YES | No |
| Redis Cache | standard | b | `redis-set-dev-acctach-ach-b` | 27 | 63 | YES | No |
| Service Bus | standard | b | `sb-set-dev-acctach-ach-b` | 24 | 50 | YES | No |
| Event Hub | standard | b | `evh-set-dev-acctach-ach-b` | 25 | 50 | YES | No |
| Log Analytics | standard | b | `log-set-dev-acctach-ach-b` | 25 | 63 | YES | No |
| App Configuration | small | b | `appcs-set-dev-acctach-ach-b` | 27 | 50 | YES | No |
| App Insights | small | b | `appi-set-dev-acctach-ach-b` | 26 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-set-dev-acctach-ach-b` | 26 | 64 | YES | No |
| NSG | standard | b | `nsg-set-dev-acctach-ach-b` | 25 | 80 | YES | No |
| Public IP | standard | b | `pip-set-dev-acctach-ach-b` | 25 | 80 | YES | No |
| Managed Identity | standard | b | `id-set-dev-acctach-ach-b` | 24 | 128 | YES | No |
| AKS | standard | b | `aks-set-dev-acctach-ach-b` | 25 | 63 | YES | No |
| App Gateway | standard | b | `agw-set-dev-acctach-ach-b` | 25 | 80 | YES | No |

## Test Case 2: `payments` — LOB=setf, Stage=stg, Role=web

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stvspaymentsweba` | 16 | 24 | YES | No |
| Key Vault | mini | a | `kvvspaymentsweba` | 16 | 24 | YES | No |
| Container Registry | mini | a | `crvspaymentsweba` | 16 | 50 | YES | No |
| SQL Server | standard | a | `sql-setf-stg-payments-web-a` | 27 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-setf-stg-payments-web-a` | 29 | 128 | YES | No |
| App Service | standard | a | `app-setf-stg-payments-web-a` | 27 | 60 | YES | No |
| App Service Plan | standard | a | `plan-setf-stg-payments-web-a` | 28 | 40 | YES | No |
| Function App | standard | a | `func-setf-stg-payments-web-a` | 28 | 60 | YES | No |
| API Management | standard | a | `apim-setf-stg-payments-web-a` | 28 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-setf-stg-payments-web-a` | 30 | 44 | YES | No |
| Redis Cache | standard | a | `redis-setf-stg-payments-web-a` | 29 | 63 | YES | No |
| Service Bus | standard | a | `sb-setf-stg-payments-web-a` | 26 | 50 | YES | No |
| Event Hub | standard | a | `evh-setf-stg-payments-web-a` | 27 | 50 | YES | No |
| Log Analytics | standard | a | `log-setf-stg-payments-web-a` | 27 | 63 | YES | No |
| App Configuration | small | a | `appcs-setf-stg-payments-web-a` | 29 | 50 | YES | No |
| App Insights | small | a | `appi-setf-stg-payments-web-a` | 28 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-setf-stg-payments-web-a` | 28 | 64 | YES | No |
| NSG | standard | a | `nsg-setf-stg-payments-web-a` | 27 | 80 | YES | No |
| Public IP | standard | a | `pip-setf-stg-payments-web-a` | 27 | 80 | YES | No |
| Managed Identity | standard | a | `id-setf-stg-payments-web-a` | 26 | 128 | YES | No |
| AKS | standard | a | `aks-setf-stg-payments-web-a` | 27 | 63 | YES | No |
| App Gateway | standard | a | `agw-setf-stg-payments-web-a` | 27 | 80 | YES | No |
| Storage Account | mini | b | `stvspaymentswebb` | 16 | 24 | YES | No |
| Key Vault | mini | b | `kvvspaymentswebb` | 16 | 24 | YES | No |
| Container Registry | mini | b | `crvspaymentswebb` | 16 | 50 | YES | No |
| SQL Server | standard | b | `sql-setf-stg-payments-web-b` | 27 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-setf-stg-payments-web-b` | 29 | 128 | YES | No |
| App Service | standard | b | `app-setf-stg-payments-web-b` | 27 | 60 | YES | No |
| App Service Plan | standard | b | `plan-setf-stg-payments-web-b` | 28 | 40 | YES | No |
| Function App | standard | b | `func-setf-stg-payments-web-b` | 28 | 60 | YES | No |
| API Management | standard | b | `apim-setf-stg-payments-web-b` | 28 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-setf-stg-payments-web-b` | 30 | 44 | YES | No |
| Redis Cache | standard | b | `redis-setf-stg-payments-web-b` | 29 | 63 | YES | No |
| Service Bus | standard | b | `sb-setf-stg-payments-web-b` | 26 | 50 | YES | No |
| Event Hub | standard | b | `evh-setf-stg-payments-web-b` | 27 | 50 | YES | No |
| Log Analytics | standard | b | `log-setf-stg-payments-web-b` | 27 | 63 | YES | No |
| App Configuration | small | b | `appcs-setf-stg-payments-web-b` | 29 | 50 | YES | No |
| App Insights | small | b | `appi-setf-stg-payments-web-b` | 28 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-setf-stg-payments-web-b` | 28 | 64 | YES | No |
| NSG | standard | b | `nsg-setf-stg-payments-web-b` | 27 | 80 | YES | No |
| Public IP | standard | b | `pip-setf-stg-payments-web-b` | 27 | 80 | YES | No |
| Managed Identity | standard | b | `id-setf-stg-payments-web-b` | 26 | 128 | YES | No |
| AKS | standard | b | `aks-setf-stg-payments-web-b` | 27 | 63 | YES | No |
| App Gateway | standard | b | `agw-setf-stg-payments-web-b` | 27 | 80 | YES | No |

## Test Case 3: `ledger` — LOB=jma, Stage=qa, Role=db

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stjqledgerdba` | 13 | 24 | YES | No |
| Key Vault | mini | a | `kvjqledgerdba` | 13 | 24 | YES | No |
| Container Registry | mini | a | `crjqledgerdba` | 13 | 50 | YES | No |
| SQL Server | standard | a | `sql-jma-qa-ledger-db-a` | 22 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-jma-qa-ledger-db-a` | 24 | 128 | YES | No |
| App Service | standard | a | `app-jma-qa-ledger-db-a` | 22 | 60 | YES | No |
| App Service Plan | standard | a | `plan-jma-qa-ledger-db-a` | 23 | 40 | YES | No |
| Function App | standard | a | `func-jma-qa-ledger-db-a` | 23 | 60 | YES | No |
| API Management | standard | a | `apim-jma-qa-ledger-db-a` | 23 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-jma-qa-ledger-db-a` | 25 | 44 | YES | No |
| Redis Cache | standard | a | `redis-jma-qa-ledger-db-a` | 24 | 63 | YES | No |
| Service Bus | standard | a | `sb-jma-qa-ledger-db-a` | 21 | 50 | YES | No |
| Event Hub | standard | a | `evh-jma-qa-ledger-db-a` | 22 | 50 | YES | No |
| Log Analytics | standard | a | `log-jma-qa-ledger-db-a` | 22 | 63 | YES | No |
| App Configuration | small | a | `appcs-jma-qa-ledger-db-a` | 24 | 50 | YES | No |
| App Insights | small | a | `appi-jma-qa-ledger-db-a` | 23 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-jma-qa-ledger-db-a` | 23 | 64 | YES | No |
| NSG | standard | a | `nsg-jma-qa-ledger-db-a` | 22 | 80 | YES | No |
| Public IP | standard | a | `pip-jma-qa-ledger-db-a` | 22 | 80 | YES | No |
| Managed Identity | standard | a | `id-jma-qa-ledger-db-a` | 21 | 128 | YES | No |
| AKS | standard | a | `aks-jma-qa-ledger-db-a` | 22 | 63 | YES | No |
| App Gateway | standard | a | `agw-jma-qa-ledger-db-a` | 22 | 80 | YES | No |
| Storage Account | mini | b | `stjqledgerdbb` | 13 | 24 | YES | No |
| Key Vault | mini | b | `kvjqledgerdbb` | 13 | 24 | YES | No |
| Container Registry | mini | b | `crjqledgerdbb` | 13 | 50 | YES | No |
| SQL Server | standard | b | `sql-jma-qa-ledger-db-b` | 22 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-jma-qa-ledger-db-b` | 24 | 128 | YES | No |
| App Service | standard | b | `app-jma-qa-ledger-db-b` | 22 | 60 | YES | No |
| App Service Plan | standard | b | `plan-jma-qa-ledger-db-b` | 23 | 40 | YES | No |
| Function App | standard | b | `func-jma-qa-ledger-db-b` | 23 | 60 | YES | No |
| API Management | standard | b | `apim-jma-qa-ledger-db-b` | 23 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-jma-qa-ledger-db-b` | 25 | 44 | YES | No |
| Redis Cache | standard | b | `redis-jma-qa-ledger-db-b` | 24 | 63 | YES | No |
| Service Bus | standard | b | `sb-jma-qa-ledger-db-b` | 21 | 50 | YES | No |
| Event Hub | standard | b | `evh-jma-qa-ledger-db-b` | 22 | 50 | YES | No |
| Log Analytics | standard | b | `log-jma-qa-ledger-db-b` | 22 | 63 | YES | No |
| App Configuration | small | b | `appcs-jma-qa-ledger-db-b` | 24 | 50 | YES | No |
| App Insights | small | b | `appi-jma-qa-ledger-db-b` | 23 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-jma-qa-ledger-db-b` | 23 | 64 | YES | No |
| NSG | standard | b | `nsg-jma-qa-ledger-db-b` | 22 | 80 | YES | No |
| Public IP | standard | b | `pip-jma-qa-ledger-db-b` | 22 | 80 | YES | No |
| Managed Identity | standard | b | `id-jma-qa-ledger-db-b` | 21 | 128 | YES | No |
| AKS | standard | b | `aks-jma-qa-ledger-db-b` | 22 | 63 | YES | No |
| App Gateway | standard | b | `agw-jma-qa-ledger-db-b` | 22 | 80 | YES | No |

## Test Case 4: `hris` — LOB=jmf, Stage=uat, Role=api

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stfuhrisapia` | 12 | 24 | YES | No |
| Key Vault | mini | a | `kvfuhrisapia` | 12 | 24 | YES | No |
| Container Registry | mini | a | `crfuhrisapia` | 12 | 50 | YES | No |
| SQL Server | standard | a | `sql-jmf-uat-hris-api-a` | 22 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-jmf-uat-hris-api-a` | 24 | 128 | YES | No |
| App Service | standard | a | `app-jmf-uat-hris-api-a` | 22 | 60 | YES | No |
| App Service Plan | standard | a | `plan-jmf-uat-hris-api-a` | 23 | 40 | YES | No |
| Function App | standard | a | `func-jmf-uat-hris-api-a` | 23 | 60 | YES | No |
| API Management | standard | a | `apim-jmf-uat-hris-api-a` | 23 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-jmf-uat-hris-api-a` | 25 | 44 | YES | No |
| Redis Cache | standard | a | `redis-jmf-uat-hris-api-a` | 24 | 63 | YES | No |
| Service Bus | standard | a | `sb-jmf-uat-hris-api-a` | 21 | 50 | YES | No |
| Event Hub | standard | a | `evh-jmf-uat-hris-api-a` | 22 | 50 | YES | No |
| Log Analytics | standard | a | `log-jmf-uat-hris-api-a` | 22 | 63 | YES | No |
| App Configuration | small | a | `appcs-jmf-uat-hris-api-a` | 24 | 50 | YES | No |
| App Insights | small | a | `appi-jmf-uat-hris-api-a` | 23 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-jmf-uat-hris-api-a` | 23 | 64 | YES | No |
| NSG | standard | a | `nsg-jmf-uat-hris-api-a` | 22 | 80 | YES | No |
| Public IP | standard | a | `pip-jmf-uat-hris-api-a` | 22 | 80 | YES | No |
| Managed Identity | standard | a | `id-jmf-uat-hris-api-a` | 21 | 128 | YES | No |
| AKS | standard | a | `aks-jmf-uat-hris-api-a` | 22 | 63 | YES | No |
| App Gateway | standard | a | `agw-jmf-uat-hris-api-a` | 22 | 80 | YES | No |
| Storage Account | mini | b | `stfuhrisapib` | 12 | 24 | YES | No |
| Key Vault | mini | b | `kvfuhrisapib` | 12 | 24 | YES | No |
| Container Registry | mini | b | `crfuhrisapib` | 12 | 50 | YES | No |
| SQL Server | standard | b | `sql-jmf-uat-hris-api-b` | 22 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-jmf-uat-hris-api-b` | 24 | 128 | YES | No |
| App Service | standard | b | `app-jmf-uat-hris-api-b` | 22 | 60 | YES | No |
| App Service Plan | standard | b | `plan-jmf-uat-hris-api-b` | 23 | 40 | YES | No |
| Function App | standard | b | `func-jmf-uat-hris-api-b` | 23 | 60 | YES | No |
| API Management | standard | b | `apim-jmf-uat-hris-api-b` | 23 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-jmf-uat-hris-api-b` | 25 | 44 | YES | No |
| Redis Cache | standard | b | `redis-jmf-uat-hris-api-b` | 24 | 63 | YES | No |
| Service Bus | standard | b | `sb-jmf-uat-hris-api-b` | 21 | 50 | YES | No |
| Event Hub | standard | b | `evh-jmf-uat-hris-api-b` | 22 | 50 | YES | No |
| Log Analytics | standard | b | `log-jmf-uat-hris-api-b` | 22 | 63 | YES | No |
| App Configuration | small | b | `appcs-jmf-uat-hris-api-b` | 24 | 50 | YES | No |
| App Insights | small | b | `appi-jmf-uat-hris-api-b` | 23 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-jmf-uat-hris-api-b` | 23 | 64 | YES | No |
| NSG | standard | b | `nsg-jmf-uat-hris-api-b` | 22 | 80 | YES | No |
| Public IP | standard | b | `pip-jmf-uat-hris-api-b` | 22 | 80 | YES | No |
| Managed Identity | standard | b | `id-jmf-uat-hris-api-b` | 21 | 128 | YES | No |
| AKS | standard | b | `aks-jmf-uat-hris-api-b` | 22 | 63 | YES | No |
| App Gateway | standard | b | `agw-jmf-uat-hris-api-b` | 22 | 80 | YES | No |

## Test Case 5: `okta` — LOB=jmfe, Stage=prod, Role=fe

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stepoktafea` | 11 | 24 | YES | No |
| Key Vault | mini | a | `kvepoktafea` | 11 | 24 | YES | No |
| Container Registry | mini | a | `crepoktafea` | 11 | 50 | YES | No |
| SQL Server | standard | a | `sql-jmfe-prod-okta-fe-a` | 23 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-jmfe-prod-okta-fe-a` | 25 | 128 | YES | No |
| App Service | standard | a | `app-jmfe-prod-okta-fe-a` | 23 | 60 | YES | No |
| App Service Plan | standard | a | `plan-jmfe-prod-okta-fe-a` | 24 | 40 | YES | No |
| Function App | standard | a | `func-jmfe-prod-okta-fe-a` | 24 | 60 | YES | No |
| API Management | standard | a | `apim-jmfe-prod-okta-fe-a` | 24 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-jmfe-prod-okta-fe-a` | 26 | 44 | YES | No |
| Redis Cache | standard | a | `redis-jmfe-prod-okta-fe-a` | 25 | 63 | YES | No |
| Service Bus | standard | a | `sb-jmfe-prod-okta-fe-a` | 22 | 50 | YES | No |
| Event Hub | standard | a | `evh-jmfe-prod-okta-fe-a` | 23 | 50 | YES | No |
| Log Analytics | standard | a | `log-jmfe-prod-okta-fe-a` | 23 | 63 | YES | No |
| App Configuration | small | a | `appcs-jmfe-prod-okta-fe-a` | 25 | 50 | YES | No |
| App Insights | small | a | `appi-jmfe-prod-okta-fe-a` | 24 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-jmfe-prod-okta-fe-a` | 24 | 64 | YES | No |
| NSG | standard | a | `nsg-jmfe-prod-okta-fe-a` | 23 | 80 | YES | No |
| Public IP | standard | a | `pip-jmfe-prod-okta-fe-a` | 23 | 80 | YES | No |
| Managed Identity | standard | a | `id-jmfe-prod-okta-fe-a` | 22 | 128 | YES | No |
| AKS | standard | a | `aks-jmfe-prod-okta-fe-a` | 23 | 63 | YES | No |
| App Gateway | standard | a | `agw-jmfe-prod-okta-fe-a` | 23 | 80 | YES | No |
| Storage Account | mini | b | `stepoktafeb` | 11 | 24 | YES | No |
| Key Vault | mini | b | `kvepoktafeb` | 11 | 24 | YES | No |
| Container Registry | mini | b | `crepoktafeb` | 11 | 50 | YES | No |
| SQL Server | standard | b | `sql-jmfe-prod-okta-fe-b` | 23 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-jmfe-prod-okta-fe-b` | 25 | 128 | YES | No |
| App Service | standard | b | `app-jmfe-prod-okta-fe-b` | 23 | 60 | YES | No |
| App Service Plan | standard | b | `plan-jmfe-prod-okta-fe-b` | 24 | 40 | YES | No |
| Function App | standard | b | `func-jmfe-prod-okta-fe-b` | 24 | 60 | YES | No |
| API Management | standard | b | `apim-jmfe-prod-okta-fe-b` | 24 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-jmfe-prod-okta-fe-b` | 26 | 44 | YES | No |
| Redis Cache | standard | b | `redis-jmfe-prod-okta-fe-b` | 25 | 63 | YES | No |
| Service Bus | standard | b | `sb-jmfe-prod-okta-fe-b` | 22 | 50 | YES | No |
| Event Hub | standard | b | `evh-jmfe-prod-okta-fe-b` | 23 | 50 | YES | No |
| Log Analytics | standard | b | `log-jmfe-prod-okta-fe-b` | 23 | 63 | YES | No |
| App Configuration | small | b | `appcs-jmfe-prod-okta-fe-b` | 25 | 50 | YES | No |
| App Insights | small | b | `appi-jmfe-prod-okta-fe-b` | 24 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-jmfe-prod-okta-fe-b` | 24 | 64 | YES | No |
| NSG | standard | b | `nsg-jmfe-prod-okta-fe-b` | 23 | 80 | YES | No |
| Public IP | standard | b | `pip-jmfe-prod-okta-fe-b` | 23 | 80 | YES | No |
| Managed Identity | standard | b | `id-jmfe-prod-okta-fe-b` | 22 | 128 | YES | No |
| AKS | standard | b | `aks-jmfe-prod-okta-fe-b` | 23 | 63 | YES | No |
| App Gateway | standard | b | `agw-jmfe-prod-okta-fe-b` | 23 | 80 | YES | No |

## Test Case 6: `snowflk` — LOB=to, Stage=nonprod, Role=rpt

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `sttnsnowflkrpta` | 15 | 24 | YES | No |
| Key Vault | mini | a | `kvtnsnowflkrpta` | 15 | 24 | YES | No |
| Container Registry | mini | a | `crtnsnowflkrpta` | 15 | 50 | YES | No |
| SQL Server | standard | a | `sql-to-nonprod-snowflk-rpt-a` | 28 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-to-nonprod-snowflk-rpt-a` | 30 | 128 | YES | No |
| App Service | standard | a | `app-to-nonprod-snowflk-rpt-a` | 28 | 60 | YES | No |
| App Service Plan | standard | a | `plan-to-nonprod-snowflk-rpt-a` | 29 | 40 | YES | No |
| Function App | standard | a | `func-to-nonprod-snowflk-rpt-a` | 29 | 60 | YES | No |
| API Management | standard | a | `apim-to-nonprod-snowflk-rpt-a` | 29 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-to-nonprod-snowflk-rpt-a` | 31 | 44 | YES | No |
| Redis Cache | standard | a | `redis-to-nonprod-snowflk-rpt-a` | 30 | 63 | YES | No |
| Service Bus | standard | a | `sb-to-nonprod-snowflk-rpt-a` | 27 | 50 | YES | No |
| Event Hub | standard | a | `evh-to-nonprod-snowflk-rpt-a` | 28 | 50 | YES | No |
| Log Analytics | standard | a | `log-to-nonprod-snowflk-rpt-a` | 28 | 63 | YES | No |
| App Configuration | small | a | `appcs-to-nonprod-snowflk-rpt-a` | 30 | 50 | YES | No |
| App Insights | small | a | `appi-to-nonprod-snowflk-rpt-a` | 29 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-to-nonprod-snowflk-rpt-a` | 29 | 64 | YES | No |
| NSG | standard | a | `nsg-to-nonprod-snowflk-rpt-a` | 28 | 80 | YES | No |
| Public IP | standard | a | `pip-to-nonprod-snowflk-rpt-a` | 28 | 80 | YES | No |
| Managed Identity | standard | a | `id-to-nonprod-snowflk-rpt-a` | 27 | 128 | YES | No |
| AKS | standard | a | `aks-to-nonprod-snowflk-rpt-a` | 28 | 63 | YES | No |
| App Gateway | standard | a | `agw-to-nonprod-snowflk-rpt-a` | 28 | 80 | YES | No |
| Storage Account | mini | b | `sttnsnowflkrptb` | 15 | 24 | YES | No |
| Key Vault | mini | b | `kvtnsnowflkrptb` | 15 | 24 | YES | No |
| Container Registry | mini | b | `crtnsnowflkrptb` | 15 | 50 | YES | No |
| SQL Server | standard | b | `sql-to-nonprod-snowflk-rpt-b` | 28 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-to-nonprod-snowflk-rpt-b` | 30 | 128 | YES | No |
| App Service | standard | b | `app-to-nonprod-snowflk-rpt-b` | 28 | 60 | YES | No |
| App Service Plan | standard | b | `plan-to-nonprod-snowflk-rpt-b` | 29 | 40 | YES | No |
| Function App | standard | b | `func-to-nonprod-snowflk-rpt-b` | 29 | 60 | YES | No |
| API Management | standard | b | `apim-to-nonprod-snowflk-rpt-b` | 29 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-to-nonprod-snowflk-rpt-b` | 31 | 44 | YES | No |
| Redis Cache | standard | b | `redis-to-nonprod-snowflk-rpt-b` | 30 | 63 | YES | No |
| Service Bus | standard | b | `sb-to-nonprod-snowflk-rpt-b` | 27 | 50 | YES | No |
| Event Hub | standard | b | `evh-to-nonprod-snowflk-rpt-b` | 28 | 50 | YES | No |
| Log Analytics | standard | b | `log-to-nonprod-snowflk-rpt-b` | 28 | 63 | YES | No |
| App Configuration | small | b | `appcs-to-nonprod-snowflk-rpt-b` | 30 | 50 | YES | No |
| App Insights | small | b | `appi-to-nonprod-snowflk-rpt-b` | 29 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-to-nonprod-snowflk-rpt-b` | 29 | 64 | YES | No |
| NSG | standard | b | `nsg-to-nonprod-snowflk-rpt-b` | 28 | 80 | YES | No |
| Public IP | standard | b | `pip-to-nonprod-snowflk-rpt-b` | 28 | 80 | YES | No |
| Managed Identity | standard | b | `id-to-nonprod-snowflk-rpt-b` | 27 | 128 | YES | No |
| AKS | standard | b | `aks-to-nonprod-snowflk-rpt-b` | 28 | 63 | YES | No |
| App Gateway | standard | b | `agw-to-nonprod-snowflk-rpt-b` | 28 | 80 | YES | No |

## Test Case 7: `datamart` — LOB=ocio, Stage=dev, Role=wkr

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stiddatamartwkra` | 16 | 24 | YES | No |
| Key Vault | mini | a | `kviddatamartwkra` | 16 | 24 | YES | No |
| Container Registry | mini | a | `criddatamartwkra` | 16 | 50 | YES | No |
| SQL Server | standard | a | `sql-ocio-dev-datamart-wkr-a` | 27 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-ocio-dev-datamart-wkr-a` | 29 | 128 | YES | No |
| App Service | standard | a | `app-ocio-dev-datamart-wkr-a` | 27 | 60 | YES | No |
| App Service Plan | standard | a | `plan-ocio-dev-datamart-wkr-a` | 28 | 40 | YES | No |
| Function App | standard | a | `func-ocio-dev-datamart-wkr-a` | 28 | 60 | YES | No |
| API Management | standard | a | `apim-ocio-dev-datamart-wkr-a` | 28 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-ocio-dev-datamart-wkr-a` | 30 | 44 | YES | No |
| Redis Cache | standard | a | `redis-ocio-dev-datamart-wkr-a` | 29 | 63 | YES | No |
| Service Bus | standard | a | `sb-ocio-dev-datamart-wkr-a` | 26 | 50 | YES | No |
| Event Hub | standard | a | `evh-ocio-dev-datamart-wkr-a` | 27 | 50 | YES | No |
| Log Analytics | standard | a | `log-ocio-dev-datamart-wkr-a` | 27 | 63 | YES | No |
| App Configuration | small | a | `appcs-ocio-dev-datamart-wkr-a` | 29 | 50 | YES | No |
| App Insights | small | a | `appi-ocio-dev-datamart-wkr-a` | 28 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-ocio-dev-datamart-wkr-a` | 28 | 64 | YES | No |
| NSG | standard | a | `nsg-ocio-dev-datamart-wkr-a` | 27 | 80 | YES | No |
| Public IP | standard | a | `pip-ocio-dev-datamart-wkr-a` | 27 | 80 | YES | No |
| Managed Identity | standard | a | `id-ocio-dev-datamart-wkr-a` | 26 | 128 | YES | No |
| AKS | standard | a | `aks-ocio-dev-datamart-wkr-a` | 27 | 63 | YES | No |
| App Gateway | standard | a | `agw-ocio-dev-datamart-wkr-a` | 27 | 80 | YES | No |
| Storage Account | mini | b | `stiddatamartwkrb` | 16 | 24 | YES | No |
| Key Vault | mini | b | `kviddatamartwkrb` | 16 | 24 | YES | No |
| Container Registry | mini | b | `criddatamartwkrb` | 16 | 50 | YES | No |
| SQL Server | standard | b | `sql-ocio-dev-datamart-wkr-b` | 27 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-ocio-dev-datamart-wkr-b` | 29 | 128 | YES | No |
| App Service | standard | b | `app-ocio-dev-datamart-wkr-b` | 27 | 60 | YES | No |
| App Service Plan | standard | b | `plan-ocio-dev-datamart-wkr-b` | 28 | 40 | YES | No |
| Function App | standard | b | `func-ocio-dev-datamart-wkr-b` | 28 | 60 | YES | No |
| API Management | standard | b | `apim-ocio-dev-datamart-wkr-b` | 28 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-ocio-dev-datamart-wkr-b` | 30 | 44 | YES | No |
| Redis Cache | standard | b | `redis-ocio-dev-datamart-wkr-b` | 29 | 63 | YES | No |
| Service Bus | standard | b | `sb-ocio-dev-datamart-wkr-b` | 26 | 50 | YES | No |
| Event Hub | standard | b | `evh-ocio-dev-datamart-wkr-b` | 27 | 50 | YES | No |
| Log Analytics | standard | b | `log-ocio-dev-datamart-wkr-b` | 27 | 63 | YES | No |
| App Configuration | small | b | `appcs-ocio-dev-datamart-wkr-b` | 29 | 50 | YES | No |
| App Insights | small | b | `appi-ocio-dev-datamart-wkr-b` | 28 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-ocio-dev-datamart-wkr-b` | 28 | 64 | YES | No |
| NSG | standard | b | `nsg-ocio-dev-datamart-wkr-b` | 27 | 80 | YES | No |
| Public IP | standard | b | `pip-ocio-dev-datamart-wkr-b` | 27 | 80 | YES | No |
| Managed Identity | standard | b | `id-ocio-dev-datamart-wkr-b` | 26 | 128 | YES | No |
| AKS | standard | b | `aks-ocio-dev-datamart-wkr-b` | 27 | 63 | YES | No |
| App Gateway | standard | b | `agw-ocio-dev-datamart-wkr-b` | 27 | 80 | YES | No |

## Test Case 8: `claimshub` — LOB=octo, Stage=stg, Role=msg

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stcsclaimshubmsga` | 17 | 24 | YES | No |
| Key Vault | mini | a | `kvcsclaimshubmsga` | 17 | 24 | YES | No |
| Container Registry | mini | a | `crcsclaimshubmsga` | 17 | 50 | YES | No |
| SQL Server | standard | a | `sql-octo-stg-claimshub-msg-a` | 28 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-octo-stg-claimshub-msg-a` | 30 | 128 | YES | No |
| App Service | standard | a | `app-octo-stg-claimshub-msg-a` | 28 | 60 | YES | No |
| App Service Plan | standard | a | `plan-octo-stg-claimshub-msg-a` | 29 | 40 | YES | No |
| Function App | standard | a | `func-octo-stg-claimshub-msg-a` | 29 | 60 | YES | No |
| API Management | standard | a | `apim-octo-stg-claimshub-msg-a` | 29 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-octo-stg-claimshub-msg-a` | 31 | 44 | YES | No |
| Redis Cache | standard | a | `redis-octo-stg-claimshub-msg-a` | 30 | 63 | YES | No |
| Service Bus | standard | a | `sb-octo-stg-claimshub-msg-a` | 27 | 50 | YES | No |
| Event Hub | standard | a | `evh-octo-stg-claimshub-msg-a` | 28 | 50 | YES | No |
| Log Analytics | standard | a | `log-octo-stg-claimshub-msg-a` | 28 | 63 | YES | No |
| App Configuration | small | a | `appcs-octo-stg-claimshub-msg-a` | 30 | 50 | YES | No |
| App Insights | small | a | `appi-octo-stg-claimshub-msg-a` | 29 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-octo-stg-claimshub-msg-a` | 29 | 64 | YES | No |
| NSG | standard | a | `nsg-octo-stg-claimshub-msg-a` | 28 | 80 | YES | No |
| Public IP | standard | a | `pip-octo-stg-claimshub-msg-a` | 28 | 80 | YES | No |
| Managed Identity | standard | a | `id-octo-stg-claimshub-msg-a` | 27 | 128 | YES | No |
| AKS | standard | a | `aks-octo-stg-claimshub-msg-a` | 28 | 63 | YES | No |
| App Gateway | standard | a | `agw-octo-stg-claimshub-msg-a` | 28 | 80 | YES | No |
| Storage Account | mini | b | `stcsclaimshubmsgb` | 17 | 24 | YES | No |
| Key Vault | mini | b | `kvcsclaimshubmsgb` | 17 | 24 | YES | No |
| Container Registry | mini | b | `crcsclaimshubmsgb` | 17 | 50 | YES | No |
| SQL Server | standard | b | `sql-octo-stg-claimshub-msg-b` | 28 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-octo-stg-claimshub-msg-b` | 30 | 128 | YES | No |
| App Service | standard | b | `app-octo-stg-claimshub-msg-b` | 28 | 60 | YES | No |
| App Service Plan | standard | b | `plan-octo-stg-claimshub-msg-b` | 29 | 40 | YES | No |
| Function App | standard | b | `func-octo-stg-claimshub-msg-b` | 29 | 60 | YES | No |
| API Management | standard | b | `apim-octo-stg-claimshub-msg-b` | 29 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-octo-stg-claimshub-msg-b` | 31 | 44 | YES | No |
| Redis Cache | standard | b | `redis-octo-stg-claimshub-msg-b` | 30 | 63 | YES | No |
| Service Bus | standard | b | `sb-octo-stg-claimshub-msg-b` | 27 | 50 | YES | No |
| Event Hub | standard | b | `evh-octo-stg-claimshub-msg-b` | 28 | 50 | YES | No |
| Log Analytics | standard | b | `log-octo-stg-claimshub-msg-b` | 28 | 63 | YES | No |
| App Configuration | small | b | `appcs-octo-stg-claimshub-msg-b` | 30 | 50 | YES | No |
| App Insights | small | b | `appi-octo-stg-claimshub-msg-b` | 29 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-octo-stg-claimshub-msg-b` | 29 | 64 | YES | No |
| NSG | standard | b | `nsg-octo-stg-claimshub-msg-b` | 28 | 80 | YES | No |
| Public IP | standard | b | `pip-octo-stg-claimshub-msg-b` | 28 | 80 | YES | No |
| Managed Identity | standard | b | `id-octo-stg-claimshub-msg-b` | 27 | 128 | YES | No |
| AKS | standard | b | `aks-octo-stg-claimshub-msg-b` | 28 | 63 | YES | No |
| App Gateway | standard | b | `agw-octo-stg-claimshub-msg-b` | 28 | 80 | YES | No |

## Test Case 9: `billing` — LOB=lexus, Stage=qa, Role=que

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stlqbillingquea` | 15 | 24 | YES | No |
| Key Vault | mini | a | `kvlqbillingquea` | 15 | 24 | YES | No |
| Container Registry | mini | a | `crlqbillingquea` | 15 | 50 | YES | No |
| SQL Server | standard | a | `sql-lexus-qa-billing-que-a` | 26 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-lexus-qa-billing-que-a` | 28 | 128 | YES | No |
| App Service | standard | a | `app-lexus-qa-billing-que-a` | 26 | 60 | YES | No |
| App Service Plan | standard | a | `plan-lexus-qa-billing-que-a` | 27 | 40 | YES | No |
| Function App | standard | a | `func-lexus-qa-billing-que-a` | 27 | 60 | YES | No |
| API Management | standard | a | `apim-lexus-qa-billing-que-a` | 27 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-lexus-qa-billing-que-a` | 29 | 44 | YES | No |
| Redis Cache | standard | a | `redis-lexus-qa-billing-que-a` | 28 | 63 | YES | No |
| Service Bus | standard | a | `sb-lexus-qa-billing-que-a` | 25 | 50 | YES | No |
| Event Hub | standard | a | `evh-lexus-qa-billing-que-a` | 26 | 50 | YES | No |
| Log Analytics | standard | a | `log-lexus-qa-billing-que-a` | 26 | 63 | YES | No |
| App Configuration | small | a | `appcs-lexus-qa-billing-que-a` | 28 | 50 | YES | No |
| App Insights | small | a | `appi-lexus-qa-billing-que-a` | 27 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-lexus-qa-billing-que-a` | 27 | 64 | YES | No |
| NSG | standard | a | `nsg-lexus-qa-billing-que-a` | 26 | 80 | YES | No |
| Public IP | standard | a | `pip-lexus-qa-billing-que-a` | 26 | 80 | YES | No |
| Managed Identity | standard | a | `id-lexus-qa-billing-que-a` | 25 | 128 | YES | No |
| AKS | standard | a | `aks-lexus-qa-billing-que-a` | 26 | 63 | YES | No |
| App Gateway | standard | a | `agw-lexus-qa-billing-que-a` | 26 | 80 | YES | No |
| Storage Account | mini | b | `stlqbillingqueb` | 15 | 24 | YES | No |
| Key Vault | mini | b | `kvlqbillingqueb` | 15 | 24 | YES | No |
| Container Registry | mini | b | `crlqbillingqueb` | 15 | 50 | YES | No |
| SQL Server | standard | b | `sql-lexus-qa-billing-que-b` | 26 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-lexus-qa-billing-que-b` | 28 | 128 | YES | No |
| App Service | standard | b | `app-lexus-qa-billing-que-b` | 26 | 60 | YES | No |
| App Service Plan | standard | b | `plan-lexus-qa-billing-que-b` | 27 | 40 | YES | No |
| Function App | standard | b | `func-lexus-qa-billing-que-b` | 27 | 60 | YES | No |
| API Management | standard | b | `apim-lexus-qa-billing-que-b` | 27 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-lexus-qa-billing-que-b` | 29 | 44 | YES | No |
| Redis Cache | standard | b | `redis-lexus-qa-billing-que-b` | 28 | 63 | YES | No |
| Service Bus | standard | b | `sb-lexus-qa-billing-que-b` | 25 | 50 | YES | No |
| Event Hub | standard | b | `evh-lexus-qa-billing-que-b` | 26 | 50 | YES | No |
| Log Analytics | standard | b | `log-lexus-qa-billing-que-b` | 26 | 63 | YES | No |
| App Configuration | small | b | `appcs-lexus-qa-billing-que-b` | 28 | 50 | YES | No |
| App Insights | small | b | `appi-lexus-qa-billing-que-b` | 27 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-lexus-qa-billing-que-b` | 27 | 64 | YES | No |
| NSG | standard | b | `nsg-lexus-qa-billing-que-b` | 26 | 80 | YES | No |
| Public IP | standard | b | `pip-lexus-qa-billing-que-b` | 26 | 80 | YES | No |
| Managed Identity | standard | b | `id-lexus-qa-billing-que-b` | 25 | 128 | YES | No |
| AKS | standard | b | `aks-lexus-qa-billing-que-b` | 26 | 63 | YES | No |
| App Gateway | standard | b | `agw-lexus-qa-billing-que-b` | 26 | 80 | YES | No |

## Test Case 10: `taxengine` — LOB=set, Stage=uat, Role=sch

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stsutaxenginescha` | 17 | 24 | YES | No |
| Key Vault | mini | a | `kvsutaxenginescha` | 17 | 24 | YES | No |
| Container Registry | mini | a | `crsutaxenginescha` | 17 | 50 | YES | No |
| SQL Server | standard | a | `sql-set-uat-taxengine-sch-a` | 27 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-set-uat-taxengine-sch-a` | 29 | 128 | YES | No |
| App Service | standard | a | `app-set-uat-taxengine-sch-a` | 27 | 60 | YES | No |
| App Service Plan | standard | a | `plan-set-uat-taxengine-sch-a` | 28 | 40 | YES | No |
| Function App | standard | a | `func-set-uat-taxengine-sch-a` | 28 | 60 | YES | No |
| API Management | standard | a | `apim-set-uat-taxengine-sch-a` | 28 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-set-uat-taxengine-sch-a` | 30 | 44 | YES | No |
| Redis Cache | standard | a | `redis-set-uat-taxengine-sch-a` | 29 | 63 | YES | No |
| Service Bus | standard | a | `sb-set-uat-taxengine-sch-a` | 26 | 50 | YES | No |
| Event Hub | standard | a | `evh-set-uat-taxengine-sch-a` | 27 | 50 | YES | No |
| Log Analytics | standard | a | `log-set-uat-taxengine-sch-a` | 27 | 63 | YES | No |
| App Configuration | small | a | `appcs-set-uat-taxengine-sch-a` | 29 | 50 | YES | No |
| App Insights | small | a | `appi-set-uat-taxengine-sch-a` | 28 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-set-uat-taxengine-sch-a` | 28 | 64 | YES | No |
| NSG | standard | a | `nsg-set-uat-taxengine-sch-a` | 27 | 80 | YES | No |
| Public IP | standard | a | `pip-set-uat-taxengine-sch-a` | 27 | 80 | YES | No |
| Managed Identity | standard | a | `id-set-uat-taxengine-sch-a` | 26 | 128 | YES | No |
| AKS | standard | a | `aks-set-uat-taxengine-sch-a` | 27 | 63 | YES | No |
| App Gateway | standard | a | `agw-set-uat-taxengine-sch-a` | 27 | 80 | YES | No |
| Storage Account | mini | b | `stsutaxengineschb` | 17 | 24 | YES | No |
| Key Vault | mini | b | `kvsutaxengineschb` | 17 | 24 | YES | No |
| Container Registry | mini | b | `crsutaxengineschb` | 17 | 50 | YES | No |
| SQL Server | standard | b | `sql-set-uat-taxengine-sch-b` | 27 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-set-uat-taxengine-sch-b` | 29 | 128 | YES | No |
| App Service | standard | b | `app-set-uat-taxengine-sch-b` | 27 | 60 | YES | No |
| App Service Plan | standard | b | `plan-set-uat-taxengine-sch-b` | 28 | 40 | YES | No |
| Function App | standard | b | `func-set-uat-taxengine-sch-b` | 28 | 60 | YES | No |
| API Management | standard | b | `apim-set-uat-taxengine-sch-b` | 28 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-set-uat-taxengine-sch-b` | 30 | 44 | YES | No |
| Redis Cache | standard | b | `redis-set-uat-taxengine-sch-b` | 29 | 63 | YES | No |
| Service Bus | standard | b | `sb-set-uat-taxengine-sch-b` | 26 | 50 | YES | No |
| Event Hub | standard | b | `evh-set-uat-taxengine-sch-b` | 27 | 50 | YES | No |
| Log Analytics | standard | b | `log-set-uat-taxengine-sch-b` | 27 | 63 | YES | No |
| App Configuration | small | b | `appcs-set-uat-taxengine-sch-b` | 29 | 50 | YES | No |
| App Insights | small | b | `appi-set-uat-taxengine-sch-b` | 28 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-set-uat-taxengine-sch-b` | 28 | 64 | YES | No |
| NSG | standard | b | `nsg-set-uat-taxengine-sch-b` | 27 | 80 | YES | No |
| Public IP | standard | b | `pip-set-uat-taxengine-sch-b` | 27 | 80 | YES | No |
| Managed Identity | standard | b | `id-set-uat-taxengine-sch-b` | 26 | 128 | YES | No |
| AKS | standard | b | `aks-set-uat-taxengine-sch-b` | 27 | 63 | YES | No |
| App Gateway | standard | b | `agw-set-uat-taxengine-sch-b` | 27 | 80 | YES | No |

## Test Case 11: `portfolio` — LOB=setf, Stage=prod, Role=log

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stvpportfoliologa` | 17 | 24 | YES | No |
| Key Vault | mini | a | `kvvpportfoliologa` | 17 | 24 | YES | No |
| Container Registry | mini | a | `crvpportfoliologa` | 17 | 50 | YES | No |
| SQL Server | standard | a | `sql-setf-prod-portfolio-log-a` | 29 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-setf-prod-portfolio-log-a` | 31 | 128 | YES | No |
| App Service | standard | a | `app-setf-prod-portfolio-log-a` | 29 | 60 | YES | No |
| App Service Plan | standard | a | `plan-setf-prod-portfolio-log-a` | 30 | 40 | YES | No |
| Function App | standard | a | `func-setf-prod-portfolio-log-a` | 30 | 60 | YES | No |
| API Management | standard | a | `apim-setf-prod-portfolio-log-a` | 30 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-setf-prod-portfolio-log-a` | 32 | 44 | YES | No |
| Redis Cache | standard | a | `redis-setf-prod-portfolio-log-a` | 31 | 63 | YES | No |
| Service Bus | standard | a | `sb-setf-prod-portfolio-log-a` | 28 | 50 | YES | No |
| Event Hub | standard | a | `evh-setf-prod-portfolio-log-a` | 29 | 50 | YES | No |
| Log Analytics | standard | a | `log-setf-prod-portfolio-log-a` | 29 | 63 | YES | No |
| App Configuration | small | a | `appcs-setf-prod-portfolio-log-a` | 31 | 50 | YES | No |
| App Insights | small | a | `appi-setf-prod-portfolio-log-a` | 30 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-setf-prod-portfolio-log-a` | 30 | 64 | YES | No |
| NSG | standard | a | `nsg-setf-prod-portfolio-log-a` | 29 | 80 | YES | No |
| Public IP | standard | a | `pip-setf-prod-portfolio-log-a` | 29 | 80 | YES | No |
| Managed Identity | standard | a | `id-setf-prod-portfolio-log-a` | 28 | 128 | YES | No |
| AKS | standard | a | `aks-setf-prod-portfolio-log-a` | 29 | 63 | YES | No |
| App Gateway | standard | a | `agw-setf-prod-portfolio-log-a` | 29 | 80 | YES | No |
| Storage Account | mini | b | `stvpportfoliologb` | 17 | 24 | YES | No |
| Key Vault | mini | b | `kvvpportfoliologb` | 17 | 24 | YES | No |
| Container Registry | mini | b | `crvpportfoliologb` | 17 | 50 | YES | No |
| SQL Server | standard | b | `sql-setf-prod-portfolio-log-b` | 29 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-setf-prod-portfolio-log-b` | 31 | 128 | YES | No |
| App Service | standard | b | `app-setf-prod-portfolio-log-b` | 29 | 60 | YES | No |
| App Service Plan | standard | b | `plan-setf-prod-portfolio-log-b` | 30 | 40 | YES | No |
| Function App | standard | b | `func-setf-prod-portfolio-log-b` | 30 | 60 | YES | No |
| API Management | standard | b | `apim-setf-prod-portfolio-log-b` | 30 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-setf-prod-portfolio-log-b` | 32 | 44 | YES | No |
| Redis Cache | standard | b | `redis-setf-prod-portfolio-log-b` | 31 | 63 | YES | No |
| Service Bus | standard | b | `sb-setf-prod-portfolio-log-b` | 28 | 50 | YES | No |
| Event Hub | standard | b | `evh-setf-prod-portfolio-log-b` | 29 | 50 | YES | No |
| Log Analytics | standard | b | `log-setf-prod-portfolio-log-b` | 29 | 63 | YES | No |
| App Configuration | small | b | `appcs-setf-prod-portfolio-log-b` | 31 | 50 | YES | No |
| App Insights | small | b | `appi-setf-prod-portfolio-log-b` | 30 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-setf-prod-portfolio-log-b` | 30 | 64 | YES | No |
| NSG | standard | b | `nsg-setf-prod-portfolio-log-b` | 29 | 80 | YES | No |
| Public IP | standard | b | `pip-setf-prod-portfolio-log-b` | 29 | 80 | YES | No |
| Managed Identity | standard | b | `id-setf-prod-portfolio-log-b` | 28 | 128 | YES | No |
| AKS | standard | b | `aks-setf-prod-portfolio-log-b` | 29 | 63 | YES | No |
| App Gateway | standard | b | `agw-setf-prod-portfolio-log-b` | 29 | 80 | YES | No |

## Test Case 12: `riskmodel` — LOB=jma, Stage=nonprod, Role=cfg

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stjnriskmodelcfga` | 17 | 24 | YES | No |
| Key Vault | mini | a | `kvjnriskmodelcfga` | 17 | 24 | YES | No |
| Container Registry | mini | a | `crjnriskmodelcfga` | 17 | 50 | YES | No |
| SQL Server | standard | a | `sql-jma-nonprod-riskmodel-cfg-a` | 31 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-jma-nonprod-riskmodel-cfg-a` | 33 | 128 | YES | No |
| App Service | standard | a | `app-jma-nonprod-riskmodel-cfg-a` | 31 | 60 | YES | No |
| App Service Plan | standard | a | `plan-jma-nonprod-riskmodel-cfg-a` | 32 | 40 | YES | No |
| Function App | standard | a | `func-jma-nonprod-riskmodel-cfg-a` | 32 | 60 | YES | No |
| API Management | standard | a | `apim-jma-nonprod-riskmodel-cfg-a` | 32 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-jma-nonprod-riskmodel-cfg-a` | 34 | 44 | YES | No |
| Redis Cache | standard | a | `redis-jma-nonprod-riskmodel-cfg-a` | 33 | 63 | YES | No |
| Service Bus | standard | a | `sb-jma-nonprod-riskmodel-cfg-a` | 30 | 50 | YES | No |
| Event Hub | standard | a | `evh-jma-nonprod-riskmodel-cfg-a` | 31 | 50 | YES | No |
| Log Analytics | standard | a | `log-jma-nonprod-riskmodel-cfg-a` | 31 | 63 | YES | No |
| App Configuration | small | a | `appcs-jma-nonprod-riskmodel-cfg-a` | 33 | 50 | YES | No |
| App Insights | small | a | `appi-jma-nonprod-riskmodel-cfg-a` | 32 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-jma-nonprod-riskmodel-cfg-a` | 32 | 64 | YES | No |
| NSG | standard | a | `nsg-jma-nonprod-riskmodel-cfg-a` | 31 | 80 | YES | No |
| Public IP | standard | a | `pip-jma-nonprod-riskmodel-cfg-a` | 31 | 80 | YES | No |
| Managed Identity | standard | a | `id-jma-nonprod-riskmodel-cfg-a` | 30 | 128 | YES | No |
| AKS | standard | a | `aks-jma-nonprod-riskmodel-cfg-a` | 31 | 63 | YES | No |
| App Gateway | standard | a | `agw-jma-nonprod-riskmodel-cfg-a` | 31 | 80 | YES | No |
| Storage Account | mini | b | `stjnriskmodelcfgb` | 17 | 24 | YES | No |
| Key Vault | mini | b | `kvjnriskmodelcfgb` | 17 | 24 | YES | No |
| Container Registry | mini | b | `crjnriskmodelcfgb` | 17 | 50 | YES | No |
| SQL Server | standard | b | `sql-jma-nonprod-riskmodel-cfg-b` | 31 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-jma-nonprod-riskmodel-cfg-b` | 33 | 128 | YES | No |
| App Service | standard | b | `app-jma-nonprod-riskmodel-cfg-b` | 31 | 60 | YES | No |
| App Service Plan | standard | b | `plan-jma-nonprod-riskmodel-cfg-b` | 32 | 40 | YES | No |
| Function App | standard | b | `func-jma-nonprod-riskmodel-cfg-b` | 32 | 60 | YES | No |
| API Management | standard | b | `apim-jma-nonprod-riskmodel-cfg-b` | 32 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-jma-nonprod-riskmodel-cfg-b` | 34 | 44 | YES | No |
| Redis Cache | standard | b | `redis-jma-nonprod-riskmodel-cfg-b` | 33 | 63 | YES | No |
| Service Bus | standard | b | `sb-jma-nonprod-riskmodel-cfg-b` | 30 | 50 | YES | No |
| Event Hub | standard | b | `evh-jma-nonprod-riskmodel-cfg-b` | 31 | 50 | YES | No |
| Log Analytics | standard | b | `log-jma-nonprod-riskmodel-cfg-b` | 31 | 63 | YES | No |
| App Configuration | small | b | `appcs-jma-nonprod-riskmodel-cfg-b` | 33 | 50 | YES | No |
| App Insights | small | b | `appi-jma-nonprod-riskmodel-cfg-b` | 32 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-jma-nonprod-riskmodel-cfg-b` | 32 | 64 | YES | No |
| NSG | standard | b | `nsg-jma-nonprod-riskmodel-cfg-b` | 31 | 80 | YES | No |
| Public IP | standard | b | `pip-jma-nonprod-riskmodel-cfg-b` | 31 | 80 | YES | No |
| Managed Identity | standard | b | `id-jma-nonprod-riskmodel-cfg-b` | 30 | 128 | YES | No |
| AKS | standard | b | `aks-jma-nonprod-riskmodel-cfg-b` | 31 | 63 | YES | No |
| App Gateway | standard | b | `agw-jma-nonprod-riskmodel-cfg-b` | 31 | 80 | YES | No |

## Test Case 13: `custportal` — LOB=jmf, Stage=dev, Role=be

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stfdcustportalbea` | 17 | 24 | YES | No |
| Key Vault | mini | a | `kvfdcustportalbea` | 17 | 24 | YES | No |
| Container Registry | mini | a | `crfdcustportalbea` | 17 | 50 | YES | No |
| SQL Server | standard | a | `sql-jmf-dev-custportal-be-a` | 27 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-jmf-dev-custportal-be-a` | 29 | 128 | YES | No |
| App Service | standard | a | `app-jmf-dev-custportal-be-a` | 27 | 60 | YES | No |
| App Service Plan | standard | a | `plan-jmf-dev-custportal-be-a` | 28 | 40 | YES | No |
| Function App | standard | a | `func-jmf-dev-custportal-be-a` | 28 | 60 | YES | No |
| API Management | standard | a | `apim-jmf-dev-custportal-be-a` | 28 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-jmf-dev-custportal-be-a` | 30 | 44 | YES | No |
| Redis Cache | standard | a | `redis-jmf-dev-custportal-be-a` | 29 | 63 | YES | No |
| Service Bus | standard | a | `sb-jmf-dev-custportal-be-a` | 26 | 50 | YES | No |
| Event Hub | standard | a | `evh-jmf-dev-custportal-be-a` | 27 | 50 | YES | No |
| Log Analytics | standard | a | `log-jmf-dev-custportal-be-a` | 27 | 63 | YES | No |
| App Configuration | small | a | `appcs-jmf-dev-custportal-be-a` | 29 | 50 | YES | No |
| App Insights | small | a | `appi-jmf-dev-custportal-be-a` | 28 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-jmf-dev-custportal-be-a` | 28 | 64 | YES | No |
| NSG | standard | a | `nsg-jmf-dev-custportal-be-a` | 27 | 80 | YES | No |
| Public IP | standard | a | `pip-jmf-dev-custportal-be-a` | 27 | 80 | YES | No |
| Managed Identity | standard | a | `id-jmf-dev-custportal-be-a` | 26 | 128 | YES | No |
| AKS | standard | a | `aks-jmf-dev-custportal-be-a` | 27 | 63 | YES | No |
| App Gateway | standard | a | `agw-jmf-dev-custportal-be-a` | 27 | 80 | YES | No |
| Storage Account | mini | b | `stfdcustportalbeb` | 17 | 24 | YES | No |
| Key Vault | mini | b | `kvfdcustportalbeb` | 17 | 24 | YES | No |
| Container Registry | mini | b | `crfdcustportalbeb` | 17 | 50 | YES | No |
| SQL Server | standard | b | `sql-jmf-dev-custportal-be-b` | 27 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-jmf-dev-custportal-be-b` | 29 | 128 | YES | No |
| App Service | standard | b | `app-jmf-dev-custportal-be-b` | 27 | 60 | YES | No |
| App Service Plan | standard | b | `plan-jmf-dev-custportal-be-b` | 28 | 40 | YES | No |
| Function App | standard | b | `func-jmf-dev-custportal-be-b` | 28 | 60 | YES | No |
| API Management | standard | b | `apim-jmf-dev-custportal-be-b` | 28 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-jmf-dev-custportal-be-b` | 30 | 44 | YES | No |
| Redis Cache | standard | b | `redis-jmf-dev-custportal-be-b` | 29 | 63 | YES | No |
| Service Bus | standard | b | `sb-jmf-dev-custportal-be-b` | 26 | 50 | YES | No |
| Event Hub | standard | b | `evh-jmf-dev-custportal-be-b` | 27 | 50 | YES | No |
| Log Analytics | standard | b | `log-jmf-dev-custportal-be-b` | 27 | 63 | YES | No |
| App Configuration | small | b | `appcs-jmf-dev-custportal-be-b` | 29 | 50 | YES | No |
| App Insights | small | b | `appi-jmf-dev-custportal-be-b` | 28 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-jmf-dev-custportal-be-b` | 28 | 64 | YES | No |
| NSG | standard | b | `nsg-jmf-dev-custportal-be-b` | 27 | 80 | YES | No |
| Public IP | standard | b | `pip-jmf-dev-custportal-be-b` | 27 | 80 | YES | No |
| Managed Identity | standard | b | `id-jmf-dev-custportal-be-b` | 26 | 128 | YES | No |
| AKS | standard | b | `aks-jmf-dev-custportal-be-b` | 27 | 63 | YES | No |
| App Gateway | standard | b | `agw-jmf-dev-custportal-be-b` | 27 | 80 | YES | No |

## Test Case 14: `supplychain` — LOB=jmfe, Stage=stg, Role=chk

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stessupplychainchka` | 19 | 24 | YES | No |
| Key Vault | mini | a | `kvessupplychainchka` | 19 | 24 | YES | No |
| Container Registry | mini | a | `cressupplychainchka` | 19 | 50 | YES | No |
| SQL Server | standard | a | `sql-jmfe-stg-supplychain-chk-a` | 30 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-jmfe-stg-supplychain-chk-a` | 32 | 128 | YES | No |
| App Service | standard | a | `app-jmfe-stg-supplychain-chk-a` | 30 | 60 | YES | No |
| App Service Plan | standard | a | `plan-jmfe-stg-supplychain-chk-a` | 31 | 40 | YES | No |
| Function App | standard | a | `func-jmfe-stg-supplychain-chk-a` | 31 | 60 | YES | No |
| API Management | standard | a | `apim-jmfe-stg-supplychain-chk-a` | 31 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-jmfe-stg-supplychain-chk-a` | 33 | 44 | YES | No |
| Redis Cache | standard | a | `redis-jmfe-stg-supplychain-chk-a` | 32 | 63 | YES | No |
| Service Bus | standard | a | `sb-jmfe-stg-supplychain-chk-a` | 29 | 50 | YES | No |
| Event Hub | standard | a | `evh-jmfe-stg-supplychain-chk-a` | 30 | 50 | YES | No |
| Log Analytics | standard | a | `log-jmfe-stg-supplychain-chk-a` | 30 | 63 | YES | No |
| App Configuration | small | a | `appcs-jmfe-stg-supplychain-chk-a` | 32 | 50 | YES | No |
| App Insights | small | a | `appi-jmfe-stg-supplychain-chk-a` | 31 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-jmfe-stg-supplychain-chk-a` | 31 | 64 | YES | No |
| NSG | standard | a | `nsg-jmfe-stg-supplychain-chk-a` | 30 | 80 | YES | No |
| Public IP | standard | a | `pip-jmfe-stg-supplychain-chk-a` | 30 | 80 | YES | No |
| Managed Identity | standard | a | `id-jmfe-stg-supplychain-chk-a` | 29 | 128 | YES | No |
| AKS | standard | a | `aks-jmfe-stg-supplychain-chk-a` | 30 | 63 | YES | No |
| App Gateway | standard | a | `agw-jmfe-stg-supplychain-chk-a` | 30 | 80 | YES | No |
| Storage Account | mini | b | `stessupplychainchkb` | 19 | 24 | YES | No |
| Key Vault | mini | b | `kvessupplychainchkb` | 19 | 24 | YES | No |
| Container Registry | mini | b | `cressupplychainchkb` | 19 | 50 | YES | No |
| SQL Server | standard | b | `sql-jmfe-stg-supplychain-chk-b` | 30 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-jmfe-stg-supplychain-chk-b` | 32 | 128 | YES | No |
| App Service | standard | b | `app-jmfe-stg-supplychain-chk-b` | 30 | 60 | YES | No |
| App Service Plan | standard | b | `plan-jmfe-stg-supplychain-chk-b` | 31 | 40 | YES | No |
| Function App | standard | b | `func-jmfe-stg-supplychain-chk-b` | 31 | 60 | YES | No |
| API Management | standard | b | `apim-jmfe-stg-supplychain-chk-b` | 31 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-jmfe-stg-supplychain-chk-b` | 33 | 44 | YES | No |
| Redis Cache | standard | b | `redis-jmfe-stg-supplychain-chk-b` | 32 | 63 | YES | No |
| Service Bus | standard | b | `sb-jmfe-stg-supplychain-chk-b` | 29 | 50 | YES | No |
| Event Hub | standard | b | `evh-jmfe-stg-supplychain-chk-b` | 30 | 50 | YES | No |
| Log Analytics | standard | b | `log-jmfe-stg-supplychain-chk-b` | 30 | 63 | YES | No |
| App Configuration | small | b | `appcs-jmfe-stg-supplychain-chk-b` | 32 | 50 | YES | No |
| App Insights | small | b | `appi-jmfe-stg-supplychain-chk-b` | 31 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-jmfe-stg-supplychain-chk-b` | 31 | 64 | YES | No |
| NSG | standard | b | `nsg-jmfe-stg-supplychain-chk-b` | 30 | 80 | YES | No |
| Public IP | standard | b | `pip-jmfe-stg-supplychain-chk-b` | 30 | 80 | YES | No |
| Managed Identity | standard | b | `id-jmfe-stg-supplychain-chk-b` | 29 | 128 | YES | No |
| AKS | standard | b | `aks-jmfe-stg-supplychain-chk-b` | 30 | 63 | YES | No |
| App Gateway | standard | b | `agw-jmfe-stg-supplychain-chk-b` | 30 | 80 | YES | No |

## Test Case 15: `chatbot` — LOB=to, Stage=qa, Role=cch

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `sttqchatbotccha` | 15 | 24 | YES | No |
| Key Vault | mini | a | `kvtqchatbotccha` | 15 | 24 | YES | No |
| Container Registry | mini | a | `crtqchatbotccha` | 15 | 50 | YES | No |
| SQL Server | standard | a | `sql-to-qa-chatbot-cch-a` | 23 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-to-qa-chatbot-cch-a` | 25 | 128 | YES | No |
| App Service | standard | a | `app-to-qa-chatbot-cch-a` | 23 | 60 | YES | No |
| App Service Plan | standard | a | `plan-to-qa-chatbot-cch-a` | 24 | 40 | YES | No |
| Function App | standard | a | `func-to-qa-chatbot-cch-a` | 24 | 60 | YES | No |
| API Management | standard | a | `apim-to-qa-chatbot-cch-a` | 24 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-to-qa-chatbot-cch-a` | 26 | 44 | YES | No |
| Redis Cache | standard | a | `redis-to-qa-chatbot-cch-a` | 25 | 63 | YES | No |
| Service Bus | standard | a | `sb-to-qa-chatbot-cch-a` | 22 | 50 | YES | No |
| Event Hub | standard | a | `evh-to-qa-chatbot-cch-a` | 23 | 50 | YES | No |
| Log Analytics | standard | a | `log-to-qa-chatbot-cch-a` | 23 | 63 | YES | No |
| App Configuration | small | a | `appcs-to-qa-chatbot-cch-a` | 25 | 50 | YES | No |
| App Insights | small | a | `appi-to-qa-chatbot-cch-a` | 24 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-to-qa-chatbot-cch-a` | 24 | 64 | YES | No |
| NSG | standard | a | `nsg-to-qa-chatbot-cch-a` | 23 | 80 | YES | No |
| Public IP | standard | a | `pip-to-qa-chatbot-cch-a` | 23 | 80 | YES | No |
| Managed Identity | standard | a | `id-to-qa-chatbot-cch-a` | 22 | 128 | YES | No |
| AKS | standard | a | `aks-to-qa-chatbot-cch-a` | 23 | 63 | YES | No |
| App Gateway | standard | a | `agw-to-qa-chatbot-cch-a` | 23 | 80 | YES | No |
| Storage Account | mini | b | `sttqchatbotcchb` | 15 | 24 | YES | No |
| Key Vault | mini | b | `kvtqchatbotcchb` | 15 | 24 | YES | No |
| Container Registry | mini | b | `crtqchatbotcchb` | 15 | 50 | YES | No |
| SQL Server | standard | b | `sql-to-qa-chatbot-cch-b` | 23 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-to-qa-chatbot-cch-b` | 25 | 128 | YES | No |
| App Service | standard | b | `app-to-qa-chatbot-cch-b` | 23 | 60 | YES | No |
| App Service Plan | standard | b | `plan-to-qa-chatbot-cch-b` | 24 | 40 | YES | No |
| Function App | standard | b | `func-to-qa-chatbot-cch-b` | 24 | 60 | YES | No |
| API Management | standard | b | `apim-to-qa-chatbot-cch-b` | 24 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-to-qa-chatbot-cch-b` | 26 | 44 | YES | No |
| Redis Cache | standard | b | `redis-to-qa-chatbot-cch-b` | 25 | 63 | YES | No |
| Service Bus | standard | b | `sb-to-qa-chatbot-cch-b` | 22 | 50 | YES | No |
| Event Hub | standard | b | `evh-to-qa-chatbot-cch-b` | 23 | 50 | YES | No |
| Log Analytics | standard | b | `log-to-qa-chatbot-cch-b` | 23 | 63 | YES | No |
| App Configuration | small | b | `appcs-to-qa-chatbot-cch-b` | 25 | 50 | YES | No |
| App Insights | small | b | `appi-to-qa-chatbot-cch-b` | 24 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-to-qa-chatbot-cch-b` | 24 | 64 | YES | No |
| NSG | standard | b | `nsg-to-qa-chatbot-cch-b` | 23 | 80 | YES | No |
| Public IP | standard | b | `pip-to-qa-chatbot-cch-b` | 23 | 80 | YES | No |
| Managed Identity | standard | b | `id-to-qa-chatbot-cch-b` | 22 | 128 | YES | No |
| AKS | standard | b | `aks-to-qa-chatbot-cch-b` | 23 | 63 | YES | No |
| App Gateway | standard | b | `agw-to-qa-chatbot-cch-b` | 23 | 80 | YES | No |

## Test Case 16: `auditlog` — LOB=ocio, Stage=uat, Role=api

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stiuauditlogapia` | 16 | 24 | YES | No |
| Key Vault | mini | a | `kviuauditlogapia` | 16 | 24 | YES | No |
| Container Registry | mini | a | `criuauditlogapia` | 16 | 50 | YES | No |
| SQL Server | standard | a | `sql-ocio-uat-auditlog-api-a` | 27 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-ocio-uat-auditlog-api-a` | 29 | 128 | YES | No |
| App Service | standard | a | `app-ocio-uat-auditlog-api-a` | 27 | 60 | YES | No |
| App Service Plan | standard | a | `plan-ocio-uat-auditlog-api-a` | 28 | 40 | YES | No |
| Function App | standard | a | `func-ocio-uat-auditlog-api-a` | 28 | 60 | YES | No |
| API Management | standard | a | `apim-ocio-uat-auditlog-api-a` | 28 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-ocio-uat-auditlog-api-a` | 30 | 44 | YES | No |
| Redis Cache | standard | a | `redis-ocio-uat-auditlog-api-a` | 29 | 63 | YES | No |
| Service Bus | standard | a | `sb-ocio-uat-auditlog-api-a` | 26 | 50 | YES | No |
| Event Hub | standard | a | `evh-ocio-uat-auditlog-api-a` | 27 | 50 | YES | No |
| Log Analytics | standard | a | `log-ocio-uat-auditlog-api-a` | 27 | 63 | YES | No |
| App Configuration | small | a | `appcs-ocio-uat-auditlog-api-a` | 29 | 50 | YES | No |
| App Insights | small | a | `appi-ocio-uat-auditlog-api-a` | 28 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-ocio-uat-auditlog-api-a` | 28 | 64 | YES | No |
| NSG | standard | a | `nsg-ocio-uat-auditlog-api-a` | 27 | 80 | YES | No |
| Public IP | standard | a | `pip-ocio-uat-auditlog-api-a` | 27 | 80 | YES | No |
| Managed Identity | standard | a | `id-ocio-uat-auditlog-api-a` | 26 | 128 | YES | No |
| AKS | standard | a | `aks-ocio-uat-auditlog-api-a` | 27 | 63 | YES | No |
| App Gateway | standard | a | `agw-ocio-uat-auditlog-api-a` | 27 | 80 | YES | No |
| Storage Account | mini | b | `stiuauditlogapib` | 16 | 24 | YES | No |
| Key Vault | mini | b | `kviuauditlogapib` | 16 | 24 | YES | No |
| Container Registry | mini | b | `criuauditlogapib` | 16 | 50 | YES | No |
| SQL Server | standard | b | `sql-ocio-uat-auditlog-api-b` | 27 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-ocio-uat-auditlog-api-b` | 29 | 128 | YES | No |
| App Service | standard | b | `app-ocio-uat-auditlog-api-b` | 27 | 60 | YES | No |
| App Service Plan | standard | b | `plan-ocio-uat-auditlog-api-b` | 28 | 40 | YES | No |
| Function App | standard | b | `func-ocio-uat-auditlog-api-b` | 28 | 60 | YES | No |
| API Management | standard | b | `apim-ocio-uat-auditlog-api-b` | 28 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-ocio-uat-auditlog-api-b` | 30 | 44 | YES | No |
| Redis Cache | standard | b | `redis-ocio-uat-auditlog-api-b` | 29 | 63 | YES | No |
| Service Bus | standard | b | `sb-ocio-uat-auditlog-api-b` | 26 | 50 | YES | No |
| Event Hub | standard | b | `evh-ocio-uat-auditlog-api-b` | 27 | 50 | YES | No |
| Log Analytics | standard | b | `log-ocio-uat-auditlog-api-b` | 27 | 63 | YES | No |
| App Configuration | small | b | `appcs-ocio-uat-auditlog-api-b` | 29 | 50 | YES | No |
| App Insights | small | b | `appi-ocio-uat-auditlog-api-b` | 28 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-ocio-uat-auditlog-api-b` | 28 | 64 | YES | No |
| NSG | standard | b | `nsg-ocio-uat-auditlog-api-b` | 27 | 80 | YES | No |
| Public IP | standard | b | `pip-ocio-uat-auditlog-api-b` | 27 | 80 | YES | No |
| Managed Identity | standard | b | `id-ocio-uat-auditlog-api-b` | 26 | 128 | YES | No |
| AKS | standard | b | `aks-ocio-uat-auditlog-api-b` | 27 | 63 | YES | No |
| App Gateway | standard | b | `agw-ocio-uat-auditlog-api-b` | 27 | 80 | YES | No |

## Test Case 17: `docmgmt` — LOB=octo, Stage=prod, Role=web

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stcpdocmgmtweba` | 15 | 24 | YES | No |
| Key Vault | mini | a | `kvcpdocmgmtweba` | 15 | 24 | YES | No |
| Container Registry | mini | a | `crcpdocmgmtweba` | 15 | 50 | YES | No |
| SQL Server | standard | a | `sql-octo-prod-docmgmt-web-a` | 27 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-octo-prod-docmgmt-web-a` | 29 | 128 | YES | No |
| App Service | standard | a | `app-octo-prod-docmgmt-web-a` | 27 | 60 | YES | No |
| App Service Plan | standard | a | `plan-octo-prod-docmgmt-web-a` | 28 | 40 | YES | No |
| Function App | standard | a | `func-octo-prod-docmgmt-web-a` | 28 | 60 | YES | No |
| API Management | standard | a | `apim-octo-prod-docmgmt-web-a` | 28 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-octo-prod-docmgmt-web-a` | 30 | 44 | YES | No |
| Redis Cache | standard | a | `redis-octo-prod-docmgmt-web-a` | 29 | 63 | YES | No |
| Service Bus | standard | a | `sb-octo-prod-docmgmt-web-a` | 26 | 50 | YES | No |
| Event Hub | standard | a | `evh-octo-prod-docmgmt-web-a` | 27 | 50 | YES | No |
| Log Analytics | standard | a | `log-octo-prod-docmgmt-web-a` | 27 | 63 | YES | No |
| App Configuration | small | a | `appcs-octo-prod-docmgmt-web-a` | 29 | 50 | YES | No |
| App Insights | small | a | `appi-octo-prod-docmgmt-web-a` | 28 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-octo-prod-docmgmt-web-a` | 28 | 64 | YES | No |
| NSG | standard | a | `nsg-octo-prod-docmgmt-web-a` | 27 | 80 | YES | No |
| Public IP | standard | a | `pip-octo-prod-docmgmt-web-a` | 27 | 80 | YES | No |
| Managed Identity | standard | a | `id-octo-prod-docmgmt-web-a` | 26 | 128 | YES | No |
| AKS | standard | a | `aks-octo-prod-docmgmt-web-a` | 27 | 63 | YES | No |
| App Gateway | standard | a | `agw-octo-prod-docmgmt-web-a` | 27 | 80 | YES | No |
| Storage Account | mini | b | `stcpdocmgmtwebb` | 15 | 24 | YES | No |
| Key Vault | mini | b | `kvcpdocmgmtwebb` | 15 | 24 | YES | No |
| Container Registry | mini | b | `crcpdocmgmtwebb` | 15 | 50 | YES | No |
| SQL Server | standard | b | `sql-octo-prod-docmgmt-web-b` | 27 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-octo-prod-docmgmt-web-b` | 29 | 128 | YES | No |
| App Service | standard | b | `app-octo-prod-docmgmt-web-b` | 27 | 60 | YES | No |
| App Service Plan | standard | b | `plan-octo-prod-docmgmt-web-b` | 28 | 40 | YES | No |
| Function App | standard | b | `func-octo-prod-docmgmt-web-b` | 28 | 60 | YES | No |
| API Management | standard | b | `apim-octo-prod-docmgmt-web-b` | 28 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-octo-prod-docmgmt-web-b` | 30 | 44 | YES | No |
| Redis Cache | standard | b | `redis-octo-prod-docmgmt-web-b` | 29 | 63 | YES | No |
| Service Bus | standard | b | `sb-octo-prod-docmgmt-web-b` | 26 | 50 | YES | No |
| Event Hub | standard | b | `evh-octo-prod-docmgmt-web-b` | 27 | 50 | YES | No |
| Log Analytics | standard | b | `log-octo-prod-docmgmt-web-b` | 27 | 63 | YES | No |
| App Configuration | small | b | `appcs-octo-prod-docmgmt-web-b` | 29 | 50 | YES | No |
| App Insights | small | b | `appi-octo-prod-docmgmt-web-b` | 28 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-octo-prod-docmgmt-web-b` | 28 | 64 | YES | No |
| NSG | standard | b | `nsg-octo-prod-docmgmt-web-b` | 27 | 80 | YES | No |
| Public IP | standard | b | `pip-octo-prod-docmgmt-web-b` | 27 | 80 | YES | No |
| Managed Identity | standard | b | `id-octo-prod-docmgmt-web-b` | 26 | 128 | YES | No |
| AKS | standard | b | `aks-octo-prod-docmgmt-web-b` | 27 | 63 | YES | No |
| App Gateway | standard | b | `agw-octo-prod-docmgmt-web-b` | 27 | 80 | YES | No |

## Test Case 18: `policyeng` — LOB=lexus, Stage=nonprod, Role=rpt

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stlnpolicyengrpta` | 17 | 24 | YES | No |
| Key Vault | mini | a | `kvlnpolicyengrpta` | 17 | 24 | YES | No |
| Container Registry | mini | a | `crlnpolicyengrpta` | 17 | 50 | YES | No |
| SQL Server | standard | a | `sql-lexus-nonprod-policyeng-rpt-a` | 33 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-lexus-nonprod-policyeng-rpt-a` | 35 | 128 | YES | No |
| App Service | standard | a | `app-lexus-nonprod-policyeng-rpt-a` | 33 | 60 | YES | No |
| App Service Plan | standard | a | `plan-lexus-nonprod-policyeng-rpt-a` | 34 | 40 | YES | No |
| Function App | standard | a | `func-lexus-nonprod-policyeng-rpt-a` | 34 | 60 | YES | No |
| API Management | standard | a | `apim-lexus-nonprod-policyeng-rpt-a` | 34 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-lexus-nonprod-policyeng-rpt-a` | 36 | 44 | YES | No |
| Redis Cache | standard | a | `redis-lexus-nonprod-policyeng-rpt-a` | 35 | 63 | YES | No |
| Service Bus | standard | a | `sb-lexus-nonprod-policyeng-rpt-a` | 32 | 50 | YES | No |
| Event Hub | standard | a | `evh-lexus-nonprod-policyeng-rpt-a` | 33 | 50 | YES | No |
| Log Analytics | standard | a | `log-lexus-nonprod-policyeng-rpt-a` | 33 | 63 | YES | No |
| App Configuration | small | a | `appcs-lexus-nonprod-policyeng-rpt-a` | 35 | 50 | YES | No |
| App Insights | small | a | `appi-lexus-nonprod-policyeng-rpt-a` | 34 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-lexus-nonprod-policyeng-rpt-a` | 34 | 64 | YES | No |
| NSG | standard | a | `nsg-lexus-nonprod-policyeng-rpt-a` | 33 | 80 | YES | No |
| Public IP | standard | a | `pip-lexus-nonprod-policyeng-rpt-a` | 33 | 80 | YES | No |
| Managed Identity | standard | a | `id-lexus-nonprod-policyeng-rpt-a` | 32 | 128 | YES | No |
| AKS | standard | a | `aks-lexus-nonprod-policyeng-rpt-a` | 33 | 63 | YES | No |
| App Gateway | standard | a | `agw-lexus-nonprod-policyeng-rpt-a` | 33 | 80 | YES | No |
| Storage Account | mini | b | `stlnpolicyengrptb` | 17 | 24 | YES | No |
| Key Vault | mini | b | `kvlnpolicyengrptb` | 17 | 24 | YES | No |
| Container Registry | mini | b | `crlnpolicyengrptb` | 17 | 50 | YES | No |
| SQL Server | standard | b | `sql-lexus-nonprod-policyeng-rpt-b` | 33 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-lexus-nonprod-policyeng-rpt-b` | 35 | 128 | YES | No |
| App Service | standard | b | `app-lexus-nonprod-policyeng-rpt-b` | 33 | 60 | YES | No |
| App Service Plan | standard | b | `plan-lexus-nonprod-policyeng-rpt-b` | 34 | 40 | YES | No |
| Function App | standard | b | `func-lexus-nonprod-policyeng-rpt-b` | 34 | 60 | YES | No |
| API Management | standard | b | `apim-lexus-nonprod-policyeng-rpt-b` | 34 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-lexus-nonprod-policyeng-rpt-b` | 36 | 44 | YES | No |
| Redis Cache | standard | b | `redis-lexus-nonprod-policyeng-rpt-b` | 35 | 63 | YES | No |
| Service Bus | standard | b | `sb-lexus-nonprod-policyeng-rpt-b` | 32 | 50 | YES | No |
| Event Hub | standard | b | `evh-lexus-nonprod-policyeng-rpt-b` | 33 | 50 | YES | No |
| Log Analytics | standard | b | `log-lexus-nonprod-policyeng-rpt-b` | 33 | 63 | YES | No |
| App Configuration | small | b | `appcs-lexus-nonprod-policyeng-rpt-b` | 35 | 50 | YES | No |
| App Insights | small | b | `appi-lexus-nonprod-policyeng-rpt-b` | 34 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-lexus-nonprod-policyeng-rpt-b` | 34 | 64 | YES | No |
| NSG | standard | b | `nsg-lexus-nonprod-policyeng-rpt-b` | 33 | 80 | YES | No |
| Public IP | standard | b | `pip-lexus-nonprod-policyeng-rpt-b` | 33 | 80 | YES | No |
| Managed Identity | standard | b | `id-lexus-nonprod-policyeng-rpt-b` | 32 | 128 | YES | No |
| AKS | standard | b | `aks-lexus-nonprod-policyeng-rpt-b` | 33 | 63 | YES | No |
| App Gateway | standard | b | `agw-lexus-nonprod-policyeng-rpt-b` | 33 | 80 | YES | No |

## Test Case 19: `identmgr` — LOB=set, Stage=dev, Role=db

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stsdidentmgrdba` | 15 | 24 | YES | No |
| Key Vault | mini | a | `kvsdidentmgrdba` | 15 | 24 | YES | No |
| Container Registry | mini | a | `crsdidentmgrdba` | 15 | 50 | YES | No |
| SQL Server | standard | a | `sql-set-dev-identmgr-db-a` | 25 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-set-dev-identmgr-db-a` | 27 | 128 | YES | No |
| App Service | standard | a | `app-set-dev-identmgr-db-a` | 25 | 60 | YES | No |
| App Service Plan | standard | a | `plan-set-dev-identmgr-db-a` | 26 | 40 | YES | No |
| Function App | standard | a | `func-set-dev-identmgr-db-a` | 26 | 60 | YES | No |
| API Management | standard | a | `apim-set-dev-identmgr-db-a` | 26 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-set-dev-identmgr-db-a` | 28 | 44 | YES | No |
| Redis Cache | standard | a | `redis-set-dev-identmgr-db-a` | 27 | 63 | YES | No |
| Service Bus | standard | a | `sb-set-dev-identmgr-db-a` | 24 | 50 | YES | No |
| Event Hub | standard | a | `evh-set-dev-identmgr-db-a` | 25 | 50 | YES | No |
| Log Analytics | standard | a | `log-set-dev-identmgr-db-a` | 25 | 63 | YES | No |
| App Configuration | small | a | `appcs-set-dev-identmgr-db-a` | 27 | 50 | YES | No |
| App Insights | small | a | `appi-set-dev-identmgr-db-a` | 26 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-set-dev-identmgr-db-a` | 26 | 64 | YES | No |
| NSG | standard | a | `nsg-set-dev-identmgr-db-a` | 25 | 80 | YES | No |
| Public IP | standard | a | `pip-set-dev-identmgr-db-a` | 25 | 80 | YES | No |
| Managed Identity | standard | a | `id-set-dev-identmgr-db-a` | 24 | 128 | YES | No |
| AKS | standard | a | `aks-set-dev-identmgr-db-a` | 25 | 63 | YES | No |
| App Gateway | standard | a | `agw-set-dev-identmgr-db-a` | 25 | 80 | YES | No |
| Storage Account | mini | b | `stsdidentmgrdbb` | 15 | 24 | YES | No |
| Key Vault | mini | b | `kvsdidentmgrdbb` | 15 | 24 | YES | No |
| Container Registry | mini | b | `crsdidentmgrdbb` | 15 | 50 | YES | No |
| SQL Server | standard | b | `sql-set-dev-identmgr-db-b` | 25 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-set-dev-identmgr-db-b` | 27 | 128 | YES | No |
| App Service | standard | b | `app-set-dev-identmgr-db-b` | 25 | 60 | YES | No |
| App Service Plan | standard | b | `plan-set-dev-identmgr-db-b` | 26 | 40 | YES | No |
| Function App | standard | b | `func-set-dev-identmgr-db-b` | 26 | 60 | YES | No |
| API Management | standard | b | `apim-set-dev-identmgr-db-b` | 26 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-set-dev-identmgr-db-b` | 28 | 44 | YES | No |
| Redis Cache | standard | b | `redis-set-dev-identmgr-db-b` | 27 | 63 | YES | No |
| Service Bus | standard | b | `sb-set-dev-identmgr-db-b` | 24 | 50 | YES | No |
| Event Hub | standard | b | `evh-set-dev-identmgr-db-b` | 25 | 50 | YES | No |
| Log Analytics | standard | b | `log-set-dev-identmgr-db-b` | 25 | 63 | YES | No |
| App Configuration | small | b | `appcs-set-dev-identmgr-db-b` | 27 | 50 | YES | No |
| App Insights | small | b | `appi-set-dev-identmgr-db-b` | 26 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-set-dev-identmgr-db-b` | 26 | 64 | YES | No |
| NSG | standard | b | `nsg-set-dev-identmgr-db-b` | 25 | 80 | YES | No |
| Public IP | standard | b | `pip-set-dev-identmgr-db-b` | 25 | 80 | YES | No |
| Managed Identity | standard | b | `id-set-dev-identmgr-db-b` | 24 | 128 | YES | No |
| AKS | standard | b | `aks-set-dev-identmgr-db-b` | 25 | 63 | YES | No |
| App Gateway | standard | b | `agw-set-dev-identmgr-db-b` | 25 | 80 | YES | No |

## Test Case 20: `wealthplat` — LOB=setf, Stage=stg, Role=wkr

| Resource Type | Pattern | AppId | Generated Name | Len | Max | OK | Trunc |
|---------------|---------|-------|----------------|-----|-----|----|-------|
| Storage Account | mini | a | `stvswealthplatwkra` | 18 | 24 | YES | No |
| Key Vault | mini | a | `kvvswealthplatwkra` | 18 | 24 | YES | No |
| Container Registry | mini | a | `crvswealthplatwkra` | 18 | 50 | YES | No |
| SQL Server | standard | a | `sql-setf-stg-wealthplat-wkr-a` | 29 | 63 | YES | No |
| SQL Database | standard | a | `sqldb-setf-stg-wealthplat-wkr-a` | 31 | 128 | YES | No |
| App Service | standard | a | `app-setf-stg-wealthplat-wkr-a` | 29 | 60 | YES | No |
| App Service Plan | standard | a | `plan-setf-stg-wealthplat-wkr-a` | 30 | 40 | YES | No |
| Function App | standard | a | `func-setf-stg-wealthplat-wkr-a` | 30 | 60 | YES | No |
| API Management | standard | a | `apim-setf-stg-wealthplat-wkr-a` | 30 | 50 | YES | No |
| Cosmos DB | standard | a | `cosmos-setf-stg-wealthplat-wkr-a` | 32 | 44 | YES | No |
| Redis Cache | standard | a | `redis-setf-stg-wealthplat-wkr-a` | 31 | 63 | YES | No |
| Service Bus | standard | a | `sb-setf-stg-wealthplat-wkr-a` | 28 | 50 | YES | No |
| Event Hub | standard | a | `evh-setf-stg-wealthplat-wkr-a` | 29 | 50 | YES | No |
| Log Analytics | standard | a | `log-setf-stg-wealthplat-wkr-a` | 29 | 63 | YES | No |
| App Configuration | small | a | `appcs-setf-stg-wealthplat-wkr-a` | 31 | 50 | YES | No |
| App Insights | small | a | `appi-setf-stg-wealthplat-wkr-a` | 30 | 260 | YES | No |
| Virtual Network | standard | a | `vnet-setf-stg-wealthplat-wkr-a` | 30 | 64 | YES | No |
| NSG | standard | a | `nsg-setf-stg-wealthplat-wkr-a` | 29 | 80 | YES | No |
| Public IP | standard | a | `pip-setf-stg-wealthplat-wkr-a` | 29 | 80 | YES | No |
| Managed Identity | standard | a | `id-setf-stg-wealthplat-wkr-a` | 28 | 128 | YES | No |
| AKS | standard | a | `aks-setf-stg-wealthplat-wkr-a` | 29 | 63 | YES | No |
| App Gateway | standard | a | `agw-setf-stg-wealthplat-wkr-a` | 29 | 80 | YES | No |
| Storage Account | mini | b | `stvswealthplatwkrb` | 18 | 24 | YES | No |
| Key Vault | mini | b | `kvvswealthplatwkrb` | 18 | 24 | YES | No |
| Container Registry | mini | b | `crvswealthplatwkrb` | 18 | 50 | YES | No |
| SQL Server | standard | b | `sql-setf-stg-wealthplat-wkr-b` | 29 | 63 | YES | No |
| SQL Database | standard | b | `sqldb-setf-stg-wealthplat-wkr-b` | 31 | 128 | YES | No |
| App Service | standard | b | `app-setf-stg-wealthplat-wkr-b` | 29 | 60 | YES | No |
| App Service Plan | standard | b | `plan-setf-stg-wealthplat-wkr-b` | 30 | 40 | YES | No |
| Function App | standard | b | `func-setf-stg-wealthplat-wkr-b` | 30 | 60 | YES | No |
| API Management | standard | b | `apim-setf-stg-wealthplat-wkr-b` | 30 | 50 | YES | No |
| Cosmos DB | standard | b | `cosmos-setf-stg-wealthplat-wkr-b` | 32 | 44 | YES | No |
| Redis Cache | standard | b | `redis-setf-stg-wealthplat-wkr-b` | 31 | 63 | YES | No |
| Service Bus | standard | b | `sb-setf-stg-wealthplat-wkr-b` | 28 | 50 | YES | No |
| Event Hub | standard | b | `evh-setf-stg-wealthplat-wkr-b` | 29 | 50 | YES | No |
| Log Analytics | standard | b | `log-setf-stg-wealthplat-wkr-b` | 29 | 63 | YES | No |
| App Configuration | small | b | `appcs-setf-stg-wealthplat-wkr-b` | 31 | 50 | YES | No |
| App Insights | small | b | `appi-setf-stg-wealthplat-wkr-b` | 30 | 260 | YES | No |
| Virtual Network | standard | b | `vnet-setf-stg-wealthplat-wkr-b` | 30 | 64 | YES | No |
| NSG | standard | b | `nsg-setf-stg-wealthplat-wkr-b` | 29 | 80 | YES | No |
| Public IP | standard | b | `pip-setf-stg-wealthplat-wkr-b` | 29 | 80 | YES | No |
| Managed Identity | standard | b | `id-setf-stg-wealthplat-wkr-b` | 28 | 128 | YES | No |
| AKS | standard | b | `aks-setf-stg-wealthplat-wkr-b` | 29 | 63 | YES | No |
| App Gateway | standard | b | `agw-setf-stg-wealthplat-wkr-b` | 29 | 80 | YES | No |

## Collision Analysis

**No collisions detected across all 880 generated names.**

Each combination of (appName, LOB, stage, role, appId) produces a unique name
across all resource types. Cross-resource-type collisions are structurally
impossible because prefixes differ (`st` vs `kv` vs `cr` vs `sql-` etc.).

## Length Distribution — Mini Pattern Resources

| Metric | Value |
|--------|-------|
| Total mini names | 120 |
| Min length | 11 |
| Max length | 19 |
| Avg length | 15.7 |
| Names at max (24) | 0 |
| Names requiring truncation | 0 |
| Chars remaining (avg) | 8.3 |

## Length Distribution — Standard/Small Pattern Resources

| Metric | Value |
|--------|-------|
| Total standard/small names | 760 |
| Min length | 21 |
| Max length | 36 |
| Avg length | 27.4 |
| Names requiring truncation | 0 |

## Readability Flags — Mini Pattern

Names where adjacent segments create doubled characters or confusing substrings.
These are cosmetic issues — no functional impact on uniqueness.

| Name | Resource | AppName | Role | AppId | Issue |
|------|----------|---------|------|-------|-------|
| `stsdacctachacha` | Storage Account | acctach | ach | a | Doubled `cc` at pos 5-6 |
| `kvsdacctachacha` | Key Vault | acctach | ach | a | Doubled `cc` at pos 5-6 |
| `crsdacctachacha` | Container Registry | acctach | ach | a | Doubled `cc` at pos 5-6 |
| `stsdacctachachb` | Storage Account | acctach | ach | b | Doubled `cc` at pos 5-6 |
| `kvsdacctachachb` | Key Vault | acctach | ach | b | Doubled `cc` at pos 5-6 |
| `crsdacctachachb` | Container Registry | acctach | ach | b | Doubled `cc` at pos 5-6 |
| `kvvspaymentsweba` | Key Vault | payments | web | a | Doubled `vv` at pos 1-2 |
| `stvspaymentswebb` | Storage Account | payments | web | b | Doubled `bb` at pos 14-15 |
| `kvvspaymentswebb` | Key Vault | payments | web | b | Doubled `vv` at pos 1-2 |
| `crvspaymentswebb` | Container Registry | payments | web | b | Doubled `bb` at pos 14-15 |
| `stjqledgerdbb` | Storage Account | ledger | db | b | Doubled `bb` at pos 11-12 |
| `kvjqledgerdbb` | Key Vault | ledger | db | b | Doubled `bb` at pos 11-12 |
| `crjqledgerdbb` | Container Registry | ledger | db | b | Doubled `bb` at pos 11-12 |
| `sttnsnowflkrpta` | Storage Account | snowflk | rpt | a | Doubled `tt` at pos 1-2 |
| `sttnsnowflkrptb` | Storage Account | snowflk | rpt | b | Doubled `tt` at pos 1-2 |
| `stiddatamartwkra` | Storage Account | datamart | wkr | a | Doubled `dd` at pos 3-4 |
| `kviddatamartwkra` | Key Vault | datamart | wkr | a | Doubled `dd` at pos 3-4 |
| `criddatamartwkra` | Container Registry | datamart | wkr | a | Doubled `dd` at pos 3-4 |
| `stiddatamartwkrb` | Storage Account | datamart | wkr | b | Doubled `dd` at pos 3-4 |
| `kviddatamartwkrb` | Key Vault | datamart | wkr | b | Doubled `dd` at pos 3-4 |
| `criddatamartwkrb` | Container Registry | datamart | wkr | b | Doubled `dd` at pos 3-4 |
| `stlqbillingquea` | Storage Account | billing | que | a | Doubled `ll` at pos 6-7 |
| `kvlqbillingquea` | Key Vault | billing | que | a | Doubled `ll` at pos 6-7 |
| `crlqbillingquea` | Container Registry | billing | que | a | Doubled `ll` at pos 6-7 |
| `stlqbillingqueb` | Storage Account | billing | que | b | Doubled `ll` at pos 6-7 |
| `kvlqbillingqueb` | Key Vault | billing | que | b | Doubled `ll` at pos 6-7 |
| `crlqbillingqueb` | Container Registry | billing | que | b | Doubled `ll` at pos 6-7 |
| `stvpportfoliologa` | Storage Account | portfolio | log | a | Doubled `pp` at pos 3-4 |
| `kvvpportfoliologa` | Key Vault | portfolio | log | a | Doubled `vv` at pos 1-2 |
| `crvpportfoliologa` | Container Registry | portfolio | log | a | Doubled `pp` at pos 3-4 |
| `stvpportfoliologb` | Storage Account | portfolio | log | b | Doubled `pp` at pos 3-4 |
| `kvvpportfoliologb` | Key Vault | portfolio | log | b | Doubled `vv` at pos 1-2 |
| `crvpportfoliologb` | Container Registry | portfolio | log | b | Doubled `pp` at pos 3-4 |
| `stessupplychainchka` | Storage Account | supplychain | chk | a | Doubled `ss` at pos 3-4 |
| `kvessupplychainchka` | Key Vault | supplychain | chk | a | Doubled `ss` at pos 3-4 |
| `cressupplychainchka` | Container Registry | supplychain | chk | a | Doubled `ss` at pos 3-4 |
| `stessupplychainchkb` | Storage Account | supplychain | chk | b | Doubled `ss` at pos 3-4 |
| `kvessupplychainchkb` | Key Vault | supplychain | chk | b | Doubled `ss` at pos 3-4 |
| `cressupplychainchkb` | Container Registry | supplychain | chk | b | Doubled `ss` at pos 3-4 |
| `sttqchatbotccha` | Storage Account | chatbot | cch | a | Doubled `tt` at pos 1-2 |
| `kvtqchatbotccha` | Key Vault | chatbot | cch | a | Doubled `cc` at pos 11-12 |
| `crtqchatbotccha` | Container Registry | chatbot | cch | a | Doubled `cc` at pos 11-12 |
| `sttqchatbotcchb` | Storage Account | chatbot | cch | b | Doubled `tt` at pos 1-2 |
| `kvtqchatbotcchb` | Key Vault | chatbot | cch | b | Doubled `cc` at pos 11-12 |
| `crtqchatbotcchb` | Container Registry | chatbot | cch | b | Doubled `cc` at pos 11-12 |
| `stcpdocmgmtwebb` | Storage Account | docmgmt | web | b | Doubled `bb` at pos 13-14 |
| `kvcpdocmgmtwebb` | Key Vault | docmgmt | web | b | Doubled `bb` at pos 13-14 |
| `crcpdocmgmtwebb` | Container Registry | docmgmt | web | b | Doubled `bb` at pos 13-14 |
| `stsdidentmgrdbb` | Storage Account | identmgr | db | b | Doubled `bb` at pos 13-14 |
| `kvsdidentmgrdbb` | Key Vault | identmgr | db | b | Doubled `bb` at pos 13-14 |
| `crsdidentmgrdbb` | Container Registry | identmgr | db | b | Doubled `bb` at pos 13-14 |
| `kvvswealthplatwkra` | Key Vault | wealthplat | wkr | a | Doubled `vv` at pos 1-2 |
| `kvvswealthplatwkrb` | Key Vault | wealthplat | wkr | b | Doubled `vv` at pos 1-2 |

**53 of 120 mini-pattern names (44%) have doubled characters.**

All doubled-character instances are cosmetic boundary effects (e.g., prefix `st` + LOB code `t`,
or role `db` + appId `b`). None cause ambiguity in the generated name's uniqueness.
