# Azure Naming Test Report

**Date:** 2026-02-27
**Branch:** `NETWORK_ID/fix/remove-hardcoded-network-id`
**Test file:** `governance/engine/tests/test_naming.py`
**Result:** 77/77 passed (1.19s)

---

## 1. TestNamingInputValidation (10 tests)

Tests that `NamingInput` rejects invalid inputs early with descriptive errors.

| # | Test | resource_type | lob | stage | app_name | app_id | role | Expected Error | Status |
|---|------|---------------|-----|-------|----------|--------|------|----------------|--------|
| 1 | `test_invalid_resource_type` | `Microsoft.Fake/stuff` | `set` | `dev` | `myapp` | `a` | `web` | Unsupported resource type | PASS |
| 2 | `test_invalid_lob` | `Microsoft.Sql/servers` | `badlob` | `dev` | `myapp` | `a` | `web` | Invalid LOB | PASS |
| 3 | `test_invalid_stage` | `Microsoft.Sql/servers` | `set` | `badstage` | `myapp` | `a` | `web` | Invalid stage | PASS |
| 4 | `test_invalid_app_id_too_long` | `Microsoft.Sql/servers` | `set` | `dev` | `myapp` | `ab` | `web` | Invalid app_id | PASS |
| 5 | `test_invalid_app_id_number` | `Microsoft.Sql/servers` | `set` | `dev` | `myapp` | `1` | `web` | Invalid app_id | PASS |
| 6 | `test_empty_app_name` | `Microsoft.Sql/servers` | `set` | `dev` | `""` | `a` | `web` | app_name is required | PASS |
| 7 | `test_role_required_for_standard` | `Microsoft.Sql/servers` | `set` | `dev` | `myapp` | `a` | `""` | role is required | PASS |
| 8 | `test_role_not_required_for_mini` | `Microsoft.KeyVault/vaults` | `set` | `dev` | `myapp` | `a` | `""` | _(no error — role optional for mini)_ | PASS |
| 9 | `test_role_not_required_for_small` | `Microsoft.AppConfiguration/configurationStores` | `set` | `dev` | `myapp` | `a` | `""` | _(no error — role optional for small)_ | PASS |
| 10 | `test_multiple_errors_reported` | `Microsoft.Fake/stuff` | `badlob` | `badstage` | `""` | `99` | — | 5 combined errors | PASS |

---

## 2. TestStandardPattern (4 tests)

Tests standard `{prefix}-{lob}-{stage}-{appName}-{role}-{appId}` generation.

| # | Test | resource_type | lob | stage | app_name | app_id | role | location | Expected Output | Status |
|---|------|---------------|-----|-------|----------|--------|------|----------|-----------------|--------|
| 1 | `test_basic_sql_server` | `Microsoft.Sql/servers` | `set` | `dev` | `payments` | `a` | `db` | — | `sql-set-dev-payments-db-a` | PASS |
| 2 | `test_with_location` | `Microsoft.Sql/servers` | `jma` | `prod` | `billing` | `b` | `api` | `eastus` | `sql-jma-prod-billing-api-eastus-b` | PASS |
| 3 | `test_case_normalized` | `Microsoft.Sql/servers` | `SET` | `DEV` | `MyApp` | `A` | `Web` | — | `sql-set-dev-myapp-web-a` | PASS |
| 4 | `test_all_standard_resources_generate` | _(all standard-pattern types)_ | `set` | `dev` | `testapp` | `a` | `web` | — | Starts with `{prefix}-`, within max_length | PASS |

---

## 3. TestMiniPattern (6 tests)

Tests mini `{prefix}{lobCode}{stageCode}{appName}{appId}` generation (no hyphens).

| # | Test | resource_type | lob | stage | app_name | app_id | role | Expected Output | Max Len | Status |
|---|------|---------------|-----|-------|----------|--------|------|-----------------|---------|--------|
| 1 | `test_keyvault` | `Microsoft.KeyVault/vaults` | `set` | `dev` | `myapp` | `a` | — | `kvsdmyappa` | 24 | PASS |
| 2 | `test_storage_account` | `Microsoft.Storage/storageAccounts` | `jma` | `prod` | `datalake` | `b` | — | `stjpdatalakeb` | 24 | PASS |
| 3 | `test_container_registry` | `Microsoft.ContainerRegistry/registries` | `set` | `dev` | `platform` | `a` | — | `crsdplatforma` | 50 | PASS |
| 4 | `test_mini_truncation_for_long_name` | `Microsoft.KeyVault/vaults` | `set` | `dev` | `verylongapplicationname` | `a` | — | Starts with `kvsd`, len ≤ 24 | 24 | PASS |
| 5 | `test_mini_strips_hyphens_from_app_name` | `Microsoft.KeyVault/vaults` | `set` | `dev` | `my-cool-app` | `a` | — | Contains `mycoolapp`, ends with `a`, no hyphens | 24 | PASS |
| 6 | `test_all_mini_resources_generate` | _(all mini-pattern types)_ | `set` | `dev` | `testapp` | `a` | — | No hyphens, within max_length | — | PASS |

---

## 4. TestSmallPattern (4 tests)

Tests small `{prefix}-{lob}-{stage}-{appName}-{appId}` generation.

| # | Test | resource_type | lob | stage | app_name | app_id | role | Expected Output | Max Len | Status |
|---|------|---------------|-----|-------|----------|--------|------|-----------------|---------|--------|
| 1 | `test_app_configuration` | `Microsoft.AppConfiguration/configurationStores` | `set` | `dev` | `platform` | `a` | — | `appcs-set-dev-platform-a` | 50 | PASS |
| 2 | `test_app_insights` | `Microsoft.Insights/components` | `jma` | `prod` | `analytics` | `b` | — | `appi-jma-prod-analytics-b` | — | PASS |
| 3 | `test_small_truncation` | `Microsoft.AppConfiguration/configurationStores` | `set` | `dev` | `"a" * 100` | `a` | — | len ≤ 50 | 50 | PASS |
| 4 | `test_all_small_resources_generate` | _(all small-pattern types)_ | `set` | `dev` | `testapp` | `a` | — | Within max_length | — | PASS |

---

## 5. TestDeterministicShortening (4 tests)

Tests that names exceeding max length are shortened deterministically (appName first, then role).

| # | Test | resource_type | lob | stage | app_name | app_id | role | Max Len | Assertions | Status |
|---|------|---------------|-----|-------|----------|--------|------|---------|------------|--------|
| 1 | `test_app_name_truncated_before_role` | `Microsoft.Web/serverfarms` | `set` | `dev` | `averylongapplicationname` | `a` | `web` | 40 | len ≤ 40, `-web-` intact, starts `plan-set-dev-`, ends `-a` | PASS |
| 2 | `test_role_truncated_after_app_name` | `Microsoft.Web/serverfarms` | `setf` | `nonprod` | `app` | `a` | `"a" * 40` | 40 | len ≤ 40, starts `plan-setf-nonprod-` | PASS |
| 3 | `test_shortening_preserves_fixed_parts` | `Microsoft.DocumentDB/databaseAccounts` | `lexus` | `nonprod` | `superlongapplicationname` | `a` | `database` | 44 | len ≤ 44, starts `cosmos-lexus-nonprod-`, ends `-a` | PASS |
| 4 | `test_shortening_is_deterministic` | `Microsoft.Web/serverfarms` | `set` | `dev` | `longname` | `a` | `web` | 40 | Two calls produce identical output | PASS |

---

## 6. TestValidateName (9 tests)

Tests the `validate_name()` function against known valid/invalid names.

| # | Test | Name Input | resource_type | Expected Valid | Expected Error Substring | Status |
|---|------|------------|---------------|----------------|--------------------------|--------|
| 1 | `test_valid_name` | `sql-set-dev-payments-db-a` | `Microsoft.Sql/servers` | `True` | _(none)_ | PASS |
| 2 | `test_exceeds_max_length` | `sql-` + `"a" * 100` | `Microsoft.Sql/servers` | `False` | `exceeds maximum` | PASS |
| 3 | `test_hyphens_rejected_for_mini` | `kv-set-dev-app` | `Microsoft.KeyVault/vaults` | `False` | `Hyphens are not allowed` | PASS |
| 4 | `test_wrong_prefix` | `wrongprefix-set-dev-app-web-a` | `Microsoft.Sql/servers` | `False` | `should start with` | PASS |
| 5 | `test_unsupported_resource_type` | `anything` | `Microsoft.Fake/stuff` | `False` | `Unsupported` | PASS |
| 6 | `test_empty_name` | `""` | `Microsoft.Sql/servers` | `False` | _(any)_ | PASS |
| 7 | `test_leading_hyphen` | `-sql-set-dev-app-web-a` | `Microsoft.Sql/servers` | `False` | `start or end with a hyphen` | PASS |
| 8 | `test_trailing_hyphen` | `sql-set-dev-app-web-a-` | `Microsoft.Sql/servers` | `False` | _(any)_ | PASS |
| 9 | `test_includes_length_info` | `sql-set-dev-app-web-a` | `Microsoft.Sql/servers` | `True` | max_length=63, actual_length=21 | PASS |

---

## 7. TestListResourceTypes (3 tests)

Tests the `list_resource_types()` function output.

| # | Test | Assertions | Status |
|---|------|------------|--------|
| 1 | `test_returns_all_types` | Count matches `RESOURCE_TYPES` dict | PASS |
| 2 | `test_sorted_by_resource_type` | List is alphabetically sorted | PASS |
| 3 | `test_entry_shape` | Each entry has: `resource_type`, `prefix`, `max_length`, `pattern`, `allows_hyphens` | PASS |

---

## 8. TestResourceDataIntegrity (7 tests)

Tests that `naming_data.py` constants are self-consistent.

| # | Test | Data Source | Assertions | Status |
|---|------|-------------|------------|--------|
| 1 | `test_all_lobs_are_lowercase` | `VALID_LOBS` | All lowercase | PASS |
| 2 | `test_all_stages_are_lowercase` | `VALID_STAGES` | All lowercase | PASS |
| 3 | `test_all_prefixes_are_lowercase` | `RESOURCE_TYPES[*].prefix` | All lowercase | PASS |
| 4 | `test_max_lengths_are_positive` | `RESOURCE_TYPES[*].max_length` | All > 0 | PASS |
| 5 | `test_patterns_are_valid` | `RESOURCE_TYPES[*].pattern` | All in {`standard`, `mini`, `small`} | PASS |
| 6 | `test_mini_pattern_disallows_hyphens` | `RESOURCE_TYPES` (mini only) | `allows_hyphens` is `False` | PASS |
| 7 | `test_expected_resource_count` | `RESOURCE_TYPES` | ≥ 22 entries | PASS |

---

## 9. TestCLI (10 tests)

Tests the `bin/generate-name.py` CLI via subprocess.

| # | Test | CLI Args | Expected Exit | Expected Output | Status |
|---|------|----------|---------------|-----------------|--------|
| 1 | `test_list_types` | `--list-types` | 0 | Contains `Microsoft.Sql/servers` | PASS |
| 2 | `test_list_types_json` | `--list-types --json` | 0 | Valid JSON list, len > 0 | PASS |
| 3 | `test_generate_standard` | `--resource-type Microsoft.Sql/servers --lob set --stage dev --app-name payments --app-id a --role db` | 0 | `sql-set-dev-payments-db-a` | PASS |
| 4 | `test_generate_json` | `--resource-type Microsoft.Sql/servers --lob set --stage dev --app-name payments --app-id a --role db --json` | 0 | JSON: `name=sql-set-dev-payments-db-a`, `resource_type=Microsoft.Sql/servers`, `length=26` | PASS |
| 5 | `test_generate_mini` | `--resource-type Microsoft.KeyVault/vaults --lob set --stage dev --app-name myapp --app-id a` | 0 | `kvsdmyappa` | PASS |
| 6 | `test_validate_valid` | `--validate-only sql-set-dev-payments-db-a --resource-type Microsoft.Sql/servers` | 0 | Contains `VALID` | PASS |
| 7 | `test_validate_invalid` | `--validate-only kv-bad-name --resource-type Microsoft.KeyVault/vaults` | 1 | Contains `INVALID` | PASS |
| 8 | `test_missing_required_args` | `--resource-type Microsoft.Sql/servers --lob set` | 1 | stderr contains `required` | PASS |
| 9 | `test_invalid_lob_error` | `--resource-type Microsoft.Sql/servers --lob invalid --stage dev --app-name myapp --app-id a --role web` | 1 | _(error exit)_ | PASS |
| 10 | `test_validate_without_resource_type` | `--validate-only some-name` | 1 | stderr contains `--resource-type` | PASS |
| 11 | `test_generate_with_location` | `--resource-type Microsoft.Sql/servers --lob set --stage dev --app-name payments --app-id a --role db --location eastus` | 0 | `sql-set-dev-payments-db-eastus-a` | PASS |

---

## 10. TestV2LobStageCodes (7 tests)

Tests that `LOB_CODES` and `STAGE_CODES` lookup tables are complete, unique, and single-char.

| # | Test | Data Source | Assertions | Status |
|---|------|-------------|------------|--------|
| 1 | `test_lob_codes_cover_all_valid_lobs` | `LOB_CODES` vs `VALID_LOBS` | Keys match exactly | PASS |
| 2 | `test_stage_codes_cover_all_valid_stages` | `STAGE_CODES` vs `VALID_STAGES` | Keys match exactly | PASS |
| 3 | `test_lob_codes_are_single_char` | `LOB_CODES` values | All len == 1 | PASS |
| 4 | `test_stage_codes_are_single_char` | `STAGE_CODES` values | All len == 1 | PASS |
| 5 | `test_lob_codes_are_unique` | `LOB_CODES` values | No duplicates | PASS |
| 6 | `test_stage_codes_are_unique` | `STAGE_CODES` values | No duplicates | PASS |
| 7 | `test_all_codes_are_lowercase` | `LOB_CODES` + `STAGE_CODES` | All lowercase | PASS |

---

## 11. TestV2QaStage (3 tests)

Tests that the `qa` stage works across all patterns.

| # | Test | resource_type | lob | stage | app_name | app_id | role | Expected Output | Status |
|---|------|---------------|-----|-------|----------|--------|------|-----------------|--------|
| 1 | `test_qa_stage_standard` | `Microsoft.Sql/servers` | `set` | `qa` | `myapp` | `a` | `db` | `sql-set-qa-myapp-db-a` | PASS |
| 2 | `test_qa_stage_mini` | `Microsoft.KeyVault/vaults` | `set` | `qa` | `myapp` | `a` | — | `kvsqmyappa` | PASS |
| 3 | `test_qa_stage_small` | `Microsoft.AppConfiguration/configurationStores` | `set` | `qa` | `platform` | `a` | — | `appcs-set-qa-platform-a` | PASS |

---

## 12. TestV2CollisionPrevention (5 tests)

Tests that the v2 mini naming scheme prevents collisions that v1 had.

| # | Test | Variant A | Variant B | Differentiating Field | Assertions | Status |
|---|------|-----------|-----------|----------------------|------------|--------|
| 1 | `test_different_roles_produce_different_mini_names` | `Storage/storageAccounts`, lob=`set`, stage=`dev`, app=`acctach`, id=`a`, role=`chk` | Same but role=`rpt` | `role` | Names differ, no hyphens | PASS |
| 2 | `test_different_app_ids_produce_different_mini_names` | `KeyVault/vaults`, lob=`jma`, stage=`prod`, app=`billing`, id=`a` | Same but id=`b` | `app_id` | Names differ | PASS |
| 3 | `test_different_lobs_produce_different_mini_names` | `Storage/storageAccounts`, lob=`set`, stage=`dev`, app=`myapp`, id=`a` | Same but lob=`jma` | `lob` | Names differ | PASS |
| 4 | `test_different_stages_produce_different_mini_names` | `KeyVault/vaults`, lob=`set`, stage=`dev`, app=`myapp`, id=`a` | Same but stage=`prod` | `stage` | Names differ | PASS |
| 5 | `test_si_suffix_rejected` | `Microsoft.Sql/servers`, lob=`set`, stage=`dev`, app=`shared`, id=`a-si`, role=`db` | — | — | `NamingError: Invalid app_id` | PASS |

---

## 13. TestV2MiniWithRole (2 tests)

Tests that mini pattern correctly includes role when provided.

| # | Test | resource_type | lob | stage | app_name | app_id | role | Expected Output | Max Len | Status |
|---|------|---------------|-----|-------|----------|--------|------|-----------------|---------|--------|
| 1 | `test_mini_keyvault_with_role` | `Microsoft.KeyVault/vaults` | `set` | `dev` | `myapp` | `a` | `sec` | `kvsdmyappseca` | 24 | PASS |
| 2 | `test_mini_storage_with_role` | `Microsoft.Storage/storageAccounts` | `set` | `dev` | `acctach` | `a` | `chk` | `stsdacctachchka` | 24 | PASS |

---

## 14. TestV2SmallWithRoleAndAppId (2 tests)

Tests that small pattern includes role and appId in v2.

| # | Test | resource_type | lob | stage | app_name | app_id | role | Expected Output | Status |
|---|------|---------------|-----|-------|----------|--------|------|-----------------|--------|
| 1 | `test_small_with_role` | `Microsoft.AppConfiguration/configurationStores` | `set` | `dev` | `platform` | `a` | `cfg` | `appcs-set-dev-platform-cfg-a` | PASS |
| 2 | `test_small_appid_always_present` | `Microsoft.Insights/components` | `set` | `dev` | `monitor` | `a` | — | `appi-set-dev-monitor-a` | PASS |

---

## Summary

| Test Class | Tests | Passed | Failed |
|---|---|---|---|
| TestNamingInputValidation | 10 | 10 | 0 |
| TestStandardPattern | 4 | 4 | 0 |
| TestMiniPattern | 6 | 6 | 0 |
| TestSmallPattern | 4 | 4 | 0 |
| TestDeterministicShortening | 4 | 4 | 0 |
| TestValidateName | 9 | 9 | 0 |
| TestListResourceTypes | 3 | 3 | 0 |
| TestResourceDataIntegrity | 7 | 7 | 0 |
| TestCLI | 10 | 10 | 0 |
| TestV2LobStageCodes | 7 | 7 | 0 |
| TestV2QaStage | 3 | 3 | 0 |
| TestV2CollisionPrevention | 5 | 5 | 0 |
| TestV2MiniWithRole | 2 | 2 | 0 |
| TestV2SmallWithRoleAndAppId | 2 | 2 | 0 |
| **Total** | **77** | **77** | **0** |
