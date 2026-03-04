#!/bin/bash
# governance/bin/setup-directories.sh — Create .artifacts/ project directories with migration support.
# Only runs in submodule context.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
resolve_ai_dir

PYTHON_CMD="${PYTHON_CMD:-}"
IS_SUBMODULE=false
if [ -f "$PROJECT_ROOT/.gitmodules" ] && grep -q '\.ai' "$PROJECT_ROOT/.gitmodules" 2>/dev/null; then
  IS_SUBMODULE=true
fi

if [ "$IS_SUBMODULE" != "true" ]; then
  echo "  Skipping directory setup (not a submodule context)"
  return 0 2>/dev/null || exit 0
fi

echo ""
echo "Creating project directories..."

# Migration: move old scattered dirs to .artifacts/
migrate_old_dir() {
  local old_path="$1" new_path="$2"
  if [ -d "$PROJECT_ROOT/$old_path" ] && [ ! -d "$PROJECT_ROOT/$new_path" ]; then
    run_cmd "Migrate $old_path to $new_path" mkdir -p "$PROJECT_ROOT/$new_path"
    if [ -n "$(ls -A "$PROJECT_ROOT/$old_path" 2>/dev/null)" ]; then
      run_cmd "Copy contents" cp -r "$PROJECT_ROOT/$old_path"/* "$PROJECT_ROOT/$new_path/" 2>/dev/null || true
    fi
    echo "  [MIGRATE] Moved $old_path/ -> $new_path/"
    echo "            Old directory preserved. Remove manually after verifying: rm -rf $old_path"
  fi
}

migrate_old_dir "governance/plans" ".artifacts/plans"
migrate_old_dir "governance/checkpoints" ".artifacts/checkpoints"
migrate_old_dir ".panels" ".artifacts/panels"
migrate_old_dir ".governance-state" ".artifacts/state .artifacts/emissions .artifacts/logs"

# Read directory list from config if Python is available
PROJECT_DIRS=".artifacts/plans .artifacts/panels .artifacts/checkpoints .artifacts/state .artifacts/emissions .artifacts/logs"
if [ -n "$PYTHON_CMD" ]; then
  CONFIG_DIRS=$("$PYTHON_CMD" -c "
import yaml, os, sys
config = {}
for f in sys.argv[1:]:
    if os.path.exists(f):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
            if 'project_directories' in data:
                existing = config.get('project_directories', [])
                config['project_directories'] = existing + data['project_directories']
            for k, v in data.items():
                if k != 'project_directories':
                    config[k] = v
dirs = config.get('project_directories', [{'path': '.artifacts/plans'}, {'path': '.artifacts/panels'}, {'path': '.artifacts/checkpoints'}, {'path': '.artifacts/state'}])
print(' '.join(d.get('path', '') for d in dirs if d.get('path')))
" "$AI_DIR/config.yaml" "$AI_DIR/project.yaml" "$PROJECT_ROOT/project.yaml" 2>/dev/null) && PROJECT_DIRS="$CONFIG_DIRS"
fi

for dir_name in $PROJECT_DIRS; do
  dir_path="$PROJECT_ROOT/$dir_name"
  if [ -d "$dir_path" ]; then
    echo "  $dir_name/ already exists"
  else
    run_cmd "Create $dir_name" mkdir -p "$dir_path"
    touch "$dir_path/.gitkeep"
    echo "  Created $dir_name/ with .gitkeep"
  fi
  # Ensure .gitkeep exists even if directory was created manually
  if [ ! -f "$dir_path/.gitkeep" ] && [ -z "$(ls -A "$dir_path" 2>/dev/null)" ]; then
    touch "$dir_path/.gitkeep"
  fi
done
