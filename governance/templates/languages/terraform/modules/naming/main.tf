# ============================================================================
# JM v2 Azure Resource Naming Module
# ============================================================================
#
# Generates Azure-compliant resource names following the JM v2 naming standard.
#
# Three patterns handle different Azure resource constraints:
#   - standard: {prefix}-{lob}-{stage}-{appName}-{role}-{appId}
#   - mini:     {prefix}{lobCode}{stageCode}{appName}{role}{appId}  (no hyphens)
#   - small:    {prefix}-{lob}-{stage}-{appName}-{role}-{appId}
#
# Mini uses 1-char LOB codes and 1-char stage codes for resources with strict
# length limits (Key Vault <=24, Storage <=24, Container Registry <=50).
#
# Usage:
#   module "naming" {
#     source   = "./modules/naming"
#     lob      = "set"
#     stage    = "dev"
#     app_name = "myapp"
#     app_id   = "a"
#     role     = "web"
#   }
#
#   resource "azurerm_key_vault" "main" {
#     name = module.naming.key_vault_name
#   }
#
# Use the Python CLI (bin/generate-name.py) to pre-validate that generated
# names fit within Azure length limits, especially for mini pattern resources.
# ============================================================================

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

variable "lob" {
  description = "Line of business (set, setf, jma, jmf, jmfe, to, ocio, octo, lexus)"
  type        = string
  validation {
    condition     = contains(["set", "setf", "jma", "jmf", "jmfe", "to", "ocio", "octo", "lexus"], lower(var.lob))
    error_message = "LOB must be one of: set, setf, jma, jmf, jmfe, to, ocio, octo, lexus."
  }
}

variable "stage" {
  description = "Deployment stage (dev, stg, qa, uat, prod, nonprod)"
  type        = string
  validation {
    condition     = contains(["dev", "stg", "qa", "uat", "prod", "nonprod"], lower(var.stage))
    error_message = "Stage must be one of: dev, stg, qa, uat, prod, nonprod."
  }
}

variable "app_name" {
  description = "Application name — used in all patterns"
  type        = string
  validation {
    condition     = length(var.app_name) > 0
    error_message = "app_name is required and cannot be empty."
  }
}

variable "app_id" {
  description = "Application ID — single lowercase letter (a-z)"
  type        = string
  validation {
    condition     = can(regex("^[a-z]$", lower(var.app_id)))
    error_message = "app_id must be a single lowercase letter (a-z)."
  }
}

variable "role" {
  description = "Component role (web, db, api, etc.) — required for standard pattern, optional for mini/small"
  type        = string
  default     = ""
}

variable "location" {
  description = "Azure region short name (e.g., eastus) — optional, only used in standard pattern"
  type        = string
  default     = ""
}

# ---------------------------------------------------------------------------
# LOB and stage code maps
# ---------------------------------------------------------------------------

locals {
  lob_codes = {
    set   = "s"
    setf  = "v"
    jma   = "j"
    jmf   = "f"
    jmfe  = "e"
    to    = "t"
    ocio  = "i"
    octo  = "c"
    lexus = "l"
  }

  stage_codes = {
    dev     = "d"
    stg     = "s"
    qa      = "q"
    uat     = "u"
    prod    = "p"
    nonprod = "n"
  }

  # Normalized inputs
  lob        = lower(var.lob)
  stage      = lower(var.stage)
  app_name   = lower(var.app_name)
  app_id     = lower(var.app_id)
  role       = lower(var.role)
  lob_code   = local.lob_codes[local.lob]
  stage_code = local.stage_codes[local.stage]

  # Resource prefixes
  prefixes = {
    sql_server              = "sql"
    sql_database            = "sqldb"
    app_service             = "app"
    app_service_plan        = "plan"
    function_app            = "func"
    api_management          = "apim"
    cosmos_db               = "cosmos"
    redis                   = "redis"
    service_bus             = "sb"
    event_hub               = "evh"
    log_analytics           = "log"
    key_vault               = "kv"
    storage_account         = "st"
    container_registry      = "cr"
    app_configuration       = "appcs"
    app_insights            = "appi"
    virtual_network         = "vnet"
    network_security_group  = "nsg"
    public_ip               = "pip"
    managed_identity        = "id"
    aks                     = "aks"
    application_gateway     = "agw"
  }

  # ---------------------------------------------------------------------------
  # Pattern bases (without prefix)
  # ---------------------------------------------------------------------------

  # Standard: {lob}-{stage}-{appName}-{role}-{appId} (or with location)
  standard_base = local.role != "" ? (
    var.location != "" ?
    "${local.lob}-${local.stage}-${local.app_name}-${local.role}-${lower(var.location)}-${local.app_id}" :
    "${local.lob}-${local.stage}-${local.app_name}-${local.role}-${local.app_id}"
  ) : "${local.lob}-${local.stage}-${local.app_name}-${local.app_id}"

  # Mini: {lobCode}{stageCode}{appName}{role}{appId}
  mini_clean_name = replace(replace(local.app_name, "-", ""), "_", "")
  mini_clean_role = replace(replace(local.role, "-", ""), "_", "")
  mini_base = local.mini_clean_role != "" ? (
    "${local.lob_code}${local.stage_code}${local.mini_clean_name}${local.mini_clean_role}${local.app_id}"
  ) : "${local.lob_code}${local.stage_code}${local.mini_clean_name}${local.app_id}"

  # Small: {lob}-{stage}-{appName}-{role}-{appId}
  small_base = local.role != "" ? (
    "${local.lob}-${local.stage}-${local.app_name}-${local.role}-${local.app_id}"
  ) : "${local.lob}-${local.stage}-${local.app_name}-${local.app_id}"
}

# ---------------------------------------------------------------------------
# Outputs — Standard pattern resources
# ---------------------------------------------------------------------------

output "sql_server_name" {
  description = "SQL Server name (standard pattern)"
  value       = "${local.prefixes.sql_server}-${local.standard_base}"
}

output "sql_database_name" {
  description = "SQL Database name (standard pattern)"
  value       = "${local.prefixes.sql_database}-${local.standard_base}"
}

output "app_service_name" {
  description = "App Service name (standard pattern)"
  value       = "${local.prefixes.app_service}-${local.standard_base}"
}

output "app_service_plan_name" {
  description = "App Service Plan name (standard pattern)"
  value       = "${local.prefixes.app_service_plan}-${local.standard_base}"
}

output "function_app_name" {
  description = "Function App name (standard pattern)"
  value       = "${local.prefixes.function_app}-${local.standard_base}"
}

output "api_management_name" {
  description = "API Management name (standard pattern)"
  value       = "${local.prefixes.api_management}-${local.standard_base}"
}

output "cosmos_db_name" {
  description = "Cosmos DB name (standard pattern)"
  value       = "${local.prefixes.cosmos_db}-${local.standard_base}"
}

output "redis_name" {
  description = "Redis Cache name (standard pattern)"
  value       = "${local.prefixes.redis}-${local.standard_base}"
}

output "service_bus_name" {
  description = "Service Bus name (standard pattern)"
  value       = "${local.prefixes.service_bus}-${local.standard_base}"
}

output "event_hub_name" {
  description = "Event Hub name (standard pattern)"
  value       = "${local.prefixes.event_hub}-${local.standard_base}"
}

output "log_analytics_name" {
  description = "Log Analytics name (standard pattern)"
  value       = "${local.prefixes.log_analytics}-${local.standard_base}"
}

output "virtual_network_name" {
  description = "Virtual Network name (standard pattern)"
  value       = "${local.prefixes.virtual_network}-${local.standard_base}"
}

output "network_security_group_name" {
  description = "Network Security Group name (standard pattern)"
  value       = "${local.prefixes.network_security_group}-${local.standard_base}"
}

output "public_ip_name" {
  description = "Public IP name (standard pattern)"
  value       = "${local.prefixes.public_ip}-${local.standard_base}"
}

output "managed_identity_name" {
  description = "Managed Identity name (standard pattern)"
  value       = "${local.prefixes.managed_identity}-${local.standard_base}"
}

output "aks_name" {
  description = "AKS Cluster name (standard pattern)"
  value       = "${local.prefixes.aks}-${local.standard_base}"
}

output "application_gateway_name" {
  description = "Application Gateway name (standard pattern)"
  value       = "${local.prefixes.application_gateway}-${local.standard_base}"
}

# ---------------------------------------------------------------------------
# Outputs — Mini pattern resources (no hyphens, LOB/stage codes)
# ---------------------------------------------------------------------------

output "key_vault_name" {
  description = "Key Vault name (mini pattern, max 24 chars)"
  value       = "${local.prefixes.key_vault}${local.mini_base}"
}

output "storage_account_name" {
  description = "Storage Account name (mini pattern, max 24 chars)"
  value       = "${local.prefixes.storage_account}${local.mini_base}"
}

output "container_registry_name" {
  description = "Container Registry name (mini pattern, max 50 chars)"
  value       = "${local.prefixes.container_registry}${local.mini_base}"
}

# ---------------------------------------------------------------------------
# Outputs — Small pattern resources
# ---------------------------------------------------------------------------

output "app_configuration_name" {
  description = "App Configuration name (small pattern)"
  value       = "${local.prefixes.app_configuration}-${local.small_base}"
}

output "app_insights_name" {
  description = "Application Insights name (small pattern)"
  value       = "${local.prefixes.app_insights}-${local.small_base}"
}
