# Create Signal-Adapters Directory with Example Polling Adapter Configurations

**Author:** Code Manager (agentic)
**Date:** 2026-02-23
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/98
**Branch:** itsfwcp/feat/98/signal-adapters

---

## 1. Objective

Create the `governance/policy/signal-adapters/` directory — the last missing governance artifact for the Phase 5 runtime feedback loop — with example polling adapter configurations and a README explaining the format.

## 2. Rationale

The runtime feedback architecture defines four signal ingestion modes: webhook, polling, event bus, and manual. Polling adapters require YAML configuration files stored in `governance/policy/signal-adapters/`. All other governance artifacts for the runtime feedback loop are already implemented (schemas, policies, templates, workflows). This completes the governance-side implementation.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Skip examples, create empty directory | Yes | Empty directories don't convey the adapter format; a README alone is insufficient |
| Create adapters for all integration patterns | Yes | Only polling adapters use config files; webhook/event-bus/manual are defined architecturally, not via YAML configs |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/policy/signal-adapters/README.md` | Documents the directory purpose, adapter schema, and usage |
| `governance/policy/signal-adapters/example-metrics-api.yaml` | Example: polling a metrics/alerting API |
| `governance/policy/signal-adapters/example-log-aggregator.yaml` | Example: polling a log aggregation API |
| `governance/policy/signal-adapters/example-apm-tool.yaml` | Example: polling an APM/tracing API |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/docs/runtime-feedback-architecture.md` | Update file manifest to mark `signal-adapters/` as implemented |
| `GOALS.md` | Check off "Runtime feedback loop" item |

### Files to Delete

N/A — no files to delete.

## 4. Approach

1. Create `governance/policy/signal-adapters/` directory
2. Write `README.md` documenting the adapter format (referencing the architecture doc schema)
3. Create 3 example adapter YAML files following the schema from the architecture doc (Section 1, Polling Adapter)
4. Update `runtime-feedback-architecture.md` file manifest entry for `signal-adapters/`
5. Update `GOALS.md` to check off the runtime feedback loop item
6. Commit with conventional commit message

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | YAML validity | Verify example files are valid YAML |
| Review | Schema compliance | Confirm examples match the architecture doc adapter schema |

No automated tests — this is a config-only repo with no test runner.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Example adapters reference non-existent APIs | Low | Low | Examples use placeholder URLs with clear `${ENV_VAR}` substitution |
| Adapter format drifts from architecture doc | Low | Medium | README cross-references the architecture doc section |

## 7. Dependencies

- [x] Runtime feedback architecture documented (governance/docs/runtime-feedback-architecture.md)
- [x] Runtime signal schema defined (governance/schemas/runtime-signal.schema.json)

## 8. Backward Compatibility

Fully additive. New directory and files only. No existing files are removed or have breaking changes.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| copilot-review | Yes | Standard for all PRs |
| documentation-review | Yes | New documentation created |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | 3 example adapters (metrics, logs, APM) | Covers the most common integration patterns without being exhaustive |
