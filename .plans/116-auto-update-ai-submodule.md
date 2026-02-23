# Auto-Update .AI Submodule

**Author:** Code Manager (agentic)
**Date:** 2026-02-23
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/116
**Branch:** itsfwcp/fix/116/auto-update-ai-submodule

---

## 1. Objective

Ensure consuming repos automatically check whether the `.ai` submodule is up to date and update it as part of the agentic startup sequence and init.sh bootstrap.

## 2. Rationale

The agentic loop in consuming repos reads governance artifacts (startup.md, personas, policies) from the `.ai` submodule. If the submodule pointer is stale, the agent operates with outdated governance rules. The propagate-submodule workflow (PR-based) exists but is disabled. A local check-and-update during startup provides immediate feedback and keeps the submodule current without requiring the propagation workflow.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Rely solely on propagate-submodule workflow | Yes | Currently disabled; requires cross-repo tokens; doesn't cover local development |
| Manual update reminders | Yes | Error-prone; the issue explicitly requests automatic behavior |
| Update only in init.sh | Yes | init.sh is run once during setup; startup.md runs every session — both need the check |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| N/A | No new files needed |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/prompts/startup.md` | Add pre-flight step to check and update .ai submodule |
| `init.sh` | Add submodule freshness check with optional auto-update |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. Add a new pre-flight step to `startup.md` (before the existing repo config checks):
   - Detect if running in a consuming repo (submodule context)
   - Run `git submodule update --remote .ai` to fetch latest
   - If the submodule pointer changed, commit the update and note it
   - If not in a submodule context (running in ai-submodule itself), skip

2. Add a submodule freshness check to `init.sh`:
   - After symlinks but before repo configuration
   - Fetch the remote for .ai and compare local vs remote HEAD
   - If behind, run `git submodule update --remote .ai`
   - Print status (up to date / updated / failed)

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | init.sh | Run in consuming repo, verify submodule update check runs |

Configuration-only repo with no test runner.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Submodule update introduces breaking changes | Low | Medium | Update is a pointer change, not a merge; breaking changes are caught by governance |
| Network unavailable during fetch | Low | Low | Graceful degradation — warn and continue |
| Dirty submodule working tree | Low | Low | Check for dirty state before update |

## 7. Dependencies

- None

## 8. Backward Compatibility

Fully backward compatible. The submodule check is a new pre-flight step that skips gracefully if not in submodule context or if the submodule is already current.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Shell script and markdown changes |
| documentation-review | Yes | Startup sequence modification |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Add to both startup.md and init.sh | startup.md covers agentic sessions; init.sh covers manual bootstrap — both are entry points |
| 2026-02-23 | Auto-update without prompting | Issue explicitly requests automatic behavior; submodule updates are safe pointer changes |
| 2026-02-23 | Commit submodule update in startup | The agentic loop needs a clean git state; the pointer change should be committed |
