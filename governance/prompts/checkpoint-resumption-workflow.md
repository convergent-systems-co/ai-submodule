# Checkpoint Resumption Workflow

This workflow describes how to resume an agentic session from a checkpoint file after a context reset. It is the counterpart to the Context Capacity Shutdown Protocol in `startup.md`.

## Prerequisites

- A checkpoint file exists in `.governance/checkpoints/`, written by the shutdown protocol
- The user has run `/clear` to reset context
- The agent has re-read `startup.md` and this workflow

## Resumption Steps

### Step 1: Locate the Checkpoint

Find the most recent checkpoint file:

```bash
ls -t .governance/checkpoints/*.json | head -1
```

Read the checkpoint file and parse its contents. The file conforms to `governance/schemas/checkpoint.schema.json`.

### Step 2: Validate Checkpoint Integrity

Before resuming, verify the checkpoint is usable:

1. **Git state must be clean** — if `git_state` is `"dirty"`, the shutdown protocol did not complete correctly. Run `git status` to assess the situation. Commit or stash any pending changes before proceeding.
2. **Branch exists** — verify the checkpoint's `branch` still exists:
   ```bash
   git branch --list "<branch>"
   ```
3. **Timestamp is recent** — if the checkpoint is older than 24 hours, the issue landscape may have changed significantly. Consider running a fresh scan (Phase 1 of startup.md) instead of resuming.

### Step 3: Validate Issue State

**Critical: Closed issues represent a user decision. Never resume work on a closed issue.**

For `current_issue` (if not null):
```bash
gh issue view <number> --json state --jq '.state'
```
- If **closed**: Remove from work queue. Do not resume this issue.
- If **open**: May resume from `current_step`.

For each issue in `issues_remaining`:
```bash
gh issue view <number> --json state --jq '.state'
```
- Remove any closed issues from the remaining queue.
- Re-validate that remaining issues are still actionable (not labeled `blocked`, `wontfix`, `duplicate`, or assigned to a human).

### Step 4: Validate PR State

For each PR in `prs_remaining`:
```bash
gh pr view <number> --json state --jq '.state'
```
- If **MERGED** or **CLOSED**: Remove from the queue.
- If **OPEN**: Will need to enter Phase 4 (Evaluation & Review) of startup.md.

For each PR in `prs_created`:
```bash
gh pr view <number> --json state --jq '.state'
```
- If **OPEN**: Enter Phase 1c (Resolve Open PRs) of startup.md to complete the review cycle.
- If **MERGED**: No action needed.
- If **CLOSED** (not merged): Investigate why — the PR may need to be recreated.

### Step 5: Determine Entry Point

Based on the checkpoint state, determine where to re-enter the startup sequence:

| Checkpoint State | Entry Point |
|-----------------|-------------|
| `prs_remaining` is non-empty | Phase 1c (Resolve Open PRs) |
| `current_issue` is set and still open | Resume at `current_step` |
| `current_issue` is closed or null, `issues_remaining` has open issues | Phase 2b (Validate Intent) with next remaining issue |
| All issues closed and no PRs open | Phase 1d (Scan Open Issues) for a fresh scan |

### Step 6: Restore Context and Resume

1. **Check out the appropriate branch:**
   - If resuming a PR: `gh pr checkout <pr-number>`
   - If resuming an issue mid-implementation: `git checkout <branch>`
   - If starting fresh: stay on `main`

2. **Re-read the plan** (if resuming mid-implementation):
   ```bash
   cat .governance/plans/<issue-number>-*.md
   ```
   Review the plan to recall what was done and what remains.

3. **Account for session limits:**
   - The new session starts its own 3-issue counter at zero.
   - The checkpoint's `issues_completed` array records what was done in the *previous* session — it does not count toward the new session's cap.
   - However, if the same issue spans multiple sessions (e.g., checkpoint mid-Phase 4), completing it counts as 1 issue in the new session.

4. **Enter the startup sequence** at the determined entry point.

## Error Handling

| Error | Action |
|-------|--------|
| Checkpoint file is missing or corrupt | Fall back to Phase 1 of startup.md (fresh scan) |
| Git branch from checkpoint no longer exists | Check if the PR was merged; if so, move to next issue. If not, investigate. |
| All remaining issues are closed | Run Phase 1 of startup.md for a fresh scan |
| Checkpoint is older than 24 hours | Treat as stale; run Phase 1 of startup.md instead |
| `git_state: "dirty"` in checkpoint | Resolve git state manually before resuming |

## Integration with Startup Loop

When `startup.md` is invoked after a `/clear`:

1. Check if `.governance/checkpoints/` contains recent files (< 24 hours)
2. If yes, prompt the user: "Found checkpoint from [timestamp]. Resume from checkpoint or start fresh?"
3. If the user chooses to resume, execute this workflow
4. If the user chooses fresh start (or no checkpoint exists), execute startup.md from the beginning

## Schema Reference

Checkpoint files must conform to `governance/schemas/checkpoint.schema.json`. Key fields:

| Field | Type | Required | Purpose |
|-------|------|----------|---------|
| `timestamp` | date-time | Yes | When the checkpoint was created |
| `branch` | string | Yes | Git branch at shutdown |
| `issues_completed` | string[] | Yes | Issues finished in previous session |
| `issues_remaining` | string[] | Yes | Issues not yet started (must re-validate) |
| `current_issue` | string/null | No | Issue in progress at shutdown |
| `current_step` | string | No | Startup step active at shutdown |
| `git_state` | "clean"/"dirty" | Yes | Must be "clean" for valid resume |
| `review_cycle` | int/null | No | PR review cycle number if in Phase 4 |
