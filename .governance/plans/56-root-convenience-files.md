# Add Root-Level init.md and startup.md Convenience Files

**Author:** Code Manager (agentic)
**Date:** 2026-02-21
**Status:** completed
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/56
**Branch:** itsfwcp/feat/56/root-convenience-files

---

## 1. Objective

Add root-level `startup.md` and `init.md` files as convenience entry points to governance prompts for easier discoverability.

## 2. Rationale

The governance prompts are nested under `governance/prompts/` which makes them less discoverable. Root-level files provide immediate entry points for agents and developers.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Symlinks | Yes | Git doesn't track symlinks well across platforms; some tools don't follow them |
| Re-export files with include directives | Yes | Markdown has no include mechanism |
| Thin wrapper files that reference the source | Yes | Selected — clear, portable, no duplication |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `startup.md` | Root-level reference to `governance/prompts/startup.md` |
| `init.md` | Root-level bootstrap/setup guide referencing `init.sh` and governance structure |

### Files to Modify

None. The acceptance criteria mention updating config.yaml for symlink strategy, but we're using thin wrapper files instead, so no config.yaml change is needed.

### Files to Delete

None.

## 4. Approach

1. Create `startup.md` at root that references `governance/prompts/startup.md`
2. Create `init.md` at root with bootstrap instructions and a reference to `init.sh`

## 5. Testing Strategy

N/A — documentation-only files.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Confusion about which startup.md is canonical | Low | Low | Clear header in root file pointing to source |

## 7. Dependencies

None.

## 8. Backward Compatibility

Fully additive.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| documentation-review | Yes | New documentation files |

**Policy Profile:** default
**Expected Risk Level:** negligible

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-21 | Use thin wrapper files instead of symlinks | Better cross-platform compatibility |
