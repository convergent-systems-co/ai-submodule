# Orchestrator PM Mode Agent Topology Enforcement

**Author:** Project Manager (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #687
**Branch:** itsfwcp/feat/687/pm-mode-enforcement

---

## 1. Objective

Add agent registration to the orchestrator so it can validate that required agents were spawned before allowing phase transitions. The `tree` command should show the actual agent topology.

## 2. Rationale

The engine currently returns PM mode instructions but has no enforcement. The LLM may skip spawning required agents.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Trust the LLM to follow instructions | Current state | Unreliable — observed failures |
| Add `register` CLI subcommand | Yes — chosen | Clean, explicit registration |
| Embed in step result parsing only | Yes | Less explicit, harder to validate |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/engine/orchestrator/agent_registry.py` | AgentRegistry class — track spawned agents, validate topology |
| `governance/engine/tests/test_agent_registry.py` | Tests for agent registry |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/engine/orchestrator/__main__.py` | Add `register` subcommand |
| `governance/engine/orchestrator/step_runner.py` | Validate agent topology before phase transitions |
| `governance/engine/orchestrator/session.py` | Persist agent registry in session state |
| `governance/engine/orchestrator/tree.py` | Build agent nodes from registry |

## 4. Approach

1. Create `AgentRegistry` class (similar pattern to CircuitBreaker)
2. Add `register` CLI subcommand
3. Add phase transition validation in step_runner
4. Update tree command to show registered agents
5. Persist registry in session state

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | agent_registry.py | Registration, validation, serialization |
| Unit | step_runner.py | Phase transition blocks without required agents |
| Unit | tree.py | Agent nodes populated from registry |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaks existing non-PM sessions | Low | High | Only enforce when use_project_manager=true |

## 7. Dependencies

- [ ] None

## 8. Backward Compatibility

Non-PM mode sessions unaffected. PM mode now requires explicit agent registration.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New engine module |
| architecture-review | Yes | New subsystem |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Separate AgentRegistry module | Follows CircuitBreaker pattern |
