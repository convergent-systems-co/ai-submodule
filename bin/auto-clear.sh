#!/usr/bin/env bash
# auto-clear.sh — Outer loop that restarts the agentic session after context resets.
#
# The orchestrator persists state to disk, so each new session picks up
# where the last one left off. This script handles the process lifecycle.
#
# Usage:
#   bash bin/auto-clear.sh                  # Default: 50 retries
#   bash bin/auto-clear.sh --max-retries 10 # Custom retry limit
#   bash bin/auto-clear.sh --prompt "/startup"  # Custom prompt (default)
#
# Exit codes:
#   0 — All work complete (orchestrator returned "done")
#   1 — Max retries exceeded or unrecoverable error

set -euo pipefail

MAX_RETRIES="${MAX_RETRIES:-50}"
PROMPT="${PROMPT:-/startup}"
MIN_SESSION_SECONDS=30  # Sessions shorter than this are errors

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --max-retries) MAX_RETRIES="$2"; shift 2 ;;
        --prompt) PROMPT="$2"; shift 2 ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

retry_count=0
backoff=2

echo "=== Auto-clear loop: max_retries=$MAX_RETRIES, prompt=$PROMPT ==="

while [[ $retry_count -lt $MAX_RETRIES ]]; do
    start_time=$(date +%s)
    echo "--- Session $((retry_count + 1))/$MAX_RETRIES ($(date -u +%Y-%m-%dT%H:%M:%SZ)) ---"

    # Run claude with the startup prompt
    set +e
    claude --prompt "$PROMPT"
    exit_code=$?
    set -e

    end_time=$(date +%s)
    duration=$((end_time - start_time))

    echo "--- Session ended: exit_code=$exit_code, duration=${duration}s ---"

    # Check for normal completion (orchestrator returned "done")
    if [[ $exit_code -eq 0 ]]; then
        # Check if orchestrator status shows "done"
        status_output=$(python -m governance.engine.orchestrator status 2>/dev/null || echo '{}')
        if echo "$status_output" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('action')=='done' else 1)" 2>/dev/null; then
            echo "=== All work complete ==="
            exit 0
        fi
        # Normal session end — reset backoff and continue
        backoff=2
        retry_count=$((retry_count + 1))
        continue
    fi

    # Fast exit = error — apply exponential backoff
    if [[ $duration -lt $MIN_SESSION_SECONDS ]]; then
        echo "WARNING: Session lasted only ${duration}s (< ${MIN_SESSION_SECONDS}s) — likely error"
        echo "Backing off for ${backoff}s..."
        sleep $backoff
        backoff=$((backoff * 2))
        # Cap backoff at 5 minutes
        if [[ $backoff -gt 300 ]]; then
            backoff=300
        fi
    else
        # Normal duration — reset backoff
        backoff=2
    fi

    retry_count=$((retry_count + 1))
done

echo "ERROR: Max retries ($MAX_RETRIES) exceeded" >&2
exit 1
