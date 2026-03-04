# Fix Governance Approval Enforcement

**Author:** Project Manager (agentic)
**Date:** 2026-03-02
**Status:** approved
**Issue:** #680
**Branch:** itsfwcp/fix/680/governance-approval-enforcement

---

## 1. Objective

Ensure the Dark Forge workflow only approves PRs when the policy engine decision is `auto_merge`. Currently, the workflow approves on `human_review_required`, which bypasses the intent of governance gates.

## 2. Rationale

The workflow at `.github/workflows/dark-factory-governance.yml` lines 393-398 unconditionally approves PRs when the decision is `human_review_required`. This defeats the purpose of governance — `human_review_required` means a human should review, not that the bot should auto-approve.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Remove human_review_required approval entirely | Yes — chosen | Most correct: only auto_merge should approve |
| Add conditions to human_review_required approval | Yes | Still auto-approves when human review was requested |

## 3. Scope

### Files to Modify

| File | Change Description |
|------|-------------------|
| `.github/workflows/dark-factory-governance.yml` | Remove or condition the approval step for `human_review_required`; only approve on `auto_merge` |

## 4. Approach

1. Read the workflow file and identify all approval steps
2. Change the `human_review_required` step to post a comment (not approval) stating human review is needed
3. Only the `auto_merge` step should use `gh pr review --approve`
4. Test by verifying workflow logic

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Manual | Workflow logic | Review YAML conditions for correctness |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PRs stop merging if no auto_merge path | Medium | Medium | Ensure auto_merge conditions are reachable for approved changes |

## 7. Dependencies

- [ ] None

## 8. Backward Compatibility

PRs that previously auto-merged on `human_review_required` will now require manual human review. This is the intended behavior.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| security-review | Yes | Workflow changes affect merge gates |
| code-review | Yes | CI/CD pipeline modification |

**Policy Profile:** default
**Expected Risk Level:** high

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Only approve on auto_merge | human_review_required is not an approval signal |
