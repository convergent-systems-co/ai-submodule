# Workflow: Refactoring

Safe, incremental code restructuring with verification at every step.

## Prerequisites

- Code to refactor (identified smell, tech debt, or structural improvement)
- Existing test coverage (or willingness to add it first)
- Clear goal for the refactoring (not just "make it better")

## Phases

1. **Analysis** → `[REF-1]` — **GATE**
2. **Strategy** → `[REF-2]` — **GATE**
3. **Execute** → `[REF-3.N]` — **per-step GATE**
4. **Verify** → `[REF-4]`
5. **Review** → `[REF-5]` — **GATE**

---

## Phase 1: Analysis

> **Adopt persona:** `governance/personas/engineering/refactor-specialist.md`

### Input

- Code to refactor (files, modules, or patterns)
- Motivation (why this refactoring is needed)

### Process

1. Read and understand the current code structure
2. Identify the specific code smells or structural issues
3. Map dependencies — what depends on this code, what does it depend on
4. Assess current test coverage of the code to be changed
5. Identify risks (behavioral changes, performance implications)

### Output

**Artifact `[REF-1]: Refactoring Analysis`**

```
## Current State
<Description of the code being refactored>

## Issues Identified
- <Code smell / structural issue>
- ...

## Dependency Map
- **Depended on by:** <list of callers/consumers>
- **Depends on:** <list of dependencies>

## Test Coverage
<Adequate / Gaps in: ...>

## Risks
- <Risk and severity>
- ...

## Goal State
<What the code should look like after refactoring>
```

### GATE

**Stop.** Present `[REF-1]` for review.

**Approval criteria:** Issues are clearly identified. Dependencies are mapped. Risks are acknowledged. Goal state is well-defined. Test coverage is adequate (or adding tests is included as a pre-step).

- **Approved** → proceed to Phase 2
- **Revise** → address feedback, re-present `[REF-1]`

---

## Phase 2: Strategy

> **Adopt persona:** `governance/personas/engineering/refactor-specialist.md`
> **Invoke prompt:** `governance/prompts/plan.md`

### Input

- `[REF-1]: Refactoring Analysis`

### Process

1. Break the refactoring into the smallest safe steps possible
2. Each step should keep the code in a working state (tests pass)
3. Order steps to minimize risk — easy/safe changes first
4. Identify which steps can be verified independently
5. Define rollback approach for each step

### Output

**Artifact `[REF-2]: Refactoring Strategy`**

```
## Approach
<High-level refactoring approach (e.g., extract class, inline function, split module)>

## Steps

### Step 1: <Name>
- **Change:** <what to do>
- **Verification:** <how to confirm it's safe>
- **Rollback:** <how to undo if needed>

### Step 2: <Name>
- **Change:** <what to do>
- **Verification:** <how to confirm it's safe>
- **Rollback:** <how to undo if needed>

...

## Pre-conditions
- <Any prep needed before starting — e.g., "add missing tests for X">
```

### GATE

**Stop.** Present `[REF-2]` for review.

**Approval criteria:** Steps are small and incremental. Each step keeps the code working. Verification method is defined for each step.

- **Approved** → proceed to Phase 3
- **Revise** → adjust strategy, re-present `[REF-2]`

---

## Phase 3: Execute

> **Invoke prompt:** `governance/prompts/refactor.md`
> **Secondary persona:** `governance/personas/engineering/test-engineer.md`

### Input

- `[REF-2]: Refactoring Strategy`

### Process

For each step in the strategy:

1. Execute the change described in the step
2. Run the verification defined for that step (typically: run tests)
3. Confirm the code still works
4. Document what was done

### Output (per step)

**Artifact `[REF-3.N]: Step N Result`**

```
## Step N: <Name>

### Changes Made
- `path/to/file` — <description>
- ...

### Verification Result
<Tests pass / Tests fail — details>

### Status
<Complete / Rolled back — reason>
```

### GATE (per step)

**Stop** after each step. Present `[REF-3.N]` for review.

**Approval criteria:** Verification passes. Changes match the strategy.

- **Approved** → proceed to next step (or Phase 4 if all steps complete)
- **Rollback** → undo step, revise strategy if needed

---

## Phase 4: Verify

> **Adopt persona:** `governance/personas/engineering/test-engineer.md`
> **Invoke prompt:** `governance/prompts/write-tests.md`

### Input

- `[REF-1]: Refactoring Analysis` (goal state)
- All `[REF-3.N]` artifacts
- Current code state

### Process

1. Run the full test suite
2. Add any missing tests for the new code structure
3. Verify the goal state from `[REF-1]` has been achieved
4. Confirm no behavioral changes (unless intentional)
5. Check for any remaining code smells

### Output

**Artifact `[REF-4]: Verification Report`**

```
## Full Test Suite
<Pass / Fail — details>

## New Tests Added
- <test file> — <what it covers>
- ...

## Goal State Achieved?
<Yes / Partially — what remains>

## Behavioral Changes
<None / List of intentional changes>

## Remaining Issues
<None / List of remaining smells or concerns>
```

---

## Phase 5: Review

> **Invoke panel:** `governance/prompts/reviews/code-review.md`

### Input

- `[REF-1]: Refactoring Analysis`
- `[REF-2]: Refactoring Strategy`
- `[REF-4]: Verification Report`
- The full code diff (all steps combined)

### Process

1. Review the overall refactoring for correctness
2. Verify the goal state has been achieved
3. Check that no behavioral changes were introduced unintentionally
4. Assess code quality of the result

### Output

**Artifact `[REF-5]: Review Verdict`**

```
## Verdict
<Approved / Changes Requested>

## Assessment
- **Goal achieved:** <Yes / No>
- **Behavioral preservation:** <Confirmed / Concerns>
- **Code quality:** <Assessment>

## Findings
- [severity] <finding>
- ...

## Required Changes (if any)
- <Change>
```

### GATE

**Stop.** Present `[REF-5]` for review.

**Approval criteria:** Verdict is "Approved." Goal state achieved. No unintended behavioral changes.

- **Approved** → refactoring is complete, commit the changes
- **Changes Requested** → address findings, re-present at Phase 5
