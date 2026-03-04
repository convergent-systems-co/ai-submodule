# Plan: Integrate Agentic Agent Dispatch into Python Orchestrator Engine

**Issue:** #675
**Type:** feat
**Status:** in-progress

## Objective

Move agent dispatch validation and state tracking into the Python orchestrator engine so dispatch rules are enforced programmatically rather than relying on prompt instructions alone.

## Deliverables

1. `governance/engine/orchestrator/dispatch_validator.py` - Validation functions for dispatch tasks
2. `governance/engine/orchestrator/dispatch_state.py` - State tracking enum, dataclass, and tracker
3. Extend `dispatcher.py` ABC with optional validation and state query methods
4. Integrate validator into `claude_code_dispatcher.py` dispatch flow
5. Wire validation into `step_runner.py` Phase 3 flow
6. Add `dispatch_state` to `session.py` for persistence
7. Add `require_worktree` field to `DispatchInstruction` in `step_result.py`
8. Tests for dispatch_validator and dispatch_state

## Design Decisions

- New ABC methods have default implementations for backward compatibility
- Validation is composable: individual validators can be called separately or via `validate_dispatch()`
- DispatchState enum follows existing `AgentPersona` Enum pattern
- DispatchTracker serializes to/from dict for session persistence
- Validation errors are returned (not raised) for orchestrator control flow
