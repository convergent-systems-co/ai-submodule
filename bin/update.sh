#!/bin/bash
# .ai/bin/update.sh — Single-command update for the governance framework.
#
# Pulls the latest submodule, shows a changelog, detects drift from upstream,
# checks for breaking changes, and runs init.sh --refresh automatically.
#
# Usage:
#   bash .ai/bin/update.sh              # Standard update with changelog
#   bash .ai/bin/update.sh --check      # Check for updates without applying
#   bash .ai/bin/update.sh --force      # Update even if no changes detected
#   bash .ai/bin/update.sh --dry-run    # Show what would happen
#
# Exit codes:
#   0 = success (or no updates available)
#   1 = breaking changes detected (update applied, review required)
#   2 = drift detected (warnings emitted)
#   3 = update failed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$AI_DIR")"
GOVERNANCE_BIN="$AI_DIR/governance/bin"

# State tracking
STATE_DIR="$PROJECT_ROOT/.artifacts/state"
HASH_FILE="$STATE_DIR/upstream-hashes.json"

CHECK_ONLY=false
FORCE=false
DRY_RUN=false
EXIT_CODE=0

# Colors (if terminal supports them)
if [ -t 1 ]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[0;33m'
  BLUE='\033[0;34m'
  NC='\033[0m'
else
  RED='' GREEN='' YELLOW='' BLUE='' NC=''
fi

# --- Parse arguments ---
for arg in "$@"; do
  case "$arg" in
    --check)   CHECK_ONLY=true ;;
    --force)   FORCE=true ;;
    --dry-run) DRY_RUN=true ;;
    --help|-h)
      echo "Usage: bash .ai/bin/update.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --check      Check for updates without applying"
      echo "  --force      Update even if no changes detected"
      echo "  --dry-run    Show what would happen without making changes"
      echo "  --help, -h   Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg"
      exit 1
      ;;
  esac
done

# --- Helper functions ---

log_info()  { echo -e "  ${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo -e "  ${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "  ${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "  ${RED}[ERROR]${NC} $1"; }

get_current_sha() {
  git -C "$AI_DIR" rev-parse HEAD 2>/dev/null || echo "unknown"
}

get_short_sha() {
  echo "$1" | head -c 12
}

# --- Pre-flight checks ---

echo ""
echo "Dark Forge — Update"
echo "================================"
echo ""

# Must be in a git repository with .ai as submodule
if [ ! -d "$AI_DIR/.git" ] && [ ! -f "$AI_DIR/.git" ]; then
  log_error ".ai is not a git submodule or repository"
  exit 3
fi

CURRENT_SHA="$(get_current_sha)"
log_info "Current version: $(get_short_sha "$CURRENT_SHA")"

# --- Step 1: Check for updates ---

echo ""
echo "Step 1: Checking for updates..."

# Fetch latest without applying
git -C "$AI_DIR" fetch origin main --quiet 2>/dev/null || {
  log_error "Failed to fetch from origin. Check your network connection."
  exit 3
}

REMOTE_SHA="$(git -C "$AI_DIR" rev-parse origin/main 2>/dev/null || echo "unknown")"

if [ "$CURRENT_SHA" = "$REMOTE_SHA" ] && [ "$FORCE" != "true" ]; then
  log_ok "Already up to date ($(get_short_sha "$CURRENT_SHA"))"
  if [ "$CHECK_ONLY" = "true" ]; then
    echo ""
    echo "No updates available."
  fi
  exit 0
fi

log_info "Update available: $(get_short_sha "$CURRENT_SHA") -> $(get_short_sha "$REMOTE_SHA")"

# --- Step 2: Generate changelog ---

echo ""
echo "Step 2: Changelog"
echo "-----------------"

CHANGELOG="$(git -C "$AI_DIR" log --oneline "${CURRENT_SHA}..origin/main" 2>/dev/null | head -30)"
if [ -n "$CHANGELOG" ]; then
  echo "$CHANGELOG"
else
  echo "  (no commits between versions)"
fi

COMMIT_COUNT="$(git -C "$AI_DIR" rev-list --count "${CURRENT_SHA}..origin/main" 2>/dev/null || echo "0")"
log_info "$COMMIT_COUNT commit(s) in this update"

# --- Check-only mode exits here ---

if [ "$CHECK_ONLY" = "true" ]; then
  echo ""
  echo "Run 'bash .ai/bin/update.sh' to apply this update."
  exit 0
fi

# --- Step 3: Breaking change detection ---

echo ""
echo "Step 3: Breaking change detection..."

BREAKING_CHANGES=false

# Check for schema changes
SCHEMA_CHANGES="$(git -C "$AI_DIR" diff --name-only "${CURRENT_SHA}..origin/main" -- governance/schemas/ 2>/dev/null || echo "")"
if [ -n "$SCHEMA_CHANGES" ]; then
  log_warn "Schema files changed:"
  echo "$SCHEMA_CHANGES" | while read -r f; do echo "    $f"; done
  BREAKING_CHANGES=true
fi

# Check for policy profile changes
POLICY_CHANGES="$(git -C "$AI_DIR" diff --name-only "${CURRENT_SHA}..origin/main" -- governance/policy/ 2>/dev/null || echo "")"
if [ -n "$POLICY_CHANGES" ]; then
  log_warn "Policy profiles changed:"
  echo "$POLICY_CHANGES" | while read -r f; do echo "    $f"; done
fi

# Check for deleted files that consuming repos might reference
DELETED_FILES="$(git -C "$AI_DIR" diff --diff-filter=D --name-only "${CURRENT_SHA}..origin/main" 2>/dev/null || echo "")"
if [ -n "$DELETED_FILES" ]; then
  log_warn "Files deleted in this update:"
  echo "$DELETED_FILES" | while read -r f; do echo "    $f"; done
  BREAKING_CHANGES=true
fi

if [ "$BREAKING_CHANGES" = "true" ]; then
  log_warn "Breaking changes detected. Review the changelog above carefully."
  EXIT_CODE=1
else
  log_ok "No breaking changes detected"
fi

# --- Step 4: Drift detection ---

echo ""
echo "Step 4: Drift detection..."

if [ -f "$GOVERNANCE_BIN/drift-detection.sh" ]; then
  bash "$GOVERNANCE_BIN/drift-detection.sh" --check 2>/dev/null && {
    log_ok "No local drift detected"
  } || {
    log_warn "Local customizations detected that may conflict with update"
    if [ "$EXIT_CODE" -eq 0 ]; then EXIT_CODE=2; fi
  }
else
  # Inline basic drift detection
  DRIFT_FOUND=false
  for policy_file in "$AI_DIR"/governance/policy/*.yaml; do
    [ -f "$policy_file" ] || continue
    basename_file="$(basename "$policy_file")"
    # Check if file differs from what git tracks
    if ! git -C "$AI_DIR" diff --quiet HEAD -- "governance/policy/$basename_file" 2>/dev/null; then
      log_warn "Local modification: governance/policy/$basename_file"
      DRIFT_FOUND=true
    fi
  done
  if [ "$DRIFT_FOUND" = "false" ]; then
    log_ok "No local drift detected"
  else
    if [ "$EXIT_CODE" -eq 0 ]; then EXIT_CODE=2; fi
  fi
fi

# --- Step 5: Apply update ---

echo ""
echo "Step 5: Applying update..."

if [ "$DRY_RUN" = "true" ]; then
  log_info "[DRY-RUN] Would run: git submodule update --remote .ai"
  log_info "[DRY-RUN] Would run: bash .ai/bin/init.sh --refresh"
else
  # Update submodule
  (cd "$PROJECT_ROOT" && git submodule update --remote .ai) || {
    log_error "Submodule update failed"
    exit 3
  }
  log_ok "Submodule updated to $(get_short_sha "$(get_current_sha)")"

  # Run init.sh --refresh
  log_info "Running init.sh --refresh..."
  bash "$AI_DIR/bin/init.sh" --refresh || {
    log_warn "init.sh --refresh reported issues (non-fatal)"
  }
  log_ok "Refresh complete"
fi

# --- Step 6: Summary ---

echo ""
echo "================================"
echo "Update Summary"
echo "================================"
echo ""
echo "  Previous: $(get_short_sha "$CURRENT_SHA")"
echo "  Current:  $(get_short_sha "$(get_current_sha)")"
echo "  Commits:  $COMMIT_COUNT"

if [ "$BREAKING_CHANGES" = "true" ]; then
  echo ""
  log_warn "Breaking changes were detected. Review above warnings."
fi

echo ""
exit $EXIT_CODE
