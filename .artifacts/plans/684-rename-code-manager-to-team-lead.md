# Rename Code Manager Persona to Team Lead

**Author:** Project Manager (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #684
**Branch:** itsfwcp/refactor/684/rename-code-manager-team-lead

---

## 1. Objective

Rename "Code Manager" to "Team Lead" across the entire codebase — persona files, engine code, docs, tests, and config.

## 2. Rationale

"Team Lead" better describes the coordination responsibility. Code Managers plan work, dispatch Coders, and create PRs — that's team leadership, not code management.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep Code Manager | Yes | Name is misleading |
| Rename to Team Lead | Yes — chosen | Better reflects the role |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/personas/agentic/team-lead.md` | Renamed from code-manager.md |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/engine/orchestrator/dispatcher.py` | Rename enum CODE_MANAGER → TEAM_LEAD |
| `governance/engine/orchestrator/config.py` | Rename parallel_code_managers → parallel_team_leads (with backward compat) |
| `governance/engine/orchestrator/step_runner.py` | Update PM mode descriptions |
| `governance/engine/orchestrator/claude_code_dispatcher.py` | Update persona path mapping |
| `governance/engine/orchestrator/tree.py` | Update config reference |
| `governance/engine/tests/test_persona_structure.py` | Update expected persona list |
| `project.yaml` | Rename config key (with backward compat) |
| `CLAUDE.md` | Update persona references |
| Multiple docs and prompts | Update "Code Manager" references |

### Files to Delete

| File | Reason |
|------|--------|
| `governance/personas/agentic/code-manager.md` | Replaced by team-lead.md |

## 4. Approach

1. Rename persona file and update all self-references
2. Update Python engine code (enum, config, dispatcher, tree)
3. Add backward compatibility in config loader for `parallel_code_managers`
4. Update project.yaml
5. Grep and fix all doc references
6. Update tests

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | test_persona_structure.py | Verify team-lead.md exists with required sections |
| Unit | test_config.py | Verify both old and new config keys work |
| Integration | Full test suite | All tests pass |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Missing a reference | Medium | Low | Comprehensive grep |
| Breaking config backward compat | Low | High | Loader accepts both keys |

## 7. Dependencies

- [ ] None

## 8. Backward Compatibility

Config loader will accept both `parallel_code_managers` and `parallel_team_leads`, with new key taking precedence.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Engine code changes |
| documentation-review | Yes | Massive doc updates |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Backward compat for config key | Avoid breaking consuming repos |
