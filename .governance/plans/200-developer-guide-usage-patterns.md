# Developer Guide — Common Usage Patterns and Recovery Procedures

**Author:** Code Manager (agentic)
**Date:** 2026-02-24
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/200
**Branch:** `itsfwcp/docs/200/developer-guide-usage-patterns`

---

## 1. Objective

Add comprehensive "Recovery & Re-Entry Patterns" and "Troubleshooting" sections to DEVELOPER_GUIDE.md, giving developers actionable guidance for getting back into the agentic loop when things go wrong — missing checkpoints, dirty git state, stuck PRs, context loss, etc.

## 2. Rationale

Recovery procedures exist in governance prompts (checkpoint-resumption-workflow.md, startup.md) and docs (context-management.md), but they are written for agent consumption with detailed jq filters and multi-step protocols. Developers need a concise, human-readable reference covering the most common failure modes with copy-paste commands.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Separate troubleshooting.md | Yes | Fragments the Developer Guide; better to keep developer-facing content in one place |
| Expand startup.md | Yes | startup.md is agent-facing; mixing human instructions dilutes agent instructions |
| Add to README.md | Yes | README is overview-level; DEVELOPER_GUIDE.md is the operational reference |

## 3. Scope

### Files to Create

None.

### Files to Modify

| File | Change Description |
|------|-------------------|
| `DEVELOPER_GUIDE.md` | Add "Recovery & Re-Entry Patterns" section with 7 scenarios, "Troubleshooting" FAQ, and "Diagnostic Commands" quick reference |

### Files to Delete

None.

## 4. Approach

1. Add a "Recovery & Re-Entry Patterns" section after "Common Operations" with subsections for each failure scenario
2. Add a "Diagnostic Commands" quick reference table
3. Add a "Troubleshooting" FAQ section
4. Cross-reference governance docs for deeper reading
5. Update "Further Reading" with new cross-references

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | All commands | Verify all diagnostic commands are valid and executable |
| Link check | Cross-references | Verify all referenced files exist |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Commands become stale | Low | Low | Commands reference stable gh CLI and git interfaces |
| Over-documentation | Medium | Low | Keep each scenario to ≤10 lines with a command block |

## 7. Dependencies

- None (documentation-only change)

## 8. Backward Compatibility

Additive change only. No existing content modified.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | Documentation change |
| security-review | Yes | Required on all PRs |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Keep in DEVELOPER_GUIDE.md rather than separate file | Single operational reference for developers |
