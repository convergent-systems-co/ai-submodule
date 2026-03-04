# Startup: Orchestrator-Driven Agentic Loop

Execute this on agent launch. The Python orchestrator is the sole control plane — it holds the program counter and persists state to disk. You follow its instructions.

<!-- ANCHOR: This instruction must survive context resets -->

## Protocol

The orchestrator is a CLI step function. You call it, parse the JSON response, do the creative work it requests, then call it again. Repeat until it says `shutdown` or `done`.

### 1. Initialize

```bash
python -m governance.engine.orchestrator init --config project.yaml
```

Parse the JSON response. The `action` field tells you what to do.

### 2. Execute Phase

The response contains:
- `action`: What to do (`execute_phase`, `dispatch`, `collect`, `merge`, `loop`, `shutdown`, `done`)
- `phase`: Current phase number (0-5)
- `instructions`: Phase-specific guidance (name, description, outputs_expected)
- `gate_block`: Context gate status (print this verbatim)
- `signals`: Current capacity counters
- `work`: Issues selected, completed, PRs created

**Phase-specific behavior:**

| Phase | Name | Your Job |
|-------|------|----------|
| 1 | Pre-flight & Triage | Scan issues, select work batch. Report `issues_selected`. In PM mode, auto-spawns DevOps Engineer as background agent. |
| 2 | Parallel Planning | Create plans for each issue. Report `plans`. |
| 3 | Parallel Dispatch | Spawn Coder agents per `tasks` list (or Tech Leads in PM mode). Report `dispatched_task_ids`. |
| 4 | Collect & Review | Wait for agents, run Test Evaluator eval. Report `prs_created`, `prs_resolved`. |
| 5 | Merge & Loop | Merge approved PRs. Report `merged_prs`. |

### 3. Report Signals

As you work, report capacity signals:

```bash
# After tool calls (batch reporting OK)
python -m governance.engine.orchestrator signal --type tool_call --count 5

# After conversation turns
python -m governance.engine.orchestrator signal --type turn

# After completing an issue
python -m governance.engine.orchestrator signal --type issue_completed
```

### 4. Complete Phase

When you finish a phase's work, advance:

```bash
python -m governance.engine.orchestrator step --complete 1 --result '{"issues_selected": ["#42", "#43"]}'
```

The response tells you the next phase. Continue the loop.

### 5. Handle Terminal Actions

- **`shutdown`**: Write a checkpoint and exit cleanly. The `shutdown_info` field explains why.
- **`done`**: All work is complete. Summarize results and exit.

### 6. Check Gate Before Risky Work

Before dispatching agents or starting expensive operations:

```bash
python -m governance.engine.orchestrator gate --phase 3
```

If `would_shutdown` is true, skip the operation — the orchestrator will handle shutdown at the next `step` call.

## PM Mode (Project Manager Active)

When `governance.use_project_manager: true` is set in `project.yaml`, the orchestrator operates in PM mode with these differences:

- **Phase 1**: The step result includes a `devops_background_task` instruction. Spawn a DevOps Engineer as a background agent using this instruction. The DevOps Engineer handles pre-flight, issue triage with grouping, and runs a continuous PR operations loop (`governance/prompts/devops-operations-loop.md`) for the session duration.
- **Phase 3**: The step result dispatches **Tech Lead** agents instead of Coder agents. Each Tech Lead receives a batch of grouped issues and independently runs plan-dispatch-review-merge. The `dispatch_persona` field in instructions is set to `tech_lead`.

The DevOps Engineer background agent owns the post-PR lifecycle (governance panels, Copilot review, rebase, merge, issue closing), ensuring PRs created by Tech Leads do not sit unmerged.

See `governance/prompts/startup-pm-mode.md` for the full PM pipeline reference and `docs/architecture/project-manager-architecture.md` for the architecture overview.

## Phase Details

### Phase 1: Pre-flight & Triage

#### Pre-flight Cleanup
Before scanning issues, clean up stale worktrees from previous sessions:
```bash
bash governance/bin/cleanup-worktrees.sh
```
This removes worktrees older than 2 days and their orphaned branches.

1. Scan Dependabot alerts: `gh api repos/{owner}/{repo}/dependabot/alerts --jq '[.[] | select(.state == "open")]'`
2. Run `gh issue list --state open --json number,title,labels,assignees`
3. Load `governance/paved-roads-catalog.yaml` — match issue keywords against domain keywords to identify relevant JM Paved Roads repos. When triaging infrastructure-related issues, surface applicable paved-road repos so Coder agents can reference established patterns instead of generating non-standard implementations.
4. Filter/prioritize by labels and project conventions. Interleave dependabot alerts by severity (critical/high = P0/P1).
5. Select up to N work items — issues + dependabot alerts (N = `parallel_coders` from project.yaml)
6. Complete: `step --complete 1 --result '{"issues_selected": ["#N", ...], "dependabot_alerts": ["dependabot-1", ...]}'`

### Phase 2: Parallel Planning
1. For each selected issue, read the issue body and comments
2. Create implementation plans in `.artifacts/plans/`
3. Complete: `step --complete 2 --result '{"plans": {"#42": "plan content", ...}}'`

### Phase 3: Parallel Dispatch

**Coder scaling:** Read `coder_min`, `coder_max`, and `require_worktree` from the step result `instructions` (sourced from `project.yaml` governance section). Dispatch at least `coder_min` agents, up to `coder_max` agents. If `coder_max` is -1, dispatch is unlimited (bounded only by context pressure).

**Worktree isolation (mandatory by default):** When `require_worktree` is `true` (the default), all Coder agents MUST run in isolated git worktrees. The primary repo must remain on `main`. Use the Agent tool with `isolation: worktree` for each task. If worktree isolation is unavailable, fall back to sequential execution but never modify the primary repo working tree.

1. Parse `tasks` from the step result — each has persona, branch, plan details
2. Validate task count is within `[coder_min, coder_max]` range
3. For each task, spawn an agent using the Task tool with worktree isolation
4. Complete: `step --complete 3 --result '{"dispatched_task_ids": ["cc-abc123", ...]}'`

### Phase 4: Collect & Review
1. Wait for dispatched agents to complete
2. Run Test Evaluator persona evaluation on each result (4a) — APPROVE/FEEDBACK/BLOCK
3. Run security review (4b) and context-specific panels (4c)
4. **Dispatch Document Writer** — after Coder agents complete and before PR creation, spawn a Document Writer agent (`governance/personas/agentic/document-writer.md`) for each branch:
   - The Document Writer analyzes the diff of all changes on the branch
   - Runs `bin/check-doc-staleness.py` to detect stale counts, paths, and descriptions
   - Updates all affected documentation (CLAUDE.md, GOALS.md, README.md, docs/, etc.)
   - Commits documentation updates to the same branch with `docs:` conventional commits
5. Push PR and enter monitoring loop (4d)
6. **CI & Copilot Review Loop (4e)** — poll CI status, fetch and classify ALL Copilot recommendations (inline + review threads), implement or dismiss each one with rationale
7. **Copilot Recommendation Triage (4e-bis)** — create sub-issues for medium+ findings, track disposition, post Copilot Recommendation Summary table on the PR, verify all findings resolved before merge
8. **Pre-merge thread verification (4f)** — GraphQL `reviewThreads` query must show zero active unresolved threads before merge proceeds
9. Complete: `step --complete 4 --result '{"prs_created": [...], "prs_resolved": [...], "issues_completed": [...]}'`

**Mandatory:** Steps 6-8 are NOT optional. The policy engine blocks auto-merge when Copilot findings are unresolved (`copilot_findings_unresolved == true`) or Dependabot alerts are open (`dependabot_alerts_open == true`). See `governance/prompts/devops-operations-loop.md` for the full Outgoing Mode spec.

### Phase 5: Merge & Loop Decision
1. Merge approved PRs
2. Complete: `step --complete 5 --result '{"merged_prs": ["#100", ...]}'`
3. The orchestrator decides whether to loop or finish

## Status Check

At any time, check session state:

```bash
python -m governance.engine.orchestrator status
```

## Context Resets

If your context is reset (compaction, `/clear`):
1. Run `python -m governance.engine.orchestrator init` — it auto-detects the existing session
2. Continue from where you left off — all state is on disk

## Governance Pipeline

The governance pipeline still applies to every change:
- Plans before code (`.artifacts/plans/`)
- Panel reviews execute on every change
- Documentation updates with every commit
- `jm-compliance.yml` is enterprise-locked — never modify

<!-- /ANCHOR -->
