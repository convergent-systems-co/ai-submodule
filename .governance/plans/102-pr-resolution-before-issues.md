# Plan: Fix Agentic Improvement Loop — PR Resolution Before Issues

**Author:** Claude Code (Coder persona)
**Date:** 2026-02-23
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/102
**Branch:** itsfwcp/fix/102/pr-resolution-before-issues

---

## 1. Objective

Ensure the agentic improvement loop resolves all open PRs (CI checks, Copilot recommendations, panel evaluations) before scanning for new issues. Currently the startup sequence goes straight to issue scanning, which means open PRs can languish unresolved while new work is started.

## 2. Rationale

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Separate PR monitor workflow | Yes | Adds complexity; the startup loop already has all the review machinery (Steps 7a-7g) |
| PR check as a constraint on issue selection | Yes | Doesn't address the core problem — PRs need active resolution, not just gating |
| **Insert PR resolution step before issue scan** | **Selected** | Reuses existing Step 7 review loop; minimal change; clear ordering guarantee |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Add "Step 0: Resolve Open PRs" section before Step 1. This step lists open PRs by the agent, enters the Step 7 review loop for each, and only proceeds to issue scanning when all PRs are resolved or escalated. |
| `GOALS.md` | N/A — no goals items affected |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. Add a new "Step 0: Resolve Open PRs" section in startup.md between the Pre-flight check and Step 1
2. Step 0 queries open PRs authored by the agent (using `gh pr list`)
3. For each open PR, enters the existing Step 7 review loop (7a-7g)
4. PRs from non-agentic sources (human PRs) also get panel evaluation if they haven't been reviewed
5. Only after all PRs are resolved (merged, closed, or escalated) does the loop proceed to Step 1
6. Add a maximum PR resolution limit (3 PRs) consistent with the 3-issue session cap

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | startup.md | Verify the new step is correctly positioned and references existing steps |
| Review | Workflow logic | Verify the PR resolution loop correctly reuses Step 7 sub-steps |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PR resolution consumes entire context budget | Medium | Medium | Count resolved PRs toward the 3-issue session cap |
| Infinite loop if PR can't be resolved | Low | High | Maximum 3 review cycles per PR (existing constraint), then escalate |

## 7. Dependencies

- [x] Step 7 review loop already exists in startup.md (no new machinery needed)

## 8. Backward Compatibility

Fully backward compatible. If no open PRs exist, Step 0 is a no-op and the loop proceeds to Step 1 as before.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Modifying the core agentic workflow |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | PR resolution counts toward session issue cap | Prevents context exhaustion from resolving many PRs |
| 2026-02-23 | Include non-agent PRs for panel evaluation | Issue requirement: "All Panels must be evaluated since the PRs may not be from an Agentic Loop" |
