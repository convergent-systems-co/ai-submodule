# Plan: Cross-session work locking (#762)

## Summary

Implement a lock manager that prevents multiple concurrent orchestrator sessions from claiming the same GitHub issue. Uses advisory file locking (fcntl.flock) for TOCTOU safety.

## Scope

1. **Lock file schema** -- JSON lock files in `~/.local/state/dark-governance/locks/issues/` containing issue number, session ID, heartbeat timestamp, TTL
2. **LockManager class** -- Core class with `claim()`, `release()`, `heartbeat()`, `is_stale()`, `list_claimed()` methods
3. **Phase 1 filtering** -- During triage, `filter_claimed_issues()` excludes issues already claimed by other active sessions
4. **Heartbeat** -- Active sessions update lock timestamps. Locks expire after TTL (default 1 hour).
5. **CLI command** -- `python3 -m governance.engine.orchestrator locks` to inspect active locks
6. **Tests** -- Comprehensive unit tests for all lock manager methods

## Files

| File | Action |
|------|--------|
| `governance/engine/orchestrator/lock_manager.py` | **Create** -- LockManager class |
| `governance/engine/orchestrator/__init__.py` | **Modify** -- Export LockManager |
| `governance/engine/orchestrator/__main__.py` | **Modify** -- Add `locks` CLI command |
| `governance/engine/orchestrator/step_runner.py` | **Modify** -- Integrate lock filtering in phase 1 |
| `governance/engine/tests/test_lock_manager.py` | **Create** -- Unit tests |
| `governance/schemas/work-lock.schema.json` | **Create** -- JSON Schema for lock files |

## Design

- Uses `fcntl.flock` for advisory file locking (Unix) with fallback for Windows
- Lock directory defaults to XDG state path from `storage.py`
- StorageAdapter not used for locks (advisory locking needs direct file I/O)
- Backward compatible: single-session repos see no behavioral change
- TTL default: 3600 seconds (1 hour)
