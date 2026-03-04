#!/bin/bash
# bin/issue-monitor.sh — Background issue monitor for Linux/macOS.
# Polls GitHub for actionable issues and dispatches them to Claude or Copilot.
#
# Usage (from consuming repo root, where .ai is the submodule):
#   bash .ai/bin/issue-monitor.sh                    # Foreground
#   nohup bash .ai/bin/issue-monitor.sh &            # Background
#   AI_MONITOR_BACKEND=copilot bash .ai/bin/issue-monitor.sh  # Copilot backend
#
# Environment variables:
#   AI_MONITOR_INTERVAL  — Poll interval in seconds (default: 300)
#   AI_MONITOR_BACKEND   — AI backend: "claude" or "copilot" (default: claude)
#   AI_MONITOR_REPO      — Repository in owner/repo format (auto-detected)
#   AI_MONITOR_MODEL     — Claude model to use (default: claude-opus-4-6)
#   AI_MONITOR_DRY_RUN   — Set to "true" to log without dispatching (default: false)
#   AI_MONITOR_LOG       — Log file path (default: bin/issue-monitor.log)
#
# Security note:
#   This script dispatches issues to AI agents. Only run on repositories where
#   issue authors are trusted (org-internal or with restricted issue creation).
#   Untrusted issue content could be used for prompt injection.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_DIR="$(dirname "$SCRIPT_DIR")"
STATE_FILE="$SCRIPT_DIR/.issue-monitor-state"
LOG_FILE="${AI_MONITOR_LOG:-$SCRIPT_DIR/issue-monitor.log}"
INTERVAL="${AI_MONITOR_INTERVAL:-300}"
BACKEND="${AI_MONITOR_BACKEND:-claude}"
DRY_RUN="${AI_MONITOR_DRY_RUN:-false}"
MODEL="${AI_MONITOR_MODEL:-claude-opus-4-6}"

# --- Argument parsing ---

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --claude) BACKEND=claude ;;
    --copilot) BACKEND=copilot ;;
    --interval=*) INTERVAL="${arg#*=}" ;;
    --model=*) MODEL="${arg#*=}" ;;
    --help|-h)
      echo "Usage: bash .ai/bin/issue-monitor.sh [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --dry-run         Log actions without dispatching"
      echo "  --claude          Use Claude backend (default)"
      echo "  --copilot         Use Copilot backend"
      echo "  --interval=SECS   Poll interval in seconds (default: 300)"
      echo "  --model=MODEL     Claude model (default: claude-opus-4-6)"
      echo "  --help, -h        Show this help message"
      echo ""
      echo "Environment variables:"
      echo "  AI_MONITOR_INTERVAL, AI_MONITOR_BACKEND, AI_MONITOR_REPO,"
      echo "  AI_MONITOR_MODEL, AI_MONITOR_DRY_RUN, AI_MONITOR_LOG"
      echo ""
      echo "Security: Only run on repos with trusted issue authors."
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg (use --help for usage)"
      exit 1
      ;;
  esac
done

# --- Detect repository ---

detect_repo() {
  if [ -n "${AI_MONITOR_REPO:-}" ]; then
    echo "$AI_MONITOR_REPO"
    return
  fi
  local remote_url
  remote_url="$(git remote get-url upstream 2>/dev/null || git remote get-url origin 2>/dev/null || echo "")"
  if [ -z "$remote_url" ]; then
    echo ""
    return
  fi
  # Extract owner/repo from SSH or HTTPS URLs
  echo "$remote_url" | sed -E 's|.*github\.com[:/]||; s|\.git$||'
}

NETWORK_ID="$(whoami)"
REPO="$(detect_repo)"
if [ -z "$REPO" ]; then
  echo "ERROR: Could not detect repository. Set AI_MONITOR_REPO=owner/repo" >&2
  exit 1
fi

# --- Logging ---

log() {
  local ts
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "[$ts] $*" | tee -a "$LOG_FILE"
}

# --- State management (uses simple line-per-issue format for robustness) ---

init_state() {
  if [ ! -f "$STATE_FILE" ]; then
    touch "$STATE_FILE"
  fi
}

is_seen() {
  local issue_number="$1"
  grep -qx "$issue_number" "$STATE_FILE" 2>/dev/null
}

mark_seen() {
  local issue_number="$1"
  echo "$issue_number" >> "$STATE_FILE"
}

# --- Issue filtering ---

is_actionable() {
  local issue_json="$1"
  local issue_number="$2"

  # Check exclusion labels
  local labels
  labels="$(echo "$issue_json" | jq -r '.labels[].name' 2>/dev/null)"
  for label in blocked wontfix duplicate refine; do
    if echo "$labels" | grep -qx "$label"; then
      return 1
    fi
  done

  # Check if assigned to a human (bot assignees are OK per startup.md)
  local human_assignees
  human_assignees="$(echo "$issue_json" | jq '[.assignees[] | select(.type != "Bot" and .type != "bot")] | length' 2>/dev/null || echo "0")"
  if [ "$human_assignees" -gt 0 ]; then
    return 1
  fi

  # Check if updated by a human in the last 24 hours (avoid conflicts per startup.md)
  local updated_at
  updated_at="$(echo "$issue_json" | jq -r '.updatedAt // empty' 2>/dev/null)"
  if [ -n "$updated_at" ]; then
    local updated_epoch now_epoch
    if date -d "$updated_at" +%s &>/dev/null; then
      # GNU date
      updated_epoch="$(date -d "$updated_at" +%s)"
      now_epoch="$(date +%s)"
    elif date -j -f "%Y-%m-%dT%H:%M:%SZ" "$updated_at" +%s &>/dev/null; then
      # BSD/macOS date
      updated_epoch="$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$updated_at" +%s)"
      now_epoch="$(date +%s)"
    else
      updated_epoch=0
      now_epoch=0
    fi
    if [ "$now_epoch" -gt 0 ] && [ "$updated_epoch" -gt 0 ]; then
      local age_hours=$(( (now_epoch - updated_epoch) / 3600 ))
      if [ "$age_hours" -lt 24 ]; then
        # Check if the last update was by a human (heuristic: if the issue was
        # recently updated and we can't determine who, skip it to be safe)
        return 1
      fi
    fi
  fi

  # Check if branch exists
  local branches
  branches="$(gh api "repos/$REPO/branches" --jq '.[].name' 2>/dev/null || echo "")"
  if echo "$branches" | grep -qE "($NETWORK_ID|feature)/[^/]+/$issue_number/"; then
    return 1
  fi

  return 0
}

# --- Dispatch ---

dispatch_claude() {
  local issue_number="$1"
  local issue_title="$2"

  log "Dispatching issue #$issue_number to Claude ($MODEL)..."

  if [ "$DRY_RUN" = "true" ]; then
    log "[DRY RUN] Would invoke Claude Code for issue #$issue_number: $issue_title"
    return 0
  fi

  # Check if claude CLI is available
  if ! command -v claude &>/dev/null; then
    log "ERROR: Claude Code CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
    return 1
  fi

  # Build prompt as a temp file to avoid quoting issues
  local prompt_file
  prompt_file="$(mktemp)"
  cat > "$prompt_file" <<EOF
You are the Team Lead persona from the Dark Forge governance platform.
Read governance/prompts/startup.md for the full agentic loop specification.

An issue needs processing:
- Issue #$issue_number: $issue_title
- Repository: $REPO

Enter the Startup Sequence at Step 4 (Validate Intent) for issue #$issue_number.
Follow all governance steps through Step 7 (PR Monitoring & Review Loop).
EOF

  local prompt
  prompt="$(cat "$prompt_file")"
  rm -f "$prompt_file"

  claude --model "$MODEL" --print --prompt "$prompt" >> "$LOG_FILE" 2>&1 &
  log "Claude Code launched in background (PID: $!)"
}

dispatch_copilot() {
  local issue_number="$1"
  local issue_title="$2"

  log "Dispatching issue #$issue_number to Copilot coding agent..."

  if [ "$DRY_RUN" = "true" ]; then
    log "[DRY RUN] Would assign issue #$issue_number to Copilot"
    return 0
  fi

  if gh api "repos/$REPO/issues/$issue_number/assignees" \
    --method POST -f "assignees[]=copilot" >> "$LOG_FILE" 2>&1; then
    log "Issue #$issue_number assigned to Copilot coding agent"
  else
    log "WARNING: Failed to assign issue #$issue_number to Copilot. Agent may not be enabled."
  fi
}

dispatch() {
  local issue_number="$1"
  local issue_title="$2"

  case "$BACKEND" in
    claude)  dispatch_claude "$issue_number" "$issue_title" ;;
    copilot) dispatch_copilot "$issue_number" "$issue_title" ;;
    *)
      log "ERROR: Unknown backend '$BACKEND'. Use 'claude' or 'copilot'."
      return 1
      ;;
  esac
}

# --- Graceful shutdown ---

RUNNING=true
cleanup() {
  log "Shutting down issue monitor..."
  RUNNING=false
}
trap cleanup SIGINT SIGTERM

# --- Main loop ---

main() {
  init_state
  log "Issue monitor started (repo=$REPO, backend=$BACKEND, interval=${INTERVAL}s, dry_run=$DRY_RUN)"
  log "Log file: $LOG_FILE"
  log "State file: $STATE_FILE"

  while [ "$RUNNING" = "true" ]; do
    log "Polling for open issues..."

    # Fetch issues (include updatedAt for 24-hour check)
    local issues
    issues="$(gh issue list --repo "$REPO" --state open --json number,title,labels,assignees,updatedAt --limit 50 2>/dev/null || echo "[]")"

    local issue_count
    issue_count="$(echo "$issues" | jq 'length' 2>/dev/null || echo "0")"
    log "Found $issue_count open issues"

    # Process each issue (use process substitution to avoid subshell pipe issue)
    while IFS= read -r issue; do
      [ -z "$issue" ] && continue
      local number title
      number="$(echo "$issue" | jq -r '.number')"
      title="$(echo "$issue" | jq -r '.title')"

      # Skip if already seen
      if is_seen "$number"; then
        continue
      fi

      # Check actionability
      if is_actionable "$issue" "$number"; then
        log "Actionable issue found: #$number — $title"
        dispatch "$number" "$title"
        mark_seen "$number"
      else
        log "Skipping issue #$number (not actionable)"
        mark_seen "$number"
      fi
    done < <(echo "$issues" | jq -c '.[]' 2>/dev/null)

    if [ "$RUNNING" = "true" ]; then
      log "Next poll in ${INTERVAL}s..."
      sleep "$INTERVAL" &
      wait $! 2>/dev/null || true
    fi
  done

  log "Issue monitor stopped."
}

main
