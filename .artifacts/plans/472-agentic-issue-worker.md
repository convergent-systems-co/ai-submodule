# CI-native issue-to-PR worker with governance gate

**Author:** Claude (Coder persona)
**Date:** 2026-02-27
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/472
**Branch:** NETWORK_ID/feat/472/agentic-issue-worker

---

## 1. Objective

Create a GitHub Actions workflow that automates the issue-to-PR pipeline: it claims issues labeled `agentic-ready`, assesses complexity, generates plans for complex issues, delegates implementation to the reusable `agentic-loop.yml` convergence loop, and creates PRs that automatically trigger the existing `dark-factory-governance.yml` governance gate. The workflow also supports human feedback via `/agentic-retry:` comments and self-dispatches to process queued issues.

## 2. Rationale

The existing `issue-monitor.yml` and `event-trigger.yml` workflows handle issue evaluation and dispatch but lack the full pipeline: claiming, planning, agentic execution, result handling, retry, and self-dispatch. This dedicated worker workflow closes the loop from issue to governance-approved PR.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Extend issue-monitor.yml | Yes | Would overload a workflow designed for evaluation/dispatch; violates single-responsibility |
| Extend event-trigger.yml | Yes | Event-trigger is a thin routing layer; adding execution logic would conflate concerns |
| New dedicated workflow | Yes | **Selected** -- clean separation, clear trigger surface, composable with agentic-loop.yml |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.github/workflows/agentic-issue-worker.yml` | CI-native issue-to-PR worker with 6-job pipeline |
| `.governance/plans/472-agentic-issue-worker.md` | This plan |

### Files to Modify

| File | Change Description |
|------|-------------------|
| N/A | No existing files modified |

### Files to Delete

| File | Reason |
|------|--------|
| N/A | No files deleted |

## 4. Approach

1. Create `.github/workflows/agentic-issue-worker.yml` with triggers: `issues.labeled`, `issue_comment.created`, `workflow_dispatch`
2. Implement Job 1 (`select-issue`): filter by label/comment, claim issue, detect/create branch, check for existing plan
3. Implement Job 2 (`assess-complexity`): classify issue as simple/complex based on body length and keywords
4. Implement Job 3 (`create-plan`): generate plan markdown for complex issues, commit to branch, post as issue comment
5. Implement Job 4 (`run-agent`): call `agentic-loop.yml` reusable workflow with task prompt and plan content
6. Implement Job 5 (`handle-result`): post success/failure comments, manage labels, self-dispatch to next issue
7. Implement Job 6 (`handle-retry`): parse `/agentic-retry:` feedback, re-call agentic loop with human guidance

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| YAML Lint | Workflow file | Validate YAML syntax is correct |
| Manual dispatch | Full pipeline | Test via `workflow_dispatch` with a known issue number |
| Label trigger | Jobs 1-5 | Apply `agentic-ready` label to a test issue |
| Retry trigger | Job 6 | Post `/agentic-retry: <feedback>` comment on an in-progress issue |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| agentic-loop.yml not yet merged (PR #471) | High | Medium | Workflow references it via `uses:` -- will fail gracefully until #471 lands; no runtime dependency at merge time |
| Infinite self-dispatch loop | Low | High | Guard: only dispatch if queued issues exist and current run succeeded; concurrency group prevents overlap |
| Label race conditions | Low | Medium | Atomic label swap (add in-progress, remove ready) in a single step; concurrency group per issue |
| Comment parsing edge cases | Medium | Low | Strict regex for `/agentic-retry:` prefix; ignore non-matching comments early |

## 7. Dependencies

- [ ] PR #471 (agentic-loop.yml reusable workflow) -- non-blocking; this workflow can merge first, but Job 4 will skip until #471 lands

## 8. Backward Compatibility

Fully additive. No existing workflows or files are modified. The new workflow only activates on explicit label application or comment patterns.

## 9. Governance

Expected panel reviews and policy profile:

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New workflow file with significant logic |
| security-review | Yes | Workflow has write permissions to contents, PRs, issues |
| threat-modeling | Yes | Automated pipeline with self-dispatch capability |
| cost-analysis | Yes | Workflow consumes GitHub Actions minutes |
| documentation-review | Yes | Plan document included |
| data-governance-review | Yes | Default required panel |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Use `uses: ./.github/workflows/agentic-loop.yml` for Job 4 | Composable reusable workflow pattern per issue #471 spec |
| 2026-02-27 | Self-dispatch via `gh workflow run` in handle-result | Matches existing event-trigger.yml pattern for workflow chaining |
| 2026-02-27 | Concurrency with `cancel-in-progress: false` | Prevent premature cancellation of in-progress agent runs |
