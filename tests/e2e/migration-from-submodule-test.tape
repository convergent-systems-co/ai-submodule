# migration-from-submodule-test.tape — VHS end-to-end test for migrating
# a project that already has the .ai/ submodule to the binary distribution.
#
# Validates that `dark-governance install` + `dark-governance init` works
# correctly alongside an existing .ai/ submodule.
#
# Prerequisites:
#   - `dark-governance` binary on PATH (built via `cd src && make build`)
#   - VHS (https://github.com/charmbracelet/vhs)
#
# Run:
#   vhs tests/e2e/migration-from-submodule-test.tape
#
# Output:
#   tests/e2e/output/migration-from-submodule-test.mp4

Output tests/e2e/output/migration-from-submodule-test.mp4

Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"

# -- Setup: simulate a project with .ai/ submodule --

Type "export PROJECT=$(mktemp -d)/submodule-project"
Enter
Sleep 500ms

Type "mkdir -p $PROJECT && cd $PROJECT"
Enter
Sleep 500ms

Type "git init && echo '# Submodule Project' > README.md"
Enter
Sleep 1s

# Simulate the .ai/ submodule structure
Type "mkdir -p .ai/governance/policy .ai/governance/prompts .ai/governance/schemas .ai/bin"
Enter
Sleep 500ms

Type "echo 'policy_profile: default' > .ai/governance/policy/default.yaml"
Enter
Sleep 500ms

Type "echo '#!/bin/bash' > .ai/bin/init.sh && echo 'name: my-project' > .ai/project.yaml"
Enter
Sleep 500ms

Type "git add -A && git commit -m 'initial with .ai submodule'"
Enter
Sleep 1s

Type "echo '--- Existing .ai/ submodule structure ---'"
Enter
Sleep 500ms

Type "find .ai -maxdepth 3 | sort"
Enter
Sleep 1s

# -- Step 1: Install the binary distribution --

Type "echo '--- Step 1: dark-governance install ---'"
Enter
Sleep 500ms

Type "dark-governance install --json"
Enter
Sleep 2s

# -- Step 2: Initialize governance (binary mode alongside submodule) --

Type "echo '--- Step 2: dark-governance init ---'"
Enter
Sleep 500ms

Type "dark-governance init --json"
Enter
Sleep 2s

# -- Verify: .ai/ submodule is untouched --

Type "echo '--- Verifying .ai/ submodule untouched ---'"
Enter
Sleep 500ms

Type "test -f .ai/governance/policy/default.yaml && echo 'PASS: submodule policy intact' || echo 'FAIL: submodule modified'"
Enter
Sleep 500ms

Type "test -f .ai/project.yaml && echo 'PASS: submodule project.yaml intact' || echo 'FAIL: submodule modified'"
Enter
Sleep 500ms

# -- Verify: binary governance scaffolded --

Type "echo '--- Verifying binary governance scaffolding ---'"
Enter
Sleep 500ms

Type "test -f .github/workflows/dark-factory-governance.yml && echo 'PASS: CI workflow' || echo 'FAIL: CI workflow'"
Enter
Sleep 500ms

Type "test -f CLAUDE.md && echo 'PASS: CLAUDE.md' || echo 'FAIL: CLAUDE.md'"
Enter
Sleep 500ms

Type "test -f .dark-governance.lock && echo 'PASS: lockfile' || echo 'FAIL: lockfile'"
Enter
Sleep 500ms

# -- Verify: binary version check --

Type "echo '--- Binary version ---'"
Enter
Sleep 500ms

Type "dark-governance version"
Enter
Sleep 1s

# -- Verify: integrity --

Type "dark-governance verify --json"
Enter
Sleep 2s

# -- Cleanup --

Type "cd / && rm -rf $PROJECT"
Enter
Sleep 500ms

Type "echo '--- migration-from-submodule-test complete ---'"
Enter
Sleep 1s
