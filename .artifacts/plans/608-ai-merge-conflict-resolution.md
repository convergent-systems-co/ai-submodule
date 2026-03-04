# Plan: AI-Based Merge Conflict Resolution (#608)

## Problem
When N parallel Coders work in worktrees and their PRs converge on main, merge conflicts
are inevitable. Currently there is no automated resolution -- conflicts require manual
intervention. DACH's Safe Push pattern provides automated push-retry, rebase, and
AI-assisted conflict resolution that AI-Submodule lacks.

## Solution

### 1. Safe Push Script (`governance/bin/safe-push.sh`)
Bash script implementing the Safe Push pattern:
- Push with retry (3 attempts)
- On rejection: fetch and rebase
- Regenerate known generated files (manifests, catalogs) before AI resolution
- Invoke LLM agent for conflict resolution (model-agnostic via `claude` CLI)
- Containment check: refuse AI resolution on governance-protected files
- `--force-with-lease` as final fallback after rebase
- Full audit trail logged to `.governance/state/conflict-resolutions/`

### 2. Conflict Resolver Engine (`governance/engine/conflict_resolver.py`)
Python module for programmatic conflict resolution:
- Parse git conflict markers from files
- Classify conflicts (generated file, code, governance-protected)
- Invoke LLM for code conflict resolution with structured prompts
- Validate resolution via containment hook
- Emit audit record as JSON

### 3. Tests (`governance/engine/tests/test_conflict_resolver.py`)
- Test conflict marker parsing
- Test file classification (generated, protected, code)
- Test resolution audit trail
- Test containment enforcement (protected files blocked)
- Test resolution strategies (regenerate, ai-resolve, escalate)

### 4. Documentation (`docs/guides/merge-conflict-resolution.md`)
- How the Safe Push pattern works
- Integration with Phase 5 merge workflow
- Protected file handling
- Audit trail format

## Files Changed
- `governance/bin/safe-push.sh` (NEW)
- `governance/engine/conflict_resolver.py` (NEW)
- `governance/engine/tests/test_conflict_resolver.py` (NEW)
- `docs/guides/merge-conflict-resolution.md` (NEW)

## Risk
Low -- additive feature. Does not modify existing merge behavior. Falls back to human
review when AI resolution fails or touches protected files.
