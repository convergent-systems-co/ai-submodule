# migration-no-ai-test.tape — VHS end-to-end test for installing governance
# into a pre-existing project with no AI/governance setup.
#
# Validates that `dark-governance install` + `dark-governance init` correctly
# scaffolds governance alongside existing project files.
#
# Prerequisites:
#   - `dark-governance` binary on PATH (built via `cd src && make build`)
#   - VHS (https://github.com/charmbracelet/vhs)
#
# Run:
#   vhs tests/e2e/migration-no-ai-test.tape
#
# Output:
#   tests/e2e/output/migration-no-ai-test.mp4

Output tests/e2e/output/migration-no-ai-test.mp4

Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"

# -- Setup: create a realistic pre-existing project --

Type "export PROJECT=$(mktemp -d)/my-existing-app"
Enter
Sleep 500ms

Type "mkdir -p $PROJECT/src $PROJECT/tests && cd $PROJECT"
Enter
Sleep 500ms

Type "git init && echo '# My Existing App' > README.md"
Enter
Sleep 1s

Type "echo 'console.log(42)' > src/index.js && echo 'my-app' > package.json"
Enter
Sleep 500ms

Type "git add -A && git commit -m 'initial commit'"
Enter
Sleep 1s

Type "echo '--- Pre-existing project structure ---'"
Enter
Sleep 500ms

Type "find . -not -path './.git/*' -not -path './.git' | sort"
Enter
Sleep 1s

# -- Step 1: Install governance content --

Type "echo '--- Step 1: dark-governance install ---'"
Enter
Sleep 500ms

Type "dark-governance install --json"
Enter
Sleep 2s

# -- Step 2: Initialize governance in this project --

Type "echo '--- Step 2: dark-governance init ---'"
Enter
Sleep 500ms

Type "dark-governance init --json"
Enter
Sleep 2s

# -- Verify: existing files are untouched --

Type "echo '--- Verifying existing files untouched ---'"
Enter
Sleep 500ms

Type "cat README.md"
Enter
Sleep 500ms

Type "cat src/index.js"
Enter
Sleep 500ms

Type "cat package.json"
Enter
Sleep 500ms

# -- Verify: governance files scaffolded --

Type "echo '--- Verifying governance scaffolding ---'"
Enter
Sleep 500ms

Type "test -f .github/workflows/dark-factory-governance.yml && echo 'PASS: CI workflow' || echo 'FAIL: CI workflow'"
Enter
Sleep 500ms

Type "test -f CLAUDE.md && echo 'PASS: CLAUDE.md' || echo 'FAIL: CLAUDE.md'"
Enter
Sleep 500ms

Type "test -d .artifacts/plans && echo 'PASS: .artifacts/' || echo 'FAIL: .artifacts/'"
Enter
Sleep 500ms

Type "test -f .dark-governance.lock && echo 'PASS: lockfile' || echo 'FAIL: lockfile'"
Enter
Sleep 500ms

# -- Verify: full project structure --

Type "echo '--- Final project structure ---'"
Enter
Sleep 500ms

Type "find . -not -path './.git/*' -not -path './.git' -maxdepth 3 | sort"
Enter
Sleep 1s

# -- Integrity check --

Type "dark-governance verify --json"
Enter
Sleep 2s

# -- Cleanup --

Type "cd / && rm -rf $PROJECT"
Enter
Sleep 500ms

Type "echo '--- migration-no-ai-test complete ---'"
Enter
Sleep 1s
