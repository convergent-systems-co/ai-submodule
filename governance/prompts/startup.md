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
| 1 | Pre-flight & Triage | Scan issues, select work batch. Report `issues_selected`. |
| 2 | Parallel Planning | Create plans for each issue. Report `plans`. |
| 3 | Parallel Dispatch | Spawn Coder agents per `tasks` list. Report `dispatched_task_ids`. |
| 4 | Collect & Review | Wait for agents, run Tester eval. Report `prs_created`, `prs_resolved`. |
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

## Phase Details

### Phase 1: Pre-flight & Triage
1. Scan Dependabot alerts: `gh api repos/{owner}/{repo}/dependabot/alerts --jq '[.[] | select(.state == "open")]'`
2. Run `gh issue list --state open --json number,title,labels,assignees`
3. Filter/prioritize by labels and project conventions. Interleave dependabot alerts by severity (critical/high = P0/P1).
4. Select up to N work items — issues + dependabot alerts (N = `parallel_coders` from project.yaml)
5. Complete: `step --complete 1 --result '{"issues_selected": ["#N", ...], "dependabot_alerts": ["dependabot-1", ...]}'`

### Phase 2: Parallel Planning
1. For each selected issue, read the issue body and comments
2. Create implementation plans in `.governance/plans/`
3. Complete: `step --complete 2 --result '{"plans": {"#42": "plan content", ...}}'`

### Phase 3: Parallel Dispatch
1. Parse `tasks` from the step result — each has persona, branch, plan details
2. For each task, spawn an agent using the Task tool with worktree isolation
3. Complete: `step --complete 3 --result '{"dispatched_task_ids": ["cc-abc123", ...]}'`

### Phase 4: Collect & Review
1. Wait for dispatched agents to complete
2. Run Tester persona evaluation on each result
3. Handle FEEDBACK (re-dispatch) or APPROVE outcomes
4. Complete: `step --complete 4 --result '{"prs_created": [...], "prs_resolved": [...], "issues_completed": [...]}'`

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
- Plans before code (`.governance/plans/`)
- Panel reviews execute on every change
- Documentation updates with every commit
- `jm-compliance.yml` is enterprise-locked — never modify

<!-- /ANCHOR -->
