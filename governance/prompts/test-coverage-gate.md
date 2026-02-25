# Test Coverage Gate

**Mandatory pre-push quality gate.** This step runs AFTER implementation and tests are written, BEFORE any `git push`. It is a blocking gate — the push must not proceed until all checks pass.

## When to Execute

- **Always** after Step 6 (Execute) in the startup loop, before pushing the branch
- **Always** after Step 7d (Implement Recommendations), before pushing review-cycle fixes
- **Always** before any `git push` that will trigger CI

## Prerequisites

- Implementation is complete (code changes committed)
- Tests are written (test files committed)
- Working tree is clean (`git status` shows no uncommitted changes)

## Gate Procedure

### 1. Detect Test Runner

Determine the project's test runner from `project.yaml`, common config files, or directory conventions:

```bash
# Check for pytest (Python)
test -f pytest.ini || test -f pyproject.toml || test -f setup.cfg && echo "pytest"

# Check for jest/vitest (JavaScript/TypeScript)
test -f jest.config.js || test -f jest.config.ts || test -f vitest.config.ts && echo "jest/vitest"

# Check for go test (Go)
test -f go.mod && echo "go test"

# Check for cargo test (Rust)
test -f Cargo.toml && echo "cargo test"
```

If no test runner is detected, check `project.yaml` for `test_command`. If still none, log a warning and skip to Step 5 (the gate passes with a warning, not a block).

### 2. Run Tests

Execute the full test suite. The command must exit cleanly (exit code 0).

```bash
# Python example
python -m pytest tests/ -v --tb=short

# JavaScript example
npm test

# Go example
go test ./...
```

**If tests fail:**
1. Read the failure output
2. Identify the failing tests and root cause
3. Fix the code or tests (adopt Coder persona)
4. Commit the fix (isolated commit: `fix: correct failing test in <module>`)
5. **Re-run this gate from Step 2** — do not proceed until all tests pass

Maximum fix attempts: **3**. If tests still fail after 3 attempts, escalate to the Code Manager with the failure details. Do not push.

### 3. Run Coverage Check

Execute the test suite with coverage measurement. The minimum threshold is **80%** on changed/new code.

```bash
# Python example
python -m pytest tests/ --cov=<source-package> --cov-report=term-missing --cov-fail-under=80

# JavaScript example (jest)
npx jest --coverage --coverageThreshold='{"global":{"lines":80}}'

# Go example
go test ./... -coverprofile=coverage.out && go tool cover -func=coverage.out
```

**If coverage is below 80%:**
1. Identify uncovered lines from the coverage report
2. Write additional tests targeting the uncovered code paths
3. Commit the new tests (isolated commit: `test: add coverage for <module>`)
4. **Re-run this gate from Step 2** — coverage must meet the threshold

Maximum coverage-fix attempts: **3**. If coverage still fails after 3 attempts, log the current coverage percentage, list the uncovered modules, and escalate. Do not push.

### 4. Verify Test Completeness

Check that every new or modified source file has corresponding test coverage:

1. **List changed files** in this branch vs. the base branch:
   ```bash
   git diff --name-only origin/main...HEAD -- '*.py' '*.js' '*.ts' '*.go' '*.rs'
   ```

2. **For each changed source file**, verify a corresponding test file exists:
   - `src/foo.py` → `tests/test_foo.py` or `tests/foo_test.py`
   - `src/foo.ts` → `src/foo.test.ts` or `tests/foo.test.ts`
   - `pkg/foo/foo.go` → `pkg/foo/foo_test.go`

3. **Log any gaps** — files without corresponding tests. This is a **warning**, not a block (some files like configs, type definitions, or pure data files don't need tests).

### 5. Gate Decision

| Condition | Result |
|-----------|--------|
| All tests pass AND coverage >= 80% | **PASS** — proceed to push |
| Tests fail after 3 fix attempts | **BLOCK** — escalate, do not push |
| Coverage below 80% after 3 attempts | **BLOCK** — escalate, do not push |
| No test runner detected | **WARN** — proceed with warning logged |
| No tests exist for this project | **WARN** — proceed with warning logged |

### 6. Log Result

Record the gate result for the review cycle summary (Step 7e):

```
## Test Coverage Gate
- **Tests:** <PASS/FAIL> (<N> tests, <M> failures)
- **Coverage:** <X>% (threshold: 80%)
- **Uncovered files:** <list or "none">
- **Fix attempts:** <N>
- **Gate result:** <PASS/BLOCK/WARN>
```

## Integration Points

- **Step 6 (Execute & Push PR):** Run this gate after Step 6.3 (write tests) and before Step 6.6 (push the branch)
- **Step 7d (Implement Recommendations):** Run this gate after implementing recommendation fixes and before pushing
- **Step 7f (Push and Re-run Governance):** This gate must have passed before any push in Step 7f

## Failure Escalation

When the gate blocks:
1. Comment on the issue with the gate result (test failures, coverage gaps)
2. The Code Manager decides whether to:
   - Assign additional test writing to the Coder
   - Escalate to human review with the coverage report
   - Accept the coverage gap with documented rationale (only for non-critical changes)

## Principles

- Tests must pass before push — broken tests never reach CI
- 80% coverage is the floor, not the ceiling
- Coverage gaps must be explicit and documented, never silent
- The gate runs every time, no exceptions — it is cheaper to catch failures locally than in CI
- Fix attempts are bounded to prevent infinite loops
