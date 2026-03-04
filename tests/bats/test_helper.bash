#!/usr/bin/env bash
# tests/bats/test_helper.bash — Shared setup/teardown for init.sh bats tests
#
# Strategy: init.sh runs top-level code on source, so we cannot source it
# directly. Instead, we extract function definitions using sed and source
# those in a controlled environment with the required global variables set.

# Resolve paths relative to this file
BATS_TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$BATS_TEST_DIR/../.." && pwd)"
INIT_SH="$REPO_ROOT/bin/init.sh"

# Extract function bodies from init.sh into a sourceable file.
# This uses awk to pull out function definitions (function_name() { ... })
# while skipping all top-level imperative code.
_extract_functions() {
  local output="$1"
  awk '
    /^[a-zA-Z_][a-zA-Z0-9_]*\(\)[[:space:]]*\{/ { infunc=1; depth=0 }
    infunc {
      # Count braces to track nesting
      n = split($0, chars, "")
      for (i = 1; i <= n; i++) {
        if (chars[i] == "{") depth++
        if (chars[i] == "}") depth--
      }
      print
      if (depth <= 0 && infunc) infunc = 0
      next
    }
  ' "$INIT_SH" > "$output"
}

# Common setup: create temp dirs, extract functions, set globals
setup() {
  # Create isolated temp directory for each test
  TEST_TMPDIR="$(mktemp -d)"
  export TEST_TMPDIR

  # Simulate the directory structure init.sh expects
  export AI_DIR="$TEST_TMPDIR/.ai"
  export PROJECT_ROOT="$TEST_TMPDIR"
  export SCRIPT_DIR="$AI_DIR/bin"
  export VENV_DIR="$AI_DIR/.venv"
  export REQUIREMENTS="$AI_DIR/governance/bin/requirements.txt"
  export PYPROJECT="$AI_DIR/governance/engine/pyproject.toml"

  mkdir -p "$AI_DIR/bin"
  mkdir -p "$AI_DIR/governance/bin"
  mkdir -p "$AI_DIR/governance/engine"
  mkdir -p "$AI_DIR/governance/emissions"
  mkdir -p "$AI_DIR/governance/templates"
  mkdir -p "$AI_DIR/.github/workflows"
  mkdir -p "$AI_DIR/.github/ISSUE_TEMPLATE"
  mkdir -p "$PROJECT_ROOT/.github"

  # Python version constraints (matching init.sh defaults)
  export PYTHON_MIN_MAJOR=3
  export PYTHON_MIN_MINOR=12

  # Detect Python (needed by parse_yaml_field, generate_codeowners, etc.)
  # Try versioned commands first (python3.14, python3.13, python3.12) to find
  # a suitable version even when the default python3 is too old (e.g. macOS system Python).
  export PYTHON_CMD=""
  export PYTHON_OK=false
  for cmd in python3.14 python3.13 python3.12 python3 python; do
    local cmd_path
    cmd_path="$(command -v "$cmd" 2>/dev/null)" || continue
    local version
    version="$("$cmd_path" --version 2>&1)"
    if [[ "$version" =~ Python\ ([0-9]+)\.([0-9]+) ]]; then
      local major="${BASH_REMATCH[1]}"
      local minor="${BASH_REMATCH[2]}"
      if [ "$major" -gt "$PYTHON_MIN_MAJOR" ] || { [ "$major" -eq "$PYTHON_MIN_MAJOR" ] && [ "$minor" -ge "$PYTHON_MIN_MINOR" ]; }; then
        PYTHON_CMD="$cmd_path"
        PYTHON_OK=true
        break
      fi
    fi
  done
  # Fallback: if no suitable version found, still set PYTHON_CMD for tests
  # that don't need the version check
  if [ -z "$PYTHON_CMD" ]; then
    PYTHON_CMD="$(command -v python3 2>/dev/null || command -v python 2>/dev/null || true)"
  fi

  # Extract functions from init.sh into a sourceable file
  FUNCTIONS_FILE="$TEST_TMPDIR/_init_functions.sh"
  _extract_functions "$FUNCTIONS_FILE"

  # Source the extracted functions
  # shellcheck disable=SC1090
  source "$FUNCTIONS_FILE"
}

# Teardown: remove temp directory
teardown() {
  if [ -n "${TEST_TMPDIR:-}" ] && [ -d "$TEST_TMPDIR" ]; then
    rm -rf "$TEST_TMPDIR"
  fi
}
