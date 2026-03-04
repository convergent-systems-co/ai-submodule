# Visual Workload Tree Command

**Author:** Code Manager (Claude)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #671
**Branch:** itsfwcp/feat/671/workload-tree-command

---

## 1. Objective

Add `python -m governance.engine.orchestrator tree` CLI command that outputs the current agent topology with issue assignments, PR status, and config-driven scaling info.

## 2. Rationale

No visibility into what agents are doing during parallel dispatch. The `status` command shows phase/tier but not agent assignments. A tree command provides the missing observability.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Add tree to existing status command | Yes | Status is already dense; tree deserves its own command |
| External dashboard | Yes | Over-engineered for CLI tool |
| CLI tree command | Yes | Selected — fits existing patterns, JSON output |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/engine/orchestrator/tree.py` | Tree builder: takes session + dispatcher state, produces structured tree dict |
| `governance/engine/tests/test_tree.py` | Unit tests for tree builder |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/engine/orchestrator/__main__.py` | Add `tree` subparser and `_cmd_tree()` handler |
| `governance/engine/orchestrator/step_runner.py` | Add `get_workload_tree() -> dict` method that queries dispatcher + session |

### Files to Delete

None.

## 4. Approach

1. Create `tree.py` with `build_tree(session, dispatcher, config) -> dict` function:
   - Reads dispatched task instructions and results from dispatcher
   - Groups by persona
   - Adds config context (parallel_coders, coder_min/max)
   - Includes summary stats
   - Renders ASCII tree string for terminal output
2. Add `get_workload_tree()` to `StepRunner` that calls the tree builder
3. Add `tree` subparser and `_cmd_tree` handler in `__main__.py`
4. Write unit tests covering: empty session, standard mode flat tree, various task states
5. JSON output includes both structured data and rendered ASCII string

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | tree.py | Empty session, populated session, various persona combos |
| Unit | tree.py | ASCII rendering matches expected format |
| Existing | All tests | No regressions |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Dispatcher not initialized | Low | Low | Handle gracefully with empty tree |
| Session state missing fields | Low | Low | Default to empty lists |

## 7. Dependencies

None.

## 8. Backward Compatibility

Additive change only — new command, no existing behavior modified.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New engine module |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | MVP flat tree for standard mode first | PM hierarchy tracking is a separate concern (#652) |
