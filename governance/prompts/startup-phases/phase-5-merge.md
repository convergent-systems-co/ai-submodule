# Phase 5: Merge & Loop

**Personas:** Code Manager (merge), DevOps Engineer (checkpoint)

> **Context Gate -- Phase 5 Entry:** Execute the Context Gate protocol from startup.md before proceeding. Yellow tier: proceed with merge but do not loop back to Phase 1. Orange/Red: execute Shutdown Protocol immediately -- do not merge (leave PRs open for next session).

### 5a: Merge

1. Verify branch is up to date: `git fetch origin main && git merge origin/main`
2. Final push if merge was needed
3. Wait for final governance run
4. Merge: `gh pr merge <pr-number> --squash --delete-branch`
5. Close issue: `gh issue close <number> --comment "Merged via PR #<pr-number>. All governance checks passed."`

### 5b: Retrospective

Per `governance/prompts/retrospective.md`:

1. Evaluate planning accuracy, review cycle count, token cost
2. **Verify documentation completeness** -- check `GOALS.md`, `README.md`, `DEVELOPER_GUIDE.md`, `CLAUDE.md` for consistency. If gaps found, create a follow-up `docs` issue.
3. Post findings on closed issue
4. Update plan status to `completed`
5. **Commit the agent audit log** -- ensure the session log file (`.governance/state/agent-log/{session-id}.jsonl`) is committed. Include it in the PR commit or as a separate commit on the branch before merge:

   ```bash
   git add .governance/state/agent-log/
   git commit -m "audit: add agent session log for ${SESSION_ID}" --allow-empty
   ```

   If multiple PRs were created this session, commit the log file with the final PR. The log is append-only and captures the full session's agent protocol messages.

### 5c: Loop or Shutdown

After all parallel work from this batch is merged, decide whether to **continue** or **stop**:

1. **Check hard-stop conditions** (any one triggers Shutdown Protocol):
   - N or more issues/PRs completed this session (cumulative across all batches), where N = `governance.parallel_coders` (ignored when N = -1)
   - Any context pressure signal (see Detection Signals in startup.md)
2. **If a hard-stop condition is met**: execute the Shutdown Protocol -- checkpoint, clean git, report, and tell the user to run `/clear`. The next `/startup` will auto-restore from the checkpoint. Do not ask the user to "restart the loop" or take any other action beyond `/clear`.
3. **If NO hard-stop condition is met**: **return to Phase 1 immediately**. Do not write a checkpoint. Do not request `/clear`. Do not pause for user input. Do not summarize or ask permission to continue. Just loop -- the agent keeps working autonomously until a hard-stop condition or exit condition is reached.

### 5d: GOALS.md Fallback

If no actionable issues remain after Phase 1d:

1. Scan `GOALS.md` for unchecked items
2. Filter out items with existing open issues
3. Prioritize by phase (4b before 5)
4. Create a GitHub issue for the highest-priority actionable item
5. Enter Phase 2 with the new issue
6. If no items are actionable, exit the loop
