# Plan Template

Use this template when creating implementation plans. All plans must be saved to `governance/plans/` (Dark Forge repo) or `.artifacts/plans/` (consuming repos) with a descriptive filename (e.g., `.artifacts/plans/add-user-authentication.md`).

Both AI agents and human engineers use this template. Every section is required. If a section is not applicable, state "N/A" with a brief explanation.

---

## Instructions

Copy the template below into a new file. Fill in every section. Do not remove sections.

---

```markdown
# [Plan Title]

**Author:** [agent name or human author]
**Date:** [YYYY-MM-DD]
**Status:** [draft | in_review | approved | in_progress | completed | abandoned]
**Issue:** [link to GitHub issue or DI reference, if applicable]
**Branch:** [target branch name]

---

## 1. Objective

What does this change accomplish? State the outcome, not the activity.

## 2. Rationale

Why this approach? What alternatives were considered and why were they rejected?

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| [Option A] | Yes/No | [Reason] |
| [Option B] | Yes/No | [Reason] |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| [path] | [description] |

### Files to Modify

| File | Change Description |
|------|-------------------|
| [path] | [what changes and why] |

### Files to Delete

| File | Reason |
|------|--------|
| [path] | [why this file is no longer needed] |

## 4. Approach

Step-by-step implementation strategy. Each step should be a discrete, reviewable unit of work.

1. [Step 1 description]
2. [Step 2 description]
3. [Step 3 description]

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | [files/functions] | [what is tested] |
| Integration | [components] | [what interactions are tested] |
| E2E | [flows] | [what user flows are tested] |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| [Risk 1] | Low/Med/High | Low/Med/High | [How to mitigate] |
| [Risk 2] | Low/Med/High | Low/Med/High | [How to mitigate] |

## 7. Dependencies

- [ ] [Dependency 1 — blocking or non-blocking]
- [ ] [Dependency 2 — blocking or non-blocking]

## 8. Backward Compatibility

Does this change break existing behavior? If yes, describe the migration path.

## 9. Governance

Expected panel reviews and policy profile:

| Panel | Required | Rationale |
|-------|----------|-----------|
| [panel name] | Yes/No | [why this panel is needed] |

**Policy Profile:** [default | fin_pii_high | infrastructure_critical]
**Expected Risk Level:** [critical | high | medium | low | negligible]

## 10. Decision Log

Record decisions made during implementation that deviate from or extend this plan.

| Date | Decision | Rationale |
|------|----------|-----------|
| [YYYY-MM-DD] | [What was decided] | [Why] |
```

---

## Usage

### For AI Agents (Coder persona)

1. Create the plan file before writing any code.
2. Submit the plan to the Tech Lead for review.
3. Begin implementation only after plan status is `approved`.
4. Update the Decision Log section as you work.
5. Set status to `completed` when the branch is merged.

### For Human Engineers

1. Create the plan when starting non-trivial work.
2. Use it as a PR description or link it from the PR body.
3. The plan serves as the audit trail for architectural decisions.
4. Update the Decision Log for any deviations during implementation.
