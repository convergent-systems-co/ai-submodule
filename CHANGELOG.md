# Changelog

All notable changes to the Dark Forge are documented here.

This project uses [Conventional Commits](https://www.conventionalcommits.org/) and [Keep a Changelog](https://keepachangelog.com/) conventions.

---

## [Unreleased]

### Added

- **MIT License** — Repository is now MIT-licensed
- **Project Manager persona** (#464) — Opt-in portfolio-level orchestrator (`governance.use_project_manager: true`) implementing multiplexed Team Leads for higher throughput. 7-agent architecture: Project Manager, DevOps Engineer, Team Lead, Coder, IaC Engineer, Tester, Document Writer
- **Developer prompt library** (#469) — 12 production-ready global prompts in `prompts/global/` covering code review, debugging, PR creation, refactoring, test writing, and more
- **Prompt catalog system** — Auto-generated `catalog/prompt-catalog.json` with SHA-256 hashes and git timestamps; `bin/generate-prompt-catalog.py` generator; `prompt-catalog.yml` CI workflow for regeneration on push; `prompt-catalog.schema.json` validation schema
- **Skills system** — `.skill.md` format in `mcp-server/skills/` with Zod validation and MCP tool registration; initial `governance-review` skill
- **MCP server enhancements** — Hybrid fetch system, IDE auto-installer (`install.sh`/`install.ps1` for Claude Code, VS Code, Cursor), new CLI options (`--no-cache`, `--refresh`, `--validate-hash`, `--offline`), Docker support
- **Agentic CI workflows** — `agentic-issue-worker.yml` (CI-native issue-to-PR pipeline with complexity assessment, plan generation, and human feedback via `/agentic-retry:`) and `agentic-loop.yml` (reusable AI convergence loop with checkpoint/resume, judge evaluation, and manifest logging)
- **Self-repair workflows** — `auto-rebase.yml` (keep agent PRs rebased on main, runs on push and every 6 hours), `branch-cleanup.yml` (delete merged/stale branches weekly), `self-repair-lint.yml` (detect actionlint errors and create remediation issues)
- **Publishing workflows** — `prompt-catalog.yml` (regenerate prompt catalog on prompt changes), `publish-mcp.yml` (publish MCP server to npm and Docker on release)
- **Retroactive ADRs** — 5 architectural decision records in `docs/decisions/`: deterministic policy engine (001), panel-based review system (002), agent persona model (003), submodule distribution (004), JIT context management (005)
- **Documentation** — `docs/guides/project-yaml-configuration.md` (complete project.yaml reference), `docs/architecture/ci-workflows.md` (all 16 workflows), `docs/guides/prompt-library.md` (prompt catalog guide), `docs/guides/skills-development.md` (skills system guide)

### Removed

- **78 deprecated persona and panel files removed** (#257)
  - 58 individual persona files across 13 category directories (`architecture/`, `compliance/`, `documentation/`, `domain/`, `engineering/`, `finops/`, `governance/`, `language/`, `leadership/`, `operations/`, `platform/`, `quality/`, `specialist/`)
  - 19 panel files from `governance/personas/panels/`
  - `governance/personas/index.md` persona reference grid
  - Consolidated review prompts at `governance/prompts/reviews/` are the canonical location
  - Agentic personas (`governance/personas/agentic/`) are preserved (6 files)
  - All documentation references updated to point to `governance/prompts/reviews/`

### Breaking Changes

- **`init.sh` and `init.ps1` moved to `bin/`** (#226)
  - Old path: `bash .ai/init.sh` / `powershell -File .ai\init.ps1`
  - New path: `bash .ai/bin/init.sh` / `powershell -File .ai\bin\init.ps1`
  - All consuming repos must update their bootstrap commands after pulling the latest submodule.

### Changed

- **Documentation reorganization** (#226)
  - All documentation from `governance/docs/` moved to root `docs/` with domain subdirectories
  - New structure: `docs/{architecture,configuration,decisions,governance,onboarding,operations,research,tutorials}/`
  - `DEVELOPER_GUIDE.md` moved to `docs/onboarding/developer-guide.md` (symlink at root for backward compatibility)
  - `docs/README.md` added as navigation hub

- **Root filesystem cleanup** (#222)
  - `scripts/` directory removed — `issue-monitor.sh` and `issue-monitor.ps1` moved to `bin/`
  - `docs/onboarding/` HTML guides moved under `docs/onboarding/`
  - `TECHNIQUE_COMPARE.md` moved to `docs/research/technique-comparison.md`

- **Multi-agent prompt-chained architecture** (#228)
  - New agentic personas: DevOps Engineer (session entry/routing) and Tester (independent evaluation)
  - New inter-agent communication protocol (`governance/prompts/agent-protocol.md`) with typed messages
  - `startup.md` rewritten as 5-phase prompt-chained orchestrator (577→404 lines)
  - Team Lead updated: Orchestrator-Workers pattern, Tester approval gate, dynamic panel selection, security review gate
  - Coder updated: structured RESULT output, cannot-self-approve constraint
  - Security review is now a mandatory gate after Tester approval, always producing a JSON report
  - Team Lead dynamically selects context-appropriate review panels (docs, API, infrastructure, etc.)
  - All ASCII art diagrams converted to Mermaid
  - If a needed panel/persona is missing, Team Lead creates an issue in Dark Forge

- **Persona consolidation** (#220)
  - 19 consolidated review prompts added to `governance/prompts/reviews/`
  - Individual persona files in `governance/personas/` and panel files in `governance/personas/panels/` are now deprecated
  - New `governance/prompts/shared-perspectives.md` provides canonical definitions for cross-cutting perspectives
  - See `docs/research/README.md` for the research supporting this decision
