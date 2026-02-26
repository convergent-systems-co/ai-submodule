# Plan: Consolidate Python code into governance/engine/ package (#317)

## Objective
Move the policy engine, tests, and dependencies into `governance/engine/` as a proper Python package.

## Changes

1. Created `governance/engine/` package with `__init__.py`
2. Copied `governance/bin/policy-engine.py` to `governance/engine/policy_engine.py` (underscore for import compatibility)
3. Replaced `governance/bin/policy-engine.py` with a thin backward-compatible wrapper
4. Moved all Python test files from `tests/` to `governance/engine/tests/` via `git mv`
5. Updated `conftest.py` to import from `governance.engine.policy_engine` instead of using `importlib` hacks
6. Created `governance/engine/pyproject.toml` with dependencies from `governance/bin/requirements.txt`
7. Updated `bin/init.sh` to prefer `pyproject.toml` over `requirements.txt`
8. Updated CI workflow to install from `pyproject.toml` and run tests from new location
9. Updated `CLAUDE.md`, `README.md`, `governance/bin/README.md`, `governance/prompts/init.md`
10. Updated `tests/bats/test_helper.bash` to include `PYPROJECT` variable

## Backward Compatibility
- `governance/bin/policy-engine.py` still works as an entry point (thin wrapper)
- `governance/bin/requirements.txt` still exists (init.sh falls back to it)
- Bats tests for `init.sh` remain in `tests/bats/`
