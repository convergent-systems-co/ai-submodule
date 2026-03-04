#!/usr/bin/env bash
set -euo pipefail

# cleanup-worktrees.sh — Remove stale git worktrees and orphaned branches
# Usage: bash governance/bin/cleanup-worktrees.sh [--max-age-days N] [--dry-run]

MAX_AGE_DAYS=2
DRY_RUN="${DRY_RUN:-false}"
WORKTREE_DIR=".artifacts/worktrees"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --max-age-days)
      MAX_AGE_DAYS="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      echo "Usage: bash governance/bin/cleanup-worktrees.sh [--max-age-days N] [--dry-run]" >&2
      exit 1
      ;;
  esac
done

removed_wt=0
removed_br=0

# Cross-platform age check (macOS vs Linux)
is_older_than_days() {
  local dir="$1" days="$2"
  if [[ "$OSTYPE" == "darwin"* ]]; then
    local mtime
    mtime=$(stat -f %m "$dir" 2>/dev/null || echo 0)
  else
    local mtime
    mtime=$(stat -c %Y "$dir" 2>/dev/null || echo 0)
  fi
  local now
  now=$(date +%s)
  local age_days=$(( (now - mtime) / 86400 ))
  [ "$age_days" -ge "$days" ]
}

# 1. Remove stale worktrees
if [ -d "$WORKTREE_DIR" ]; then
  for wt in "$WORKTREE_DIR"/*/; do
    [ -d "$wt" ] || continue
    if is_older_than_days "$wt" "$MAX_AGE_DAYS"; then
      if [ "$DRY_RUN" = "true" ]; then
        echo "[DRY-RUN] Would remove worktree: $wt"
      else
        git worktree remove --force "$wt" 2>/dev/null || true
        echo "[REMOVED] Worktree: $wt"
      fi
      ((removed_wt++)) || true
    fi
  done
fi

# 2. Prune worktree references
git worktree prune 2>/dev/null || true

# 3. Delete orphaned worktree-agent-* branches
for branch in $(git branch --list 'worktree-agent-*' | sed 's/^[* +]*//'); do
  # Check if any worktree still references this branch
  if ! git worktree list | grep -q "$branch"; then
    if [ "$DRY_RUN" = "true" ]; then
      echo "[DRY-RUN] Would delete branch: $branch"
    else
      git branch -D "$branch" 2>/dev/null || true
      echo "[DELETED] Branch: $branch"
    fi
    ((removed_br++)) || true
  fi
done

echo "--- Worktree Cleanup Summary ---"
echo "Worktrees removed: $removed_wt"
echo "Branches deleted: $removed_br"
