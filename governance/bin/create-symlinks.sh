#!/bin/bash
# governance/bin/create-symlinks.sh — Copy CLAUDE.md, copilot-instructions.md, and slash commands from .ai/.
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

# Slash commands — source of truth is governance/commands/
# Sync to .claude/commands/ (Claude Code) and .github/copilot-chat/ (Copilot)
COMMANDS_SOURCE="$AI_DIR/governance/commands"
if [ ! -d "$COMMANDS_SOURCE" ]; then
  # Legacy fallback
  COMMANDS_SOURCE="$AI_DIR/.claude/commands"
fi

if [ -d "$COMMANDS_SOURCE" ]; then
  mkdir -p "$PROJECT_ROOT/.claude"
  sync_dir_with_diff "$COMMANDS_SOURCE" "$PROJECT_ROOT/.claude/commands"

  mkdir -p "$PROJECT_ROOT/.github/copilot-chat"
  sync_dir_with_diff "$COMMANDS_SOURCE" "$PROJECT_ROOT/.github/copilot-chat"
else
  log_debug "governance/commands/ not found; skipping commands sync"
fi
