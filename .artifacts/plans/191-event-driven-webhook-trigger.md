# Event-Driven Webhook Trigger (Phase 5c)

**Author:** Team Lead (agentic)
**Date:** 2026-02-24
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/191
**Branch:** NETWORK_ID/feat/191/event-driven-webhook-trigger

---

## 1. Objective

Create a GitHub Actions workflow that triggers governance sessions on key repository events — issue creation, PR events, and deployment status changes. This completes the first of two remaining Phase 5c (Always-On Orchestration) items in GOALS.md.

## 2. Rationale

The existing `issue-monitor.yml` is manual-dispatch only (`workflow_dispatch`). The scheduled trigger from #74 handles periodic scans. What's missing is event-driven triggers — reacting immediately to events rather than waiting for manual dispatch or scheduled polling.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Extend issue-monitor.yml with event triggers | Yes | issue-monitor.yml is for single-issue dispatch; adding event triggers would mix concerns and break its concurrency model |
| Create a new dedicated event-trigger workflow | Yes (chosen) | Clean separation of concerns; event filtering and dispatch logic is distinct from the issue monitor |
| External webhook service | Yes | Out of scope for a config-only governance repo; GitHub Actions natively supports the required events |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.github/workflows/event-trigger.yml` | GitHub Actions workflow triggered by issue/PR/deployment events |
| `governance/docs/event-driven-triggers.md` | Documentation for adopting and configuring the event-driven trigger |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `config.yaml` | Add `event-trigger.yml` to the optional workflows list |
| `GOALS.md` | Check off "Event-driven webhook trigger" item |
| `CLAUDE.md` | Update Phase 5c status description if needed |
| `README.md` | Update Phase 5c description if needed |

### Files to Delete

None.

## 4. Approach

1. Create `event-trigger.yml` workflow with triggers for `issues.opened`, `issues.labeled`, `pull_request.opened`, `pull_request.synchronize`, `deployment_status`
2. Add event filtering logic — skip bot-created issues, skip draft PRs, skip issues with exclusion labels
3. Dispatch to the existing `issue-monitor.yml` workflow via `workflow_dispatch` (reuse existing evaluation + Claude dispatch)
4. Create documentation in `governance/docs/event-driven-triggers.md`
5. Add `event-trigger.yml` to `config.yaml` optional workflows list
6. Update GOALS.md to check off the item
7. Update CLAUDE.md and README.md Phase 5c descriptions as needed

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Validation | YAML syntax | Workflow YAML is valid |
| Manual | Consuming repo | Document how to test by creating an issue in a consuming repo |

No automated tests — this is a configuration-only repo with no test runner.

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Event storm (many issues created rapidly) triggers too many workflows | Low | Medium | Concurrency group prevents duplicate runs for the same issue |
| Bot-created issues trigger loops (agent creates issue → triggers workflow → agent picks it up) | Medium | High | Filter out bot-authored issues and issues labeled `refine`, `blocked`, etc. |
| Workflow dispatch token permissions | Low | Medium | Document required permissions; use GITHUB_TOKEN (default) |

## 7. Dependencies

- [x] issue-monitor.yml exists and handles single-issue dispatch (non-blocking — already exists)
- [x] config.yaml workflow copy pattern established (non-blocking — already exists)

## 8. Backward Compatibility

Fully additive. The new workflow is added to the `optional` list in config.yaml, so consuming repos only get it if they run `init.sh` after this update. Existing repos are unaffected.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New workflow file |
| security-review | Yes | Workflow permissions and event filtering |
| documentation-review | Yes | New docs file |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-24 | Use workflow_dispatch to call issue-monitor.yml rather than inline evaluation | Reuses existing actionability logic; DRY |
| 2026-02-24 | Add to optional (not required) workflows | Event triggers are opt-in; not all repos want automatic dispatch |
