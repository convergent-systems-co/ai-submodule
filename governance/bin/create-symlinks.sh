#!/bin/bash
# governance/bin/create-symlinks.sh — Copy CLAUDE.md, copilot-instructions.md, and .claude/commands from .ai/.
# Replaces legacy symlinks with copies and uses diff-based staleness detection.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
resolve_ai_dir

echo "Initializing .ai submodule files..."

# instructions.md -> CLAUDE.md (copy with diff detection)
copy_with_diff "$AI_DIR/instructions.md" "$PROJECT_ROOT/CLAUDE.md"

# GitHub Copilot instructions (copy with diff detection)
mkdir -p "$PROJECT_ROOT/.github"
copy_with_diff "$AI_DIR/instructions.md" "$PROJECT_ROOT/.github/copilot-instructions.md"

# Claude Code slash commands (.claude/commands/) — sync directory
if [ -d "$AI_DIR/.claude/commands" ]; then
  mkdir -p "$PROJECT_ROOT/.claude"
  sync_dir_with_diff "$AI_DIR/.claude/commands" "$PROJECT_ROOT/.claude/commands"
else
  log_debug ".ai/.claude/commands/ not found; skipping commands sync"
fi
