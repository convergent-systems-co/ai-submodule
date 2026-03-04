# Workflow: Feature Implementation

End-to-end delivery of a new feature, from requirements gathering through committed code.

## Prerequisites

- Feature request or user story (even rough/informal is fine)
- Access to the relevant codebase
- Knowledge of which system/service this feature belongs to

## Phases

1. **Requirements** → `[FEAT-1]` — **GATE**
2. **Design** → `[FEAT-2]` — **GATE**
3. **Implementation** → `[FEAT-3]`
4. **Testing** → `[FEAT-4]`
5. **Review** → `[FEAT-5]` — **GATE**
6. **Commit** → `[FEAT-6]`

---

## Phase 1: Requirements

> **Adopt persona:** `governance/personas/leadership/product-manager.md`

### Input

- Raw feature request or user story
- Any existing context (conversations, tickets, screenshots)

### Process

1. Clarify the user problem being solved
2. Define acceptance criteria (concrete, testable)
3. Identify affected users and usage scenarios
4. List assumptions and open questions
5. Define what is explicitly out of scope

### Output

**Artifact `[FEAT-1]: Requirements Spec`**

```
## Problem Statement
<What user problem does this solve?>

## Acceptance Criteria
- [ ] <Criterion 1>
- [ ] <Criterion 2>
- ...

## User Scenarios
1. <Scenario>

## Assumptions
- <Assumption>

## Out of Scope
- <Item>

## Open Questions
- <Question>
```

### GATE

**Stop.** Present `[FEAT-1]` for review.

**Approval criteria:** Acceptance criteria are concrete and testable. Scope is clear. No critical open questions remain.

- **Approved** → proceed to Phase 2
- **Revise** → address feedback, re-present `[FEAT-1]`

---

## Phase 2: Design

> **Adopt persona:** `governance/personas/architecture/architect.md`
> **Invoke prompt:** `governance/prompts/plan.md`

### Input

- `[FEAT-1]: Requirements Spec`
- Relevant codebase context (existing patterns, conventions)

### Process

1. Identify which files/modules are affected
2. Determine the approach — new code, extension of existing, or both
3. Define the data model changes (if any)
4. Map out the API surface changes (if any)
5. Identify risks and edge cases
6. Produce a step-by-step implementation plan

### Output

**Artifact `[FEAT-2]: Design & Plan`**

```
## Approach
<High-level description of the design>

## Files Affected
- `path/to/file` — <what changes>
- ...

## Data Model Changes
<Schema changes, new types, etc. or "None">

## API Changes
<New/modified endpoints or interfaces, or "None">

## Implementation Steps
1. <Step>
2. <Step>
...

## Risks & Edge Cases
- <Risk/edge case and mitigation>
```

### GATE

**Stop.** Present `[FEAT-2]` for review.

**Approval criteria:** Design aligns with requirements. Implementation steps are clear and ordered. Risks are acknowledged with mitigations.

- **Approved** → proceed to Phase 3
- **Revise** → address feedback, re-present `[FEAT-2]`

---

## Phase 3: Implementation

> **Adopt persona:** `governance/personas/leadership/tech-lead.md`

### Input

- `[FEAT-1]: Requirements Spec`
- `[FEAT-2]: Design & Plan`

### Process

1. Follow implementation steps from `[FEAT-2]` in order
2. Write code that matches existing project conventions
3. Keep changes minimal — only what the feature requires
4. Note any deviations from the plan and why

### Output

**Artifact `[FEAT-3]: Implementation Summary`**

```
## Changes Made
- `path/to/file` — <description>
- ...

## Deviations from Plan
- <Deviation and reason, or "None">

## Known Limitations
- <Limitation, or "None">
```

---

## Phase 4: Testing

> **Adopt persona:** `governance/personas/engineering/test-engineer.md`
> **Invoke prompt:** `governance/prompts/write-tests.md`

### Input

- `[FEAT-1]: Requirements Spec` (acceptance criteria)
- `[FEAT-3]: Implementation Summary`

### Process

1. Write tests covering each acceptance criterion from `[FEAT-1]`
2. Add edge case tests identified in `[FEAT-2]`
3. Run existing test suite to confirm no regressions
4. Verify all new tests pass

### Output

**Artifact `[FEAT-4]: Test Report`**

```
## Tests Written
- <test file> — <what it covers>
- ...

## Coverage of Acceptance Criteria
- [ ] Criterion 1 → <test name>
- [ ] Criterion 2 → <test name>
- ...

## Test Results
<Pass/fail summary>

## Regressions
<None, or details>
```

---

## Phase 5: Review

> **Invoke panel:** `governance/prompts/reviews/code-review.md`

### Input

- `[FEAT-1]: Requirements Spec`
- `[FEAT-2]: Design & Plan`
- `[FEAT-3]: Implementation Summary`
- `[FEAT-4]: Test Report`
- The actual code diff

### Process

1. Review code against design and requirements
2. Check for correctness, readability, maintainability
3. Verify test coverage is adequate
4. Flag security, performance, or style concerns

### Output

**Artifact `[FEAT-5]: Review Verdict`**

```
## Verdict
<Approved / Changes Requested>

## Findings
- [severity] <finding>
- ...

## Required Changes (if any)
- <Change>
```

### GATE

**Stop.** Present `[FEAT-5]` for review.

**Approval criteria:** Verdict is "Approved" with no blocking findings.

- **Approved** → proceed to Phase 6
- **Changes Requested** → address findings, return to Phase 3 or 4 as needed, then re-present at Phase 5

---

## Phase 6: Commit

> **Invoke prompt:** `governance/prompts/commit.md`

### Input

- `[FEAT-1]: Requirements Spec` (for commit message context)
- `[FEAT-3]: Implementation Summary`
- `[FEAT-5]: Review Verdict`

### Process

1. Stage all relevant files
2. Write a commit message that references the feature and summarizes the change
3. Commit

### Output

**Artifact `[FEAT-6]: Commit Reference`**

```
## Commit
<hash> — <commit message summary>

## Files Committed
- <file list>
```
