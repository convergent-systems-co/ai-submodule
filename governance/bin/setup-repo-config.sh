#!/bin/bash
# governance/bin/setup-repo-config.sh — Repository settings via gh API + ruleset validation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
resolve_ai_dir

PYTHON_CMD="${PYTHON_CMD:-}"
PYTHON_OK="${PYTHON_OK:-false}"

configure_repository() {
  echo "Configuring repository settings..."

  if ! check_command gh; then
    log_skip "GitHub CLI (gh) not found. Skipping repository configuration."
    echo "         Install from: https://cli.github.com/"
    return 0
  fi

  if ! gh auth status &>/dev/null 2>&1; then
    log_skip "Not authenticated with GitHub CLI. Run: gh auth login"
    return 0
  fi

  local repo
  repo=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null) || {
    log_skip "Could not detect GitHub repository."
    return 0
  }

  local has_repo_config
  has_repo_config=$(parse_yaml_field "repository" "__MISSING__")
  if [ "$has_repo_config" = "__MISSING__" ]; then
    log_skip "No repository section in config.yaml"
    return 0
  fi

  local auto_merge delete_branch allow_squash allow_merge allow_rebase
  auto_merge=$(parse_yaml_field "repository.auto_merge" "__UNSET__")
  delete_branch=$(parse_yaml_field "repository.delete_branch_on_merge" "true")
  allow_squash=$(parse_yaml_field "repository.allow_squash_merge" "true")
  allow_merge=$(parse_yaml_field "repository.allow_merge_commit" "true")
  allow_rebase=$(parse_yaml_field "repository.allow_rebase_merge" "true")

  # Conditional auto-merge: if not explicitly set, auto-enable when the governance
  # bot pipeline is fully configured (CODEOWNERS includes github-actions[bot] AND
  # the dark-factory-governance.yml workflow is deployed).
  if [ "$auto_merge" = "__UNSET__" ]; then
    local codeowners_has_bot=false
    local governance_workflow_exists=false

    # Check CODEOWNERS for github-actions[bot]
    local codeowners_path=""
    for candidate in "$PROJECT_ROOT/.github/CODEOWNERS" "$PROJECT_ROOT/CODEOWNERS" "$PROJECT_ROOT/docs/CODEOWNERS"; do
      if [ -f "$candidate" ]; then
        codeowners_path="$candidate"
        break
      fi
    done
    if [ -n "$codeowners_path" ] && grep -q 'github-actions\[bot\]' "$codeowners_path" 2>/dev/null; then
      codeowners_has_bot=true
    fi

    # Check for governance workflow
    if [ -f "$PROJECT_ROOT/.github/workflows/dark-factory-governance.yml" ]; then
      governance_workflow_exists=true
    fi

    if [ "$codeowners_has_bot" = "true" ] && [ "$governance_workflow_exists" = "true" ]; then
      auto_merge=true
      log_ok "Auto-merge conditionally enabled (CODEOWNERS has github-actions[bot] + governance workflow present)"
    else
      auto_merge=false
      if [ "$codeowners_has_bot" = "false" ]; then
        log_debug "Auto-merge not enabled: CODEOWNERS missing github-actions[bot]"
      fi
      if [ "$governance_workflow_exists" = "false" ]; then
        log_debug "Auto-merge not enabled: dark-factory-governance.yml workflow not found"
      fi
    fi
  fi

  echo "  Configuring $repo..."

  if [ "$DRY_RUN" = "true" ]; then
    echo "  [DRY-RUN] Would apply: auto_merge=$auto_merge, delete_branch=$delete_branch"
    return 0
  fi

  if gh api "repos/$repo" -X PATCH \
    --input <(cat <<EOF
{
  "allow_auto_merge": $auto_merge,
  "delete_branch_on_merge": $delete_branch,
  "allow_squash_merge": $allow_squash,
  "allow_merge_commit": $allow_merge,
  "allow_rebase_merge": $allow_rebase
}
EOF
    ) --silent 2>/dev/null; then
    log_ok "Repository settings applied (auto_merge=$auto_merge, delete_branch=$delete_branch)"
  else
    log_warn "Could not apply repository settings (may require admin permissions)"
    echo "         Ask a repository admin to enable auto-merge in Settings > General"
  fi

  # CODEOWNERS handled by setup-codeowners.sh (called separately by orchestrator)
}

validate_rulesets() {
  echo ""
  echo "Validating org/repo rulesets..."

  if ! check_command gh || ! gh auth status &>/dev/null 2>&1; then
    log_skip "GitHub CLI not available or not authenticated"
    return 0
  fi

  local repo
  repo=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null) || {
    log_skip "Could not detect GitHub repository"
    return 0
  }

  local python_cmd
  if [ -d "$VENV_DIR" ]; then
    python_cmd="$VENV_DIR/bin/python"
  elif [ -n "$PYTHON_CMD" ] && [ "$PYTHON_OK" = "true" ]; then
    python_cmd="$PYTHON_CMD"
  else
    log_skip "Python not available for config parsing"
    return 0
  fi

  local expected_names
  expected_names=$("$python_cmd" -c "
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

rulesets = config.get('repository', {}).get('branch_protection', {}).get('expected_rulesets', [])
for rs in rulesets:
    name = rs.get('name', '')
    if name:
        print(name)
" "$AI_DIR/config.yaml" "$AI_DIR/project.yaml" "$PROJECT_ROOT/project.yaml" 2>/dev/null)

  if [ -z "$expected_names" ]; then
    log_skip "No expected rulesets configured"
    return 0
  fi

  local active_rulesets
  active_rulesets=$(gh api "repos/$repo/rulesets" --jq '.[].name' 2>/dev/null) || {
    log_warn "Could not fetch rulesets (may require admin permissions)"
    echo "         Verify rulesets manually in Settings > Rules > Rulesets"
    return 0
  }

  local missing=0
  while IFS= read -r expected; do
    if echo "$active_rulesets" | grep -qF "$expected"; then
      log_ok "Ruleset found: $expected"
    else
      log_warn "Expected ruleset not found: $expected"
      missing=$((missing + 1))
    fi
  done <<< "$expected_names"

  if [ "$missing" -gt 0 ]; then
    log_warn "$missing expected ruleset(s) not found. Check org/repo settings."
    echo "         These are validated, not applied — configure them in GitHub Settings > Rules."
  else
    log_ok "All expected rulesets present"
  fi
}

configure_repository
validate_rulesets
