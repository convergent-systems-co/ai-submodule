# init-test.tape — VHS end-to-end test for `dark-governance init`
#
# Validates that `dark-governance init` correctly scaffolds governance
# into a fresh consumer repository, including:
#   - .github/workflows/dark-factory-governance.yml
#   - CLAUDE.md
#   - .artifacts/ directory structure
#   - .dark-governance.lock lockfile
#
# Prerequisites:
#   - `dark-governance` binary on PATH (built via `cd src && make build`)
#   - VHS (https://github.com/charmbracelet/vhs)
#
# Run:
#   vhs tests/e2e/init-test.tape
#
# Output:
#   tests/e2e/output/init-test.gif

Output tests/e2e/output/init-test.mp4

Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"

# -- Setup: create a mock consumer repo --

Type "export TEST_REPO=$(mktemp -d)/my-consumer-repo"
Enter
Sleep 500ms

Type "mkdir -p $TEST_REPO && cd $TEST_REPO"
Enter
Sleep 500ms

Type "git init"
Enter
Sleep 1s

Type "echo '--- Testing: dark-governance init ---'"
Enter
Sleep 500ms

# -- Run init with dry-run first --

Type "dark-governance init --dry-run"
Enter
Sleep 2s

# -- Run init for real --

Type "dark-governance init --json"
Enter
Sleep 2s

# -- Verify: expected files and directories --

Type "echo '--- Verifying scaffolded files ---'"
Enter
Sleep 500ms

Type "test -f .github/workflows/dark-factory-governance.yml && echo 'PASS: CI workflow exists' || echo 'FAIL: CI workflow missing'"
Enter
Sleep 500ms

Type "test -f CLAUDE.md && echo 'PASS: CLAUDE.md exists' || echo 'FAIL: CLAUDE.md missing'"
Enter
Sleep 500ms

Type "test -d .artifacts/plans && echo 'PASS: .artifacts/plans/ exists' || echo 'FAIL: .artifacts/plans/ missing'"
Enter
Sleep 500ms

Type "test -d .artifacts/panels && echo 'PASS: .artifacts/panels/ exists' || echo 'FAIL: .artifacts/panels/ missing'"
Enter
Sleep 500ms

Type "test -d .artifacts/checkpoints && echo 'PASS: .artifacts/checkpoints/ exists' || echo 'FAIL: .artifacts/checkpoints/ missing'"
Enter
Sleep 500ms

Type "test -d .artifacts/emissions && echo 'PASS: .artifacts/emissions/ exists' || echo 'FAIL: .artifacts/emissions/ missing'"
Enter
Sleep 500ms

# -- Verify: lockfile --

Type "test -f .dark-governance.lock && echo 'PASS: lockfile exists' || echo 'FAIL: lockfile missing'"
Enter
Sleep 500ms

Type "cat .dark-governance.lock"
Enter
Sleep 1s

# -- Verify: integrity check --

Type "echo '--- Testing: dark-governance verify ---'"
Enter
Sleep 500ms

Type "dark-governance verify --json"
Enter
Sleep 2s

# -- Verify: init is idempotent (re-run should skip existing files) --

Type "echo '--- Testing: idempotent re-init ---'"
Enter
Sleep 500ms

Type "dark-governance init --json"
Enter
Sleep 2s

# -- Cleanup --

Type "cd / && rm -rf $TEST_REPO"
Enter
Sleep 500ms

Type "echo '--- init-test complete ---'"
Enter
Sleep 1s
