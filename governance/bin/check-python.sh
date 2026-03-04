#!/bin/bash
# governance/bin/check-python.sh — Detect Python and verify minimum version.
# Outputs: sets PYTHON_CMD and PYTHON_OK in the calling environment.
# When sourced, exports these variables. When run standalone, prints status.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
resolve_ai_dir

PYTHON_MIN_MAJOR="${PYTHON_MIN_MAJOR:-3}"
PYTHON_MIN_MINOR="${PYTHON_MIN_MINOR:-9}"

check_python_version() {
  local cmd="$1"
  local version
  version="$($cmd --version 2>&1)"
  if [[ "$version" =~ Python\ ([0-9]+)\.([0-9]+) ]]; then
    local major="${BASH_REMATCH[1]}"
    local minor="${BASH_REMATCH[2]}"
    if [ "$major" -gt "$PYTHON_MIN_MAJOR" ] || { [ "$major" -eq "$PYTHON_MIN_MAJOR" ] && [ "$minor" -ge "$PYTHON_MIN_MINOR" ]; }; then
      log_ok "$version"
      return 0
    else
      log_warn "$version found, but $PYTHON_MIN_MAJOR.$PYTHON_MIN_MINOR+ required"
      return 1
    fi
  fi
  log_warn "Could not parse Python version from: $version"
  return 1
}

PYTHON_CMD=""
PYTHON_OK=false

echo "Checking dependencies..."

if PYTHON_CMD="$(find_python)"; then
  if check_python_version "$PYTHON_CMD"; then
    PYTHON_OK=true
  fi
else
  log_warn "Python is not installed or not in PATH"
  echo "         The policy engine requires Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+"
  echo "         Install from: https://www.python.org/downloads/"
fi

echo ""

log_debug "PYTHON_CMD=$PYTHON_CMD PYTHON_OK=$PYTHON_OK"
