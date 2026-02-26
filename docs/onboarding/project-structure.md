# Project Structure After Init

What `bash .ai/bin/init.sh` creates in your consuming repository, where governance artifacts are stored, and what you can expect in each location.

## Directory Tree

After running `init.sh`, your consuming repo will look like this:

```
my-project/
├── .ai/                                    # Git submodule (read-only reference)
│   ├── bin/                                # Bootstrap scripts
│   ├── config.yaml                         # Submodule defaults
│   ├── governance/
│   │   ├── personas/agentic/              # Agent persona definitions
│   │   ├── prompts/                       # Review prompts, templates, workflows
│   │   ├── policy/                        # Deterministic policy profiles (YAML)
│   │   ├── schemas/                       # JSON Schema validation
│   │   └── emissions/                     # Baseline panel emissions
│   └── docs/                              # This documentation
│
├── .github/
│   ├── copilot-instructions.md             # → .ai/instructions.md (symlink)
│   ├── ISSUE_TEMPLATE/
│   │   ├── design-intent.yml              # Copied from .ai
│   │   ├── bug-report.yml                 # Copied from .ai
│   │   └── ...                            # Other issue templates
│   └── workflows/
│       ├── dark-factory-governance.yml     # → .ai/.github/workflows/ (symlink, required)
│       ├── issue-monitor.yml              # → .ai/.github/workflows/ (symlink, optional)
│       ├── event-trigger.yml              # → .ai/.github/workflows/ (symlink, optional)
│       ├── plan-archival.yml              # → .ai/.github/workflows/ (symlink, optional)
│       └── propagate-submodule.yml        # → .ai/.github/workflows/ (symlink, optional)
│
├── .governance/                            # All governance output lives here
│   ├── plans/                             # Implementation plans
│   │   └── .gitkeep
│   ├── panels/                            # Panel review reports
│   │   └── .gitkeep
│   ├── checkpoints/                       # Context capacity checkpoints
│   │   └── .gitkeep
│   └── state/                             # Cross-session persistence
│       └── .gitkeep
│
├── CLAUDE.md                               # → .ai/instructions.md (symlink)
├── GOALS.md                                # Copied from template (editable)
├── project.yaml                            # Project-level configuration (editable)
│
└── src/                                    # Your application code
```

## What Each Location Contains

### `.ai/` — The Governance Submodule (Read-Only)

The `.ai/` directory is a git submodule pointing to the [ai-submodule](https://github.com/SET-Apps/ai-submodule) repository. It contains all governance definitions — personas, prompts, review templates, policy profiles, schemas, and documentation.

**You should never write files into `.ai/`.** It is a read-only reference. Templates and prompts are *read* from `.ai/governance/prompts/` at runtime, but all *emitted* artifacts (plans, panel reports, checkpoints) are written to `.governance/` in your project root.

### `.governance/` — Governance Output

This dot-prefixed directory is where all governance artifacts produced during agent sessions are stored. It lives in your project root and is tracked by your repo's own git history.

#### `.governance/plans/`

Implementation plans created before any code is written. Every non-trivial change requires a plan.

| Property | Value |
|----------|-------|
| **Retention** | Accumulated — all plans are retained |
| **Naming** | `{issue-number}-{short-name}.md` (e.g., `42-add-auth.md`) |
| **Template** | Based on `.ai/governance/prompts/templates/plan-template.md` |
| **Created by** | Code Manager persona during Phase 2 |

Example contents:
```
.governance/plans/
├── 42-add-auth.md
├── 55-fix-pagination.md
└── 78-migrate-database.md
```

#### `.governance/panels/`

Panel review reports produced by the governance review prompts. Each panel type overwrites its previous report to avoid repository bloat.

| Property | Value |
|----------|-------|
| **Retention** | Latest only — overwrite per panel type |
| **Naming** | `{panel-type}.json` (e.g., `security-review.json`) |
| **Schema** | Validated against `.ai/governance/schemas/panel-output.schema.json` |
| **Created by** | Review panels during Phase 4 |

Example contents:
```
.governance/panels/
├── code-review.json
├── security-review.json
├── threat-modeling.json
├── cost-analysis.json
├── documentation-review.json
└── data-governance-review.json
```

#### `.governance/checkpoints/`

Session state snapshots written when the agent hits the 80% context capacity hard stop. These allow a new session to resume where the previous one left off.

| Property | Value |
|----------|-------|
| **Retention** | Session lifecycle — stale after 24 hours |
| **Naming** | `{timestamp}.json` |
| **Created by** | Context Capacity Shutdown Protocol |
| **Consumed by** | Checkpoint Resumption Workflow on next `/startup` |

Example contents:
```
.governance/checkpoints/
└── 2026-02-25T18-30-00Z.json
```

#### `.governance/state/`

Cross-session governance state that persists across agent sessions. Includes retrospective data, issue tracking state, and metrics.

| Property | Value |
|----------|-------|
| **Retention** | Accumulated — grows over time |
| **Created by** | Various agent personas across sessions |

### `.github/` — GitHub Integration

#### Symlinked Workflows

Governance workflows are **symlinked** (not copied) from `.ai/.github/workflows/`. This means submodule updates flow automatically without re-running `init.sh`.

- **`dark-factory-governance.yml`** (required) — Policy engine evaluation and PR auto-approval
- **`issue-monitor.yml`** (optional) — Issue lifecycle monitoring
- **`event-trigger.yml`** (optional) — Event-driven governance triggers
- **`plan-archival.yml`** (optional) — Plan file management
- **`propagate-submodule.yml`** (optional) — Submodule update propagation

#### Copied Issue Templates

Issue templates are **copied** (not symlinked) into `.github/ISSUE_TEMPLATE/`. This allows you to customize them for your project. Existing templates are not overwritten.

#### `copilot-instructions.md`

Symlinked to `.ai/instructions.md`. Provides GitHub Copilot with the same base instructions as Claude Code.

### Root-Level Files

- **`CLAUDE.md`** — Symlink to `.ai/instructions.md`. Provides Claude Code with governance context.
- **`GOALS.md`** — Copied from `.ai/governance/templates/GOALS.md`. Edit this to define your project's goals and priorities. The agentic loop falls back to `GOALS.md` when no open issues remain.
- **`project.yaml`** — Your project's configuration. Defines language, framework, policy profile, and governance settings. The Code Manager auto-generates this if missing.

## Worktrees — Parallel Agent Workspaces

When the agentic loop runs in parallel mode (the default), the Code Manager spawns up to N concurrent Coder agents (N = `governance.parallel_coders` from `project.yaml`, default 5). Each Coder works in its own **git worktree** — an isolated file system copy of the repository checked out to a feature branch.

### Where Worktrees Live

Git worktrees are created as siblings to your project root, managed by git itself:

```
~/repos/
├── my-project/                         # Main working tree (Code Manager)
│   ├── .ai/
│   ├── .governance/
│   └── src/
│
├── my-project-worktree-issue-42/       # Coder Agent 1 (worktree)
│   ├── .ai/                            # Shared submodule
│   ├── .governance/
│   └── src/                            # Branch: itsfwcp/feat/42/add-auth
│
├── my-project-worktree-issue-55/       # Coder Agent 2 (worktree)
│   ├── .ai/
│   ├── .governance/
│   └── src/                            # Branch: itsfwcp/fix/55/pagination
│
└── my-project-worktree-issue-78/       # Coder Agent N (worktree)
    ├── .ai/
    ├── .governance/
    └── src/                            # Branch: itsfwcp/feat/78/migrate-db
```

### How Worktrees Work

1. **Code Manager** (Phase 3) creates a worktree per issue using `git worktree add`
2. Each **Coder agent** runs in its own worktree with its own context window
3. Coders **commit** to their worktree branch but **do not push** — the Code Manager pushes after evaluation
4. The Code Manager **reads results** from each worktree as Coder agents complete
5. After evaluation and PR creation, worktrees are cleaned up

### Key Properties

| Property | Value |
|----------|-------|
| **Isolation** | Full file system isolation — Coders cannot interfere with each other |
| **Branch** | Each worktree is checked out to a feature branch (`itsfwcp/{type}/{issue}/{name}`) |
| **Context** | Each Coder has its own AI context window — no shared context pressure |
| **Cleanup** | Worktrees are removed after the Code Manager integrates the results |
| **Fallback** | If worktree creation fails, the Code Manager falls back to sequential execution (one issue at a time) |

### Worktrees vs. the Main Working Tree

The **main working tree** is where the Code Manager orchestrates. It:
- Creates plans in `.governance/plans/`
- Dispatches Coder agents to worktrees
- Collects results and runs evaluations
- Pushes PRs and monitors CI

**Worktrees** are temporary. They exist only for the duration of a Coder agent's execution and are cleaned up after integration.

## What Is NOT Created in Your Repo

The following stay inside the `.ai/` submodule and are never written to your project:

- Persona definitions (`governance/personas/`)
- Review prompts (`governance/prompts/reviews/`)
- Policy profiles (`governance/policy/`)
- JSON schemas (`governance/schemas/`)
- Baseline emissions (`governance/emissions/`)
- Documentation (`docs/`)

These are read at runtime but never modified by the governance pipeline in your repo.

## Resource Location Summary

Both the ai-submodule and consuming repos use `.governance/` for all emitted artifacts. The only difference is how read-only governance source files are accessed — directly in the ai-submodule, or via the `.ai/` submodule prefix in consumers.

| Resource | AI Submodule | Consuming Repo |
|----------|-------------|----------------|
| Implementation plans | `.governance/plans/` | `.governance/plans/` |
| Panel review reports | `.governance/panels/` | `.governance/panels/` |
| Context checkpoints | `.governance/checkpoints/` | `.governance/checkpoints/` |
| Cross-session state | `.governance/state/` | `.governance/state/` |
| Agent worktrees | `../{repo}-worktree-issue-{N}/` | `../{repo}-worktree-issue-{N}/` |
| Persona definitions | `governance/personas/agentic/` | `.ai/governance/personas/agentic/` (read-only) |
| Review prompts | `governance/prompts/reviews/` | `.ai/governance/prompts/reviews/` (read-only) |
| Policy profiles | `governance/policy/` | `.ai/governance/policy/` (read-only) |
| JSON schemas | `governance/schemas/` | `.ai/governance/schemas/` (read-only) |
| Instructions | `instructions.md` | `CLAUDE.md` → `.ai/instructions.md` (symlink) |
