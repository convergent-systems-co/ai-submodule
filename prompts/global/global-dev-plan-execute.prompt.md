---
name: global-dev-plan-execute
description: "Execute an existing implementation plan step by step"
status: production
tags: [dev, planning, execution, implementation]
model: null
---

# Execute Implementation Plan

Follow an existing implementation plan, executing each step methodically while tracking progress and decisions.

## Workflow

1. **Read the plan** in full before starting any work. Understand the objective, scope, and approach.
2. **Verify preconditions**:
   - Is the plan status `approved` or `in_progress`?
   - Are blocking dependencies resolved?
   - Is the branch created and up to date with the base branch?
   - Are required tools and dependencies available?
3. **Execute each step** in order (see execution protocol below).
4. **Update the plan** as you go -- record decisions, deviations, and completion status.
5. **Mark the plan as completed** when all steps are done and tests pass.

## Execution Protocol

For each step in the plan's Approach section:

### Before Starting the Step
- Re-read the step description and acceptance criteria.
- Check if previous steps introduced changes that affect this step.
- Identify the specific files you will touch.

### During the Step
- Make the changes described in the plan.
- If you need to deviate from the plan, document why in the Decision Log before proceeding.
- If you discover the plan is missing something, add it and note the addition.
- Keep changes focused -- do not fix unrelated issues you happen to notice (file a separate issue or note).

### After Completing the Step
- Run the project's test suite to verify nothing is broken.
- Run any linters or formatters the project uses.
- Verify the step's intended outcome is achieved.
- Commit the step with a descriptive message referencing the plan step number.

## Decision Tracking

When deviating from the plan, record the decision:

```markdown
| Date | Step | Decision | Rationale |
|------|------|----------|-----------|
| YYYY-MM-DD | Step N | What you decided | Why the plan changed |
```

Common reasons for deviation:
- The plan's approach does not work as expected (explain what failed)
- A simpler approach was discovered during implementation
- A dependency or API changed since the plan was written
- A risk materialized that requires a different approach

## Completion Checklist

Before marking the plan as complete:

- [ ] All steps in the Approach section are done
- [ ] All tests pass (existing and new)
- [ ] Linters and formatters pass
- [ ] Documentation is updated per the plan's scope
- [ ] The Decision Log captures all deviations
- [ ] The branch is clean (no uncommitted changes)
- [ ] Plan status is updated to `completed`

## Error Recovery

If a step fails:
1. Do not proceed to the next step.
2. Understand why it failed -- is it a bug in the plan, a missing prerequisite, or an implementation error?
3. If the fix is small (< 10 lines), apply it and document in the Decision Log.
4. If the fix requires rethinking the approach, stop and update the plan before continuing.
5. If the plan is fundamentally flawed, mark it as `abandoned` and create a new plan.

## Output Format

After executing each step, report:

```
## Step N: [title]
Status: complete | blocked | deviated
Changes: [files modified]
Tests: [pass/fail, number of tests]
Notes: [anything noteworthy]
```
