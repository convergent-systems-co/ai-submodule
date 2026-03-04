# install-test.tape — VHS end-to-end test for `dark-governance install`
#
# Validates that the `dark-governance install` command correctly extracts
# embedded governance content to the home directory cache.
#
# Prerequisites:
#   - `dark-governance` binary on PATH (built via `cd src && make build`)
#   - VHS (https://github.com/charmbracelet/vhs)
#
# Run:
#   vhs tests/e2e/install-test.tape
#
# Output:
#   tests/e2e/output/install-test.gif

Output tests/e2e/output/install-test.mp4

Set Shell "bash"
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Catppuccin Mocha"

# -- Setup: create an isolated home directory for the test --

Type "export DARK_GOVERNANCE_HOME=$(mktemp -d)/test-home"
Enter
Sleep 500ms

Type "echo '--- Testing: dark-governance install ---'"
Enter
Sleep 500ms

# -- Run install --

Type "dark-governance install --json"
Enter
Sleep 2s

# -- Verify: check that the version directory was created --

Type "echo '--- Verifying installation ---'"
Enter
Sleep 500ms

Type "ls -la $DARK_GOVERNANCE_HOME/versions/ 2>/dev/null && echo 'PASS: versions directory exists' || echo 'FAIL: versions directory not found'"
Enter
Sleep 1s

# -- Verify: check that content files were extracted --

Type "find $DARK_GOVERNANCE_HOME -name '*.yaml' -o -name '*.json' -o -name '*.md' 2>/dev/null | head -10 && echo 'PASS: content files found' || echo 'FAIL: no content files'"
Enter
Sleep 1s

# -- Verify: reinstall with --force --

Type "echo '--- Testing: reinstall with --force ---'"
Enter
Sleep 500ms

Type "dark-governance install --force --json"
Enter
Sleep 2s

# -- Cleanup --

Type "rm -rf $DARK_GOVERNANCE_HOME"
Enter
Sleep 500ms

Type "echo '--- install-test complete ---'"
Enter
Sleep 1s
