# Symlink .claude/commands/ to Consuming Repos

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/524
**Branch:** itsfwcp/fix/524/symlink-claude-commands

---

## 1. Objective

Fix `governance/bin/create-symlinks.sh` to symlink `.claude/commands/` from the `.ai` submodule into consuming project roots, making slash commands (`/startup`, `/checkpoint`, `/threat-model`) automatically available.

## 2. Rationale

Claude Code discovers slash commands at `<project-root>/.claude/commands/`. The submodule ships commands at `.ai/.claude/commands/` but `create-symlinks.sh` only creates symlinks for `CLAUDE.md` and `copilot-instructions.md`. Without this fix, consuming repos must manually set up the symlink.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Manual symlink in docs | Yes | Error-prone, not automated |
| Copy files instead of symlink | Yes | Would desync on submodule updates |
| Symlink in create-symlinks.sh | Yes (selected) | Follows existing pattern, idempotent, auto-updates |

## 3. Scope

### Files to Create

None.

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/bin/create-symlinks.sh` | Add symlink block for `.claude/commands/` |
| `config.yaml` | Add `.claude/commands` symlink entry for documentation/consistency |

### Files to Delete

None.

## 4. Approach

1. Add a new block to `governance/bin/create-symlinks.sh` that:
   - Checks if `.ai/.claude/commands/` exists (guard: only activate when submodule provides commands)
   - Creates `.claude/` directory if needed (preserving existing files like `settings.local.json`)
   - Creates symlink `.claude/commands` → `../.ai/.claude/commands` if not already linked
   - Uses `run_cmd` wrapper for dry-run support
   - Is idempotent (re-running is safe)

2. Update `config.yaml` to document the commands symlink

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Script execution | Run `bash governance/bin/create-symlinks.sh` and verify symlink created |
| Idempotency | Re-run | Run twice, verify no errors or changes on second run |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Overwrite existing .claude/commands dir | Low | Medium | Check if target exists and is not a symlink before creating |
| Break existing .claude/ contents | Low | Low | mkdir -p preserves existing files |

## 7. Dependencies

- [x] `.claude/commands/` directory exists in submodule — confirmed

## 8. Backward Compatibility

Fully additive. Existing repos without `.ai/.claude/commands/` are unaffected (guard check). Repos with existing `.claude/` directories are preserved (mkdir -p).

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | Script modification |
| security-review | Yes | Always required |
| documentation-review | Yes | Config updated |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Symlink entire directory, not individual files | Auto-discovers new commands on submodule update |
