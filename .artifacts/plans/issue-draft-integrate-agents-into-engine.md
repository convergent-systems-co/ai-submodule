# Issue Draft: Integrate Agentic Agent Dispatch into Python Orchestrator Engine

**Type:** enhancement
**Priority:** high

## Title
feat: integrate agentic agent dispatch into Python orchestrator engine

## Body

### Summary

Currently, the orchestrator CLI (`governance.engine.orchestrator`) is a step function that tells the LLM *what* to do, but the actual agent dispatch (spawning Coder agents, Document Writer agents, etc.) happens outside the engine — the LLM interprets orchestrator output and uses Claude Code's Agent tool. This means:

1. Agent dispatch is not deterministic or reproducible
2. The orchestrator can't enforce dispatch rules (worktree isolation, coder scaling) at runtime
3. If the parent LLM's context resets mid-dispatch, agent state is lost
4. No programmatic control over agent lifecycle

### Proposed Change

Integrate agent dispatch directly into the Python orchestrator engine so that:
- The engine spawns and manages sub-agents programmatically
- Dispatch rules (coder_min, coder_max, require_worktree) are enforced by code, not LLM interpretation
- Agent results are collected and stored deterministically
- The engine can monitor agent health and enforce timeouts

### Acceptance Criteria

- [ ] Orchestrator engine can dispatch Coder agents programmatically
- [ ] Worktree isolation is enforced by the engine (not relying on LLM)
- [ ] Agent results are collected and persisted to session state
- [ ] Engine enforces coder_min/coder_max scaling limits
- [ ] Existing CLI step-function interface remains backward compatible
