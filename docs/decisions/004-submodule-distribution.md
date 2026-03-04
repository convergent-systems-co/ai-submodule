# ADR-004: Git Submodule Distribution Model

**Status:** Accepted
**Date:** 2024-06-01 (retroactive)
**Author:** Dark Forge Team

---

## Context

The Dark Forge needed a distribution mechanism to deliver governance artifacts (policies, schemas, personas, review prompts, workflows) to consuming repositories. The mechanism had to satisfy several constraints:

1. **Atomic versioning** -- all governance artifacts must move together; partial updates create inconsistent state
2. **Read-only enforcement** -- consuming repositories must not modify governance artifacts; local modifications would cause drift and compliance failures
3. **Zero build step** -- the governance framework contains no application code, so npm/pip packaging adds unnecessary complexity
4. **Transparent updates** -- teams should be able to update governance with a single command
5. **Separation of mutable and immutable** -- governance definitions (read-only, from the framework) must be cleanly separated from governance state (mutable, per-project: plans, panel reports, checkpoints)

The consuming repository's filesystem needed a clear boundary: `.ai/` for read-only governance sources and `.artifacts/` for mutable project-specific state.

## Decision

Distribute the governance platform as a git submodule mounted at `.ai/` in consuming repositories. Bootstrap via `bin/init.sh`, which creates symlinks, project directories, and validates configuration.

The distribution model works as follows:

- **Installation**: `git submodule add git@github.com:convergent-systems-co/dark-forge.git .ai`
- **Updates**: `git submodule update --remote .ai` (or automatic via `init.sh` freshness check)
- **Bootstrap**: `bash .ai/bin/init.sh` creates symlinks (`CLAUDE.md`, `.github/copilot-instructions.md`), project directories (`.artifacts/plans/`, `.artifacts/panels/`, `.artifacts/checkpoints/`, `.artifacts/state/`), and validates required panel emissions
- **Quick install**: `curl -sSL https://raw.githubusercontent.com/.../quick-install.sh | bash` for new projects

The submodule pin in the consuming repo's `.gitmodules` and commit SHA provide version control. Teams can pin to a specific governance version or track the latest.

## Consequences

### Positive

- Atomic updates: `git submodule update --remote` pulls all governance artifacts in a single operation
- Natural read-only enforcement: submodule contents are tracked by SHA; local modifications show as dirty state and are overwritten on update
- Clear filesystem boundary: `.ai/` (read-only governance) vs. `.artifacts/` (mutable project state)
- No package registry, no build step, no dependency resolution -- git is the only requirement
- Version pinning via git SHA: consuming repos control exactly which governance version they use
- Framework changes propagate to all consuming repos when they update the submodule

### Negative

- Git submodules have a steeper learning curve than package managers; developers unfamiliar with submodules may encounter confusion
- `init.sh` must handle edge cases: SSH-to-HTTPS conversion, stale submodule state, missing `.gitmodules`, branch protection detection
- Framework bugs cascade to every consuming repo simultaneously upon update (no staged rollout without explicit SHA pinning)
- Submodule updates create noisy commits (SHA pointer change) in consuming repos

### Neutral

- The symlink strategy (`instructions.md` -> `CLAUDE.md`, `.github/copilot-instructions.md`) ensures both Claude Code and GitHub Copilot receive identical base instructions, but relies on filesystem symlink support
- The `--refresh` flag on `init.sh` exists specifically because the agentic startup loop needs to re-apply structural setup after every submodule state check without re-running the full freshness logic

## Alternatives Considered

| Alternative | Reason Rejected |
|-------------|----------------|
| npm/pip package | Adds build step and package registry dependency; governance artifacts are not code libraries; version resolution adds complexity with no benefit |
| Monorepo (governance + application code) | Violates separation of concerns; governance framework serves multiple consuming repos; coupling to one repo prevents reuse |
| Template repository (GitHub template) | One-time copy with no update mechanism; governance drift is guaranteed as the template evolves |
| Copy-paste / vendoring | No atomic updates; partial copies create inconsistent state; no mechanism to detect or prevent local modifications |
| Git subtree | Merge-based workflow pollutes consuming repo history; harder to identify governance vs. application commits; no clean read-only boundary |

## References

- `bin/init.sh` -- bootstrap orchestrator (~165 lines, delegates to modular scripts)
- `governance/bin/` -- modular setup scripts invoked by `init.sh`
- `config.yaml` -- symlink configuration and project directory definitions
- `bin/quick-install.sh` -- one-line installation for new projects
- `docs/configuration/repository-setup.md` -- detailed setup documentation
- `docs/onboarding/project-structure.md` -- filesystem layout explanation
- `docs/decisions/README.md` (ADR-001: Governance-Only Repository) -- the zero-application-code constraint
