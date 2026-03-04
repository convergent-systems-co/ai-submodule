# Plan: Add coder_min/coder_max config and mandatory worktree isolation (#548)

## Problem

The current `parallel_coders` is a single number. Need min/max range and enforcement that coders ALWAYS work in worktrees (primary repo stays on main).

## Changes

1. **governance/schemas/project.schema.json** - Add `coder_min`, `coder_max`, `require_worktree` to governance object
2. **governance/engine/orchestrator/config.py** - Add fields to `OrchestratorConfig`, validate min <= max, load from YAML
3. **governance/engine/orchestrator/step_runner.py** - Include coder scaling config in Phase 3 instructions
4. **governance/prompts/startup.md** - Document coder_min/coder_max/require_worktree in Phase 3
5. **docs/architecture/agent-architecture.md** - Add coder scaling and worktree requirements section

## Validation

- coder_min <= coder_max enforced at config load (unless coder_max is -1)
- All existing tests pass unchanged
- Phase 3 dispatch instructions include coder_min, coder_max, require_worktree
