#!/bin/bash
# governance/bin/check-branch-protection.sh — Query if default branch requires PRs.
# Outputs REQUIRES_PR=true|false and exits. Early-exit path for init.sh.
#
# Usage (standalone): bash governance/bin/check-branch-protection.sh
# Usage (from init.sh): source governance/bin/check-branch-protection.sh

set -euo pipefail

# Allow caller to set AI_DIR/PROJECT_ROOT/VENV_DIR; fall back to auto-detect
if [ -z "${AI_DIR:-}" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  AI_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
  PROJECT_ROOT="$(dirname "$AI_DIR")"
  VENV_DIR="$AI_DIR/.venv"
fi

if ! command -v gh &>/dev/null; then
  echo "REQUIRES_PR=false"
  exit 0
fi

# Check for config override (best-effort — requires Python for YAML parsing)
_bp_override="auto"
_bp_python=""
if [ -d "$VENV_DIR" ] && [ -x "$VENV_DIR/bin/python" ]; then
  _bp_python="$VENV_DIR/bin/python"
elif command -v python3 &>/dev/null; then
  _bp_python="python3"
fi
if [ -n "$_bp_python" ]; then
  _bp_override=$("$_bp_python" -c "
import yaml, os, sys
def deep_merge(base, override):
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        elif k in result and isinstance(result[k], list) and isinstance(v, list):
            result[k] = result[k] + v
        else:
            result[k] = v
    return result
config = {}
for f in sys.argv[1:]:
    if os.path.exists(f):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
            config = deep_merge(config, data)
val = config.get('repository', {}).get('branch_protection', {}).get('require_pr_for_structural_commits', 'auto')
print(val)
" "$AI_DIR/config.yaml" "$AI_DIR/project.yaml" "$PROJECT_ROOT/project.yaml" 2>/dev/null) || _bp_override="auto"
fi

if [ "$_bp_override" = "true" ]; then
  echo "REQUIRES_PR=true"
  exit 0
elif [ "$_bp_override" = "false" ]; then
  echo "REQUIRES_PR=false"
  exit 0
fi

# Auto-detect via GitHub API
_bp_repo=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null) || {
  echo "REQUIRES_PR=false"
  exit 0
}
_bp_branch=$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name' 2>/dev/null) || _bp_branch="main"

# Try rulesets API (modern)
_bp_rules=$(gh api "repos/$_bp_repo/rules/branches/$_bp_branch" --jq '[.[] | select(.type == "pull_request")] | length' 2>/dev/null) || _bp_rules="0"
if [ "$_bp_rules" != "0" ] && [ -n "$_bp_rules" ]; then
  echo "REQUIRES_PR=true"
  exit 0
fi

# Fallback: legacy branch protection
_bp_pr_reviews=$(gh api "repos/$_bp_repo/branches/$_bp_branch/protection" --jq '.required_pull_request_reviews // empty' 2>/dev/null) || _bp_pr_reviews=""
if [ -n "$_bp_pr_reviews" ]; then
  echo "REQUIRES_PR=true"
  exit 0
fi

echo "REQUIRES_PR=false"
exit 0
