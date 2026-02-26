# Persona Effectiveness Scoring Schema

**Author:** Code Manager (agentic)
**Date:** 2026-02-23
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/142
**Branch:** itsfwcp/feat/142/persona-effectiveness-schema

---

## 1. Objective

Create a JSON Schema for tracking per-persona signal-to-noise ratio across governance runs, enabling automated persona weight adjustment as part of Phase 5b (Self-Evolution).

## 2. Rationale

The governance framework uses 62 personas across 19 panels. Not all personas contribute equally — some may surface findings that are consistently dismissed (noise) while others produce high-signal recommendations. Tracking effectiveness per persona enables data-driven weight adjustment and identifies personas that need refinement.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Embed in retrospective-aggregation.schema.json | Yes | Separation of concerns — retro schema tracks runs, this tracks personas over time |
| Track only at panel level (not persona) | Yes | Panels aggregate multiple personas; per-persona granularity is needed for weight tuning |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/persona-effectiveness.schema.json` | JSON Schema for persona effectiveness scoring |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off the persona effectiveness scoring schema item |

### Files to Delete

None.

## 4. Approach

1. Create the JSON Schema following patterns from `retrospective-aggregation.schema.json`
2. Include per-persona metrics, time-series support, and weight adjustment recommendations
3. Add an `examples` field with a sample document
4. Update GOALS.md

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Schema validity | Verify schema is valid JSON Schema Draft 2020-12 |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Schema doesn't align with retro aggregation | Low | Low | Cross-referenced fields match existing schema |

## 7. Dependencies

- [x] No blocking dependencies

## 8. Backward Compatibility

Fully additive — new schema file, no existing behavior changes.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Standard |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Separate schema from retro aggregation | Per-persona data has different lifecycle than per-run data |
