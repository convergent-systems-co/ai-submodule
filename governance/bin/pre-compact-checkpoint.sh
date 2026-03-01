#!/bin/bash
# PreCompact Hook — Emergency Checkpoint Writer
# Called by Claude Code before context compaction occurs.
# Writes an emergency checkpoint so the next /startup can auto-recover.

set -euo pipefail

CHECKPOINT_DIR=".governance/checkpoints"
mkdir -p "$CHECKPOINT_DIR"

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
BRANCH_SAFE=$(echo "$BRANCH" | tr '/' '-')
GIT_STATUS=$(git status --porcelain 2>/dev/null | head -10 || echo "unknown")
GIT_DIRTY="false"
if [ -n "$GIT_STATUS" ] && [ "$GIT_STATUS" != "unknown" ]; then
  GIT_DIRTY="true"
  # Auto-commit WIP if there are staged or modified tracked files
  TRACKED_CHANGES=$(git diff --name-only 2>/dev/null; git diff --cached --name-only 2>/dev/null)
  if [ -n "$TRACKED_CHANGES" ]; then
    git add -A 2>/dev/null || true
    git commit -m "wip: emergency checkpoint before compaction" --no-verify 2>/dev/null || true
  fi
fi

CHECKPOINT_FILE="${CHECKPOINT_DIR}/${TIMESTAMP}-emergency-${BRANCH_SAFE}.json"

cat > "$CHECKPOINT_FILE" << CHECKPOINT_EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "session_id": "emergency",
  "phase": "interrupted",
  "phase_label": "Compaction interrupted agentic loop",
  "context_capacity": {
    "tier": "Red",
    "signals": ["pre_compact_hook_fired"],
    "trigger": "claude_code_pre_compact_hook"
  },
  "git_state": {
    "branch": "${BRANCH}",
    "clean": $([ "$GIT_DIRTY" = "false" ] && echo "true" || echo "false"),
    "stash": false
  },
  "completed_work": [],
  "remaining_work": ["Check git log for recent commits to determine what was in progress"],
  "issues": [],
  "notes": "Emergency checkpoint written by PreCompact hook. The agentic loop was interrupted by context compaction. Run /startup to auto-recover."
}
CHECKPOINT_EOF

echo "Emergency checkpoint written to: $CHECKPOINT_FILE" >&2
