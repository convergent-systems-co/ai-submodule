# feat: ADO Integration Configuration Schema and Sync Ledger Schema

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** #492
**Branch:** itsfwcp/feat/492/ado-config-sync-ledger-schemas

---

## 1. Objective

Create three JSON Schemas (ADO integration config, sync ledger, sync error) as enforcement artifacts for the Azure DevOps integration, extend the policy engine to validate ADO config, and add ADO configuration examples to project templates.

## 2. Rationale

The ADO client library (#491) is implemented but sync operations need schema-enforced configuration and state tracking. Schemas are enforcement artifacts — validated programmatically, never interpreted by AI.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Inline validation in config.py only | Yes | No schema artifact for policy engine; inconsistent with other enforcement patterns |
| Single combined schema | Yes | Separation of concerns: config vs runtime state vs error tracking |
| YAML schemas | Yes | All existing schemas use JSON Schema draft 2020-12 |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/ado-integration.schema.json` | Full ADO config schema with sync, state mapping, type mapping, field mapping, user mapping, filters |
| `governance/schemas/ado-sync-ledger.schema.json` | Sync ledger tracking GitHub↔ADO work item mappings |
| `governance/schemas/ado-sync-error.schema.json` | Error schema for failed sync operations |
| `governance/engine/tests/test_ado_schemas.py` | Validation tests for all three schemas |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/project.schema.json` | Extend `ado_integration` with `$ref` to the new config schema or add sync/mapping fields inline |
| `governance/engine/policy_engine.py` | Add ADO config validation: load `ado_integration` from project.yaml, validate against schema |
| `governance/integrations/ado/config.py` | Add `validate_against_schema()` method using jsonschema |
| `CLAUDE.md` | Document the three new schemas |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. **Create `ado-integration.schema.json`** — JSON Schema 2020-12 covering:
   - `enabled` (boolean), `organization` (URL pattern), `project` (string)
   - `auth_method` enum (service_principal, managed_identity, pat)
   - `auth_secret_name` (string)
   - `sync` object: direction enum, auto_create, auto_close, grace_period_seconds, conflict_strategy enum, sync_comments, sync_attachments
   - `state_mapping` object: GitHub state → ADO state
   - `type_mapping` object: issue type → ADO work item type
   - `field_mapping` object: area_path, iteration_path, priority_labels
   - `user_mapping` object: ADO email → GitHub username
   - `filters` object: include_labels, exclude_labels, ado_area_path_filter
   - Schema version: `"const": "1.0.0"`

2. **Create `ado-sync-ledger.schema.json`** — JSON Schema for sync state:
   - `schema_version` (const "1.0.0")
   - `mappings` array with items: github_issue_number, github_repo, ado_work_item_id, ado_project, ado_work_item_type, ado_work_item_url, sync_direction, last_synced_at, last_sync_source, last_sync_fields, created_at, sync_status
   - Validation: positive integers, ISO 8601 timestamps, enum constraints

3. **Create `ado-sync-error.schema.json`** — JSON Schema for error tracking:
   - `schema_version` (const "1.0.0")
   - `errors` array with items: error_id (UUID), timestamp, operation enum (create/update/delete), source enum (github/ado), github_issue_number, ado_work_item_id, error_type, error_message, retry_count, resolved

4. **Extend project.schema.json** — Add the new sync/mapping/filter fields to the existing `ado_integration` section to match the full config schema.

5. **Update policy engine** — Add `validate_ado_config()` function that loads `ado_integration` from project.yaml and validates against the schema. Non-blocking validation (warn, don't block).

6. **Update config.py** — Add optional schema validation method using jsonschema library.

7. **Add tests** — pytest tests validating example configs against all three schemas.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | All three schemas | Validate example data against each schema; verify rejection of invalid data |
| Unit | `policy_engine.py` | Test ADO config loading and validation |
| Unit | `config.py` | Test schema validation integration |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| project.schema.json breaking change | Low | High | Additive changes only; existing configs remain valid |
| Schema too strict for real-world configs | Med | Med | Use sensible defaults; only `organization` required |
| jsonschema dependency missing | Low | Low | Already used by policy engine |

## 7. Dependencies

- [x] ADO client library (#491) — already merged
- [x] `project.schema.json` exists with `ado_integration` stub
- [ ] No blocking dependencies

## 8. Backward Compatibility

All changes are additive. The existing `ado_integration` section in `project.schema.json` gains new optional fields. Existing project.yaml files with minimal ADO config remain valid.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Auth config schema must be reviewed |
| documentation-review | Yes | Schema documentation and CLAUDE.md updates |
| code-review | Yes | Policy engine and test changes |
| data-governance-review | Yes | Sync ledger handles work item data mappings |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Three separate schemas (not one combined) | Separation of concerns: config vs state vs errors |
| 2026-02-27 | Extend project.schema.json inline (not $ref) | Consistent with existing patterns; all other sections are inline |
