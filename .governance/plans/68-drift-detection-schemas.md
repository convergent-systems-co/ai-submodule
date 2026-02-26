# Add Drift Detection Schemas and Policy Configuration

**Author:** Code Manager (agentic)
**Date:** 2026-02-22
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/68
**Branch:** itsfwcp/feat/68/drift-detection-schemas

---

## 1. Objective

Create the 10 enforcement artifacts (JSON Schemas + YAML policy configs) referenced in the runtime feedback architecture doc to complete Phase 4b drift detection scaffolding.

## 2. Rationale

The architecture doc (`governance/docs/runtime-feedback-architecture.md`) fully specifies these files' content but they don't exist yet. Creating them completes the enforcement layer, enabling consuming repos to implement runtime detection.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Wait for full runtime implementation | Yes | Schemas and policies are standalone enforcement artifacts that can be created independently |
| Create only schemas, skip policy files | Yes | Policy files are equally well-defined and needed for completeness |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/runtime-signal.schema.json` | Signal normalization schema |
| `governance/schemas/baseline.schema.json` | Baseline snapshot schema |
| `governance/policy/drift-policy.yaml` | Drift-specific policy engine rules |
| `governance/policy/drift-remediation.yaml` | Auto-remediation rules |
| `governance/policy/signal-panel-mapping.yaml` | Signal to panel routing |
| `governance/policy/rate-limits.yaml` | Rate limit config |
| `governance/policy/circuit-breaker.yaml` | Circuit breaker parameters |
| `governance/policy/severity-reclassification.yaml` | Severity reclassification rules |
| `governance/policy/deduplication.yaml` | Deduplication window config |
| `governance/policy/component-registry.yaml` | Component criticality registry |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off "Drift detection" in Phase 4b |

## 4. Approach

Extract content from the architecture doc into standalone files. Each file's content is already specified in the doc — this is a mechanical extraction task.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | JSON Schemas | Verify valid JSON |
| Manual | YAML files | Verify valid YAML |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Schema diverges from architecture doc | Low | Low | Extract directly from doc |

## 7. Dependencies

- [x] runtime-feedback-architecture.md exists (it does)

## 8. Backward Compatibility

Fully additive. No existing files modified.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| ai-expert-review | Yes | Governance enforcement artifacts |
| copilot-review | Yes | Standard review |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

N/A — content is extracted directly from the architecture doc.
