# DevOps Engineer Auto-Spawn in PM Mode

**Author:** Code Manager (Claude)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #652
**Branch:** itsfwcp/fix/652/devops-auto-spawn-pm-mode

---

## 1. Objective

Make the orchestrator auto-spawn a DevOps Engineer as a background agent when PM mode is active, and cleanly separate Code Manager (plan+dispatch+create PR) from DevOps Engineer (review+merge+monitor) responsibilities.

## 2. Rationale

The orchestrator has `use_project_manager` config but never checks it to alter phase behavior. All PM-mode persona docs and protocols exist — only the step_runner routing is missing. Without this, PRs accumulate unmerged and no governance panels run on them.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add merge logic to Code Manager | Yes | Violates separation of concerns; Code Manager should move on to next issue |
| Manual DevOps spawn in startup.md instructions | Yes | LLM-interpreted, not enforced by engine |
| Engine-level PM-mode routing in step_runner | Yes | Selected — deterministic, config-driven |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/prompts/devops-operations-loop.md` | Standalone prompt for DevOps background loop covering all 11 responsibilities |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/engine/orchestrator/step_runner.py` | Add PM-mode branching: check `config.use_project_manager` in `_next_phase()` and `_build_phase_result()`. Phase 1 returns DevOps Task when PM mode active. Phase 2 dispatches Code Managers instead of Coders. |
| `governance/personas/agentic/code-manager.md` | Remove review, merge, monitoring, Copilot, and panel responsibilities. Scope to: plan + dispatch + create PR. |
| `governance/personas/agentic/devops-engineer.md` | Add explicit post-PR lifecycle responsibilities (11 items from issue). |
| `governance/prompts/startup.md` | Add note that PM mode triggers DevOps auto-spawn via orchestrator. |
| `docs/architecture/project-manager-architecture.md` | Update to reflect the clean responsibility separation. |

### Files to Delete

None.

## 4. Approach

1. Update `step_runner.py` `_build_phase_result()`: when `config.use_project_manager` and phase == 1, include a DevOps Engineer task in the dispatch instructions with `run_in_background: true`
2. Update `step_runner.py` `_next_phase()`: when PM mode, route Phase 1 → Phase 2 (Code Manager dispatch) instead of Phase 2 → Phase 3 (Coder dispatch)
3. Update `step_runner.py` Phase 3 result: when PM mode, tasks are Code Manager agents (not Coders)
4. Create `governance/prompts/devops-operations-loop.md` with the full background loop
5. Update Code Manager persona: remove post-PR responsibilities
6. Update DevOps Engineer persona: add explicit post-PR lifecycle
7. Update startup.md and PM architecture docs

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | step_runner.py | Test PM-mode phase routing with `use_project_manager=True` |
| Unit | step_runner.py | Test standard mode unchanged when `use_project_manager=False` |
| Existing | All 1719 tests | Verify no regressions |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking standard mode | Low | High | All changes gated behind `config.use_project_manager` |
| DevOps loop runs forever | Medium | Medium | Circuit breaker limits apply |

## 7. Dependencies

None.

## 8. Backward Compatibility

All changes gated behind `use_project_manager: true` (default: false). Standard mode is unchanged.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Engine logic changes |
| security-review | Yes | Agent dispatch changes |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Gate all changes behind use_project_manager flag | Zero risk to standard mode |
