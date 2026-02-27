# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is the **Dark Factory Governance Platform** — an AI governance framework for autonomous software delivery, distributed as a git submodule to consuming repositories. It contains no application source code; it is entirely configuration, policy, schemas, and documentation.

Current maturity: **Phase 4b (Autonomous Remediation)** — all governance artifacts implemented. Phase 5 sub-phases (5a-5e) are defined with achievability assessments; 5a (self-proving systems), 5b (self-evolution), 5c (always-on orchestration), and 5e (spec-driven interface) governance artifacts are complete.

## Repository Commands

There is no build system or linter. The policy engine has a pytest test suite in `governance/engine/tests/`.

**Bootstrap (for consuming repos):**
```bash
bash .ai/bin/init.sh                          # Symlinks only
bash .ai/bin/init.sh --install-deps           # Symlinks + Python venv + dependencies
bash .ai/bin/init.sh --refresh                # Re-apply structural setup after submodule update
bash .ai/bin/init.sh --check-branch-protection  # Query if default branch requires PRs
```
Checks `.ai` submodule freshness (auto-updates if behind), creates symlinks for CLAUDE.md and .github/copilot-instructions.md, creates `.governance/plans/`, `.governance/panels/`, `.governance/checkpoints/`, and `.governance/state/` directories (with migration from legacy paths), generates GOALS.md from template, and validates required panel emissions. The `--refresh` flag skips the submodule freshness check and SSH-to-HTTPS conversion (already handled by the caller) but runs all other steps; the agentic startup loop calls this automatically after every submodule state check. The `--check-branch-protection` flag queries the GitHub API to detect if the default branch requires PRs and outputs `REQUIRES_PR=true|false`; the agentic startup loop uses this to route structural commits through PRs when required.

**Agentic bootstrap (interactive):**
Tell your AI assistant to read and execute `governance/prompts/init.md`. This walks through setup interactively — choosing a language template, configuring repository settings, and installing dependencies — with the agent asking about each option.

**Azure resource naming (generate compliant names):**
```bash
python bin/generate-name.py \
    --resource-type Microsoft.KeyVault/vaults \
    --lob set --stage dev --app-name myapp --app-id a
python bin/generate-name.py --list-types                    # List supported resource types
python bin/generate-name.py --validate-only "kvsetdevmyapp" \
    --resource-type Microsoft.KeyVault/vaults               # Validate an existing name
```
See `docs/guides/naming-cli-usage.md` for full usage documentation.

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

- **Consolidated review prompts** (`governance/prompts/reviews/`) — 19 self-contained review prompts implementing Anthropic's Parallelization (Voting) pattern. Each prompt inlines its participant perspectives with full evaluation criteria, scoring, and output schema. This is the canonical location for review definitions.
- **Shared perspectives** (`governance/prompts/shared-perspectives.md`) — Canonical definitions for the 19 perspectives appearing in 2+ review prompts. Serves as the authoring-time DRY mechanism; compiled prompts have full locality at runtime.
- **Agentic personas** (`governance/personas/agentic/`) — Five-agent prompt-chained architecture:
  - **DevOps Engineer** — Session entry point: pre-flight, triage, routing (Anthropic's Routing pattern)
  - **Code Manager** — Pipeline orchestrator: intent validation, panel selection, review coordination, merge (Orchestrator-Workers pattern)
  - **Coder** — Execution agent: implementation, tests, documentation (Worker)
  - **IaC Engineer** — Infrastructure execution agent: Bicep/Terraform, JM Paved Roads standards, security-first defaults (Worker)
  - **Tester** — Independent evaluator: test coverage gate, documentation verification, structured feedback (Evaluator-Optimizer pattern)
- **Agent protocol** (`governance/prompts/agent-protocol.md`) — Structured inter-agent communication with typed messages: ASSIGN, STATUS, RESULT, FEEDBACK, ESCALATE, APPROVE, BLOCK, CANCEL

> See `docs/research/README.md` for the research supporting the persona consolidation decision (Issue #220).

> For the full agent architecture — including protocol details, transport phases, failure modes, and extension points — see `docs/architecture/agent-architecture.md`.

### Compliance Coverage

The platform's controls are mapped to the [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) in `docs/compliance/owasp-llm-top10-mapping.md`. This coverage matrix identifies the specific panels, policy rules, schema fields, and persona guardrails addressing each LLM risk, along with gap analysis and mitigation recommendations.

### Policy Engine

Four deterministic YAML profiles in `governance/policy/`:
- `default.yaml` — Standard risk tolerance, auto-merge enabled with conditions
- `fin_pii_high.yaml` — SOC2/PCI-DSS/HIPAA/GDPR, auto-merge disabled, 3-approver override
- `infrastructure_critical.yaml` — Mandatory architecture and SRE review
- `reduced_touchpoint.yaml` — Near-full autonomy, human approval only for policy overrides and dismissed security-critical findings (Phase 5e)

All profiles require security-review, threat-modeling, cost-analysis, documentation-review, and data-governance-review panels on every PR. Policies are evaluated programmatically. AI models never interpret policy rules.

### Regulatory Compliance

The governance platform maps to three major AI regulatory and standards frameworks:
- **EU AI Act** (`docs/compliance/eu-ai-act-mapping.md`) -- four-tier risk classification (`ai_act_risk_tier` field in panel emissions), model provenance tracking, GDPR Article 22 automated decision-making controls. Full enforcement: 2 August 2026.
- **NIST AI RMF** (`docs/compliance/nist-ai-rmf-mapping.md`) -- four functions (Govern, Map, Measure, Manage) mapped to governance layers, policy engine, panel system, and structured emissions.
- **ISO/IEC 42001** (`docs/compliance/iso-42001-mapping.md`) -- clauses 4-10 mapped to governance artifacts, from context definition (`project.yaml`) through continual improvement (`GOALS.md`).

### Context Management (JIT Loading)

Context is loaded in tiers to prevent window overflow:
- **Tier 0** (~400 tokens, survives resets): `instructions.md` + project identity
- **Tier 1** (~2,000 tokens, session): Language conventions + active personas
- **Tier 2** (~3,000 tokens, per-phase): Workflow phase + panel context
- **Tier 3** (0 tokens, on-demand): Policies, schemas, docs — queried only when needed

**Hard stop at 80% context capacity.** When approaching this limit: stop all work, clean git state, write a checkpoint to `.governance/checkpoints/`, report to user, and request `/clear`. Never allow context to compact with dirty state. See `docs/architecture/context-management.md` for the full shutdown protocol.

### Structured Emissions

All panel output must include JSON between `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers, validated against `governance/schemas/panel-output.schema.json`. Missing markers or invalid JSON means panel execution failed.

## Key Conventions

- **Commit style**: Conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`)
- **Branch naming**: `itsfwcp/{issue-type}/{issue-number}/{branch-name}` (e.g., `itsfwcp/feat/42/add-auth`)
- **Plans before code**: Every implementation requires a plan in `.governance/plans/` using `governance/prompts/templates/plan-template.md`
- **Governance pipeline is mandatory**: The governance pipeline applies in all modes (local and remote). Required panels must execute, plan-first is non-negotiable, and the CI workflow blocks merges when panel emissions are missing. Projects can opt out via `governance.skip_panel_validation: true` in `project.yaml` (project root).
- **`jm-compliance.yml` is enterprise-locked**: Never modify, move, or override `jm-compliance.yml`. It is managed centrally.
- **Backward compatibility**: All changes must be additive. Breaking changes require migration plans and version bumps.
- **Enforcement artifacts use semantic versioning** in their `profile_version` or `version` field
- **Cognitive artifacts version by git SHA** — they evolve with the submodule
- **Manifests are immutable** — never edit after creation
- **Slash commands**: `/startup` begins the agentic loop, `/checkpoint` saves state and offers context reset. Copilot equivalents are in `.github/copilot-chat/`.

## Agentic Startup Sequence

When operating autonomously (via `governance/prompts/startup.md`), the pipeline chains five personas through five phases with **parallel Coder dispatch**:

| Phase | Persona | What Happens |
|-------|---------|-------------|
| 1 | DevOps Engineer | Pre-flight (submodule, repo config, branch protection detection — respects `project.yaml` pin), resolve open PRs, triage and route issues |
| 2 | Code Manager | Validate intent, select review panels, and create plans for **all issues** (up to N = `governance.parallel_coders`; all actionable issues when N = -1) |
| 3 | Code Manager | **Parallel dispatch**: spawn up to N Coder agents via `Task` tool with `isolation: "worktree"` (N = `governance.parallel_coders`, default 5; all planned issues when N = -1). IaC Engineer dispatched for infrastructure changes (conditional — infrastructure changes only) |
| 4 | Code Manager + Tester | Collect results as each Coder/IaC Engineer finishes → Tester evaluates → Security review → PR monitoring |
| 5 | Code Manager + DevOps Engineer | Merge all PRs, retrospective, loop or shutdown |

Max N issues per session where N = `governance.parallel_coders` (default 5; set to -1 for unlimited — context pressure becomes the sole session limiter; parallel execution is context-efficient — Coder subagents use their own context windows); **hard stop at 80% context capacity** — executes shutdown protocol (clean git, write checkpoint, request `/clear`)

## Symlink Configuration

`config.yaml` defines symlinks created by `init.sh` for consuming repos:
- `instructions.md` → `CLAUDE.md`, `.github/copilot-instructions.md`

This ensures Claude Code and GitHub Copilot receive the same base instructions in consuming projects.

## Project Directories

`init.sh` creates these directories:
- `.governance/plans/` — Implementation plans for issues and features (accumulated)
- `.governance/panels/` — Panel review reports (latest only per panel type, overwrite strategy)
- `.governance/checkpoints/` — Context capacity checkpoints (session state)
- `.governance/state/` — Cross-session governance state persistence (accumulated)

Directories are configured in `config.yaml` under `project_directories` and can be extended in `project.yaml` (project root).

### Resource Locations — AI Submodule vs. Consuming Repos

Emitted output uses identical `.governance/` paths everywhere. Read-only governance sources differ by the `.ai/` submodule prefix in consumers:

| Resource | AI Submodule | Consuming Repo |
|----------|-------------|----------------|
| Plans | `.governance/plans/` | `.governance/plans/` |
| Panel reports | `.governance/panels/` | `.governance/panels/` |
| Checkpoints | `.governance/checkpoints/` | `.governance/checkpoints/` |
| Cross-session state | `.governance/state/` | `.governance/state/` |
| Worktrees | `../{repo}-worktree-issue-{N}/` | `../{repo}-worktree-issue-{N}/` |
| Personas | `governance/personas/agentic/` | `.ai/governance/personas/agentic/` (read-only) |
| Review prompts | `governance/prompts/reviews/` | `.ai/governance/prompts/reviews/` (read-only) |
| Policy profiles | `governance/policy/` | `.ai/governance/policy/` (read-only) |
| Schemas | `governance/schemas/` | `.ai/governance/schemas/` (read-only) |
| Instructions | `instructions.md` | `CLAUDE.md` → `.ai/instructions.md` (symlink) |

See `docs/onboarding/project-structure.md` for a full breakdown of what `init.sh` creates and what to expect in each directory.
