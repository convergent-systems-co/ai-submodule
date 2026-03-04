---
name: global-dev-plan-create
description: "Create an implementation plan for a feature or fix"
status: production
tags: [dev, planning, architecture]
model: null
---

# Create Implementation Plan

Create a structured implementation plan before writing any code. Plans ensure alignment, reduce rework, and serve as the decision audit trail.

## Workflow

1. **Understand the requirement** -- read the issue, design document, or verbal description. Ask clarifying questions if anything is ambiguous.
2. **Analyze the codebase** to understand what exists:
   - Search for related code, types, and patterns
   - Identify which files will be created, modified, or deleted
   - Look for reusable utilities, base classes, or shared patterns
3. **Consider alternatives** -- think of at least two approaches before committing to one. Document why the chosen approach is preferred.
4. **Write the plan** using the structure below.
5. **Validate scope** -- if the plan exceeds what can be done in a single PR, break it into phases.

## Plan Structure

```markdown
# [Plan Title]

**Author:** [name or agent ID]
**Date:** [YYYY-MM-DD]
**Status:** draft
**Issue:** [link to GitHub issue]
**Branch:** [target branch name]

---

## 1. Objective
What does this change accomplish? State the outcome, not the activity.
One to three sentences maximum.

## 2. Rationale
Why this approach? What alternatives were considered?

| Alternative | Pros | Cons | Verdict |
|-------------|------|------|---------|
| Option A | ... | ... | Chosen / Rejected |
| Option B | ... | ... | Chosen / Rejected |

## 3. Scope

### Files to Create
| File | Purpose |
|------|---------|
| path/to/file | description |

### Files to Modify
| File | Change Description |
|------|-------------------|
| path/to/file | what changes and why |

### Files to Delete
| File | Reason |
|------|--------|
| path/to/file | why no longer needed |

## 4. Approach
Numbered steps. Each step is a discrete, reviewable unit of work.

1. Step one...
2. Step two...
3. Step three...

## 5. Testing Strategy
| Test Type | What | How |
|-----------|------|-----|
| Unit | core logic | mock dependencies, test edge cases |
| Integration | component interaction | test with real dependencies |
| Manual | user-facing flow | steps to verify manually |

## 6. Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Risk 1 | Low/Med/High | Low/Med/High | mitigation |

## 7. Dependencies
- Blocking: [list any blocking dependencies]
- Non-blocking: [list any non-blocking dependencies]

## 8. Backward Compatibility
Does this change break existing behavior? If yes, describe the migration path.
```

## Guidelines

- Be specific about file paths and function names, not vague ("update the auth module").
- The plan should be detailed enough that a different developer (or agent) could implement it without further clarification.
- Keep the plan under 200 lines. If it is longer, the scope is too large -- split into phases.
- Save the plan to `.governance/plans/` (or the project's configured plan directory).
- Do not start implementation until the plan is reviewed and approved.

## Anti-patterns to Avoid

- Plans that describe the solution but not the problem (missing "why")
- Plans with no alternatives considered (confirmation bias)
- Plans that conflate multiple unrelated changes (scope creep)
- Plans with vague testing ("add tests") instead of specific test scenarios
