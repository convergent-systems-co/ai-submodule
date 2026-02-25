#!/bin/bash
# .ai/bin/init.sh — Run once after adding the .ai submodule to a project.
# Creates symlinks, detects platform, and optionally installs all dependencies.
#
# Usage:
#   bash .ai/bin/init.sh                 # Symlinks only (existing behavior)
#   bash .ai/bin/init.sh --install-deps  # Symlinks + Python venv + dependencies
#
# This script is idempotent — safe to run multiple times.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # .ai/bin/
AI_DIR="$(dirname "$SCRIPT_DIR")"                             # .ai/
PROJECT_ROOT="$(dirname "$AI_DIR")"                           # project root
VENV_DIR="$AI_DIR/.venv"
REQUIREMENTS="$AI_DIR/governance/bin/requirements.txt"
INSTALL_DEPS=false
PYTHON_MIN_MAJOR=3
PYTHON_MIN_MINOR=12

# --- Parse arguments ---

for arg in "$@"; do
  case "$arg" in
    --install-deps) INSTALL_DEPS=true ;;
    --help|-h)
      echo "Usage: bash .ai/bin/init.sh [--install-deps]"
      echo ""
      echo "Options:"
      echo "  --install-deps  Install Python virtual environment and dependencies"
      echo "  --help, -h      Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: bash .ai/bin/init.sh [--install-deps]"
      exit 1
      ;;
  esac
done

# --- Platform detection ---

detect_platform() {
  local os
  os="$(uname -s)"
  case "$os" in
    Darwin) echo "macOS" ;;
    Linux)  echo "Linux" ;;
    *)      echo "$os" ;;
  esac
}

PLATFORM="$(detect_platform)"
echo "Platform: $PLATFORM"
echo ""

# --- Python detection (must run before symlinks section which uses PYTHON_CMD) ---

find_python() {
  # Try python3 first, then python
  for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
      echo "$cmd"
      return 0
    fi
  done
  return 1
}

check_python_version() {
  local cmd="$1"
  local version
  version="$($cmd --version 2>&1)"
  if [[ "$version" =~ Python\ ([0-9]+)\.([0-9]+) ]]; then
    local major="${BASH_REMATCH[1]}"
    local minor="${BASH_REMATCH[2]}"
    if [ "$major" -gt "$PYTHON_MIN_MAJOR" ] || { [ "$major" -eq "$PYTHON_MIN_MAJOR" ] && [ "$minor" -ge "$PYTHON_MIN_MINOR" ]; }; then
      echo "  [OK] $version"
      return 0
    else
      echo "  [WARN] $version found, but $PYTHON_MIN_MAJOR.$PYTHON_MIN_MINOR+ required"
      return 1
    fi
  fi
  echo "  [WARN] Could not parse Python version from: $version"
  return 1
}

PYTHON_CMD=""
PYTHON_OK=false

echo "Checking dependencies..."

if PYTHON_CMD="$(find_python)"; then
  if check_python_version "$PYTHON_CMD"; then
    PYTHON_OK=true
  fi
else
  echo "  [WARN] Python is not installed or not in PATH"
  echo "         The policy engine requires Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+"
  echo "         Install from: https://www.python.org/downloads/"
fi

echo ""

# --- Submodule freshness check ---

# If running in a consuming repo (submodule context), check if .ai is up to date
if [ -f "$PROJECT_ROOT/.gitmodules" ] && grep -q '\.ai' "$PROJECT_ROOT/.gitmodules" 2>/dev/null; then
  echo "Checking .ai submodule freshness..."
  # Check for dirty state before attempting update
  if ! git -C "$AI_DIR" diff-index --quiet HEAD -- 2>/dev/null; then
    echo "  [WARN] .ai submodule has uncommitted changes; skipping automatic update"
    echo "         Commit, stash, or discard local changes in .ai, then re-run init.sh"
  elif git -C "$AI_DIR" fetch origin main --quiet 2>/dev/null; then
    LOCAL_SHA=$(git -C "$AI_DIR" rev-parse HEAD 2>/dev/null)
    REMOTE_SHA=$(git -C "$AI_DIR" rev-parse origin/main 2>/dev/null)
    if [ -n "$LOCAL_SHA" ] && [ -n "$REMOTE_SHA" ]; then
      if [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
        echo "  [OK] .ai submodule is up to date (${LOCAL_SHA:0:8})"
      else
        echo "  [UPDATE] .ai submodule is behind (local: ${LOCAL_SHA:0:8}, remote: ${REMOTE_SHA:0:8})"
        if git -C "$PROJECT_ROOT" submodule update --remote .ai 2>/dev/null; then
          NEW_SHA=$(git -C "$AI_DIR" rev-parse HEAD 2>/dev/null)
          echo "  [OK] .ai submodule updated to ${NEW_SHA:0:8}"
          echo "  Run 'git add .ai && git commit -m \"chore: update .ai submodule\"' to save the update"
        else
          echo "  [WARN] Could not update .ai submodule automatically"
          echo "         Run: git submodule update --remote .ai"
        fi
      fi
    fi
  else
    echo "  [WARN] Could not fetch .ai remote (network error or no remote configured)"
    echo "         Continuing with current version"
  fi
  echo ""
fi

# --- SSH to HTTPS URL conversion for CI compatibility ---

# GitHub Actions uses GITHUB_TOKEN with HTTPS; SSH URLs fail in CI.
# Only convert the .ai submodule entry to avoid affecting other submodules.
if [ -f "$PROJECT_ROOT/.gitmodules" ]; then
  if grep -q 'git@github\.com:' "$PROJECT_ROOT/.gitmodules" 2>/dev/null; then
    echo "Converting .ai submodule SSH URL to HTTPS for CI compatibility..."
    awk '
      BEGIN { in_ai = 0 }
      /^\[submodule ".ai"\]$/ { in_ai = 1 }
      /^\[submodule / && $0 !~ /^\[submodule ".ai"\]$/ { in_ai = 0 }
      {
        if (in_ai && $0 ~ /^[[:space:]]*url[[:space:]]*=[[:space:]]*git@github\.com:/) {
          sub(/git@github\.com:/, "https://github.com/")
        }
        print
      }
    ' "$PROJECT_ROOT/.gitmodules" > "$PROJECT_ROOT/.gitmodules.tmp"
    mv "$PROJECT_ROOT/.gitmodules.tmp" "$PROJECT_ROOT/.gitmodules"
    echo "  [OK] Converted SSH URL to HTTPS in .gitmodules (.ai submodule only)"
    # Sync .git/config so existing clones use the updated URL immediately
    if git -C "$PROJECT_ROOT" submodule sync .ai 2>/dev/null; then
      echo "  [OK] Synchronized .ai submodule URL in .git/config"
    else
      echo "  [WARN] Could not sync submodule URL. Run: git submodule sync .ai" >&2
    fi
    echo "  Run 'git add .gitmodules && git commit -m \"chore: use HTTPS URL for .ai submodule\"' to save"
  fi
  echo ""
fi

# --- Symlinks ---

echo "Initializing .ai submodule symlinks..."

# instructions.md -> CLAUDE.md, copilot-instructions, .cursorrules
for target in "CLAUDE.md" ".cursorrules"; do
  if [ ! -L "$PROJECT_ROOT/$target" ] || [ "$(readlink "$PROJECT_ROOT/$target")" != ".ai/instructions.md" ]; then
    ln -sf .ai/instructions.md "$PROJECT_ROOT/$target"
    echo "  Linked $target -> .ai/instructions.md"
  else
    echo "  $target already linked"
  fi
done

# GitHub Copilot instructions
mkdir -p "$PROJECT_ROOT/.github"
COPILOT_TARGET=".github/copilot-instructions.md"
if [ ! -L "$PROJECT_ROOT/$COPILOT_TARGET" ] || [ "$(readlink "$PROJECT_ROOT/$COPILOT_TARGET")" != "../.ai/instructions.md" ]; then
  ln -sf ../.ai/instructions.md "$PROJECT_ROOT/$COPILOT_TARGET"
  echo "  Linked $COPILOT_TARGET -> .ai/instructions.md"
else
  echo "  $COPILOT_TARGET already linked"
fi

# Issue templates — copy to consuming repo's .github/ISSUE_TEMPLATE/
IS_SUBMODULE=false
if [ -f "$PROJECT_ROOT/.gitmodules" ] && grep -q '\.ai' "$PROJECT_ROOT/.gitmodules" 2>/dev/null; then
  IS_SUBMODULE=true
fi

if [ "$IS_SUBMODULE" = "true" ]; then
  TEMPLATE_SRC="$AI_DIR/.github/ISSUE_TEMPLATE"
  TEMPLATE_DST="$PROJECT_ROOT/.github/ISSUE_TEMPLATE"
  if [ -d "$TEMPLATE_SRC" ]; then
    mkdir -p "$TEMPLATE_DST"
    for tmpl in "$TEMPLATE_SRC"/*.yml; do
      [ -f "$tmpl" ] || continue
      TMPL_NAME=$(basename "$tmpl")
      if [ ! -f "$TEMPLATE_DST/$TMPL_NAME" ]; then
        cp "$tmpl" "$TEMPLATE_DST/$TMPL_NAME"
        echo "  Copied issue template $TMPL_NAME"
      else
        echo "  Issue template $TMPL_NAME already exists, skipping"
      fi
    done
  fi
  # Governance workflows — symlink to consuming repo's .github/workflows/
  # Symlinks ensure submodule updates flow automatically without re-running init.sh
  WORKFLOW_SRC="$AI_DIR/.github/workflows"
  WORKFLOW_DST="$PROJECT_ROOT/.github/workflows"
  if [ -d "$WORKFLOW_SRC" ]; then
    mkdir -p "$WORKFLOW_DST"
    # Read workflow lists from config.yaml if Python is available, otherwise use default
    REQUIRED_WORKFLOWS="dark-factory-governance.yml"
    OPTIONAL_WORKFLOWS=""
    if [ -n "$PYTHON_CMD" ]; then
      CONFIG_WORKFLOWS=$("$PYTHON_CMD" -c "
import yaml, os

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
for f in ['$AI_DIR/config.yaml', '$AI_DIR/project.yaml', '$PROJECT_ROOT/project.yaml']:
    if os.path.exists(f):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
            config = deep_merge(config, data)

# Support both new (workflows.required/optional) and legacy (workflows_to_copy) config
wf = config.get('workflows', {})
if isinstance(wf, dict):
    req = wf.get('required', ['dark-factory-governance.yml'])
    opt = wf.get('optional', [])
else:
    req = config.get('workflows_to_copy', ['dark-factory-governance.yml'])
    opt = []
print('REQUIRED=' + ' '.join(req))
print('OPTIONAL=' + ' '.join(opt))
" 2>/dev/null)
      if [ -n "$CONFIG_WORKFLOWS" ]; then
        REQUIRED_WORKFLOWS=$(echo "$CONFIG_WORKFLOWS" | grep '^REQUIRED=' | sed 's/^REQUIRED=//')
        OPTIONAL_WORKFLOWS=$(echo "$CONFIG_WORKFLOWS" | grep '^OPTIONAL=' | sed 's/^OPTIONAL=//')
      fi
    fi

    # Link required workflows (warn if source is missing)
    for wf_name in $REQUIRED_WORKFLOWS; do
      if [ -f "$WORKFLOW_SRC/$wf_name" ]; then
        link_target="../../.ai/.github/workflows/$wf_name"
        if [ -L "$WORKFLOW_DST/$wf_name" ] && [ "$(readlink "$WORKFLOW_DST/$wf_name")" = "$link_target" ]; then
          echo "  Workflow $wf_name already linked"
        elif [ -f "$WORKFLOW_DST/$wf_name" ] && [ ! -L "$WORKFLOW_DST/$wf_name" ]; then
          echo "  Workflow $wf_name exists as regular file, skipping (remove to use symlink)"
        else
          ln -sf "$link_target" "$WORKFLOW_DST/$wf_name"
          echo "  Linked $wf_name -> .ai/.github/workflows/$wf_name"
        fi
      else
        echo "  [WARN] Required workflow $wf_name not found in .ai/.github/workflows/"
      fi
    done

    # Link optional workflows (skip silently if source is missing)
    for wf_name in $OPTIONAL_WORKFLOWS; do
      if [ -f "$WORKFLOW_SRC/$wf_name" ]; then
        link_target="../../.ai/.github/workflows/$wf_name"
        if [ -L "$WORKFLOW_DST/$wf_name" ] && [ "$(readlink "$WORKFLOW_DST/$wf_name")" = "$link_target" ]; then
          echo "  Workflow $wf_name already linked (optional)"
        elif [ -f "$WORKFLOW_DST/$wf_name" ] && [ ! -L "$WORKFLOW_DST/$wf_name" ]; then
          echo "  Workflow $wf_name exists as regular file, skipping (optional)"
        else
          ln -sf "$link_target" "$WORKFLOW_DST/$wf_name"
          echo "  Linked $wf_name -> .ai/.github/workflows/$wf_name (optional)"
        fi
      fi
    done
  fi
  # GOALS.md — create from template if not present in consuming repo
  GOALS_TEMPLATE="$AI_DIR/governance/templates/GOALS.md"
  GOALS_DST="$PROJECT_ROOT/GOALS.md"
  if [ -f "$GOALS_TEMPLATE" ]; then
    if [ -f "$GOALS_DST" ]; then
      echo "  GOALS.md already exists, skipping"
    else
      cp "$GOALS_TEMPLATE" "$GOALS_DST"
      echo "  Created GOALS.md from template"
    fi
  else
    echo "  [WARN] GOALS.md template not found at $GOALS_TEMPLATE"
  fi

  # Panel emission validation — check required panels have baseline emissions
  echo ""
  echo "Validating panel emissions..."
  EMISSIONS_DIR="$AI_DIR/governance/emissions"
  REQUIRED_PANELS="code-review security-review threat-modeling cost-analysis documentation-review data-governance-review"
  MISSING_PANELS=""
  for panel in $REQUIRED_PANELS; do
    if [ ! -f "$EMISSIONS_DIR/${panel}.json" ]; then
      MISSING_PANELS="$MISSING_PANELS $panel"
    fi
  done
  if [ -n "$MISSING_PANELS" ]; then
    echo "  [WARN] Missing required panel emissions:$MISSING_PANELS"
    echo "         The governance workflow will block PRs until these panels have emissions."
    echo "         See governance/policy/default.yaml for required panel definitions."
  else
    echo "  [OK] All required panel emissions present"
  fi

  # Project directories — create .plans/ and .panels/ in consuming repo
  echo ""
  echo "Creating project directories..."
  # Read directory list from config if Python is available, otherwise use defaults
  PROJECT_DIRS=".plans .panels"
  if [ -n "$PYTHON_CMD" ]; then
    CONFIG_DIRS=$("$PYTHON_CMD" -c "
import yaml, os
config = {}
for f in ['$AI_DIR/config.yaml', '$AI_DIR/project.yaml', '$PROJECT_ROOT/project.yaml']:
    if os.path.exists(f):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
            # Merge project_directories lists
            if 'project_directories' in data:
                existing = config.get('project_directories', [])
                config['project_directories'] = existing + data['project_directories']
            for k, v in data.items():
                if k != 'project_directories':
                    config[k] = v
dirs = config.get('project_directories', [{'path': '.plans'}, {'path': '.panels'}])
print(' '.join(d.get('path', '') for d in dirs if d.get('path')))
" 2>/dev/null) && PROJECT_DIRS="$CONFIG_DIRS"
  fi
  for dir_name in $PROJECT_DIRS; do
    dir_path="$PROJECT_ROOT/$dir_name"
    if [ -d "$dir_path" ]; then
      echo "  $dir_name/ already exists"
    else
      mkdir -p "$dir_path"
      touch "$dir_path/.gitkeep"
      echo "  Created $dir_name/ with .gitkeep"
    fi
    # Ensure .gitkeep exists even if directory was created manually
    if [ ! -f "$dir_path/.gitkeep" ] && [ -z "$(ls -A "$dir_path" 2>/dev/null)" ]; then
      touch "$dir_path/.gitkeep"
    fi
  done
else
  echo "  Skipping template/workflow/directory setup (not a submodule context)"
fi

# --- Migration warning: project.yaml location ---

if [ -f "$AI_DIR/project.yaml" ] && [ ! -f "$PROJECT_ROOT/project.yaml" ]; then
  echo ""
  echo "  [MIGRATE] project.yaml found at .ai/project.yaml (legacy location)"
  echo "            The preferred location is now the project root: ./project.yaml"
  echo "            Move it with: mv .ai/project.yaml project.yaml"
  echo "            Both locations are read; root takes precedence."
fi

echo ""

# --- Dependency installation ---

if [ "$INSTALL_DEPS" = "true" ]; then
  echo ""
  echo "Installing dependencies..."

  if [ "$PYTHON_OK" = "false" ]; then
    echo "  [ERROR] Cannot install dependencies: Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+ is required but not found."
    echo "          Install Python from https://www.python.org/downloads/ and re-run with --install-deps."
    exit 1
  fi

  # Create virtual environment
  if [ ! -d "$VENV_DIR" ]; then
    echo "  Creating virtual environment at .ai/.venv ..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    echo "  [OK] Virtual environment created"
  else
    echo "  [OK] Virtual environment already exists at .ai/.venv"
  fi

  # Install requirements
  if [ ! -f "$REQUIREMENTS" ]; then
    echo "  [ERROR] requirements.txt not found at $REQUIREMENTS"
    echo "          Cannot install dependencies without a requirements file."
    echo "          Either create a requirements file at $REQUIREMENTS or rerun without --install-deps."
    exit 1
  fi

  echo "  Installing packages from requirements.txt ..."
  "$VENV_DIR/bin/pip" install --quiet --upgrade pip
  "$VENV_DIR/bin/pip" install --quiet -r "$REQUIREMENTS"
  echo "  [OK] Packages installed"

  # Verify installation
  echo ""
  echo "Verifying installation..."
  if "$VENV_DIR/bin/python" -c "import jsonschema; import yaml; print('  [OK] jsonschema and pyyaml verified')" 2>/dev/null; then
    :
  else
    echo "  [ERROR] Package verification failed. Check the install output above."
    exit 1
  fi
else
  echo ""
  if [ "$PYTHON_OK" = "true" ]; then
    # Check if packages are available (in venv or system)
    if [ -d "$VENV_DIR" ]; then
      echo "  [OK] Virtual environment exists at .ai/.venv"
    else
      echo "  [INFO] No virtual environment found. Run with --install-deps to create one."
    fi
  fi
fi

# --- Repository configuration ---

# Parse a YAML field using Python (already a dependency via policy engine).
# Usage: parse_yaml_field "repository.auto_merge" "true" [config_file]
parse_yaml_field() {
  local field="$1"
  local default_value="$2"
  local config_file="${3:-$AI_DIR/config.yaml}"
  local project_file="$AI_DIR/project.yaml"
  local root_project_file="$PROJECT_ROOT/project.yaml"

  # Build a Python snippet that reads config.yaml, merges project.yaml overrides,
  # and extracts the nested field.
  local python_cmd
  if [ -d "$VENV_DIR" ]; then
    python_cmd="$VENV_DIR/bin/python"
  elif [ -n "$PYTHON_CMD" ] && [ "$PYTHON_OK" = "true" ]; then
    python_cmd="$PYTHON_CMD"
  else
    echo "$default_value"
    return 0
  fi

  "$python_cmd" -c "
import yaml, sys, os

def deep_get(d, keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d

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
for f in ['$config_file', '$project_file', '$root_project_file']:
    if os.path.exists(f):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
            config = deep_merge(config, data)

val = deep_get(config, '$field'.split('.'))
if val is None:
    print('$default_value')
else:
    print(str(val).lower() if isinstance(val, bool) else val)
" 2>/dev/null || echo "$default_value"
}

# Generate CODEOWNERS content from config
generate_codeowners() {
  local python_cmd
  if [ -d "$VENV_DIR" ]; then
    python_cmd="$VENV_DIR/bin/python"
  elif [ -n "$PYTHON_CMD" ] && [ "$PYTHON_OK" = "true" ]; then
    python_cmd="$PYTHON_CMD"
  else
    return 1
  fi

  "$python_cmd" -c "
import yaml, os

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
for f in ['$AI_DIR/config.yaml', '$AI_DIR/project.yaml', '$PROJECT_ROOT/project.yaml']:
    if os.path.exists(f):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
            config = deep_merge(config, data)

repo = config.get('repository', {})
co = repo.get('codeowners', {})
if not co.get('enabled', True):
    exit(0)

print('# CODEOWNERS — generated by .ai/bin/init.sh from config.yaml')
print('# Manual edits outside the managed section will be preserved.')
print('#')
print('# github-actions[bot] is included so the Dark Factory governance workflow')
print('# approval can satisfy code owner review requirements.')
print('# See .ai/docs/configuration/repository-setup.md for details.')
print()

default_owner = co.get('default_owner', '')
if default_owner:
    print(f'* {default_owner}')
    print()

for rule in co.get('rules', []):
    pattern = rule.get('pattern', '')
    owners = ' '.join(rule.get('owners', []))
    if pattern and owners:
        print(f'{pattern} {owners}')
" 2>/dev/null
}

configure_repository() {
  echo "Configuring repository settings..."

  # Check if gh CLI is available
  if ! command -v gh &>/dev/null; then
    echo "  [SKIP] GitHub CLI (gh) not found. Skipping repository configuration."
    echo "         Install from: https://cli.github.com/"
    return 0
  fi

  # Check auth
  if ! gh auth status &>/dev/null 2>&1; then
    echo "  [SKIP] Not authenticated with GitHub CLI. Run: gh auth login"
    return 0
  fi

  # Detect repo from git remote
  local repo
  repo=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null) || {
    echo "  [SKIP] Could not detect GitHub repository."
    return 0
  }

  # Check if repository section exists in config
  local has_repo_config
  has_repo_config=$(parse_yaml_field "repository" "__MISSING__")
  if [ "$has_repo_config" = "__MISSING__" ]; then
    echo "  [SKIP] No repository section in config.yaml"
    return 0
  fi

  # Read settings
  local auto_merge delete_branch allow_squash allow_merge allow_rebase
  auto_merge=$(parse_yaml_field "repository.auto_merge" "true")
  delete_branch=$(parse_yaml_field "repository.delete_branch_on_merge" "true")
  allow_squash=$(parse_yaml_field "repository.allow_squash_merge" "true")
  allow_merge=$(parse_yaml_field "repository.allow_merge_commit" "true")
  allow_rebase=$(parse_yaml_field "repository.allow_rebase_merge" "true")

  echo "  Configuring $repo..."

  # Apply settings via gh api
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
    echo "  [OK] Repository settings applied (auto_merge=$auto_merge, delete_branch=$delete_branch)"
  else
    echo "  [WARN] Could not apply repository settings (may require admin permissions)"
    echo "         Ask a repository admin to enable auto-merge in Settings > General"
  fi

  # Generate CODEOWNERS if configured
  configure_codeowners
}

configure_codeowners() {
  local codeowners_enabled
  codeowners_enabled=$(parse_yaml_field "repository.codeowners.enabled" "true")

  if [ "$codeowners_enabled" != "true" ]; then
    echo "  [SKIP] CODEOWNERS generation disabled"
    return 0
  fi

  local codeowners_path="$PROJECT_ROOT/CODEOWNERS"

  # If CODEOWNERS is missing or empty, generate from scratch
  if [ ! -s "$codeowners_path" ]; then
    local content
    content=$(generate_codeowners)
    if [ -z "$content" ]; then
      echo "  [SKIP] No CODEOWNERS content generated (check config)"
      return 0
    fi
    echo "$content" > "$codeowners_path"
    echo "  [OK] CODEOWNERS generated at $codeowners_path"
    return 0
  fi

  # CODEOWNERS exists — merge governance-required entries
  merge_codeowners "$codeowners_path"
}

# Merge governance-required CODEOWNERS entries into an existing file.
# Uses a managed-section marker so governance entries can be updated on
# subsequent runs without touching user-added rules.
merge_codeowners() {
  local codeowners_path="$1"
  local python_cmd
  if [ -d "$VENV_DIR" ]; then
    python_cmd="$VENV_DIR/bin/python"
  elif [ -n "$PYTHON_CMD" ] && [ "$PYTHON_OK" = "true" ]; then
    python_cmd="$PYTHON_CMD"
  else
    echo "  [SKIP] CODEOWNERS merge requires Python"
    return 0
  fi

  "$python_cmd" -c "
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
for f in ['$AI_DIR/config.yaml', '$AI_DIR/project.yaml', '$PROJECT_ROOT/project.yaml']:
    if os.path.exists(f):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
            config = deep_merge(config, data)

repo = config.get('repository', {})
co = repo.get('codeowners', {})
if not co.get('enabled', True):
    sys.exit(0)

# Build required entries from config
required_entries = {}
default_owner = co.get('default_owner', '')
if default_owner:
    required_entries['*'] = default_owner.split()

for rule in co.get('rules', []):
    pattern = rule.get('pattern', '')
    owners = rule.get('owners', [])
    if pattern and owners:
        required_entries[pattern] = owners

# Read existing CODEOWNERS
codeowners_path = '$codeowners_path'
with open(codeowners_path, 'r') as f:
    existing_lines = f.readlines()

# Parse existing rules (pattern -> set of owners)
existing_rules = {}
for line in existing_lines:
    stripped = line.strip()
    if not stripped or stripped.startswith('#'):
        continue
    parts = stripped.split()
    if len(parts) >= 2:
        pattern = parts[0]
        owners = parts[1:]
        existing_rules[pattern] = owners

# Determine what needs to be added or updated
changes_made = False
updated_lines = list(existing_lines)

for pattern, required_owners in required_entries.items():
    if pattern in existing_rules:
        # Pattern exists — check if all required owners are present
        current_owners = existing_rules[pattern]
        missing_owners = [o for o in required_owners if o not in current_owners]
        if missing_owners:
            # Find the line with this pattern and append missing owners
            new_owners = current_owners + missing_owners
            new_line = pattern + ' ' + ' '.join(new_owners) + '\n'
            for i, line in enumerate(updated_lines):
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    parts = stripped.split()
                    if parts and parts[0] == pattern:
                        updated_lines[i] = new_line
                        changes_made = True
                        break
    else:
        # Pattern does not exist — append it
        new_line = pattern + ' ' + ' '.join(required_owners) + '\n'
        # Ensure trailing newline before appending
        if updated_lines and not updated_lines[-1].endswith('\n'):
            updated_lines[-1] += '\n'
        updated_lines.append('\n')
        updated_lines.append('# Added by .ai/bin/init.sh — governance-required entry\n')
        updated_lines.append(new_line)
        changes_made = True

if changes_made:
    with open(codeowners_path, 'w') as f:
        f.writelines(updated_lines)
    print('  [OK] CODEOWNERS updated — governance entries merged')
else:
    print('  [OK] CODEOWNERS already has all governance-required entries')
" 2>/dev/null

  local exit_code=$?
  if [ $exit_code -ne 0 ]; then
    echo "  [WARN] CODEOWNERS merge failed (Python error). Existing file preserved."
  fi
}

validate_rulesets() {
  echo ""
  echo "Validating org/repo rulesets..."

  # Check if gh CLI is available and authenticated (already verified in configure_repository)
  if ! command -v gh &>/dev/null || ! gh auth status &>/dev/null 2>&1; then
    echo "  [SKIP] GitHub CLI not available or not authenticated"
    return 0
  fi

  local repo
  repo=$(gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>/dev/null) || {
    echo "  [SKIP] Could not detect GitHub repository"
    return 0
  }

  # Read expected rulesets from config
  local python_cmd
  if [ -d "$VENV_DIR" ]; then
    python_cmd="$VENV_DIR/bin/python"
  elif [ -n "$PYTHON_CMD" ] && [ "$PYTHON_OK" = "true" ]; then
    python_cmd="$PYTHON_CMD"
  else
    echo "  [SKIP] Python not available for config parsing"
    return 0
  fi

  local expected_names
  expected_names=$("$python_cmd" -c "
import yaml, os

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
for f in ['$AI_DIR/config.yaml', '$AI_DIR/project.yaml', '$PROJECT_ROOT/project.yaml']:
    if os.path.exists(f):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
            config = deep_merge(config, data)

rulesets = config.get('repository', {}).get('branch_protection', {}).get('expected_rulesets', [])
for rs in rulesets:
    name = rs.get('name', '')
    if name:
        print(name)
" 2>/dev/null)

  if [ -z "$expected_names" ]; then
    echo "  [SKIP] No expected rulesets configured"
    return 0
  fi

  # Fetch active rulesets from GitHub API (repo-level and org-level)
  local active_rulesets
  active_rulesets=$(gh api "repos/$repo/rulesets" --jq '.[].name' 2>/dev/null) || {
    echo "  [WARN] Could not fetch rulesets (may require admin permissions)"
    echo "         Verify rulesets manually in Settings > Rules > Rulesets"
    return 0
  }

  local missing=0
  while IFS= read -r expected; do
    if echo "$active_rulesets" | grep -qF "$expected"; then
      echo "  [OK] Ruleset found: $expected"
    else
      echo "  [WARN] Expected ruleset not found: $expected"
      missing=$((missing + 1))
    fi
  done <<< "$expected_names"

  if [ "$missing" -gt 0 ]; then
    echo "  [WARN] $missing expected ruleset(s) not found. Check org/repo settings."
    echo "         These are validated, not applied — configure them in GitHub Settings > Rules."
  else
    echo "  [OK] All expected rulesets present"
  fi
}

# Run repository configuration (only if Python is available for YAML parsing)
if [ "$PYTHON_OK" = "true" ]; then
  echo ""
  configure_repository
  validate_rulesets
else
  echo ""
  echo "  [SKIP] Repository configuration requires Python for YAML parsing"
fi

# --- Done ---

echo ""
echo "Done."
echo ""
echo "Next steps:"
if [ "$INSTALL_DEPS" = "false" ] && [ ! -d "$VENV_DIR" ]; then
  echo "  0. Install dependencies:     bash .ai/bin/init.sh --install-deps"
fi
echo "  1. Copy a language template:  cp .ai/governance/templates/python/project.yaml project.yaml"
echo "  2. Customize personas and conventions in project.yaml"
echo "  3. Set governance profile:    governance.policy_profile: default"
if [ -d "$VENV_DIR" ]; then
  echo ""
  echo "To activate the virtual environment:"
  echo "  source .ai/.venv/bin/activate"
fi
