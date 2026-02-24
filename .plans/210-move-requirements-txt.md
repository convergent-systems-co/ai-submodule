# Move requirements.txt to .governance directory

**Author:** Code Manager (agentic)
**Date:** 2026-02-24
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/210
**Branch:** itsfwcp/fix/210/move-requirements-txt

---

## 1. Objective

Move `requirements.txt` from the repository root to `.governance/` so Python dependencies are co-located with the Python code (`policy-engine.py`) that uses them.

## 2. Rationale

The `requirements.txt` at the repo root is a project hygiene issue — it belongs next to the Python code it supports. The `.governance/` directory contains `policy-engine.py`, which is the sole consumer of these dependencies.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Move to `.governance/` | Yes | Selected approach |
| Keep at root | Yes | Issue explicitly says it should not be in the root |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.governance/requirements.txt` | Python dependencies (moved from root) |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `init.sh` | Update `REQUIREMENTS` variable path from `$SCRIPT_DIR/requirements.txt` to `$SCRIPT_DIR/.governance/requirements.txt`; update error message |
| `init.ps1` | Update `$RequirementsFile` path from `Join-Path $ScriptDir "requirements.txt"` to `Join-Path $ScriptDir ".governance\requirements.txt"` |
| `governance/prompts/init.md` | Update pip install path from `.ai/requirements.txt` to `.ai/.governance/requirements.txt` |

### Files to Delete

| File | Reason |
|------|--------|
| `requirements.txt` (root) | Moved to `.governance/requirements.txt` |

## 4. Approach

1. Move `requirements.txt` to `.governance/requirements.txt`
2. Update the internal comment in the file to reflect new path
3. Update `init.sh` `REQUIREMENTS` variable
4. Update `init.ps1` `$RequirementsFile` variable
5. Update `governance/prompts/init.md` pip install reference
6. Verify no other references are broken

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | init.sh path resolution | Verify `REQUIREMENTS` variable resolves correctly |
| Manual | init.ps1 path resolution | Verify `$RequirementsFile` resolves correctly |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Consuming repos break if they reference the old path directly | Low | Low | The old path was internal to the submodule; consuming repos use `init.sh --install-deps` |

## 7. Dependencies

- None

## 8. Backward Compatibility

Consuming repos that run `bash .ai/init.sh --install-deps` will work without changes — the path is resolved internally by the script. No external API changes.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | File move + script updates |
| security-review | Yes | Default required |
| documentation-review | Yes | Path references in docs |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Move to `.governance/` rather than creating a new directory | Co-locate with `policy-engine.py`, the sole consumer |
