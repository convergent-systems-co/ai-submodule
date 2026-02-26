# Plan: Convert issue-monitor workflow to manual trigger

**Issue:** #76 — Workflow for monitored task shouldn't run automatically yet
**Priority:** P0
**Type:** bug fix
**Status:** in_progress

## Problem

The `.github/workflows/issue-monitor.yml` workflow triggers automatically on `issues.opened` and `issues.labeled` events. This is premature — the autonomous pipeline should not run automatically yet.

## Solution

1. Replace `on: issues: types: [opened, labeled]` with `on: workflow_dispatch` with an `issue_number` input
2. Update all `github.event.issue.*` references to use `inputs.issue_number` and fetch issue data via API
3. Add issue state validation (check issue is open) since manual dispatch doesn't guarantee this
4. Pass `issue_title` as a job output from evaluate to dispatch-claude
5. Update documentation per Step 6.4

## Files Changed

- `.github/workflows/issue-monitor.yml` — Trigger and event reference changes
- `GOALS.md` — Add PR #74 to completed work (missed in last merge), add #76
- `.plans/76-workflow-manual-trigger.md` — This plan

## Risk

Low — only changes the trigger mechanism, no logic changes to evaluation or dispatch.
