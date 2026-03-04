# Add Model Provenance Tracking to Panel Emission Schema (#560)

**Author:** Claude (Coder)
**Date:** 2026-03-01
**Status:** approved
**Issue:** #560
**Branch:** NETWORK_ID/feat/560/model-provenance-schema

---

## 1. Objective

Add model provenance fields to `panel-output.schema.json` so past emissions can be traced to specific model versions. Also make `aggregate_verdict` required (all existing emissions already include it).

## 2. Rationale

If a model is later found to have a blind spot, there is currently no way to identify which past emissions it produced. Adding `model_id`, `system_prompt_hash`, and `inference_config` enables retroactive analysis.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Top-level required fields | Yes | Breaking change — would invalidate all existing emissions |
| Separate provenance schema | Yes | Unnecessary complexity for 3 fields |
| Add to execution_context (optional) | Yes | Selected — backward compatible, additive |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| governance/schemas/panel-output.schema.json | Add model_id, system_prompt_hash, inference_config to execution_context; add aggregate_verdict to required |

## 4. Approach

1. Add `model_id` to `execution_context` (optional string)
2. Add `system_prompt_hash` to `execution_context` (optional, SHA-256 pattern)
3. Add `inference_config` object to `execution_context` (optional, with temperature/max_tokens/top_p)
4. Add `aggregate_verdict` to top-level `required` array
5. Bump schema_version default to 1.1.0

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | schema_validation tests | Existing 47 schema tests pass |
| Full suite | all 706 tests | No regressions |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Existing emissions fail validation | None | N/A | New fields are optional in execution_context; aggregate_verdict already present in all emissions |

## 7. Dependencies

None.

## 8. Backward Compatibility

Fully backward compatible. New fields are optional within the optional `execution_context` object. `aggregate_verdict` was already present in all existing emissions.

## 9. Governance

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-01 | Place provenance in execution_context, not top-level | Backward compatible; execution_context is the natural home for metadata |
| 2026-03-01 | Pattern-validate system_prompt_hash as SHA-256 | Ensures consistent format across providers |
