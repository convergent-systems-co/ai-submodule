# Plan: Configure GitHub Copilot for Auto-Fixing Issues

**Author:** Code Manager (agentic)
**Date:** 2026-02-23
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/112
**Branch:** itsfwcp/docs/112/copilot-auto-fix-plan

---

## 1. Objective

Deliver a research-backed plan documenting how to configure GitHub Copilot to automatically detect and fix issues in PRs and code scanning alerts. This is a planning/documentation task — no implementation in this PR.

## 2. Rationale

The governance workflow already integrates Copilot PR review (see `governance/prompts/startup.md`, steps 7b-7d). However, the current flow requires the agentic loop (Code Manager + Coder) to read Copilot suggestions and manually implement fixes. The question is whether Copilot can be configured to fix issues itself, reducing the Code Manager's workload.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Do nothing — keep current manual flow | Yes | Issue explicitly requests investigation; current flow works but is slower |
| Implement full auto-fix pipeline now | Yes | Issue says "planning purposes only" — defer implementation |
| Research only one mechanism | Yes | Multiple Copilot features overlap; comprehensive coverage needed |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/docs/copilot-auto-fix.md` | Configuration guide for Copilot auto-fix capabilities |

### Files to Modify

| File | Change Description |
|------|-------------------|
| None | Documentation-only change |

### Files to Delete

| File | Reason |
|------|--------|
| None | No files to delete |

## 4. Approach

1. Write `governance/docs/copilot-auto-fix.md` covering:
   - Current Copilot capabilities (Code Review, Autofix, Coding Agent, Agentic Workflows)
   - Configuration steps for each mechanism
   - Integration with Dark Factory governance workflow
   - Limitations and gaps
   - Recommended approach for this project
2. Keep it actionable — when implementation is ready, someone should be able to follow the doc

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| N/A | N/A | Documentation-only task |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Information becomes outdated | Medium | Low | Document dates capabilities; link to official docs |
| Recommended approach doesn't work in practice | Low | Low | This is a plan, not implementation — validation comes later |

## 7. Dependencies

- None

## 8. Backward Compatibility

N/A — documentation-only change.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | New documentation file |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Documentation-only deliverable | Issue explicitly says "planning purposes only" |
