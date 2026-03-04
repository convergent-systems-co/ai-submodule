#!/bin/bash
# governance/bin/drift-detection.sh — Detect local customizations that diverge from upstream.
#
# Computes SHA256 hashes of key governance files and compares against stored
# upstream hashes to detect drift. Similar to DACH's template hash drift detection.
#
# Usage:
#   bash .ai/governance/bin/drift-detection.sh              # Full report
#   bash .ai/governance/bin/drift-detection.sh --check      # Exit 0=clean, 1=drift
#   bash .ai/governance/bin/drift-detection.sh --snapshot    # Save current hashes as baseline
#
# State file: .artifacts/state/upstream-hashes.json

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh" 2>/dev/null || true
resolve_ai_dir 2>/dev/null || {
  AI_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
  PROJECT_ROOT="$(dirname "$AI_DIR")"
}

STATE_DIR="$PROJECT_ROOT/.artifacts/state"
HASH_FILE="$STATE_DIR/upstream-hashes.json"

CHECK_ONLY=false
SNAPSHOT=false

for arg in "$@"; do
  case "$arg" in
    --check)    CHECK_ONLY=true ;;
    --snapshot) SNAPSHOT=true ;;
  esac
done

# Files to track for drift detection
TRACKED_PATHS=(
  "governance/policy/default.yaml"
  "governance/policy/strict.yaml"
  "governance/policy/lenient.yaml"
  "governance/schemas/panel-output.schema.json"
  "governance/schemas/run-manifest.schema.json"
  "governance/schemas/checkpoint.schema.json"
  "governance/prompts/agent-protocol.md"
  "governance/prompts/startup.md"
  "CLAUDE.md"
)

# --- Hash computation ---

compute_hash() {
  local file="$1"
  if [ -f "$AI_DIR/$file" ]; then
    shasum -a 256 "$AI_DIR/$file" 2>/dev/null | awk '{print $1}'
  else
    echo "MISSING"
  fi
}

compute_all_hashes() {
  echo "{"
  local first=true
  for path in "${TRACKED_PATHS[@]}"; do
    if [ "$first" = "true" ]; then
      first=false
    else
      echo ","
    fi
    hash="$(compute_hash "$path")"
    printf '  "%s": "%s"' "$path" "$hash"
  done
  echo ""
  echo "}"
}

# --- Snapshot mode ---

if [ "$SNAPSHOT" = "true" ]; then
  mkdir -p "$STATE_DIR"
  compute_all_hashes > "$HASH_FILE"
  echo "Snapshot saved to $HASH_FILE"
  exit 0
fi

# --- Drift detection ---

if [ ! -f "$HASH_FILE" ]; then
  if [ "$CHECK_ONLY" = "true" ]; then
    exit 0  # No baseline = no drift to report
  fi
  echo "No baseline snapshot found. Run with --snapshot first."
  echo "  bash .ai/governance/bin/drift-detection.sh --snapshot"
  exit 0
fi

DRIFT_COUNT=0

for path in "${TRACKED_PATHS[@]}"; do
  current_hash="$(compute_hash "$path")"
  # Extract stored hash from JSON (simple grep approach, no jq dependency)
  stored_hash="$(grep "\"$path\"" "$HASH_FILE" 2>/dev/null | sed 's/.*: *"\([a-f0-9]*\)".*/\1/' || echo "")"

  if [ -z "$stored_hash" ]; then
    continue  # File not in baseline, skip
  fi

  if [ "$current_hash" != "$stored_hash" ]; then
    DRIFT_COUNT=$((DRIFT_COUNT + 1))
    if [ "$CHECK_ONLY" != "true" ]; then
      echo "  DRIFT: $path"
      echo "    baseline: ${stored_hash:0:12}..."
      echo "    current:  ${current_hash:0:12}..."
    fi
  fi
done

if [ "$DRIFT_COUNT" -gt 0 ]; then
  if [ "$CHECK_ONLY" != "true" ]; then
    echo ""
    echo "$DRIFT_COUNT file(s) have drifted from upstream baseline."
    echo "These local modifications may conflict with the next update."
  fi
  exit 1
else
  if [ "$CHECK_ONLY" != "true" ]; then
    echo "No drift detected. All tracked files match the baseline."
  fi
  exit 0
fi
