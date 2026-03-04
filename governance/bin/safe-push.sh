#!/usr/bin/env bash
# Safe Push — push-with-retry, rebase, and AI-based conflict resolution.
#
# Implements the Safe Push pattern for parallel Coder merges:
#   1. Attempt git push
#   2. On rejection: fetch + rebase
#   3. Regenerate generated files on conflict
#   4. AI-resolve code conflicts via the conflict resolver engine
#   5. Escalate governance-protected file conflicts to human review
#   6. --force-with-lease fallback after max retries
#
# Usage:
#   bash governance/bin/safe-push.sh [OPTIONS]
#
# Options:
#   --branch NAME       Branch to push (default: current branch)
#   --remote NAME       Remote name (default: origin)
#   --max-retries N     Maximum push attempts (default: 3)
#   --dry-run           Simulate without executing
#   --force-with-lease  Skip retries, go straight to force-with-lease
#   --help              Show this help
#
# Requires: git, python3 (for conflict resolver engine)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Defaults
BRANCH=""
REMOTE="origin"
MAX_RETRIES=3
DRY_RUN=false
FORCE_LEASE=false
AUDIT_DIR="${REPO_ROOT}/.artifacts/state/conflict-resolutions"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --remote)
            REMOTE="$2"
            shift 2
            ;;
        --max-retries)
            MAX_RETRIES="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force-with-lease)
            FORCE_LEASE=true
            shift
            ;;
        --help)
            head -28 "$0" | tail -25
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

# Detect branch if not specified
if [[ -z "$BRANCH" ]]; then
    BRANCH="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
fi

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log() { echo "[safe-push] $*"; }
warn() { echo "[safe-push] WARNING: $*" >&2; }
fail() { echo "[safe-push] ERROR: $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------
write_audit() {
    local status="$1"
    local details="$2"
    mkdir -p "$AUDIT_DIR"
    local timestamp
    timestamp="$(date -u +%Y%m%d-%H%M%S)"
    cat > "${AUDIT_DIR}/safe-push-${timestamp}.json" <<AUDITEOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "branch": "${BRANCH}",
  "remote": "${REMOTE}",
  "status": "${status}",
  "details": "${details}"
}
AUDITEOF
}

# ---------------------------------------------------------------------------
# Direct force-with-lease mode
# ---------------------------------------------------------------------------
if [[ "$FORCE_LEASE" == "true" ]]; then
    log "Force-with-lease push to ${REMOTE}/${BRANCH}"
    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: would execute git push --force-with-lease ${REMOTE} ${BRANCH}"
        exit 0
    fi
    git -C "$REPO_ROOT" push --force-with-lease "$REMOTE" "$BRANCH"
    write_audit "success" "force-with-lease push"
    exit 0
fi

# ---------------------------------------------------------------------------
# Safe Push loop
# ---------------------------------------------------------------------------
log "Safe Push: branch=${BRANCH} remote=${REMOTE} max_retries=${MAX_RETRIES}"

for attempt in $(seq 1 "$MAX_RETRIES"); do
    log "Push attempt ${attempt}/${MAX_RETRIES}"

    if [[ "$DRY_RUN" == "true" ]]; then
        log "DRY RUN: would attempt git push ${REMOTE} ${BRANCH}"
        write_audit "success" "dry run"
        exit 0
    fi

    # Attempt push
    if git -C "$REPO_ROOT" push "$REMOTE" "$BRANCH" 2>/dev/null; then
        log "Push succeeded on attempt ${attempt}"
        write_audit "success" "push succeeded on attempt ${attempt}"
        exit 0
    fi

    log "Push rejected. Fetching and rebasing..."

    # Fetch latest
    git -C "$REPO_ROOT" fetch "$REMOTE"

    # Attempt rebase
    if git -C "$REPO_ROOT" rebase "${REMOTE}/${BRANCH}" 2>/dev/null; then
        log "Rebase succeeded. Retrying push..."
        continue
    fi

    # Rebase had conflicts — check for conflicted files
    CONFLICTED_FILES="$(git -C "$REPO_ROOT" diff --name-only --diff-filter=U 2>/dev/null || true)"

    if [[ -z "$CONFLICTED_FILES" ]]; then
        warn "Rebase failed for non-conflict reasons. Aborting."
        git -C "$REPO_ROOT" rebase --abort 2>/dev/null || true
        write_audit "failed" "rebase failed (non-conflict)"
        fail "Rebase failed and no conflicts detected."
    fi

    log "Conflicts detected in: ${CONFLICTED_FILES}"

    # Invoke Python conflict resolver
    log "Running AI conflict resolver..."
    if python3 -c "
from governance.engine.conflict_resolver import ConflictResolver
import sys, json

resolver = ConflictResolver(repo_root='${REPO_ROOT}')
files = '''${CONFLICTED_FILES}'''.strip().split('\n')
result = resolver.resolve_all(files)

print(json.dumps(result.to_dict()))

if not result.success:
    sys.exit(1)
" 2>/dev/null; then
        log "Conflicts resolved. Continuing rebase..."
        GIT_EDITOR=true git -C "$REPO_ROOT" rebase --continue 2>/dev/null || {
            warn "Rebase --continue failed after resolution."
            git -C "$REPO_ROOT" rebase --abort 2>/dev/null || true
            write_audit "failed" "rebase --continue failed after AI resolution"
            fail "Rebase continue failed after AI resolution."
        }
    else
        warn "AI conflict resolution failed or escalated. Aborting rebase."
        git -C "$REPO_ROOT" rebase --abort 2>/dev/null || true
        write_audit "escalated" "AI resolution failed or governance-protected files conflicted"
        fail "Conflict resolution requires human intervention."
    fi
done

# All retries exhausted — force-with-lease fallback
log "All ${MAX_RETRIES} attempts exhausted. Falling back to --force-with-lease."
if git -C "$REPO_ROOT" push --force-with-lease "$REMOTE" "$BRANCH"; then
    log "Force-with-lease push succeeded."
    write_audit "success" "force-with-lease fallback after ${MAX_RETRIES} retries"
    exit 0
else
    write_audit "failed" "force-with-lease fallback also failed"
    fail "Force-with-lease push failed. Manual intervention required."
fi
