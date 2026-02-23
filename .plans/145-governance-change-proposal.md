# Governance Change Proposal Workflow

**Author:** Code Manager (agentic)
**Date:** 2026-02-23
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/145
**Branch:** itsfwcp/feat/145/governance-change-proposal

---

## 1. Objective

Create an agentic workflow prompt that analyzes retrospective and persona effectiveness data to propose governance configuration changes for human approval.

## 2. Rationale

The governance framework tracks panel accuracy, persona effectiveness, and override frequency. Without a structured way to translate this data into actionable configuration changes, the data just accumulates. This workflow closes the self-evolution feedback loop (Phase 5b) by generating concrete, evidence-backed proposals.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Auto-apply changes | Yes | Too risky — governance changes should always have human oversight |
| Embed in retrospective prompt | Yes | Separation of concerns — retro captures data, this proposes changes |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/prompts/governance-change-proposal.md` | Agentic workflow for proposing governance changes |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `GOALS.md` | Check off the governance change proposal workflow item |

## 4. Approach

1. Create the workflow prompt with structured steps
2. Reference both data schemas as inputs
3. Define proposal output format
4. Document safety guardrails
5. Update GOALS.md

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Prompt review | Verify workflow steps are complete and reference correct schemas |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Proposals too aggressive | Low | Low | Human approval always required |

## 7. Dependencies

- [x] retrospective-aggregation.schema.json (exists)
- [x] persona-effectiveness.schema.json (just created, PR #143)

## 8. Backward Compatibility

Fully additive — new prompt file.

## 9. Governance

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Always require human approval | Governance changes affect all consuming repos |
