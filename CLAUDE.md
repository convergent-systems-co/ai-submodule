# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is the **Dark Factory Governance Platform** — an AI governance framework for autonomous software delivery, distributed as a git submodule to consuming repositories. It contains no application source code; it is entirely configuration, policy, schemas, and documentation.

Current maturity: **Phase 4b (Autonomous Remediation)** — all governance artifacts implemented. Phase 5 sub-phases (5a-5e) are defined with achievability assessments; select 5b artifacts (retrospective aggregation, threshold auto-tuning) are implemented.

## Repository Commands

There is no build system, test runner, or linter. This is a configuration-only repo.

**Bootstrap (for consuming repos):**
```bash
bash .ai/init.sh                    # Symlinks only
bash .ai/init.sh --install-deps     # Symlinks + Python venv + dependencies
```
Checks `.ai` submodule freshness (auto-updates if behind), creates symlinks for CLAUDE.md, .cursorrules, and .github/copilot-instructions.md, and creates `.plans/` and `.panels/` directories for governance artifacts.

**Agentic bootstrap (interactive):**
Tell your AI assistant to read and execute `governance/prompts/init.md`. This walks through setup interactively — choosing a language template, configuring repository settings, and installing dependencies — with the agent asking about each option.

**Submodule operations (from consuming repo):**
```bash
git submodule add git@github.com:SET-Apps/ai-submodule.git .ai
git submodule update --remote .ai
```

## Architecture

### Five Governance Layers

Every code change flows through these layers in order:

1. **Intent** — Design Intent intake, completeness validation, risk classification
2. **Cognitive** — Persona-based reasoning via multi-persona panels producing structured emissions
3. **Execution** — Deterministic policy engine evaluates panel emissions, produces merge decisions
4. **Runtime** (Phase 5) — Drift detection, incident-to-DI generation
5. **Evolution** (Phase 5) — Self-improvement loops with backward compatibility checks

### Three Artifact Types

| Type | Format | Purpose | Mutability |
|------|--------|---------|------------|
| **Cognitive** | Markdown | Personas, prompts, workflows — interpreted by AI | Editable |
| **Enforcement** | JSON Schema / YAML | Policies, schemas — evaluated programmatically, never by AI | Versioned |
| **Audit** | JSON + Markdown | Run manifests — immutable decision records | Append-only |

### Persona and Panel System

- **Personas** (`governance/personas/`) — 60 role definitions across 13 categories. Each defines Role, Evaluate For, Output Format, Principles, Anti-patterns. They are reasoning roles, not model prompts.
- **Panels** (`governance/personas/panels/`) — 16 multi-persona review workflows. Panels coordinate personas and emit structured JSON conforming to `governance/schemas/panel-output.schema.json`.
- **Agentic personas** (`governance/personas/agentic/`) — Code Manager (orchestrator, never writes code) and Coder (executor, follows Code Manager direction).

### Policy Engine

Three deterministic YAML profiles in `governance/policy/`:
- `default.yaml` — Standard risk tolerance, auto-merge enabled with conditions
- `fin_pii_high.yaml` — SOC2/PCI-DSS/HIPAA/GDPR, auto-merge disabled, 3-approver override
- `infrastructure_critical.yaml` — Mandatory architecture and SRE review

All profiles require security-review, threat-modeling, cost-analysis, and documentation-review panels on every PR. Policies are evaluated programmatically. AI models never interpret policy rules.

### Context Management (JIT Loading)

Context is loaded in tiers to prevent window overflow:
- **Tier 0** (~400 tokens, survives resets): `instructions.md` + project identity
- **Tier 1** (~2,000 tokens, session): Language conventions + active personas
- **Tier 2** (~3,000 tokens, per-phase): Workflow phase + panel context
- **Tier 3** (0 tokens, on-demand): Policies, schemas, docs — queried only when needed

**Hard stop at 80% context capacity.** When approaching this limit: stop all work, clean git state, write a checkpoint to `.checkpoints/`, report to user, and request `/clear`. Never allow context to compact with dirty state. See `governance/docs/context-management.md` for the full shutdown protocol.

### Structured Emissions

All panel output must include JSON between `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers, validated against `governance/schemas/panel-output.schema.json`. Missing markers or invalid JSON means panel execution failed.

## Key Conventions

- **Commit style**: Conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`)
- **Branch naming**: `itsfwcp/{issue-type}/{issue-number}/{branch-name}` (e.g., `itsfwcp/feat/42/add-auth`)
- **Plans before code**: Every implementation requires a plan in `.plans/` using `governance/prompts/templates/plan-template.md`
- **Backward compatibility**: All changes must be additive. Breaking changes require migration plans and version bumps.
- **Enforcement artifacts use semantic versioning** in their `profile_version` or `version` field
- **Cognitive artifacts version by git SHA** — they evolve with the submodule
- **Manifests are immutable** — never edit after creation

## Agentic Startup Sequence

When operating autonomously (via `governance/prompts/startup.md`), the Code Manager:
1. Updates `.ai` submodule to latest (pre-flight, in consuming repos)
2. Scans open GitHub issues
3. Filters for actionable (no branch, not blocked/wontfix/duplicate, not recently human-edited)
4. Prioritizes by label (P0 > P1 > P2 > P3 > P4), then creation date
5. Validates intent clarity, creates plan, executes via Coder persona
6. Invokes review panels, logs run manifest
7. Max 5 issues per session; **hard stop at 80% context capacity** — executes shutdown protocol (clean git, write checkpoint, request `/clear`)

## Symlink Configuration

`config.yaml` defines symlinks created by `init.sh` for consuming repos:
- `instructions.md` → `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`

This ensures Claude Code, GitHub Copilot, and Cursor all receive the same base instructions in consuming projects.

## Project Directories

`init.sh` creates these directories in consuming repos (not in the submodule):
- `.plans/` — Implementation plans for issues and features (accumulated)
- `.panels/` — Panel review reports (latest only per panel type, overwrite strategy)

Directories are configured in `config.yaml` under `project_directories` and can be extended in `project.yaml`.
