# Changelog

All notable changes to the Dark Factory Governance Platform are documented here.

This project uses [Conventional Commits](https://www.conventionalcommits.org/) and [Keep a Changelog](https://keepachangelog.com/) conventions.

---

## [Unreleased]

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
  - Code Manager updated: Orchestrator-Workers pattern, Tester approval gate, dynamic panel selection, security review gate
  - Coder updated: structured RESULT output, cannot-self-approve constraint
  - Security review is now a mandatory gate after Tester approval, always producing a JSON report
  - Code Manager dynamically selects context-appropriate review panels (docs, API, infrastructure, etc.)
  - All ASCII art diagrams converted to Mermaid
  - If a needed panel/persona is missing, Code Manager creates an issue in ai-submodule

- **Persona consolidation** (#220)
  - 19 consolidated review prompts added to `governance/prompts/reviews/`
  - Individual persona files in `governance/personas/` and panel files in `governance/personas/panels/` are now deprecated
  - New `governance/prompts/shared-perspectives.md` provides canonical definitions for cross-cutting perspectives
  - See `docs/research/README.md` for the research supporting this decision
