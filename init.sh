#!/bin/bash
# .ai/init.sh — Run once after adding the .ai submodule to a project.
# Creates symlinks, detects platform, and optionally installs all dependencies.
#
# Usage:
#   bash .ai/init.sh                 # Symlinks only (existing behavior)
#   bash .ai/init.sh --install-deps  # Symlinks + Python venv + dependencies
#
# This script is idempotent — safe to run multiple times.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS="$SCRIPT_DIR/requirements.txt"
INSTALL_DEPS=false
PYTHON_MIN_MAJOR=3
PYTHON_MIN_MINOR=12

# --- Parse arguments ---

for arg in "$@"; do
  case "$arg" in
    --install-deps) INSTALL_DEPS=true ;;
    --help|-h)
      echo "Usage: bash .ai/init.sh [--install-deps]"
      echo ""
      echo "Options:"
      echo "  --install-deps  Install Python virtual environment and dependencies"
      echo "  --help, -h      Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: bash .ai/init.sh [--install-deps]"
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

# --- Submodule freshness check ---

# If running in a consuming repo (submodule context), check if .ai is up to date
if [ -f "$PROJECT_ROOT/.gitmodules" ] && grep -q '\.ai' "$PROJECT_ROOT/.gitmodules" 2>/dev/null; then
  echo "Checking .ai submodule freshness..."
  # Check for dirty state before attempting update
  if ! git -C "$SCRIPT_DIR" diff-index --quiet HEAD -- 2>/dev/null; then
    echo "  [WARN] .ai submodule has uncommitted changes; skipping automatic update"
    echo "         Commit, stash, or discard local changes in .ai, then re-run init.sh"
  elif git -C "$SCRIPT_DIR" fetch origin main --quiet 2>/dev/null; then
    LOCAL_SHA=$(git -C "$SCRIPT_DIR" rev-parse HEAD 2>/dev/null)
    REMOTE_SHA=$(git -C "$SCRIPT_DIR" rev-parse origin/main 2>/dev/null)
    if [ -n "$LOCAL_SHA" ] && [ -n "$REMOTE_SHA" ]; then
      if [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
        echo "  [OK] .ai submodule is up to date (${LOCAL_SHA:0:8})"
      else
        echo "  [UPDATE] .ai submodule is behind (local: ${LOCAL_SHA:0:8}, remote: ${REMOTE_SHA:0:8})"
        if git -C "$PROJECT_ROOT" submodule update --remote .ai 2>/dev/null; then
          NEW_SHA=$(git -C "$SCRIPT_DIR" rev-parse HEAD 2>/dev/null)
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
  TEMPLATE_SRC="$SCRIPT_DIR/.github/ISSUE_TEMPLATE"
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
  WORKFLOW_SRC="$SCRIPT_DIR/.github/workflows"
  WORKFLOW_DST="$PROJECT_ROOT/.github/workflows"
  if [ -d "$WORKFLOW_SRC" ]; then
    mkdir -p "$WORKFLOW_DST"
    # Read workflow list from config.yaml if Python is available, otherwise use default
    WORKFLOWS_TO_LINK="dark-factory-governance.yml"
    if [ -n "$PYTHON_CMD" ]; then
      CONFIG_WORKFLOWS=$("$PYTHON_CMD" -c "
import yaml, os
config = {}
for f in ['$SCRIPT_DIR/config.yaml', '$SCRIPT_DIR/project.yaml']:
    if os.path.exists(f):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
            config.update(data)
wf = config.get('workflows_to_copy', ['dark-factory-governance.yml'])
print(' '.join(wf))
" 2>/dev/null) && WORKFLOWS_TO_LINK="$CONFIG_WORKFLOWS"
    fi
    for wf_name in $WORKFLOWS_TO_LINK; do
      if [ -f "$WORKFLOW_SRC/$wf_name" ]; then
        local link_target="../../.ai/.github/workflows/$wf_name"
        if [ -L "$WORKFLOW_DST/$wf_name" ] && [ "$(readlink "$WORKFLOW_DST/$wf_name")" = "$link_target" ]; then
          echo "  Workflow $wf_name already linked"
        elif [ -f "$WORKFLOW_DST/$wf_name" ] && [ ! -L "$WORKFLOW_DST/$wf_name" ]; then
          echo "  Workflow $wf_name exists as regular file, skipping (remove to use symlink)"
        else
          ln -sf "$link_target" "$WORKFLOW_DST/$wf_name"
          echo "  Linked $wf_name -> .ai/.github/workflows/$wf_name"
        fi
      else
        echo "  [WARN] Workflow $wf_name not found in .ai/.github/workflows/"
      fi
    done
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
for f in ['$SCRIPT_DIR/config.yaml', '$SCRIPT_DIR/project.yaml']:
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

echo ""

# --- Dependency installation ---

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
    echo "          Either create .ai/requirements.txt or rerun without --install-deps."
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
  local config_file="${3:-$SCRIPT_DIR/config.yaml}"
  local project_file="$SCRIPT_DIR/project.yaml"

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
for f in ['$config_file', '$project_file']:
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
for f in ['$SCRIPT_DIR/config.yaml', '$SCRIPT_DIR/project.yaml']:
    if os.path.exists(f):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
            config = deep_merge(config, data)

repo = config.get('repository', {})
co = repo.get('codeowners', {})
if not co.get('enabled', True):
    exit(0)

print('# CODEOWNERS — generated by .ai/init.sh from config.yaml')
print('# Manual edits will be overwritten on next init run.')
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

  # Only generate if file is missing or empty
  if [ -s "$codeowners_path" ]; then
    echo "  [OK] CODEOWNERS already populated"
    return 0
  fi

  local content
  content=$(generate_codeowners)
  if [ -z "$content" ]; then
    echo "  [SKIP] No CODEOWNERS content generated (check config)"
    return 0
  fi

  echo "$content" > "$codeowners_path"
  echo "  [OK] CODEOWNERS generated at $codeowners_path"
}

# Run repository configuration (only if Python is available for YAML parsing)
if [ "$PYTHON_OK" = "true" ]; then
  echo ""
  configure_repository
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
  echo "  0. Install dependencies:     bash .ai/init.sh --install-deps"
fi
echo "  1. Copy a language template:  cp .ai/templates/python/project.yaml .ai/project.yaml"
echo "  2. Customize personas and conventions in project.yaml"
echo "  3. Set governance profile:    governance.policy_profile: default"
if [ -d "$VENV_DIR" ]; then
  echo ""
  echo "To activate the virtual environment:"
  echo "  source .ai/.venv/bin/activate"
fi
