# Incident-to-DI Generation Schemas and Workflow

**Author:** Team Lead (agentic)
**Date:** 2026-02-22
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/87
**Branch:** NETWORK_ID/feat/87/incident-to-di-generation

---

## 1. Objective

Add the governance artifacts for Phase 4b incident-to-DI (Design Intent) generation. Runtime anomalies should be able to automatically create Design Intents that flow through the existing governance pipeline. This completes Phase 4b governance artifacts.

## 2. Rationale

The architecture is fully specified in `governance/docs/runtime-feedback-architecture.md` Section 2 (Incident-to-DI Generator). This follows the same pattern as drift detection (PR #69) and auto-remediation (PR #81) — creating versioned governance artifacts (schemas, templates, workflows) without runtime implementation.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Implement runtime DI generator | Yes | Phase 5 scope; Phase 4b only creates governance artifacts |
| Single monolithic workflow file | Yes | Separating schema, template, and workflow follows established pattern |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/runtime-di.schema.json` | JSON Schema for runtime-generated Design Intents |
| `governance/prompts/templates/runtime-di-template.md` | Markdown template hydrated when generating a DI |
| `governance/prompts/di-generation-workflow.md` | Agentic workflow for DI generation |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off "Incident-to-DI generation" in Phase 4b, update Phase 4b status |

### Files to Delete

None.

## 4. Approach

1. Create `runtime-di.schema.json` following the structure in architecture spec Section 2 (lines 510-584)
2. Create `runtime-di-template.md` with all fields from the DI template structure, including structured emission block
3. Create `di-generation-workflow.md` covering the 6-step generation process (signal validation, deduplication, correlation, priority calculation, template hydration, panel routing)
4. Update `GOALS.md` to check off the incident-to-DI generation item

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | `runtime-di.schema.json` | Schema is valid JSON Schema Draft 2020-12 |
| Manual review | All files | Cross-reference with architecture spec for completeness |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Schema inconsistency with existing schemas | Low | Medium | Cross-reference all `$ref` fields against existing schemas |
| Missing fields from architecture spec | Low | Medium | Line-by-line comparison with spec Section 2 |

## 7. Dependencies

- [x] `runtime-signal.schema.json` exists (created in PR #69)
- [x] `baseline.schema.json` exists (created in PR #69)
- [x] `panel-output.schema.json` exists (Phase 4)
- [x] Architecture spec is complete (`runtime-feedback-architecture.md`)

## 8. Backward Compatibility

No breaking changes. This is purely additive — new files only. The single modification to GOALS.md is a checkbox update.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Mandatory per all policy profiles |
| threat-modeling | Yes | Mandatory per all policy profiles |
| cost-analysis | Yes | Mandatory per all policy profiles |
| documentation-review | Yes | Mandatory per all policy profiles |
| code-review | Yes | Standard review |
| ai-expert-review | Yes | Standard review |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-22 | Place template in `governance/prompts/templates/` not `templates/` | Architecture spec says `templates/runtime-di.md` but all prompts live under `governance/prompts/` per filesystem collapse (PR #46). Created `templates/` subdirectory under `governance/prompts/`. |
