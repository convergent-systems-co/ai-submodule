# Command/Prompt Install

**Author:** Code Manager (agentic)
**Date:** 2026-02-23
**Status:** in_progress
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/109
**Branch:** itsfwcp/feat/109/command-prompt-install

---

## 1. Objective

Create an agentic-readable `init.md` prompt that AI agents (Claude Code, GitHub Copilot, Cursor) can read and execute to bootstrap the `.ai` submodule in a consuming project. This complements the existing `init.sh`/`init.ps1` shell scripts with an interactive, agent-driven installation path that asks the user about configuration options.

## 2. Rationale

The existing shell scripts (`init.sh`, `init.ps1`) handle installation from the command line but require the user to know which flags to pass and which template to choose. An agentic prompt (`init.md`) allows the user to simply tell their AI assistant "run @init.md" or "install the .ai submodule" and have the agent walk them through setup interactively — asking about auto-merge preferences, language templates, and other options.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Replace init.sh with init.md entirely | Yes | Shell scripts are still needed for CI and non-agentic contexts |
| Create install.md separately from init.md | Yes | Inconsistency — the issue prefers `init.md` for naming consistency with `init.sh`/`init.ps1` |
| Add interactive prompts to init.sh | Yes | Shell-based interactivity is fragile; agents handle multi-step Q&A natively |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/prompts/init.md` | Agentic installation prompt — AI agents read and execute this to bootstrap the submodule |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `CLAUDE.md` (root) | Add reference to `init.md` as an installation method |
| `.ai/CLAUDE.md` | Add `init.md` to the Repository Commands section alongside `init.sh` |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files to delete |

## 4. Approach

1. **Create `governance/prompts/init.md`** with the following sections:
   - Pre-flight: Detect if `.ai` submodule exists, if symlinks are already configured
   - Step 1: Ask the user which language template to use (python, node, react, go, csharp, or skip)
   - Step 2: Ask about repository configuration options (auto-merge, delete branch on merge)
   - Step 3: Execute symlink creation (same operations as init.sh)
   - Step 4: Copy the selected language template to `project.yaml`
   - Step 5: Apply repository settings via `gh api` (if user opted in)
   - Step 6: Generate CODEOWNERS (if applicable)
   - Step 7: Install Python dependencies (if user wants to run the policy engine)
   - Post-flight: Verify setup and print next steps

2. **Update documentation** in both CLAUDE.md files to reference the new `init.md` prompt.

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | init.md | Read through prompt, verify each step is executable by an AI agent |
| Manual | Idempotency | Verify the prompt handles "already configured" scenarios gracefully |

Note: Config-only repo with no test framework. Manual verification of prompt correctness is appropriate.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Prompt instructions diverge from init.sh behavior | Medium | Medium | Reference init.sh operations explicitly; note that init.sh is the canonical implementation |
| Agent misinterprets prompt steps | Low | Low | Use clear, numbered steps with explicit commands |
| Prompt grows stale as init.sh evolves | Medium | Low | Add a note in init.md referencing init.sh as the source of truth |

## 7. Dependencies

- [x] No blocking dependencies — additive change

## 8. Backward Compatibility

Fully backward compatible. This adds a new file and updates documentation. No existing behavior is changed. `init.sh` and `init.ps1` continue to work as before.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New prompt file needs review for correctness |
| documentation-review | Yes | Documentation updates in CLAUDE.md |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-23 | Place in `governance/prompts/init.md` | Consistent with other agentic prompts in `governance/prompts/` |
| 2026-02-23 | Complement, not replace, shell scripts | Shell scripts serve CI and non-agentic workflows |
| 2026-02-23 | Interactive options via agent Q&A | Agents handle multi-step configuration better than shell flags |
