#!/usr/bin/env bash
# run-tests.sh — Execute VHS tape end-to-end tests for dark-governance CLI.
#
# Usage:
#   bash tests/e2e/run-tests.sh              # Run all tapes
#   bash tests/e2e/run-tests.sh init-test    # Run a specific tape (without .tape extension)
#   bash tests/e2e/run-tests.sh --list       # List available tapes
#   bash tests/e2e/run-tests.sh --ci         # CI mode: skip if VHS not installed (exit 0)
#
# Exit codes:
#   0 — All tests passed (or skipped in CI mode)
#   1 — One or more tests failed
#   2 — VHS not installed (non-CI mode)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TAPE_DIR="$SCRIPT_DIR"
OUTPUT_DIR="$SCRIPT_DIR/output"
CI_MODE=false
SPECIFIC_TAPE=""

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ci)
      CI_MODE=true
      shift
      ;;
    --list)
      echo "Available VHS tapes:"
      for tape in "$TAPE_DIR"/*.tape; do
        [ -f "$tape" ] || continue
        name="$(basename "$tape" .tape)"
        echo "  $name"
      done
      exit 0
      ;;
    --help|-h)
      echo "Usage: $0 [--ci] [--list] [tape-name]"
      echo ""
      echo "Options:"
      echo "  --ci       Skip gracefully (exit 0) if VHS is not installed"
      echo "  --list     List available tape files"
      echo "  --help     Show this help message"
      echo ""
      echo "Arguments:"
      echo "  tape-name  Run only the specified tape (without .tape extension)"
      exit 0
      ;;
    -*)
      echo "Error: unknown option: $1" >&2
      exit 1
      ;;
    *)
      SPECIFIC_TAPE="$1"
      shift
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Check prerequisites
# ---------------------------------------------------------------------------

if ! command -v vhs &>/dev/null; then
  if [ "$CI_MODE" = true ]; then
    echo "SKIP: VHS is not installed — skipping e2e tests (CI mode)"
    echo "Install VHS: https://github.com/charmbracelet/vhs#installation"
    exit 0
  else
    echo "ERROR: VHS is not installed." >&2
    echo "" >&2
    echo "Install VHS to run end-to-end tests:" >&2
    echo "  brew install charmbracelet/tap/vhs    # macOS" >&2
    echo "  go install github.com/charmbracelet/vhs@latest  # Go" >&2
    echo "" >&2
    echo "See: https://github.com/charmbracelet/vhs#installation" >&2
    exit 2
  fi
fi

if ! command -v dark-governance &>/dev/null; then
  echo "WARNING: dark-governance binary not found on PATH." >&2
  echo "Build it first: cd src && make build" >&2
  echo "Then add to PATH: export PATH=\"\$PWD/src/bin:\$PATH\"" >&2
  echo "" >&2

  if [ "$CI_MODE" = true ]; then
    echo "SKIP: dark-governance not on PATH — skipping e2e tests (CI mode)"
    exit 0
  fi
fi

# ---------------------------------------------------------------------------
# Prepare output directory
# ---------------------------------------------------------------------------

mkdir -p "$OUTPUT_DIR"

# ---------------------------------------------------------------------------
# Run tapes
# ---------------------------------------------------------------------------

passed=0
failed=0
skipped=0
total=0

run_tape() {
  local tape_file="$1"
  local tape_name
  tape_name="$(basename "$tape_file" .tape)"

  total=$((total + 1))
  echo "--- Running: $tape_name ---"

  if vhs "$tape_file" 2>&1; then
    echo "  PASS: $tape_name"
    passed=$((passed + 1))
  else
    echo "  FAIL: $tape_name"
    failed=$((failed + 1))
  fi
  echo ""
}

if [ -n "$SPECIFIC_TAPE" ]; then
  tape_file="$TAPE_DIR/${SPECIFIC_TAPE}.tape"
  if [ ! -f "$tape_file" ]; then
    echo "Error: tape file not found: $tape_file" >&2
    echo "Run '$0 --list' to see available tapes." >&2
    exit 1
  fi
  run_tape "$tape_file"
else
  for tape_file in "$TAPE_DIR"/*.tape; do
    [ -f "$tape_file" ] || continue
    run_tape "$tape_file"
  done
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo "================================"
echo "E2E Test Summary"
echo "  Total:   $total"
echo "  Passed:  $passed"
echo "  Failed:  $failed"
echo "  Skipped: $skipped"
echo "================================"

if [ "$failed" -gt 0 ]; then
  exit 1
fi

exit 0
