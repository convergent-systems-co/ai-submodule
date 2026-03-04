# Plan: VHS Tape End-to-End Testing (#748)

## Objective

Create VHS tape-based end-to-end tests that validate the `dark-governance` CLI binary's consumer repo installation flow. These tape files serve as both regression tests and documentation demos.

## Scope

This plan covers the **scoped subset** from the issue: creating the E2E test infrastructure and initial tape files for `install` and `init` commands. The full 5-tape recording suite (first-pr, agentic-loop, cli-only, update) depends on binary capabilities not yet shipped (#743, #744, #745) and is out of scope for this iteration.

## Files to Create

### 1. `tests/e2e/install-test.tape`
VHS tape file that:
- Creates a temp directory as a mock consuming repo
- Runs `dark-governance install` (or mocks it if binary not built)
- Verifies expected files/directories are created
- Verifies lockfile is written
- Runs `dark-governance verify` to check integrity

### 2. `tests/e2e/init-test.tape`
VHS tape file that:
- Creates a temp directory, initializes git
- Runs `dark-governance init`
- Verifies project.yaml, CLAUDE.md, .github/workflows/, .artifacts/ created
- Verifies .dark-governance.lock written

### 3. `tests/e2e/run-tests.sh`
Executable script that:
- Checks if `vhs` CLI is installed
- Skips gracefully with informative message if not
- Iterates over all `.tape` files in `tests/e2e/`
- Runs each tape, captures exit code
- Reports pass/fail summary

### 4. `docs/guides/e2e-testing.md`
Developer guide covering:
- How to install VHS
- How to run existing tapes
- How to write new tape files
- CI integration notes

### 5. `src/Makefile` update
- Add `test-e2e` target that invokes `tests/e2e/run-tests.sh`

## Design Decisions

- Tape files use VHS DSL (charmbracelet/vhs) — `Type`, `Enter`, `Sleep`, `Output`
- Tests are self-contained: each tape creates its own temp directory and cleans up
- `run-tests.sh` exits 0 if VHS not installed (skip, not fail) for CI environments without VHS
- Golden file comparison deferred to a later iteration (requires stable binary output)

## Dependencies

- VHS CLI (optional — tests skip gracefully without it)
- `dark-governance` binary (tests reference it but can be run with a mock/placeholder)

## Acceptance Criteria

- [ ] `tests/e2e/install-test.tape` exists and is valid VHS syntax
- [ ] `tests/e2e/init-test.tape` exists and is valid VHS syntax
- [ ] `tests/e2e/run-tests.sh` runs and reports results
- [ ] `docs/guides/e2e-testing.md` explains how to use the test framework
- [ ] `make test-e2e` target works from `src/`
- [ ] All conventional commits on branch `itsfwcp/test/748/vhs-consumer-repo-test`
