# Event-Driven Governance Triggers

## Overview

The `event-trigger.yml` workflow provides event-driven governance session dispatch. When key repository events occur — issue creation, labeling, or deployment failures — the workflow evaluates the event and dispatches to the `issue-monitor.yml` workflow for processing.

This is part of **Phase 5c (Always-On Orchestration)** and complements the existing mechanisms:

| Mechanism | Trigger | Use Case |
|-----------|---------|----------|
| `issue-monitor.yml` | Manual (`workflow_dispatch`) | Process a specific issue on demand |
| Scheduled triggers (#74) | Cron schedule | Periodic scans for unprocessed issues |
| **`event-trigger.yml`** | Repository events | Immediate reaction to new issues and deployments |

## Supported Events

| Event | Action | Behavior |
|-------|--------|----------|
| `issues.opened` | New issue created | Dispatches to issue-monitor if not bot-created and has no exclusion labels |
| `issues.labeled` | Label added to issue | Dispatches to issue-monitor if no exclusion labels remain (e.g., a priority label is added to an issue without `refine`) |
| `issues.unlabeled` | Label removed from issue | Dispatches to issue-monitor (e.g., when `refine` label is removed, making the issue actionable) |
| `pull_request.opened` | New PR created | Logged only — PRs are handled by `dark-factory-governance.yml` |
| `pull_request.synchronize` | PR updated with new commits | Logged only — PRs are handled by `dark-factory-governance.yml` |
| `deployment_status` | Deployment status changes | Logs deployment failures for drift monitoring |

## Event Filtering

The workflow filters out events that should not trigger governance sessions:

- **Bot-created issues** — Prevents feedback loops where an agent creates an issue that triggers another agent session
- **Issues with exclusion labels** — `blocked`, `wontfix`, `duplicate`, `refine` are skipped
- **Draft PRs** — Not ready for governance review
- **Bot-created PRs** — Handled by the governance workflow directly
- **Non-failure deployments** — Only deployment failures are monitored

## Architecture

```
Repository Event (issue created, labeled, deployment failure)
    |
    v
event-trigger.yml (filter job)
    |
    +-- Skip: bot-created, excluded labels, draft, non-failure deployment
    |
    +-- Dispatch: workflow_dispatch to issue-monitor.yml
            |
            v
        issue-monitor.yml (evaluate + dispatch-claude jobs)
            |
            +-- Evaluate actionability
            +-- Dispatch to Claude Code / Copilot
```

The event-trigger workflow does not evaluate issue actionability itself — it delegates to `issue-monitor.yml` which already has the full actionability evaluation logic. This avoids duplicating logic across workflows.

## Adoption in Consuming Repos

The workflow is listed as **optional** in `config.yaml`. Consuming repos receive it when running `bash .ai/bin/init.sh`:

```bash
bash .ai/bin/init.sh
```

The init script symlinks optional workflows from `.ai/.github/workflows/` into the consuming repo's `.github/workflows/` directory.

### Prerequisites

1. **`issue-monitor.yml` must be present and enabled** — the event-trigger dispatches to it
2. **`ANTHROPIC_API_KEY` secret** — required by issue-monitor's Claude dispatch job
3. **`actions: write` permission** — the event-trigger needs permission to dispatch other workflows

### Opting Out

To disable event-driven triggers while keeping other governance workflows:

1. Delete or disable `event-trigger.yml` in the consuming repo's `.github/workflows/`
2. The other governance workflows (governance review, issue monitor, plan archival) are unaffected

## Concurrency

The workflow uses a concurrency group keyed on the issue/PR number or deployment ID:

```yaml
concurrency:
  group: event-trigger-${{ github.event.issue.number || ... }}
  cancel-in-progress: true
```

This prevents duplicate dispatches if multiple events fire for the same issue in quick succession (e.g., issue opened and immediately labeled).

## Limitations

- **PR events are logged but not dispatched** — PRs are already handled by the existing `dark-factory-governance.yml` workflow. Adding PR dispatch to issue-monitor would be redundant.
- **Deployment failures are logged but not auto-triaged** — Future work (incident-to-DI automation) could create issues automatically from deployment failures. Currently, failures are logged as workflow annotations.
- **Requires `issue-monitor.yml`** — If the issue-monitor workflow is not present or enabled, the dispatch will fail with a non-blocking warning.
