# Phase 5e — Acceptance verification workflow

**Author:** Team Lead (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/165
**Branch:** NETWORK_ID/feat/165/acceptance-verification

---

## 1. Objective

Create an agentic workflow that validates implementation against formal spec acceptance criteria and completion conditions before triggering review panels.

## 2. Rationale

The formal spec schema (PR #164) defines machine-verifiable contracts. This workflow operationalizes those contracts — it reads a formal spec and systematically verifies each criterion and condition, producing a structured verification report.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Inline verification in startup.md | Yes | Startup.md is already long; a dedicated workflow is composable |
| Python script for verification | Yes | Would require runtime changes; a workflow prompt is a cognitive artifact consistent with existing patterns |
| Workflow prompt | Yes | **Selected** — follows existing workflow conventions in governance/prompts/workflows/ |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/prompts/workflows/acceptance-verification.md` | The workflow prompt |
| `governance/docs/acceptance-verification.md` | Documentation |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/workflows/index.md` | Add new workflow to the index |
| `GOALS.md` | Check off the item |

### Files to Delete

N/A

## 4. Approach

1. Create workflow prompt following existing conventions (phases with personas, gates, inputs/outputs)
2. Write documentation
3. Add to workflows index
4. Update GOALS.md

## 5. Testing Strategy

N/A — cognitive artifact (workflow prompt), not executable code.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Workflow too prescriptive for diverse specs | Low | Low | Use flexible verification methods that adapt to spec content |

## 7. Dependencies

- [x] Formal spec schema (PR #164, merged)

## 8. Backward Compatibility

Additive — new files only.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | New documentation |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Follow existing workflow conventions | Consistency with 8 existing workflows |
