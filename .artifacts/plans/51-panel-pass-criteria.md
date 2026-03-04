# Panel Pass/Fail Criteria and Local Override System

**Author:** Team Lead (agentic)
**Date:** 2026-02-21
**Status:** completed
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/51
**Branch:** NETWORK_ID/feat/51/panel-pass-criteria

---

## 1. Objective

Define transparent pass/fail criteria for every governance panel and create a `panels.local.json` override mechanism that allows consuming projects to increase (but never decrease) panel strictness.

## 2. Rationale

Panels currently lack standardized pass/fail thresholds. Only ai-expert-review and copilot-review have confidence score calculations. The policy engine references confidence scores but individual panels don't document what constitutes passing. Developers cannot see or influence which panels run or what thresholds apply.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Per-panel YAML config files | Yes | Adds complexity; single JSON file is simpler |
| Embed criteria in policy YAML | Yes | Mixes panel-level detail with policy-level concerns |
| Separate schema + defaults JSON | Yes | Selected — clean separation, schema-validated, overridable |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/panels.schema.json` | JSON Schema for panels.local.json validation |
| `governance/schemas/panels.defaults.json` | Default panel configuration (thresholds, scoring) |

### Files to Modify

| File | Change Description |
|------|-------------------|
| 13 panel .md files (all except ai-expert-review, copilot-review) | Add "Pass/Fail Criteria" and "Confidence Score Calculation" sections |

### Files to Delete

None.

## 4. Approach

1. Create `panels.schema.json` defining the structure for panel configuration
2. Create `panels.defaults.json` with default thresholds for all 15 panels
3. Add "Pass/Fail Criteria" and "Confidence Score Calculation" sections to the 13 panels that lack them
4. Commit each logical unit separately

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | panels.defaults.json | Validate defaults against schema |
| Manual review | All 15 panels | Verify criteria sections are consistent |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Inconsistent criteria across panels | Medium | Low | Use template-based approach |
| Thresholds too strict/lenient | Medium | Low | Conservative defaults, override mechanism |

## 7. Dependencies

None.

## 8. Backward Compatibility

Fully additive. No existing behavior changes. Consuming repos without panels.local.json get defaults.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Schema and documentation changes |
| documentation-review | Yes | Panel documentation updates |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Use confidence base 0.85 for most panels, 0.90 for security/threat | Security panels need higher baseline |
| 2026-02-21 | Deduction model: critical -0.25, high -0.15, medium -0.05, low -0.01 | Consistent with existing ai-expert-review model |
