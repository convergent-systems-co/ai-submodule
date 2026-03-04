# Add Autonomy Metrics Schema and Weekly Reporting Template

**Author:** Team Lead (agentic)
**Date:** 2026-02-23
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/100
**Branch:** NETWORK_ID/feat/100/autonomy-metrics

---

## 1. Objective

Create governance artifacts for tracking and reporting on autonomous operation effectiveness: a metrics schema, health thresholds, and a weekly report template.

## 2. Rationale

The governance platform operates autonomously but has no structured way to measure its own effectiveness. Without metrics, there is no way to detect degradation in autonomous operation quality, justify continued autonomy, or identify areas for improvement.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Ad-hoc reporting | Yes | Not auditable, not comparable across weeks |
| Full dashboard application | Yes | Out of scope for config-only repo; dashboards consume these schemas |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/autonomy-metrics.schema.json` | Defines the structure for weekly autonomy metrics |
| `governance/prompts/templates/weekly-report-template.md` | Structured report template for weekly autonomy summaries |
| `governance/policy/autonomy-thresholds.yaml` | Health thresholds for each metric |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off "Autonomy metrics and weekly reporting dashboard" |

### Files to Delete

N/A

## 4. Approach

1. Design the metrics schema based on data already captured in checkpoints and run manifests
2. Create the JSON schema with metric categories: throughput, quality, efficiency, safety
3. Create threshold config defining healthy vs. degraded vs. critical ranges
4. Create report template that consumes the schema
5. Update GOALS.md
6. Commit

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Schema validity | Verify JSON schema is valid |
| Manual | YAML validity | Verify thresholds file is valid YAML |
| Review | Completeness | Verify all metric categories from issue are covered |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Metrics don't align with what checkpoints capture | Low | Medium | Schema designed from existing checkpoint/manifest structure |

## 7. Dependencies

- [x] Run manifest schema exists (governance/schemas/run-manifest.schema.json)
- [x] Checkpoint structure established (startup.md)

## 8. Backward Compatibility

Fully additive. New files only.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| copilot-review | Yes | Standard |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | 4 metric categories (throughput, quality, efficiency, safety) | Covers the key dimensions of autonomous operation health |
