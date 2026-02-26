# Update README for Current Agentic Workflow

**Author:** Code Manager (agentic)
**Date:** 2026-02-25
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/334
**Branch:** itsfwcp/docs/334/readme-workflow-update

---

## 1. Objective

Update outdated README.md sections to reflect the current 5-phase parallel agentic workflow, context management shutdown protocol, and consolidated review prompts.

## 2. Rationale

The README described a sequential pipeline and referenced deprecated personas removed in #257. The context management section lacked the checkpoint/shutdown protocol and parallel dispatch model that are core to current operation.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Full README rewrite | Yes | Too broad; targeted edits are sufficient |
| Keep as-is with links to detailed docs | Yes | README is the entry point — it should be accurate |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | N/A |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `README.md` | Update agentic pipeline, compliance, and context management sections |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | N/A |

## 4. Approach

1. Replace sequential pipeline diagram with 5-phase parallel workflow diagram
2. Add CANCEL to agent protocol message types
3. Fix compliance section — reference consolidated review prompts instead of removed personas
4. Add shutdown protocol, checkpoint system, and parallel dispatch model to context management section

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Visual | README | Verify Mermaid diagram renders correctly |
| Accuracy | Content | Verify all claims match startup.md and CLAUDE.md |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Diagram too complex | Low | Low | Keep high-level, link to detailed docs |

## 7. Dependencies

- None

## 8. Backward Compatibility

Documentation-only change. No breaking changes.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Documentation change |
| security-review | Yes | Always required |
| threat-modeling | Yes | Always required |
| cost-analysis | Yes | Always required |
| data-governance-review | Yes | Always required |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-25 | Keep tier table, add operational details below | Table is a good quick reference; operational details complement it |
