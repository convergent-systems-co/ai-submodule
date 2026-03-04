# Workflow: Bug Fix

Systematic investigation and resolution of a bug, from reproduction through committed fix.

## Prerequisites

- Bug report (symptoms, steps to reproduce if available, affected environment)
- Access to the relevant codebase and logs

## Phases

1. **Reproduce** → `[BUG-1]`
2. **Investigate** → `[BUG-2]`
3. **Root Cause** → `[BUG-3]` — **GATE**
4. **Fix** → `[BUG-4]`
5. **Test** → `[BUG-5]`
6. **Review** → `[BUG-6]` — **GATE**
7. **Commit** → `[BUG-7]`

---

## Phase 1: Reproduce

> **Adopt persona:** `governance/personas/engineering/debugger.md`

### Input

- Bug report (symptoms, steps, environment)

### Process

1. Attempt to reproduce the bug using the reported steps
2. If reproducible, document the exact reproduction steps and observed behavior
3. If not reproducible, document what was tried and request more information
4. Identify the minimal reproduction case

### Output

**Artifact `[BUG-1]: Reproduction Report`**

```
## Reported Symptoms
<Summary from bug report>

## Reproduction Steps
1. <Step>
2. <Step>
...

## Observed Behavior
<What actually happens>

## Expected Behavior
<What should happen>

## Reproducible?
<Yes / No / Intermittent>

## Minimal Reproduction
<Shortest path to trigger the bug>

## Environment
<OS, runtime versions, relevant config>
```

---

## Phase 2: Investigate

> **Adopt persona:** `governance/personas/engineering/debugger.md`
> **Invoke prompt:** `governance/prompts/debug.md`

### Input

- `[BUG-1]: Reproduction Report`

### Process

1. Trace the execution path from the reproduction case
2. Identify where behavior diverges from expectation
3. Examine relevant code, logs, and state
4. Form hypotheses about the cause
5. Narrow down to the specific code location

### Output

**Artifact `[BUG-2]: Investigation Notes`**

```
## Execution Trace
<Key points in the code path>

## Divergence Point
<Where behavior goes wrong>

## Hypotheses
1. <Hypothesis> — <evidence for/against>
2. <Hypothesis> — <evidence for/against>

## Suspect Code
- `path/to/file:line` — <why this is suspicious>
```

---

## Phase 3: Root Cause

> **Adopt persona:** `governance/personas/engineering/debugger.md`

### Input

- `[BUG-1]: Reproduction Report`
- `[BUG-2]: Investigation Notes`

### Process

1. Confirm or eliminate each hypothesis from `[BUG-2]`
2. Identify the definitive root cause
3. Determine why the bug was introduced (missed case, wrong assumption, regression)
4. Assess blast radius — what else might be affected

### Output

**Artifact `[BUG-3]: Root Cause Analysis`**

```
## Root Cause
<Clear explanation of what causes the bug>

## Location
- `path/to/file:line` — <the problematic code>

## Why It Was Introduced
<Context — missed edge case, incorrect assumption, regression from change X, etc.>

## Blast Radius
<Other features/paths affected, or "Isolated to reported scenario">

## Proposed Fix Approach
<Brief description of how to fix it>
```

### GATE

**Stop.** Present `[BUG-3]` for review.

**Approval criteria:** Root cause is confirmed (not just a hypothesis). Fix approach is clear and scoped.

- **Approved** → proceed to Phase 4
- **Revise** → investigate further, re-present `[BUG-3]`

---

## Phase 4: Fix

> **Adopt persona:** `governance/personas/leadership/tech-lead.md`

### Input

- `[BUG-3]: Root Cause Analysis`

### Process

1. Implement the fix as described in `[BUG-3]`
2. Keep changes minimal — fix the bug, nothing else
3. Ensure the fix handles the blast radius items identified in `[BUG-3]`

### Output

**Artifact `[BUG-4]: Fix Summary`**

```
## Changes Made
- `path/to/file` — <description>
- ...

## Approach
<What was changed and why this approach>
```

---

## Phase 5: Test

> **Adopt persona:** `governance/personas/engineering/test-engineer.md`
> **Invoke prompt:** `governance/prompts/write-tests.md`

### Input

- `[BUG-1]: Reproduction Report`
- `[BUG-3]: Root Cause Analysis`
- `[BUG-4]: Fix Summary`

### Process

1. Write a regression test that reproduces the original bug (should fail without fix, pass with fix)
2. Add tests for blast radius scenarios from `[BUG-3]`
3. Run existing test suite to confirm no regressions
4. Verify all tests pass

### Output

**Artifact `[BUG-5]: Test Report`**

```
## Regression Test
- <test file> — reproduces original bug scenario

## Additional Tests
- <test file> — <what it covers>

## Test Results
<Pass/fail summary>

## Regressions
<None, or details>
```

---

## Phase 6: Review

> **Adopt persona:** `governance/personas/quality/code-reviewer.md`

### Input

- `[BUG-3]: Root Cause Analysis`
- `[BUG-4]: Fix Summary`
- `[BUG-5]: Test Report`
- The actual code diff

### Process

1. Verify the fix addresses the root cause
2. Check that the fix doesn't introduce new issues
3. Confirm regression test adequately covers the bug
4. Review for correctness and minimal scope

### Output

**Artifact `[BUG-6]: Review Verdict`**

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

**Stop.** Present `[BUG-6]` for review.

**Approval criteria:** Verdict is "Approved." Fix addresses root cause. Regression test exists.

- **Approved** → proceed to Phase 7
- **Changes Requested** → address findings, return to Phase 4 or 5 as needed, then re-present at Phase 6

---

## Phase 7: Commit

> **Invoke prompt:** `governance/prompts/commit.md`

### Input

- `[BUG-3]: Root Cause Analysis` (for commit message context)
- `[BUG-4]: Fix Summary`
- `[BUG-6]: Review Verdict`

### Process

1. Stage all relevant files
2. Write a commit message that describes the bug and the fix
3. Commit

### Output

**Artifact `[BUG-7]: Commit Reference`**

```
## Commit
<hash> — <commit message summary>

## Files Committed
- <file list>
```
