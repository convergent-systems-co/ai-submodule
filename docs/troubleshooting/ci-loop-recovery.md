# Troubleshooting: CI Cancellation Loops

This guide covers diagnosis and recovery when GitHub Actions workflows enter a cancellation loop — where runs cancel each other endlessly and no run completes.

## The Auto-Rebase Loop

**The most common loop** involves three workflows:

1. **Auto-Rebase Agent PRs** (`auto-rebase.yml`) — triggers on every push to `main`, rebases all open agent PRs (`NETWORK_ID/*` branches) with `--force-with-lease`
2. **Dark Forge** (`dark-factory-governance.yml`) — triggers on `pull_request: [opened, synchronize]`, has `cancel-in-progress: true` on its concurrency group
3. **Event-Driven Governance Trigger** (`event-trigger.yml`) — triggers on `pull_request` events and dispatches additional governance runs

### How the loop forms

```
push to main
  → auto-rebase fires, rebases open PR branch (force-push)
    → PR gets "synchronize" event
      → governance workflow starts new run
        → concurrency group cancels any in-progress governance run
          → if auto-rebase fires again (another push to main, or scheduled)
            → PR gets another "synchronize" event
              → governance workflow starts yet another run, cancelling the previous one
                → no run ever completes
```

The governance workflow's `review` job (which provides the bot approval required for merge) never finishes, so the PR stays in `REVIEW_REQUIRED` state indefinitely.

### Symptoms

- Multiple governance workflow runs show `cancelled` conclusion in quick succession
- The PR's `reviewDecision` stays `REVIEW_REQUIRED`
- `gh pr merge` fails with "Pull Request is not mergeable"
- New governance runs appear every 15-30 seconds

### Diagnosis

```bash
# Check for rapid cancellations on a PR branch
gh run list --workflow=dark-factory-governance.yml --limit 10 \
  --json databaseId,status,conclusion,headBranch,createdAt \
  --jq '.[] | select(.headBranch == "BRANCH_NAME") | {id: .databaseId, status: .status, conclusion: .conclusion, created: .createdAt}'

# Check if auto-rebase is firing
gh run list --workflow=auto-rebase.yml --limit 5 \
  --json databaseId,status,conclusion,createdAt \
  --jq '.[] | {id: .databaseId, status: .status, conclusion: .conclusion, created: .createdAt}'
```

If you see governance runs being cancelled every 15-30 seconds and auto-rebase runs completing in the same timeframe, this is the auto-rebase loop.

## Recovery Procedure

### Step 1: Disable the auto-rebase workflow

```bash
gh api -X PUT repos/{owner}/{repo}/actions/workflows/239591951/disable
```

Or by name:

```bash
# Get the workflow ID
WORKFLOW_ID=$(gh api repos/{owner}/{repo}/actions/workflows --jq '.workflows[] | select(.name == "Auto-Rebase Agent PRs") | .id')

# Disable it
gh api -X PUT "repos/{owner}/{repo}/actions/workflows/${WORKFLOW_ID}/disable"
```

### Step 2: Optionally disable the event-trigger workflow

If the loop persists after disabling auto-rebase, also disable the event-trigger:

```bash
WORKFLOW_ID=$(gh api repos/{owner}/{repo}/actions/workflows --jq '.workflows[] | select(.name == "Event-Driven Governance Trigger") | .id')
gh api -X PUT "repos/{owner}/{repo}/actions/workflows/${WORKFLOW_ID}/disable"
```

### Step 3: Cancel all in-progress/queued runs

```bash
gh run list --workflow=dark-factory-governance.yml --limit 10 \
  --json databaseId,status,headBranch \
  --jq '.[] | select(.headBranch == "BRANCH_NAME" and (.status == "in_progress" or .status == "queued")) | .databaseId' \
  | while read id; do gh run cancel "$id" 2>&1 || true; done
```

### Step 4: Wait for queue to drain

After cancelling, wait 10-15 seconds for the queue to fully clear:

```bash
sleep 15
gh run list --workflow=dark-factory-governance.yml --limit 3 \
  --json databaseId,status,headBranch \
  --jq '.[] | select(.headBranch == "BRANCH_NAME" and (.status == "in_progress" or .status == "queued"))'
```

If runs are still appearing, the event-trigger may need to be disabled too (Step 2).

### Step 5: Let governance complete

With auto-rebase and event-trigger disabled, push a trivial change (or wait for the next natural trigger) to get a clean governance run:

```bash
# Option A: Wait for the existing run to complete naturally

# Option B: Close and recreate the PR for a clean trigger
gh pr close NUMBER
git push origin --delete BRANCH_NAME
git checkout -b NEW_BRANCH_NAME
git push -u origin NEW_BRANCH_NAME
gh pr create --title "..." --body "..."
```

### Step 6: Merge the PR

Once the governance workflow completes and the bot approves:

```bash
gh pr merge NUMBER --squash --auto
```

### Step 7: Re-enable workflows

After merge, immediately re-enable both workflows:

```bash
# Re-enable auto-rebase
gh api -X PUT repos/{owner}/{repo}/actions/workflows/239591951/enable

# Re-enable event-trigger (if disabled)
WORKFLOW_ID=$(gh api repos/{owner}/{repo}/actions/workflows --jq '.workflows[] | select(.name == "Event-Driven Governance Trigger") | .id')
gh api -X PUT "repos/{owner}/{repo}/actions/workflows/${WORKFLOW_ID}/enable"
```

## Prevention

The root cause is that `auto-rebase.yml` fires on every push to `main` and force-pushes to open PR branches, which creates `synchronize` events that re-trigger the governance workflow.

Potential mitigations (not yet implemented):

1. **Add a rebase cooldown** — Skip rebasing PRs that were rebased within the last N minutes
2. **Exclude PRs with pending governance runs** — Check if a governance run is in progress before rebasing
3. **Use merge queue** — GitHub's merge queue avoids the rebase-retrigger problem
4. **Rate-limit the auto-rebase** — Change the trigger from `push: [main]` to schedule-only

## Related

- [CI Workflows Reference](../architecture/ci-workflows.md)
- [init.sh Failures](init-failures.md)
