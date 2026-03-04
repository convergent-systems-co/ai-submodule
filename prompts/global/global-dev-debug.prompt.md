---
name: global-dev-debug
description: "Systematic debugging workflow for errors and unexpected behavior"
status: production
tags: [dev, debug, troubleshooting]
model: null
---

# Systematic Debugging

Follow a structured debugging workflow to identify and resolve the reported issue.

## Phase 1: Understand the Problem

1. **Reproduce the error** -- get the exact error message, stack trace, or unexpected behavior description.
2. **Determine the expected behavior** -- what should happen vs. what actually happens?
3. **Identify when it started** -- did it work before? What changed recently? Check `git log --oneline -20` for recent commits.
4. **Gather environment context**:
   - Language/runtime version
   - OS and platform
   - Relevant dependency versions
   - Configuration that might affect behavior

## Phase 2: Isolate the Root Cause

1. **Read the stack trace** (if present) bottom-to-top. The first frame in user code is usually the most relevant.
2. **Trace the data flow** from input to the point of failure:
   - What values are passed to the failing function?
   - Are any values null, undefined, or of unexpected type?
   - Has the data been mutated unexpectedly?
3. **Check assumptions**:
   - Is the function being called with the arguments you expect?
   - Is the configuration loaded correctly?
   - Are environment variables set?
   - Is the database/API reachable and returning expected data?
4. **Use binary search** for hard-to-find issues:
   - If you have a working commit, use `git bisect` to find the breaking change.
   - If the issue is in a large function, add logging at midpoints to narrow down.
5. **Check common patterns**:
   - Off-by-one errors in loops or array indexing
   - Async/await missing (promise not awaited, callback not invoked)
   - Type coercion issues (string vs number, truthy/falsy)
   - Import/require path issues (wrong module loaded, circular dependency)
   - Race conditions (shared state, concurrent access)
   - Stale cache or build artifacts (try a clean build)

## Phase 3: Fix

1. **Write the minimal fix** that addresses the root cause, not the symptom.
2. **Verify the fix**:
   - Does the original error go away?
   - Does the expected behavior now work?
   - Do existing tests still pass?
3. **Add a regression test** that would have caught this bug.

## Phase 4: Prevent

1. **Why was this not caught?**
   - Missing test coverage?
   - Missing input validation?
   - Missing type safety?
   - Inadequate error handling?
2. **Recommend defensive measures**:
   - Add assertions or validation at the boundary where bad data entered.
   - Add logging that would make this faster to diagnose next time.
   - Consider stricter types or runtime checks.

## Output Format

```
## Root Cause
One-sentence summary of why the bug occurs.

## Analysis
Step-by-step explanation of how you traced the issue.

## Fix
Code changes needed (with file paths and line numbers).

## Regression Test
Test code that reproduces the original bug and verifies the fix.

## Prevention
Recommendations to avoid similar issues in the future.
```
