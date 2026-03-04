#!/usr/bin/env bash
# cleanup-state.sh — Governance state lifecycle management
#
# Removes stale governance artifacts beyond configurable retention periods.
# Safe to run manually or as part of the agentic startup sequence.
#
# Usage:
#   bash governance/bin/cleanup-state.sh [--dry-run] [--agent-log-days N] [--checkpoint-days N]
#
# Defaults:
#   Agent logs: 30 days retention
#   Checkpoints: 7 days retention
#   Plan archives: never (accumulated)

set -euo pipefail

# --- Defaults ---
AGENT_LOG_DAYS=30
CHECKPOINT_DAYS=7
DRY_RUN=false
GOVERNANCE_DIR=".governance"

# --- Parse args ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)       DRY_RUN=true; shift ;;
    --agent-log-days) AGENT_LOG_DAYS="$2"; shift 2 ;;
    --checkpoint-days) CHECKPOINT_DAYS="$2"; shift 2 ;;
    --governance-dir) GOVERNANCE_DIR="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: cleanup-state.sh [--dry-run] [--agent-log-days N] [--checkpoint-days N]"
      echo ""
      echo "Options:"
      echo "  --dry-run              Show what would be deleted without deleting"
      echo "  --agent-log-days N     Agent log retention in days (default: 30)"
      echo "  --checkpoint-days N    Checkpoint retention in days (default: 7)"
      echo "  --governance-dir DIR   Path to .governance directory (default: .governance)"
      exit 0
      ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# --- Counters ---
agent_logs_removed=0
checkpoints_removed=0
total_bytes_freed=0

echo "=== Governance State Cleanup ==="
echo "  Agent log retention: ${AGENT_LOG_DAYS} days"
echo "  Checkpoint retention: ${CHECKPOINT_DAYS} days"
echo "  Dry run: ${DRY_RUN}"
echo ""

# --- Agent logs ---
AGENT_LOG_DIR="${GOVERNANCE_DIR}/state/agent-log"
if [[ -d "$AGENT_LOG_DIR" ]]; then
  while IFS= read -r -d '' file; do
    size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
    if [[ "$DRY_RUN" == "true" ]]; then
      echo "  [dry-run] Would remove: $file ($(( size / 1024 ))KB)"
    else
      rm -f "$file"
    fi
    agent_logs_removed=$((agent_logs_removed + 1))
    total_bytes_freed=$((total_bytes_freed + size))
  done < <(find "$AGENT_LOG_DIR" -name "*.jsonl" -type f -mtime "+${AGENT_LOG_DAYS}" -print0 2>/dev/null)

  echo "Agent logs: ${agent_logs_removed} files older than ${AGENT_LOG_DAYS} days"
else
  echo "Agent logs: directory not found (${AGENT_LOG_DIR})"
fi

# --- Checkpoints ---
CHECKPOINT_DIR="${GOVERNANCE_DIR}/checkpoints"
if [[ -d "$CHECKPOINT_DIR" ]]; then
  while IFS= read -r -d '' file; do
    size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
    if [[ "$DRY_RUN" == "true" ]]; then
      echo "  [dry-run] Would remove: $file ($(( size / 1024 ))KB)"
    else
      rm -f "$file"
    fi
    checkpoints_removed=$((checkpoints_removed + 1))
    total_bytes_freed=$((total_bytes_freed + size))
  done < <(find "$CHECKPOINT_DIR" -name "*.json" -type f -mtime "+${CHECKPOINT_DAYS}" -print0 2>/dev/null)

  echo "Checkpoints: ${checkpoints_removed} files older than ${CHECKPOINT_DAYS} days"
else
  echo "Checkpoints: directory not found (${CHECKPOINT_DIR})"
fi

# --- Summary ---
echo ""
echo "=== Summary ==="
echo "  Files removed: $((agent_logs_removed + checkpoints_removed))"
echo "  Bytes freed: $((total_bytes_freed / 1024))KB"
if [[ "$DRY_RUN" == "true" ]]; then
  echo "  (dry run — no files were actually deleted)"
fi
