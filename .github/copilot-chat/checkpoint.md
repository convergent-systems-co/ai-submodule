Stop all current work immediately and execute the Context Capacity Shutdown Protocol.

## Steps

1. **Stop execution** -- do not start any new task, issue, or step.

2. **Clean git state**:
   - Run `git status` on every branch touched this session.
   - If there are uncommitted changes, commit them with a `wip:` prefix (e.g., `wip: checkpoint in-progress work`).
   - If a merge is in progress, run `git merge --abort`.
   - If a rebase is in progress, run `git rebase --abort`.
   - Verify `git status` shows `nothing to commit, working tree clean`.

3. **Write a checkpoint file** to .artifacts/checkpoints/{timestamp}-{branch}.json` where `{timestamp}` is `YYYYMMDD-HHMMSS` and `{branch}` is the current branch name (with slashes replaced by dashes). The file must contain:
   ```json
   {
     "timestamp": "ISO-8601 timestamp",
     "branch": "current branch name",
     "issues_completed": ["#N", "#M"],
     "prs_resolved": ["#P", "#Q"],
     "issues_remaining": ["#X", "#Y"],
     "prs_remaining": ["#R"],
     "current_issue": "#Z or null",
     "current_step": "Phase N description of what was in progress",
     "git_state": "clean",
     "pending_work": "description of what remains to be done",
     "prs_created": ["#A", "#B"],
     "manifests_written": ["manifest-id-1"],
     "branches_touched": ["branch-1", "branch-2"],
     "review_cycle": "current review cycle number if in Phase 4, else null"
   }
   ```
   Create the `.artifacts/checkpoints/` directory if it does not exist.

4. **Report to user** -- print a summary:
   - What was completed this session (issues, PRs)
   - What remains (issues, PRs, pending work)
   - The checkpoint file path
   - Current git state confirmation

5. **Offer two options**:
   - **Option A (recommended if context is high):** Run `/clear` to reset context, then resume with: `Resume from checkpoint: .artifacts/checkpoints/{checkpoint-file}`
   - **Option B (if context capacity permits):** Continue working from the current state.

## Important

- Never allow context to reach compaction with uncommitted changes, merge conflicts, or untracked state.
- A dirty compaction loses instructions and context that cannot be recovered.
- This protocol is defined in `docs/architecture/context-management.md` (Capacity Shutdown Protocol section).
