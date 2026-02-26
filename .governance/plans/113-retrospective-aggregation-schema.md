# Retrospective Aggregation Schema

**Author:** Code Manager (agentic)
**Date:** 2026-02-23
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/113
**Branch:** itsfwcp/feat/113/retrospective-aggregation-schema

---

## 1. Objective

Create a JSON Schema for aggregating retrospective data across governance runs. This enables data-driven self-evolution by collecting panel accuracy, false positive rates, override frequency, review cycle distributions, and time-to-merge metrics over time.

## 2. Rationale

The retrospective prompt (`governance/prompts/retrospective.md`) produces per-issue evaluations as issue comments, but there is no structured format for aggregating this data across runs. Without structured aggregation, threshold auto-tuning (5b goal #2) and persona effectiveness scoring (5b goal #3) cannot be implemented — they need historical data in a machine-readable format.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Extend autonomy-metrics schema | Yes | Autonomy metrics are period-based summaries; retrospective data is per-run and captures qualitative aspects (plan accuracy, process improvement candidates) that don't fit the metrics model |
| Extend run-manifest schema | Yes | Manifests are immutable audit artifacts; retrospective data is post-merge evaluation that may be updated as incidents are discovered |
| Standalone schema | Yes (chosen) | Clean separation of concerns; retrospective data has different lifecycle and access patterns than manifests or metrics |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/retrospective-aggregation.schema.json` | JSON Schema defining the structure for aggregated retrospective data |
| `governance/docs/retrospective-aggregation.md` | Documentation explaining schema purpose, usage, and relationship to other schemas |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off the "Retrospective aggregation schema" item in Phase 5b |
| `README.md` | Add schema to the repository structure listing |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. Create `retrospective-aggregation.schema.json` following existing schema conventions (draft/2020-12, $id with set-apps URL, schema_version const)
2. Design the schema with:
   - Top-level: schema version, report ID, aggregation period, governance version
   - `runs` array: per-run retrospective entries with timestamps
   - Per-run: panel results, plan accuracy, review cycles, copilot findings, overrides
   - Aggregated metrics: derived statistics across all runs in the period
3. Create documentation file explaining the schema
4. Update GOALS.md and README.md

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Schema | Verify schema validates against JSON Schema draft 2020-12 |
| Manual | Consistency | Verify naming and structure patterns match existing schemas |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Schema design doesn't capture needed data for auto-tuning | Low | Medium | Design with extensibility; required fields are minimal, optional fields cover future needs |
| Schema conflicts with autonomy-metrics | Low | Low | Different purpose and lifecycle documented clearly |

## 7. Dependencies

- [x] No blocking dependencies

## 8. Backward Compatibility

Fully backward compatible. New schema file, no existing behavior changed.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New schema file |
| documentation-review | Yes | New docs file + GOALS/README updates |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Standalone schema, not extending existing | Different lifecycle and access patterns than manifests or metrics |
| 2026-02-23 | Per-run entries plus aggregated metrics | Supports both individual analysis and trend detection |
