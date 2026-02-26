# Auto-Remediation Loops — Schemas, Workflow Prompt, and Verification Artifacts

**Author:** Code Manager (agentic) / Coder (agentic)
**Date:** 2026-02-21
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/81
**Branch:** itsfwcp/feat/81/auto-remediation-loops

---

## 1. Objective

Add the governance artifacts required for autonomous drift remediation: two JSON schemas (remediation action record and verification result) and an agentic workflow prompt that guides the Code Manager through the remediation decision tree. This completes the Phase 4b "auto-remediation loops" capability at the governance artifact layer.

## 2. Rationale

The drift detection infrastructure (PR #69) established schemas for signals and baselines, plus policy configuration for allowed/prohibited remediation actions. However, there are no schemas to record *what remediation was performed* or *how it was verified*, and no agentic workflow to guide autonomous execution. Without these artifacts, the remediation loop cannot be audited, reproduced, or governed.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Single combined remediation schema | Yes | Separation of action and verification allows independent evolution and clearer audit trail |
| Skip workflow prompt, rely on architecture doc | Yes | Architecture doc is 1,400+ lines; agents need a focused, step-by-step prompt like startup.md |
| Extend run-manifest schema instead of new schemas | Yes | Remediation is a distinct lifecycle event, not a merge; a separate schema prevents overloading the manifest |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/schemas/remediation-action.schema.json` | JSON Schema (Draft 2020-12) for remediation action records |
| `governance/schemas/remediation-verification.schema.json` | JSON Schema (Draft 2020-12) for post-remediation verification results |
| `governance/prompts/remediation-workflow.md` | Agentic workflow prompt for the Code Manager to execute remediation loops |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off "Auto-remediation loops" item in Phase 4b |
| `CLAUDE.md` (root `.ai/`) | Update artifact counts if needed |
| `governance/docs/runtime-feedback-architecture.md` | Add references to the new schemas in the File Manifest appendix |

### Files to Delete

None.

## 4. Approach

1. **Create `remediation-action.schema.json`** — Define the structure for recording a remediation action: which drift triggered it, which action was taken, on which component, the policy rules that authorized it, timestamps, and outcome status. Reference `runtime-signal.schema.json` for signal_id and `baseline.schema.json` for baseline_id. Reference `drift-remediation.yaml` for allowed action types.

2. **Create `remediation-verification.schema.json`** — Define the structure for verification results: what metrics were checked, baseline vs. post-remediation values, pass/fail verdict, whether revert was triggered, and the new baseline ID if verification passed.

3. **Create `remediation-workflow.md`** — An agentic prompt (similar in structure to `startup.md`) that the Code Manager follows when a drift signal triggers remediation. Steps: receive drift signal → classify severity → check policy thresholds → check circuit breaker → select remediation action → execute → verify → capture new baseline or revert → audit.

4. **Update documentation** — Add schema references to architecture doc appendix, check off GOALS.md item, update CLAUDE.md if counts change.

5. **Commit with conventional commits** — One commit per logical unit (schemas together, workflow separately, docs separately).

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Schema validation | Both new schemas | Validate schemas are valid JSON Schema Draft 2020-12 using `python -m json.tool` for syntax and structural review |
| Cross-reference check | All policy files | Verify enum values in schemas match allowed actions in `drift-remediation.yaml` |
| N/A | No runtime tests | This is a configuration-only repo with no test runner |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Schema doesn't align with architecture doc | Low | Medium | Schemas are derived directly from the architecture doc sections on remediation |
| Workflow prompt conflicts with startup.md | Low | Low | Workflow is invoked *from* the startup loop, not replacing it |
| Enum values drift from policy files | Medium | Medium | Document the canonical source of truth for each enum in schema descriptions |

## 7. Dependencies

- [x] Drift detection schemas (PR #69) — already merged
- [x] Drift policy configuration (PR #69) — already merged
- [x] Runtime feedback architecture doc — already exists
- [ ] No blocking dependencies

## 8. Backward Compatibility

Fully additive. No existing schemas or artifacts are modified. New schemas extend the governance artifact set without changing any existing contracts.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Mandatory on all PRs per policy |
| threat-modeling | Yes | Mandatory on all PRs per policy |
| cost-analysis | Yes | Mandatory on all PRs per policy |
| documentation-review | Yes | Mandatory on all PRs per policy |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Separate action and verification schemas | Independent lifecycle events; clearer audit separation |
| 2026-02-21 | Workflow prompt references policy files by path | Ensures agents load the correct policy at execution time rather than embedding rules |
