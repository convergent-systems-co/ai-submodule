#!/bin/bash
# governance/bin/ci-bootstrap.sh — Lightweight CI bootstrap for cross-org consuming repos.
#
# Sets up the minimal governance environment needed to run policy evaluation in CI
# without requiring direct submodule access. Uses a three-tier fallback:
#
#   Tier 1:   Submodule available (.ai/governance/) — use directly
#   Tier 1.5: Vendored engine (.artifacts/engine/) — use vendored copy
#   Tier 2:   Neither available — lightweight inline validation only
#
# Usage:
#   bash .ai/governance/bin/ci-bootstrap.sh          # Normal bootstrap
#   bash .ai/governance/bin/ci-bootstrap.sh --check  # Check tier and exit (for CI step outputs)
#
# Exit codes:
#   0 — bootstrap succeeded (or --check found a usable tier)
#   1 — no governance engine available (Tier 2 fallback will be used)
#
# Outputs (when run in GitHub Actions):
#   tier         — 1, 1.5, or 2
#   engine_path  — path to policy-engine.py (empty for Tier 2)
#   policy_dir   — path to policy profiles directory
#   schema_dir   — path to schemas directory
#   emissions_dir — path to emissions directory

set -euo pipefail

# --- Source common.sh if available ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/lib/common.sh" ]; then
  source "$SCRIPT_DIR/lib/common.sh"
  resolve_ai_dir
else
  # Minimal fallback when common.sh is not available (cross-org CI without submodule)
  log_ok()    { echo "  [OK] $*"; }
  log_warn()  { echo "  [WARN] $*"; }
  log_error() { echo "  [ERROR] $*"; }
  log_info()  { echo "  [INFO] $*"; }

  # Try to resolve paths from context
  AI_DIR="${AI_DIR:-}"
  PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
fi

CHECK_ONLY=false
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=true ;;
  esac
done

# --- Helper: set GitHub Actions outputs ---
set_output() {
  local key="$1" value="$2"
  if [ -n "${GITHUB_OUTPUT:-}" ]; then
    echo "${key}=${value}" >> "$GITHUB_OUTPUT"
  fi
}

# --- Tier 1: Submodule available ---
check_tier_1() {
  local gov_root=""

  # Check for submodule at .ai/
  if [ -d "${PROJECT_ROOT}/.ai/governance" ]; then
    gov_root="${PROJECT_ROOT}/.ai"
  # Check for governance root (running inside the governance repo itself)
  elif [ -d "${PROJECT_ROOT}/governance/bin/policy-engine.py" ] || [ -f "${PROJECT_ROOT}/governance/bin/policy-engine.py" ]; then
    gov_root="${PROJECT_ROOT}"
  fi

  if [ -z "$gov_root" ]; then
    return 1
  fi

  local engine_path="${gov_root}/governance/bin/policy-engine.py"
  if [ ! -f "$engine_path" ]; then
    return 1
  fi

  set_output "tier" "1"
  set_output "engine_path" "$engine_path"
  set_output "policy_dir" "${gov_root}/governance/policy"
  set_output "schema_dir" "${gov_root}/governance/schemas"

  # Emissions may be in governance/emissions/ or .artifacts/emissions/
  if [ -d "${gov_root}/governance/emissions" ]; then
    set_output "emissions_dir" "${gov_root}/governance/emissions"
  elif [ -d "${PROJECT_ROOT}/.artifacts/emissions" ]; then
    set_output "emissions_dir" "${PROJECT_ROOT}/.artifacts/emissions"
  fi

  log_ok "Tier 1: Submodule governance engine available at ${engine_path}"
  return 0
}

# --- Tier 1.5: Vendored engine ---
check_tier_1_5() {
  local vendor_dir="${PROJECT_ROOT}/.artifacts/engine"
  local engine_path="${vendor_dir}/policy-engine.py"
  local version_file="${vendor_dir}/VERSION"

  if [ ! -f "$engine_path" ]; then
    return 1
  fi

  # Verify vendored engine integrity
  local integrity_ok=true
  local missing_files=""

  # Check required files
  for required in "policy-engine.py" "VERSION"; do
    if [ ! -f "${vendor_dir}/${required}" ]; then
      missing_files="${missing_files} ${required}"
      integrity_ok=false
    fi
  done

  # Check policy directory has at least default.yaml
  if [ ! -f "${vendor_dir}/policy/default.yaml" ]; then
    missing_files="${missing_files} policy/default.yaml"
    integrity_ok=false
  fi

  if [ "$integrity_ok" = "false" ]; then
    log_warn "Vendored engine incomplete — missing:${missing_files}"
    log_warn "Run 'bash .ai/bin/init.sh --refresh' to re-vendor"
    return 1
  fi

  # Check VERSION file is non-empty
  if [ ! -s "$version_file" ]; then
    log_warn "Vendored engine VERSION file is empty — engine may be corrupted"
    return 1
  fi

  local vendored_version
  vendored_version="$(cat "$version_file" 2>/dev/null || echo "unknown")"

  set_output "tier" "1.5"
  set_output "engine_path" "$engine_path"
  set_output "policy_dir" "${vendor_dir}/policy"
  set_output "schema_dir" "${vendor_dir}/schemas"

  # Emissions are in .artifacts/emissions/ for consuming repos, or governance/emissions/ for the repo itself
  if [ -d "${PROJECT_ROOT}/.artifacts/emissions" ]; then
    set_output "emissions_dir" "${PROJECT_ROOT}/.artifacts/emissions"
  elif [ -d "${PROJECT_ROOT}/governance/emissions" ]; then
    set_output "emissions_dir" "${PROJECT_ROOT}/governance/emissions"
  fi

  log_ok "Tier 1.5: Vendored governance engine available (version: ${vendored_version:0:12}...)"
  return 0
}

# --- Tier 2: Lightweight fallback ---
set_tier_2() {
  set_output "tier" "2"
  set_output "engine_path" ""
  set_output "policy_dir" ""
  set_output "schema_dir" ""

  if [ -d "${PROJECT_ROOT}/.artifacts/emissions" ]; then
    set_output "emissions_dir" "${PROJECT_ROOT}/.artifacts/emissions"
  fi

  log_warn "Tier 2: No governance engine available — lightweight inline validation only"
  log_info "To enable full policy evaluation in CI, either:"
  log_info "  1. Run 'bash .ai/bin/init.sh --refresh' locally to vendor the engine"
  log_info "  2. Ensure the .ai/ submodule is accessible in CI"
}

# --- Bootstrap: ensure .governance directories exist ---
ensure_directories() {
  local dirs=".artifacts/emissions .artifacts/plans .artifacts/checkpoints .artifacts/state"
  for dir in $dirs; do
    local full_path="${PROJECT_ROOT}/${dir}"
    if [ ! -d "$full_path" ]; then
      mkdir -p "$full_path"
    fi
  done
}

# --- Main ---
main() {
  echo ""
  echo "CI Bootstrap: Detecting governance engine availability..."
  echo ""

  # Ensure governance directories exist
  if [ "$CHECK_ONLY" = "false" ]; then
    ensure_directories
  fi

  # Try tiers in order
  if check_tier_1; then
    [ "$CHECK_ONLY" = "true" ] && exit 0
    return 0
  fi

  if check_tier_1_5; then
    [ "$CHECK_ONLY" = "true" ] && exit 0
    return 0
  fi

  # Tier 2 fallback
  set_tier_2
  [ "$CHECK_ONLY" = "true" ] && exit 1
  return 0
}

main "$@"
