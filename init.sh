#!/bin/bash
# .ai/init.sh — Run once after adding the .ai submodule to a project.
# Creates symlinks defined in config.yaml so all AI tools pick up shared config.
#
# Usage:
#   bash .ai/init.sh
#
# This script is idempotent — safe to run multiple times.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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
# Gate: only copy when .ai is a submodule (consuming repo context).
# When running inside ai-submodule itself, templates are already committed
# at .github/ISSUE_TEMPLATE/ and don't need copying.
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
else
  echo "  Skipping issue template copy (not a submodule context)"
fi

echo "Done. Symlinks created."
echo ""
echo "Next steps:"
echo "  1. Copy a language template:  cp .ai/templates/python/project.yaml .ai/project.yaml"
echo "  2. Customize personas and conventions in project.yaml"
echo "  3. Set governance profile:    governance.policy_profile: default"
