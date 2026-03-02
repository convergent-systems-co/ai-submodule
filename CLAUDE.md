# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repository Is

This is the **Dark Factory Governance Platform** — an AI governance framework for autonomous software delivery, distributed as a git submodule to consuming repositories. It contains no application source code; it is entirely configuration, policy, schemas, and documentation.

Current maturity: **Phase 4b (Autonomous Remediation)** — all governance artifacts implemented. Phase 5 sub-phases (5a-5e) are defined with achievability assessments; 5a (self-proving systems), 5b (self-evolution), 5c (always-on orchestration), and 5e (spec-driven interface) governance artifacts are complete.

## Repository Commands

There is no build system or linter. The policy engine has a pytest test suite in `governance/engine/tests/`.

**Bootstrap (for consuming repos — recommended: agentic):**
Tell your AI assistant: "Read and execute `.ai/governance/prompts/init.md`" — this is the primary bootstrap method. It interactively configures the project, writes instruction files directly (not symlinks), installs hooks, and sets up governance directories.

**Bootstrap (shell script alternative):**
```bash
bash .ai/bin/init.sh                          # Symlinks + directories
bash .ai/bin/init.sh --install-deps           # Symlinks + Python venv + dependencies
bash .ai/bin/init.sh --refresh                # Re-apply structural setup after submodule update
bash .ai/bin/init.sh --check-branch-protection  # Query if default branch requires PRs
bash .ai/bin/init.sh --verify                 # Verify installation is complete and correct
bash .ai/bin/init.sh --dry-run                # Show what would be done without making changes
bash .ai/bin/init.sh --debug                  # Verbose output for troubleshooting
```
Checks `.ai` submodule freshness (auto-updates if behind), creates symlinks for CLAUDE.md and .github/copilot-instructions.md, creates `.governance/plans/`, `.governance/panels/`, `.governance/checkpoints/`, and `.governance/state/` directories (with migration from legacy paths), generates GOALS.md from template, and validates required panel emissions. The `--refresh` flag skips the submodule freshness check and SSH-to-HTTPS conversion (already handled by the caller) but runs all other steps; the agentic startup loop calls this automatically after every submodule state check. The `--check-branch-protection` flag queries the GitHub API to detect if the default branch requires PRs and outputs `REQUIRES_PR=true|false`; the agentic startup loop uses this to route structural commits through PRs when required. The `--verify` flag runs a read-only diagnostic that checks project.yaml, symlinks, slash commands, governance directories, workflows, and CODEOWNERS — useful after any installation method to confirm everything is correctly set up. The `--dry-run` flag shows planned actions without executing them. The `--debug` flag enables verbose output. The orchestrator (`bin/init.sh`, ~177 lines) delegates to modular scripts in `governance/bin/` — each script can also be run independently. See `docs/troubleshooting/init-failures.md` for diagnostics.

**One-line install (new project):**
```bash
curl -sSL https://raw.githubusercontent.com/SET-Apps/ai-submodule/main/bin/quick-install.sh | bash
```

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

**Prompt catalog (generate/validate prompt index):**
```bash
python bin/generate-prompt-catalog.py                    # Generate catalog
python bin/generate-prompt-catalog.py --validate         # Validate only
```
See `docs/guides/prompt-library.md` for the prompt library guide.

**MCP server (install for IDE):**
```bash
bash mcp-server/install.sh --governance-root /path/to/repo     # macOS/Linux
npx @jm-packages/ai-submodule-mcp --governance-root /path/to/repo  # npx
```
See `docs/guides/mcp-server-usage.md` for full MCP server documentation.

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

- **Consolidated review prompts** (`governance/prompts/reviews/`) — 21 self-contained review prompts implementing Anthropic's Parallelization (Voting) pattern. Each prompt inlines its participant perspectives with full evaluation criteria, scoring, and output schema. This is the canonical location for review definitions.
- **Shared perspectives** (`governance/prompts/shared-perspectives.md`) — Canonical definitions for the 24 perspectives appearing in 2+ review prompts. Serves as the authoring-time DRY mechanism; compiled prompts have full locality at runtime.
- **Agentic personas** (`governance/personas/agentic/`) — Six-agent prompt-chained architecture:
  - **Project Manager** — Portfolio-level orchestrator: multiplexes Code Managers, spawns background DevOps Engineer, cross-batch coordination (Orchestrator-Workers pattern, opt-in via `governance.use_project_manager: true`)
  - **DevOps Engineer** — Session entry point (standard) or background agent (PM mode): pre-flight, triage, routing, issue grouping, continuous polling (Anthropic's Routing pattern)
  - **Code Manager** — Pipeline orchestrator: intent validation, panel selection, review coordination, merge (Orchestrator-Workers pattern). Operates in standard or batch-scoped mode.
  - **Coder** — Execution agent: implementation, tests, documentation (Worker)
  - **IaC Engineer** — Infrastructure execution agent: Bicep/Terraform, JM Paved Roads standards, security-first defaults (Worker)
  - **Tester** — Independent evaluator: test coverage gate, documentation verification, structured feedback (Evaluator-Optimizer pattern)
- **Agent protocol** (`governance/prompts/agent-protocol.md`) — Structured inter-agent communication with typed messages: ASSIGN, STATUS, RESULT, FEEDBACK, ESCALATE, APPROVE, BLOCK, CANCEL, WATCH

> See `docs/research/README.md` for the research supporting the persona consolidation decision (Issue #220).

> For the full agent architecture — including protocol details, transport phases, failure modes, and extension points — see `docs/architecture/agent-architecture.md`.

### Compliance Coverage

The platform's controls are mapped to the [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) in `docs/compliance/owasp-llm-top10-mapping.md`. This coverage matrix identifies the specific panels, policy rules, schema fields, and persona guardrails addressing each LLM risk, along with gap analysis and mitigation recommendations.

The `jm-standards-compliance-review` panel (`governance/prompts/reviews/jm-standards-compliance-review.md`) evaluates code and infrastructure changes against JM Family Paved Roads standards, flagging unapproved technology deviations and verifying documented justifications for approved overrides.

### Developer Prompt Library

12 production-ready developer prompts in `prompts/global/` covering code review, debugging, PR creation, refactoring, test writing, and more. Each prompt uses YAML frontmatter (name, description, status, tags, model). The prompt catalog (`catalog/prompt-catalog.json`) is auto-generated by `bin/generate-prompt-catalog.py` and validated against `governance/schemas/prompt-catalog.schema.json`. The `prompt-catalog.yml` CI workflow regenerates the catalog on push. See `docs/guides/prompt-library.md`.

### Skills System

Skills (`.skill.md` files in `mcp-server/skills/`) are self-contained capabilities exposed by the MCP server as tools. Each skill has YAML frontmatter (name, description, allowed-tools) and a Markdown body that serves as the execution prompt. Available skills: `governance-review` (panel reviews against code changes) and `ado` (Azure DevOps work item operations using the Python client library). See `docs/guides/skills-development.md`.

### Azure DevOps Integration

Python client library at `governance/integrations/ado/` wrapping the ADO REST API 7.1. Provides `AdoClient` with work item CRUD, WIQL queries, comments (HTML-only), classification nodes, fields, types, project inspection (custom states/processes), and GitHub artifact link helpers. Auth via PAT, Service Principal, or Managed Identity (lazy `azure-identity` import). Configured via `ado_integration` section in `project.yaml`. The `ado` MCP skill exposes these operations to AI assistants. Includes a health check engine (`health.py`), error queue retry processor (`retry.py`), and sync status dashboard emitter (`dashboard.py`). See `docs/guides/ado-integration.md` for comprehensive setup and operations documentation.

Three JSON Schemas in `governance/schemas/` govern ADO sync configuration and state:
- **`ado-integration.schema.json`** -- Validates the `ado_integration` section of `project.yaml` (organization, auth, sync behaviour, state/type/field mappings, filters).
- **`ado-sync-ledger.schema.json`** -- Validates the sync ledger at `.governance/state/ado-sync-ledger.json` (GitHub issue to ADO work item mappings).
- **`ado-sync-error.schema.json`** -- Validates the error log at `.governance/state/ado-sync-errors.json` (failed sync operations with retry tracking).

Operational CLI commands via `bin/ado-sync.py`: `health` (6-point check battery with JSON output), `retry-failed` (error queue processor with dead-lettering), `dashboard` (sync status emission).

### CI Workflows

18 GitHub Actions workflows across five categories: Governance (dark-factory-governance, jm-compliance, plan-archival, prompt-eval), Agentic (agentic-issue-worker, agentic-loop, event-trigger, issue-monitor), Self-Repair (auto-rebase, branch-cleanup, self-repair-lint), ADO Sync (ado-sync, ado-reverse-sync), and Publishing/Automation (propagate-submodule, deploy-docs, publish-dashboard, prompt-catalog, publish-mcp). See `docs/architecture/ci-workflows.md`.

The `dark-factory-governance` workflow auto-detects consuming repos via `.gitmodules` when the `.ai` submodule content is unavailable in CI (private submodule without credentials). In consuming repo mode: the test job is skipped, the policy engine falls back to lightweight emission-only validation reading from `.governance/panels/`, and the `skip_panel_validation` setting is read from the PR merge commit (not the base branch). See `docs/configuration/repository-setup.md` for details.

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

### Checkpoint Schema

Session checkpoints in `.governance/checkpoints/` conform to `governance/schemas/checkpoint.schema.json`. Checkpoints include optional `context_capacity` (tier, signals, trigger) and `context_gates_passed` (phase-by-phase gate decisions) fields for diagnostic analysis and seamless recovery via Phase 0.

## Key Conventions

- **Commit style**: Conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`)
- **Branch naming**: `NETWORK_ID/{issue-type}/{issue-number}/{branch-name}` (e.g., `NETWORK_ID/feat/42/add-auth`)
- **Plans before code**: Every implementation requires a plan in `.governance/plans/` using `governance/prompts/templates/plan-template.md`
- **Governance pipeline is mandatory**: The governance pipeline applies in all modes (local and remote). Required panels must execute, plan-first is non-negotiable, and the CI workflow blocks merges when panel emissions are missing. Projects can opt out via `governance.skip_panel_validation: true` in `project.yaml` (project root).
- **`jm-compliance.yml` is enterprise-locked**: Never modify, move, or override `jm-compliance.yml`. It is managed centrally.
- **Backward compatibility**: All changes must be additive. Breaking changes require migration plans and version bumps.
- **Enforcement artifacts use semantic versioning** in their `profile_version` or `version` field
- **Cognitive artifacts version by git SHA** — they evolve with the submodule
- **Manifests are immutable** — never edit after creation
- **Slash commands**: `/startup` begins the agentic loop, `/checkpoint` saves state and offers context reset. Copilot equivalents are in `.github/copilot-chat/`.

## Agentic Startup Sequence

When operating autonomously (via `governance/prompts/startup.md`), the pipeline chains personas through structured phases with **parallel Coder dispatch**:

### Standard Mode (default)

| Phase | Persona | What Happens |
|-------|---------|-------------|
| 1 | DevOps Engineer | Pre-flight (submodule, repo config, branch protection detection — respects `project.yaml` pin), resolve open PRs, triage and route issues |
| 2 | Code Manager | Validate intent, select review panels, and create plans for **all issues** (up to N = `governance.parallel_coders`; all actionable issues when N = -1) |
| 3 | Code Manager | **Parallel dispatch**: spawn up to N Coder agents via `Task` tool with `isolation: "worktree"` (N = `governance.parallel_coders`, default 5; all planned issues when N = -1). IaC Engineer dispatched for infrastructure changes (conditional — infrastructure changes only) |
| 4 | Code Manager + Tester | Collect results as each Coder/IaC Engineer finishes → Tester evaluates → Security review → PR monitoring |
| 5 | Code Manager + DevOps Engineer | Merge all PRs, retrospective, loop or shutdown |

Max N issues per session where N = `governance.parallel_coders` (default 5; set to -1 for unlimited — context pressure becomes the sole session limiter; parallel execution is context-efficient — Coder subagents use their own context windows); **hard stop at 80% context capacity** — executes shutdown protocol (clean git, write checkpoint, request `/clear`)

### Project Manager Mode (opt-in: `governance.use_project_manager: true`)

When enabled, the Project Manager replaces the DevOps Engineer as the session entry point and introduces multiplexed Code Managers for higher throughput:

| PM Phase | Persona | What Happens |
|----------|---------|-------------|
| 0 | Project Manager | Checkpoint recovery (PM-specific state) |
| 1 | Project Manager + DevOps Engineer | PM spawns DevOps Engineer as background agent for pre-flight and triage |
| 1b | DevOps Engineer (background) | Pre-flight, issue scanning, grouping by change type (code/docs/infra/security/mixed), RESULT to PM |
| 2 | Project Manager | Receives grouped batches, spawns M Code Managers (one per group, M = `governance.parallel_code_managers`, default 3) |
| 2b | Code Managers (parallel) | Each CM plans its batch, dispatches Coders (nested parallelism: PM -> CM -> Coder) |
| 3 | Project Manager | Collects CM results, coordinates cross-batch dependencies, processes WATCH messages from DevOps |
| 4 | Project Manager | Merges all PRs (via CMs), retrospective, handles new WATCH work or shutdown |

Total concurrent agents = M Code Managers x N Coders per CM. The DevOps Engineer runs in background polling mode, emitting WATCH messages when new actionable issues are discovered. See `docs/architecture/project-manager-architecture.md` for the full architecture.

## Instruction Delivery

`config.yaml` declares how instructions reach consuming repos. Two delivery methods exist:

- **Direct file writes (preferred)** — `init.md` (agentic bootstrap) reads `.ai/instructions.md` and writes it to `CLAUDE.md` and `.github/copilot-instructions.md` as regular files. More portable, no symlink resolution issues.
- **Symlinks (fallback)** — `init.sh` (shell bootstrap) creates symlinks: `CLAUDE.md` → `.ai/instructions.md`. Works but fragile on some platforms.

The agentic startup loop (`/startup`) auto-repairs instruction files on every session, migrating symlinks to files and rewriting stale content. See `governance/prompts/startup.md` Phase 1a-bis.

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
| Instructions | `instructions.md` | `CLAUDE.md` ← `.ai/instructions.md` (file copy, preferred) or symlink (legacy) |

See `docs/onboarding/project-structure.md` for a full breakdown of what `init.sh` creates and what to expect in each directory.
