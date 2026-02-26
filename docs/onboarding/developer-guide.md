# Developer Quick Guide

TLDR for developers adopting the Dark Factory Governance Platform.

## What Is This?

A git submodule (`.ai/`) that gives your repository AI-powered governance: automated code review panels, deterministic merge policies, structured audit trails, and agentic workflows. No application code — just configuration, personas, policies, and schemas.

## Quick Start

### 1. Add to your repo

```bash
git submodule add git@github.com:SET-Apps/ai-submodule.git .ai
bash .ai/bin/init.sh   # macOS/Linux — creates symlinks for Claude Code and GitHub Copilot
git commit -m "Add .ai governance submodule"
```

**Windows (PowerShell):**
```powershell
git submodule add git@github.com:SET-Apps/ai-submodule.git .ai
powershell -ExecutionPolicy Bypass -File .ai\bin\init.ps1
git commit -m "Add .ai governance submodule"
```

> Windows requires Python 3.12+ for the policy engine. Install from [python.org](https://www.python.org/downloads/), then run `pip install jsonschema pyyaml`.

### 2. Configure for your stack

```bash
cp .ai/governance/templates/python/project.yaml project.yaml   # or go/, node/, react/, csharp/
# Or skip this — the Code Manager auto-generates project.yaml during /startup
```

Edit `project.yaml` to set your project name, language, and policy profile. If you skip this step, the Code Manager will analyze your repo and create `project.yaml` automatically during the first `/startup` session. See [policy profiles](../architecture/governance-model.md) for guidance on which profile fits your use case.

### 3. Update when the submodule changes

```bash
git submodule update --remote .ai
git add .ai && git commit -m "Update .ai submodule"
```

## Starting the Agentic Loop

Run `/startup` in your AI tool (Claude Code or GitHub Copilot). This activates the 5-agent pipeline:

```
/startup
```

The pipeline chains five agents through five phases, looping until the session cap is hit:

```mermaid
flowchart TD
    START([/startup]) --> PF[Phase 1: Pre-flight & Triage<br/>DevOps Engineer]
    PF -->|Submodule check, repo config,<br/>resolve open PRs| SCAN[Scan & prioritize issues]
    SCAN -->|ASSIGN highest priority| INTENT[Phase 2: Intent & Planning<br/>Code Manager]
    INTENT -->|Validate intent, ensure project.yaml,<br/>select panels, create plan| IMPL[Phase 3: Implementation<br/>Coder]
    INTENT -->|Infrastructure changes only| IAC[Phase 3: Infrastructure<br/>IaC Engineer]
    IMPL -->|Code, tests, structured RESULT| EVAL[Phase 4: Evaluation & Review<br/>Tester + Code Manager]
    IAC -->|Infrastructure RESULT| EVAL

    EVAL --> TEST{Tester evaluates}
    TEST -->|FEEDBACK| IMPL
    TEST -->|APPROVE| SEC[Security Review]
    SEC --> CTX[Context-Specific Reviews]
    CTX --> PR[Push PR → CI + Copilot loop]
    PR --> POLICY{Policy Engine}

    POLICY -->|auto_merge| MERGE[Phase 5: Merge & Loop<br/>Code Manager + DevOps Engineer]
    POLICY -->|human_review| HUMAN[Escalate to human]
    POLICY -->|block| BLOCK[Block — notify user]

    MERGE --> RETRO[Retrospective]
    RETRO --> DECIDE{Hard-stop?}
    DECIDE -->|Yes — session cap or context pressure| EXIT([Checkpoint → Exit — request /clear])
    DECIDE -->|No — more issues| SCAN
    DECIDE -->|No — no issues| GOALS[GOALS.md fallback]
    GOALS -->|Actionable item?| INTENT
    GOALS -->|Nothing left| EXIT
```

**What happens when you run `/startup`:**

1. **DevOps Engineer** checks submodule freshness, verifies repo configuration, resolves any open PRs, then scans and prioritizes issues
2. **Code Manager** validates the issue's intent, auto-manages `project.yaml`, selects review panels based on codebase type, and creates a plan
3. **Coder** implements the plan, writes tests, and emits a structured RESULT. **IaC Engineer** handles infrastructure changes (conditional — infrastructure changes only)
4. **Tester** independently evaluates the work — sends FEEDBACK (up to 3 cycles) or APPROVE
5. **Code Manager** runs security review, context-specific panels, pushes the PR, monitors CI/Copilot
6. After merge, loops back to Phase 1 for the next batch — checkpoints only on hard-stop (max 5 per session)

See [startup.md](../../governance/prompts/startup.md) for the full protocol and [agent-protocol.md](../../governance/prompts/agent-protocol.md) for inter-agent communication.

## Common Operations

**Write a plan before coding** — Every non-trivial change needs a plan:
```bash
cp .ai/governance/prompts/templates/plan-template.md .governance/plans/42-my-feature.md
```

**Branch naming:** `itsfwcp/{type}/{issue-number}/{short-name}` (e.g., `itsfwcp/feat/42/add-auth`)

**Commit style:** Conventional commits — `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`

**Apply repo settings:** `bash .ai/bin/init.sh` — creates symlinks, copies workflows, configures GitHub settings. See [repository configuration](../configuration/repository-setup.md) for details and per-project overrides.

**Context management:** Stop at 80% context capacity. Checkpoint. Request `/clear`. See [context management](../architecture/context-management.md) for the full strategy.

## Where Things Live

Emitted output (plans, panels, checkpoints, state) uses identical `.governance/` paths in both the ai-submodule and consuming repos. Read-only governance sources (personas, prompts, policies, schemas) differ — consumers access them via the `.ai/` submodule prefix.

For a complete breakdown of the project structure, see [Project Structure](project-structure.md).

## Recovery & Re-Entry Patterns

When the agentic loop stops — context reset, crash, stuck PR, dirty git state — use these patterns to get back in.

### Resume from a checkpoint

```bash
ls -t .governance/checkpoints/*.json | head -1   # find the most recent checkpoint
cat .governance/checkpoints/<latest>.json         # see where things left off
```

Then tell the agent: `continue` or `Resume from checkpoint: .governance/checkpoints/<file>`. See [checkpoint resumption workflow](../../governance/prompts/checkpoint-resumption-workflow.md) for the full protocol.

### No checkpoint exists

```bash
git status && git branch --show-current   # what branch, is it clean?
gh pr list --state open --author @me      # open PRs from the agent?
gh issue list --state open --limit 10     # what was being worked on?
```

Then tell the agent: `/startup`. It will run a fresh scan — open PRs first, then open issues. In-progress branches are picked up automatically.

### Dirty git state

```bash
git add -A && git commit -m "wip: recovery"   # Option A: commit what's there
git stash push -m "recovery stash"             # Option B: stash for later
git merge --abort                              # Option C: abort in-progress merge
git rebase --abort                             # Option C: abort in-progress rebase
```

Once `git status` shows clean, run `/startup` to re-enter the loop.

### Stuck or failed PR

```bash
gh pr checks <pr-number>                                              # check CI failures
gh pr view <pr-number> --json state,statusCheckRollup,reviews         # full PR status
```

Tell the agent: `Resume PR #<number>`. It enters the review loop. After 3 failed cycles, it escalates to human review.

### Context loss mid-session

If the agent repeats itself, forgets decisions, or re-reads files it already read — context is under pressure. Tell it: `Write a checkpoint and stop`, then `/clear` and resume.

### Manual re-entry at specific steps

| Situation | What to Say |
|-----------|-------------|
| Open PRs need resolution | `Start at Phase 1 — resolve open PRs` |
| Fresh issue scan | `Start at Phase 1 — scan open issues` |
| Specific issue | `Work on issue #N` |
| PR needs review cycle | `Resume PR #N at Phase 4` |
| Fall back to GOALS.md | `Check GOALS.md for open work items` |

## Diagnostic Commands

| What | Command |
|------|---------|
| Git state | `git status` |
| Current branch | `git branch --show-current` |
| Recent checkpoints | `ls -t .governance/checkpoints/*.json \| head -5` |
| Open PRs | `gh pr list --state open` |
| Open issues | `gh issue list --state open --limit 20` |
| Issue state | `gh issue view <N> --json state --jq '.state'` |
| PR checks | `gh pr checks <N>` |
| Governance health | `gh workflow list` |
| Submodule status | `git submodule status .ai` |
| Agent branches | `git branch -r \| grep itsfwcp` |

## Troubleshooting

**PR never merges** — All CI checks must pass + all review threads resolved. Check `gh pr checks <N>`. After 3 review cycles, the agent escalates to human review.

**Agent skips my issue** — Check for `blocked`/`wontfix`/`duplicate` labels, existing branches, human assignment, or `refine` label. Run `gh issue view <N> --json labels,assignees`.

**Issue labeled `refine`** — The agent needs clearer acceptance criteria. Update the issue body or add a comment. The agent re-evaluates `refine` issues next session.

**Governance workflow not running** — `gh workflow list` to check status. Re-enable with `gh workflow enable dark-factory-governance.yml` or run `bash .ai/bin/init.sh`.

**Stale checkpoint (>24h)** — The agent treats these as stale and runs a fresh scan. This is expected.

**Agent stops after N issues** (N = `governance.parallel_coders`, default 5) — Hard safety limit. Checkpoint → `/clear` → resume from checkpoint.

**Auto-merge fails** — Verify `allow_auto_merge` is enabled and CODEOWNERS is populated. Run `bash .ai/bin/init.sh` to apply settings.

## Further Reading

- [README.md](../../README.md) — Full architecture, governance layers, file structure, and [Documentation Index](../../README.md#documentation-index)
- [GOALS.md](../../GOALS.md) — Phase status and completed work
- [governance/prompts/reviews/](../../governance/prompts/reviews/) — 19 consolidated review prompts (preferred, replaces individual persona/panel files)
- [governance/personas/agentic/](../../governance/personas/agentic/) — 5 agentic personas (DevOps Engineer, Code Manager, Coder, IaC Engineer, Tester)
- [docs/architecture/governance-model.md](../architecture/governance-model.md) — Governance layers, policy profiles, and how changes flow through the system
- [docs/configuration/repository-setup.md](../configuration/repository-setup.md) — Repository settings, CODEOWNERS, per-project overrides
- [docs/architecture/context-management.md](../architecture/context-management.md) — Context tiers, capacity detection, shutdown protocol
- [governance/prompts/startup.md](../../governance/prompts/startup.md) — Agentic loop entry point (full protocol)
- [governance/prompts/checkpoint-resumption-workflow.md](../../governance/prompts/checkpoint-resumption-workflow.md) — Checkpoint recovery protocol
