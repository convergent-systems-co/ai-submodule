#!/usr/bin/env bats
# tests/bats/test_init.bats — bats-core tests for bin/init.sh critical paths
#
# Run: bats tests/bats/test_init.bats

load test_helper

# ---------------------------------------------------------------------------
# detect_platform
# ---------------------------------------------------------------------------

@test "detect_platform returns macOS on Darwin" {
  # Override uname to return Darwin
  uname() { echo "Darwin"; }
  export -f uname
  run detect_platform
  [ "$status" -eq 0 ]
  [ "$output" = "macOS" ]
}

@test "detect_platform returns Linux on Linux" {
  uname() { echo "Linux"; }
  export -f uname
  run detect_platform
  [ "$status" -eq 0 ]
  [ "$output" = "Linux" ]
}

@test "detect_platform returns raw os name for unknown platform" {
  uname() { echo "FreeBSD"; }
  export -f uname
  run detect_platform
  [ "$status" -eq 0 ]
  [ "$output" = "FreeBSD" ]
}

# ---------------------------------------------------------------------------
# find_python
# ---------------------------------------------------------------------------

@test "find_python locates python3 when available" {
  # find_python tries python3 first
  run find_python
  # On most CI/dev systems python3 exists
  if command -v python3 &>/dev/null; then
    [ "$status" -eq 0 ]
    [ "$output" = "python3" ]
  else
    skip "python3 not available on this system"
  fi
}

@test "find_python returns failure when no python exists" {
  # Override command -v to pretend neither python3 nor python exists
  command() {
    if [ "$1" = "-v" ]; then
      return 1
    fi
    builtin command "$@"
  }
  export -f command
  run find_python
  [ "$status" -eq 1 ]
}

# ---------------------------------------------------------------------------
# check_python_version
# ---------------------------------------------------------------------------

@test "check_python_version accepts Python 3.12+" {
  # Create a fake python that reports 3.12.0
  fake_python="$TEST_TMPDIR/fake_python"
  cat > "$fake_python" <<'SCRIPT'
#!/bin/bash
echo "Python 3.12.0"
SCRIPT
  chmod +x "$fake_python"

  run check_python_version "$fake_python"
  [ "$status" -eq 0 ]
  [[ "$output" == *"[OK]"* ]]
}

@test "check_python_version accepts Python 3.13" {
  fake_python="$TEST_TMPDIR/fake_python"
  cat > "$fake_python" <<'SCRIPT'
#!/bin/bash
echo "Python 3.13.1"
SCRIPT
  chmod +x "$fake_python"

  run check_python_version "$fake_python"
  [ "$status" -eq 0 ]
  [[ "$output" == *"[OK]"* ]]
}

@test "check_python_version accepts Python 4.0 (future major)" {
  fake_python="$TEST_TMPDIR/fake_python"
  cat > "$fake_python" <<'SCRIPT'
#!/bin/bash
echo "Python 4.0.0"
SCRIPT
  chmod +x "$fake_python"

  run check_python_version "$fake_python"
  [ "$status" -eq 0 ]
  [[ "$output" == *"[OK]"* ]]
}

@test "check_python_version rejects Python 3.11" {
  fake_python="$TEST_TMPDIR/fake_python"
  cat > "$fake_python" <<'SCRIPT'
#!/bin/bash
echo "Python 3.11.5"
SCRIPT
  chmod +x "$fake_python"

  run check_python_version "$fake_python"
  [ "$status" -eq 1 ]
  [[ "$output" == *"[WARN]"* ]]
  [[ "$output" == *"3.12"* ]]
}

@test "check_python_version rejects Python 2.7" {
  fake_python="$TEST_TMPDIR/fake_python"
  cat > "$fake_python" <<'SCRIPT'
#!/bin/bash
echo "Python 2.7.18"
SCRIPT
  chmod +x "$fake_python"

  run check_python_version "$fake_python"
  [ "$status" -eq 1 ]
  [[ "$output" == *"[WARN]"* ]]
}

@test "check_python_version handles unparseable version output" {
  fake_python="$TEST_TMPDIR/fake_python"
  cat > "$fake_python" <<'SCRIPT'
#!/bin/bash
echo "not a version"
SCRIPT
  chmod +x "$fake_python"

  run check_python_version "$fake_python"
  [ "$status" -eq 1 ]
  [[ "$output" == *"Could not parse"* ]]
}

# ---------------------------------------------------------------------------
# Symlink creation (integration — runs init.sh in a sandbox)
# ---------------------------------------------------------------------------

@test "symlink creation creates CLAUDE.md link" {
  # Set up a minimal submodule-like structure
  mkdir -p "$PROJECT_ROOT/.ai/bin"
  cp "$INIT_SH" "$PROJECT_ROOT/.ai/bin/init.sh"

  # Create the instructions.md that symlinks target
  echo "# Instructions" > "$PROJECT_ROOT/.ai/instructions.md"

  # Create a minimal config.yaml so Python parsing doesn't fail
  cat > "$PROJECT_ROOT/.ai/config.yaml" <<'YAML'
version: "1.0.0"
workflows:
  required: []
  optional: []
project_directories:
  - path: .plans
YAML

  # Run just the symlink portion by running init.sh
  # (it will try submodule checks, Python checks, etc. — some will warn but not fail)
  run bash "$PROJECT_ROOT/.ai/bin/init.sh" 2>&1
  # Verify CLAUDE.md symlink was created
  [ -L "$PROJECT_ROOT/CLAUDE.md" ]
  local target
  target="$(readlink "$PROJECT_ROOT/CLAUDE.md")"
  [ "$target" = ".ai/instructions.md" ]
}

@test "symlink creation is idempotent" {
  mkdir -p "$PROJECT_ROOT/.ai/bin"
  cp "$INIT_SH" "$PROJECT_ROOT/.ai/bin/init.sh"
  echo "# Instructions" > "$PROJECT_ROOT/.ai/instructions.md"
  cat > "$PROJECT_ROOT/.ai/config.yaml" <<'YAML'
version: "1.0.0"
workflows:
  required: []
  optional: []
project_directories:
  - path: .plans
YAML

  # Run twice
  bash "$PROJECT_ROOT/.ai/bin/init.sh" 2>&1 || true
  run bash "$PROJECT_ROOT/.ai/bin/init.sh" 2>&1

  # Second run should succeed and link should still be correct
  [ -L "$PROJECT_ROOT/CLAUDE.md" ]
  [[ "$output" == *"already linked"* ]]
}

@test "symlink creation creates copilot-instructions link" {
  mkdir -p "$PROJECT_ROOT/.ai/bin"
  cp "$INIT_SH" "$PROJECT_ROOT/.ai/bin/init.sh"
  echo "# Instructions" > "$PROJECT_ROOT/.ai/instructions.md"
  cat > "$PROJECT_ROOT/.ai/config.yaml" <<'YAML'
version: "1.0.0"
workflows:
  required: []
  optional: []
project_directories:
  - path: .plans
YAML

  bash "$PROJECT_ROOT/.ai/bin/init.sh" 2>&1 || true
  [ -L "$PROJECT_ROOT/.github/copilot-instructions.md" ]
  local target
  target="$(readlink "$PROJECT_ROOT/.github/copilot-instructions.md")"
  [ "$target" = "../.ai/instructions.md" ]
}

# ---------------------------------------------------------------------------
# parse_yaml_field
# ---------------------------------------------------------------------------

@test "parse_yaml_field extracts simple top-level value" {
  if [ "$PYTHON_OK" != "true" ]; then
    skip "Python 3.12+ required for parse_yaml_field"
  fi

  cat > "$AI_DIR/config.yaml" <<'YAML'
version: "2.0.0"
repository:
  auto_merge: true
YAML
  # Empty project.yaml files so the merge logic doesn't pick up extra data
  touch "$AI_DIR/project.yaml"
  touch "$PROJECT_ROOT/project.yaml"

  run parse_yaml_field "version" "MISSING"
  [ "$status" -eq 0 ]
  [ "$output" = "2.0.0" ]
}

@test "parse_yaml_field extracts nested dotted-path value" {
  if [ "$PYTHON_OK" != "true" ]; then
    skip "Python 3.12+ required for parse_yaml_field"
  fi

  cat > "$AI_DIR/config.yaml" <<'YAML'
repository:
  auto_merge: true
  delete_branch_on_merge: false
YAML
  touch "$AI_DIR/project.yaml"
  touch "$PROJECT_ROOT/project.yaml"

  run parse_yaml_field "repository.auto_merge" "false"
  [ "$status" -eq 0 ]
  [ "$output" = "true" ]
}

@test "parse_yaml_field returns default when key is missing" {
  if [ "$PYTHON_OK" != "true" ]; then
    skip "Python 3.12+ required for parse_yaml_field"
  fi

  cat > "$AI_DIR/config.yaml" <<'YAML'
version: "1.0.0"
YAML
  touch "$AI_DIR/project.yaml"
  touch "$PROJECT_ROOT/project.yaml"

  run parse_yaml_field "nonexistent.key" "FALLBACK"
  [ "$status" -eq 0 ]
  [ "$output" = "FALLBACK" ]
}

@test "parse_yaml_field merges project.yaml over config.yaml" {
  if [ "$PYTHON_OK" != "true" ]; then
    skip "Python 3.12+ required for parse_yaml_field"
  fi

  cat > "$AI_DIR/config.yaml" <<'YAML'
repository:
  auto_merge: false
YAML
  # project.yaml at AI_DIR (legacy location)
  cat > "$AI_DIR/project.yaml" <<'YAML'
repository:
  auto_merge: true
YAML
  touch "$PROJECT_ROOT/project.yaml"

  run parse_yaml_field "repository.auto_merge" "false"
  [ "$status" -eq 0 ]
  [ "$output" = "true" ]
}

@test "parse_yaml_field returns default when Python is unavailable" {
  # Simulate no Python
  local saved_python_ok="$PYTHON_OK"
  local saved_python_cmd="$PYTHON_CMD"
  local saved_venv="$VENV_DIR"

  PYTHON_OK=false
  PYTHON_CMD=""
  VENV_DIR="$TEST_TMPDIR/no-such-venv"

  # Re-source functions so the new globals take effect
  # shellcheck disable=SC1090
  source "$FUNCTIONS_FILE"

  run parse_yaml_field "anything" "DEFAULT_VALUE"
  [ "$status" -eq 0 ]
  [ "$output" = "DEFAULT_VALUE" ]

  # Restore
  PYTHON_OK="$saved_python_ok"
  PYTHON_CMD="$saved_python_cmd"
  VENV_DIR="$saved_venv"
}

# ---------------------------------------------------------------------------
# generate_codeowners
# ---------------------------------------------------------------------------

@test "generate_codeowners produces valid CODEOWNERS content" {
  if [ "$PYTHON_OK" != "true" ]; then
    skip "Python 3.12+ required for generate_codeowners"
  fi

  cat > "$AI_DIR/config.yaml" <<'YAML'
repository:
  codeowners:
    enabled: true
    default_owner: "@myorg/team"
    rules:
      - pattern: "/.github/"
        owners: ["@myorg/devops"]
      - pattern: "/src/"
        owners: ["@myorg/devs", "@myorg/leads"]
YAML
  touch "$AI_DIR/project.yaml"
  touch "$PROJECT_ROOT/project.yaml"

  run generate_codeowners
  [ "$status" -eq 0 ]
  # Should contain the header comment
  [[ "$output" == *"CODEOWNERS"* ]]
  # Should contain the default owner line
  [[ "$output" == *"* @myorg/team"* ]]
  # Should contain the rules
  [[ "$output" == *"/.github/ @myorg/devops"* ]]
  [[ "$output" == *"/src/ @myorg/devs @myorg/leads"* ]]
}

@test "generate_codeowners returns nothing when disabled" {
  if [ "$PYTHON_OK" != "true" ]; then
    skip "Python 3.12+ required for generate_codeowners"
  fi

  cat > "$AI_DIR/config.yaml" <<'YAML'
repository:
  codeowners:
    enabled: false
YAML
  touch "$AI_DIR/project.yaml"
  touch "$PROJECT_ROOT/project.yaml"

  run generate_codeowners
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ---------------------------------------------------------------------------
# merge_codeowners
# ---------------------------------------------------------------------------

@test "merge_codeowners preserves existing user rules" {
  if [ "$PYTHON_OK" != "true" ]; then
    skip "Python 3.12+ required for merge_codeowners"
  fi

  # Create config with a governance rule
  cat > "$AI_DIR/config.yaml" <<'YAML'
repository:
  codeowners:
    enabled: true
    default_owner: "@org/approvers"
    rules:
      - pattern: "/.ai"
        owners: ["@org/approvers"]
YAML
  touch "$AI_DIR/project.yaml"
  touch "$PROJECT_ROOT/project.yaml"

  # Create an existing CODEOWNERS with user rules
  local codeowners="$TEST_TMPDIR/CODEOWNERS"
  cat > "$codeowners" <<'EOF'
# My custom CODEOWNERS
/docs/ @org/docs-team
/api/ @org/api-team
EOF

  run merge_codeowners "$codeowners"
  [ "$status" -eq 0 ]

  # Read the merged file
  local content
  content="$(cat "$codeowners")"

  # User rules must still be present
  [[ "$content" == *"/docs/ @org/docs-team"* ]]
  [[ "$content" == *"/api/ @org/api-team"* ]]
  # Governance rules must be added
  [[ "$content" == *"@org/approvers"* ]]
}

@test "merge_codeowners is idempotent" {
  if [ "$PYTHON_OK" != "true" ]; then
    skip "Python 3.12+ required for merge_codeowners"
  fi

  cat > "$AI_DIR/config.yaml" <<'YAML'
repository:
  codeowners:
    enabled: true
    rules:
      - pattern: "/.ai"
        owners: ["@org/approvers"]
YAML
  touch "$AI_DIR/project.yaml"
  touch "$PROJECT_ROOT/project.yaml"

  local codeowners="$TEST_TMPDIR/CODEOWNERS"
  cat > "$codeowners" <<'EOF'
# Existing
/docs/ @org/docs-team
EOF

  # Run merge twice
  merge_codeowners "$codeowners"
  local content_after_first
  content_after_first="$(cat "$codeowners")"

  merge_codeowners "$codeowners"
  local content_after_second
  content_after_second="$(cat "$codeowners")"

  # Content should be identical after second run
  [ "$content_after_first" = "$content_after_second" ]
}

@test "merge_codeowners appends missing owners to existing pattern" {
  if [ "$PYTHON_OK" != "true" ]; then
    skip "Python 3.12+ required for merge_codeowners"
  fi

  cat > "$AI_DIR/config.yaml" <<'YAML'
repository:
  codeowners:
    enabled: true
    rules:
      - pattern: "/docs/"
        owners: ["@org/docs-team", "@org/governance"]
YAML
  touch "$AI_DIR/project.yaml"
  touch "$PROJECT_ROOT/project.yaml"

  local codeowners="$TEST_TMPDIR/CODEOWNERS"
  cat > "$codeowners" <<'EOF'
/docs/ @org/docs-team
EOF

  run merge_codeowners "$codeowners"
  [ "$status" -eq 0 ]

  local content
  content="$(cat "$codeowners")"
  # The existing owner should still be there, plus the new one
  [[ "$content" == *"@org/docs-team"* ]]
  [[ "$content" == *"@org/governance"* ]]
}

# ---------------------------------------------------------------------------
# init.sh argument parsing
# ---------------------------------------------------------------------------

@test "init.sh --help exits 0 with usage" {
  run bash "$INIT_SH" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"Usage"* ]]
  [[ "$output" == *"--install-deps"* ]]
  [[ "$output" == *"--refresh"* ]]
}

@test "init.sh rejects unknown arguments" {
  run bash "$INIT_SH" --bogus
  [ "$status" -eq 1 ]
  [[ "$output" == *"Unknown argument"* ]]
}

@test "init.sh --refresh is accepted and outputs Refresh complete" {
  mkdir -p "$PROJECT_ROOT/.ai/bin"
  cp "$INIT_SH" "$PROJECT_ROOT/.ai/bin/init.sh"
  echo "# Instructions" > "$PROJECT_ROOT/.ai/instructions.md"
  cat > "$PROJECT_ROOT/.ai/config.yaml" <<'YAML'
version: "1.0.0"
workflows:
  required: []
  optional: []
project_directories:
  - path: .plans
YAML

  run bash "$PROJECT_ROOT/.ai/bin/init.sh" --refresh 2>&1
  [[ "$output" == *"Refresh complete."* ]]
  # Should NOT contain "Next steps" (that's only for non-refresh mode)
  [[ "$output" != *"Next steps"* ]]
}

@test "init.sh --refresh skips submodule freshness check" {
  mkdir -p "$PROJECT_ROOT/.ai/bin"
  cp "$INIT_SH" "$PROJECT_ROOT/.ai/bin/init.sh"
  echo "# Instructions" > "$PROJECT_ROOT/.ai/instructions.md"
  cat > "$PROJECT_ROOT/.ai/config.yaml" <<'YAML'
version: "1.0.0"
workflows:
  required: []
  optional: []
project_directories:
  - path: .plans
YAML

  run bash "$PROJECT_ROOT/.ai/bin/init.sh" --refresh 2>&1
  # Should NOT contain submodule freshness output
  [[ "$output" != *"Checking .ai submodule freshness"* ]]
}

# ---------------------------------------------------------------------------
# --check-branch-protection
# ---------------------------------------------------------------------------

@test "init.sh --check-branch-protection outputs REQUIRES_PR format" {
  run bash "$INIT_SH" --check-branch-protection 2>&1
  [ "$status" -eq 0 ]
  # Output must contain the machine-readable flag
  [[ "$output" == *"REQUIRES_PR="* ]]
}

@test "init.sh --check-branch-protection defaults to false without gh" {
  # Override command to hide gh
  gh() { return 1; }
  export -f gh
  run bash "$INIT_SH" --check-branch-protection 2>&1
  [ "$status" -eq 0 ]
  [[ "$output" == *"REQUIRES_PR=false"* ]]
}

@test "init.sh --help shows --check-branch-protection" {
  run bash "$INIT_SH" --help
  [ "$status" -eq 0 ]
  [[ "$output" == *"--check-branch-protection"* ]]
}
