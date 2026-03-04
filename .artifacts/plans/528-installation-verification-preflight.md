# Installation Verification & Pre-flight Checks

**Author:** Team Lead (agentic)
**Date:** 2026-02-27
**Status:** approved
**Issue:** #528 — After "installation" regardless of method (AI Prompt - preferred)
**Branch:** NETWORK_ID/feat/528/installation-verification-preflight

---

## 1. Objective

Create a comprehensive post-installation verification system that validates the dark-forge is correctly installed in any consuming repository, regardless of installation method (quick-install, init.sh, or agentic init.md). Add a `--verify` flag to `init.sh` that checks all critical installation criteria: project.yaml configuration, symlinks, slash commands, governance directories, and workflow presence. Update the Developer Guide to document every slash command with its purpose and usage.

## 2. Rationale

Currently, `init.sh` creates resources but does not provide a single verification entry point. If a developer accidentally deletes a symlink, removes a workflow, or corrupts their project.yaml, there is no way to diagnose the problem short of re-running the full init. A dedicated `--verify` mode provides fast, non-destructive diagnostics.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Separate verify script | Yes | Increases file count; init.sh already has the modular architecture to support another mode |
| Python-based verifier | Yes | Adds dependency; shell-based verification keeps the same zero-dependency model as init.sh |
| Verify as part of --refresh | Yes | --refresh makes changes; verify should be read-only for diagnostics |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/bin/verify-installation.sh` | Modular verification script called by init.sh --verify |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `bin/init.sh` | Add `--verify` flag routing to `governance/bin/verify-installation.sh` |
| `DEVELOPER_GUIDE.md` | Add "Slash Commands & Skills" section documenting all commands with usage |
| `docs/onboarding/developer-guide.md` | Mirror the same updates (keep in sync) |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No deletions |

## 4. Approach

1. **Create `governance/bin/verify-installation.sh`** — A read-only diagnostic script that checks:
   - Git repository detection (`git rev-parse --is-inside-work-tree`)
   - `.ai` submodule presence and state (submodule context only)
   - `project.yaml` existence and basic structure (checks for `name`, `language`, `governance` keys)
   - Symlinks: CLAUDE.md → .ai/instructions.md, .github/copilot-instructions.md → .ai/instructions.md
   - Slash commands directory: `.claude/commands/` exists with expected command files (startup.md, checkpoint.md, threat-model.md)
   - Governance directories: `.governance/plans/`, `.governance/panels/`, `.governance/checkpoints/`, `.governance/state/`
   - Governance workflow: `.github/workflows/dark-factory-governance.yml` existence
   - CODEOWNERS presence
   - Output: structured pass/fail/warn report with remediation hints

2. **Update `bin/init.sh`** — Add `--verify` to the help text and flag parsing; route to `governance/bin/verify-installation.sh`

3. **Update Developer Guide** — Add a "Slash Commands & Skills" section that documents:
   - `/startup` — purpose, what it does, when to use it
   - `/checkpoint` — purpose, what it does, when to use it
   - `/threat-model` — purpose, modes (system, pr, pr=N), output
   - MCP skills: `governance-review`, `ado`

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | verify-installation.sh functions | Test each check independently using mock file structures |
| Integration | init.sh --verify | Run against the dark-forge repo itself to validate end-to-end |
| Manual | Consumer repo | Verify the script works when .ai is a submodule |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Script fails in non-submodule context | Low | Low | Detect context early and skip submodule-specific checks |
| Missing checks give false confidence | Med | Med | Start with critical checks; expand over time |
| Breaking existing --refresh behavior | Low | High | --verify is additive; does not modify existing flags |

## 7. Dependencies

- [x] No blocking dependencies — uses existing shell infrastructure

## 8. Backward Compatibility

Fully backward compatible. The `--verify` flag is additive. No existing behavior is modified.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Shell script security (injection, path traversal) |
| documentation-review | Yes | Developer Guide changes |
| code-review | Yes | Shell scripting quality |
| cost-analysis | Yes | Default policy |
| threat-modeling | Yes | Default policy |
| data-governance-review | Yes | Default policy |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Use shell-based verification over Python | Keeps zero-dependency model consistent with init.sh |
| 2026-02-27 | Read-only --verify separate from --refresh | Verify is diagnostic; refresh makes changes |
