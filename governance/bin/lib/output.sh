#!/bin/bash
# governance/bin/lib/output.sh — Centralized output library with verbosity levels.
# Sourced by common.sh; provides tiered output control for all governance scripts.
#
# Verbosity levels (VERBOSITY env var):
#   0 = quiet   — errors only, zero output on success
#   1 = summary — single-line summary per operation, warnings, errors (default)
#   2 = verbose — per-step status ([OK], [SKIP], etc.), all current output
#   3 = debug   — everything: env resolution, path lookups, command execution
#
# Flags: --quiet (0), --verbose (2), --debug (3), default (1)
#
# CI auto-detection: when CI env vars are set, defaults to summary (1) with no color.

# Guard against double-sourcing
[ -n "${_OUTPUT_SH_LOADED:-}" ] && return 0
_OUTPUT_SH_LOADED=1

# --- Defaults ---
VERBOSITY="${VERBOSITY:-1}"
IS_CI="${IS_CI:-false}"
USE_COLOR="${USE_COLOR:-auto}"

# --- Summary collector ---
_OUTPUT_STEPS_OK=0
_OUTPUT_STEPS_WARN=0
_OUTPUT_STEPS_ERROR=0
_OUTPUT_STEPS_SKIP=0
_OUTPUT_WARNINGS=()
_OUTPUT_ERRORS=()
_OUTPUT_START_TIME=""

# --- CI auto-detection ---
output_init() {
  if [ -n "${CI:-}" ] || [ -n "${GITHUB_ACTIONS:-}" ] || [ -n "${TF_BUILD:-}" ] || \
     [ -n "${JENKINS_URL:-}" ] || [ -n "${GITLAB_CI:-}" ]; then
    IS_CI=true
    [ "$USE_COLOR" = "auto" ] && USE_COLOR=false
  fi

  # Map legacy DEBUG flag
  if [ "${DEBUG:-false}" = "true" ] && [ "${VERBOSITY}" -lt 3 ]; then
    VERBOSITY=3
  fi

  # Color setup
  if [ "$USE_COLOR" = "auto" ]; then
    if [ -t 1 ]; then
      USE_COLOR=true
    else
      USE_COLOR=false
    fi
  fi

  if [ "$USE_COLOR" = "true" ]; then
    _OUT_GREEN='\033[0;32m'
    _OUT_YELLOW='\033[1;33m'
    _OUT_RED='\033[0;31m'
    _OUT_BLUE='\033[0;34m'
    _OUT_BOLD='\033[1m'
    _OUT_NC='\033[0m'
  else
    _OUT_GREEN='' _OUT_YELLOW='' _OUT_RED='' _OUT_BLUE='' _OUT_BOLD='' _OUT_NC=''
  fi

  # Start timer
  _OUTPUT_START_TIME=$(date +%s)
}

# --- Output functions ---

# Errors: always shown (all verbosity levels)
out_error() {
  _OUTPUT_STEPS_ERROR=$((_OUTPUT_STEPS_ERROR + 1))
  _OUTPUT_ERRORS+=("$*")
  echo -e "  ${_OUT_RED:-}[ERROR]${_OUT_NC:-} $*" >&2
  # GitHub Actions annotation
  if [ "$IS_CI" = "true" ] && [ -n "${GITHUB_ACTIONS:-}" ]; then
    echo "::error::$*"
  fi
}

# Warnings: shown at summary (1) and above
out_warn() {
  _OUTPUT_STEPS_WARN=$((_OUTPUT_STEPS_WARN + 1))
  _OUTPUT_WARNINGS+=("$*")
  if [ "${VERBOSITY:-1}" -ge 1 ]; then
    echo -e "  ${_OUT_YELLOW:-}[WARN]${_OUT_NC:-} $*"
  fi
  # GitHub Actions annotation
  if [ "$IS_CI" = "true" ] && [ -n "${GITHUB_ACTIONS:-}" ]; then
    echo "::warning::$*"
  fi
}

# Step OK: shown at verbose (2) and above; counted for summary
out_step_ok() {
  _OUTPUT_STEPS_OK=$((_OUTPUT_STEPS_OK + 1))
  if [ "${VERBOSITY:-1}" -ge 2 ]; then
    echo -e "  ${_OUT_GREEN:-}[OK]${_OUT_NC:-} $*"
  fi
}

# Step skip: shown at verbose (2) and above; counted for summary
out_step_skip() {
  _OUTPUT_STEPS_SKIP=$((_OUTPUT_STEPS_SKIP + 1))
  if [ "${VERBOSITY:-1}" -ge 2 ]; then
    echo "  [SKIP] $*"
  fi
}

# Detail: per-item info shown at verbose (2) and above
out_verbose() {
  if [ "${VERBOSITY:-1}" -ge 2 ]; then
    echo "  $*"
  fi
}

# Debug: shown only at debug (3)
out_debug() {
  if [ "${VERBOSITY:-1}" -ge 3 ]; then
    echo -e "  ${_OUT_BLUE:-}[DEBUG]${_OUT_NC:-} $*"
  fi
}

# Summary line: shown at summary (1) and above
out_summary() {
  if [ "${VERBOSITY:-1}" -ge 1 ]; then
    echo "$*"
  fi
}

# --- Summary collector ---

output_summary_start() {
  _OUTPUT_STEPS_OK=0
  _OUTPUT_STEPS_WARN=0
  _OUTPUT_STEPS_ERROR=0
  _OUTPUT_STEPS_SKIP=0
  _OUTPUT_WARNINGS=()
  _OUTPUT_ERRORS=()
  _OUTPUT_START_TIME=$(date +%s)
}

output_summary_end() {
  local end_time duration_s
  end_time=$(date +%s)
  duration_s=$(( end_time - ${_OUTPUT_START_TIME:-$end_time} ))

  if [ "${VERBOSITY:-1}" -ge 1 ]; then
    local parts=()
    [ "$_OUTPUT_STEPS_OK" -gt 0 ] && parts+=("$_OUTPUT_STEPS_OK ok")
    [ "$_OUTPUT_STEPS_SKIP" -gt 0 ] && parts+=("$_OUTPUT_STEPS_SKIP skipped")
    [ "$_OUTPUT_STEPS_WARN" -gt 0 ] && parts+=("$_OUTPUT_STEPS_WARN warning(s)")
    [ "$_OUTPUT_STEPS_ERROR" -gt 0 ] && parts+=("$_OUTPUT_STEPS_ERROR error(s)")

    local summary_line=""
    if [ ${#parts[@]} -gt 0 ]; then
      local IFS=', '
      summary_line="${parts[*]}"
    else
      summary_line="complete"
    fi

    echo ""
    echo -e "${_OUT_BOLD:-}Dark Forge init:${_OUT_NC:-} ${summary_line} (${duration_s}s)"

    # Show warnings inline at summary level
    if [ "${VERBOSITY:-1}" -eq 1 ] && [ ${#_OUTPUT_WARNINGS[@]} -gt 0 ]; then
      for w in "${_OUTPUT_WARNINGS[@]}"; do
        echo -e "  ${_OUT_YELLOW:-}[WARN]${_OUT_NC:-} $w"
      done
    fi
  fi
}

# Initialize on source
output_init
