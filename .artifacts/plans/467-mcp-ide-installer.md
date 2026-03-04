# MCP Server Multi-IDE Auto-Installer

**Author:** Coder (agentic)
**Date:** 2026-02-27
**Status:** in_progress
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/467
**Branch:** NETWORK_ID/feat/467/mcp-ide-installer

---

## 1. Objective

Add a TypeScript-based multi-IDE auto-installer to the MCP server so that `dark-forge-mcp install` detects installed IDEs and writes MCP server configuration entries into each one. This replaces the need for users to run the existing shell scripts (`install.sh`, `install.ps1`) and adds broader IDE coverage.

## 2. Rationale

The existing shell-based install scripts support only Claude Code, VS Code, and Cursor. A TypeScript installer shipped inside the npm package enables cross-platform execution via `npx`, adds IDE auto-detection for 6 targets (VS Code, Cursor, Claude Desktop, Copilot CLI, Claude Code, JetBrains), and provides safety features like backup/rollback and dry-run mode.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Keep shell scripts only | Yes | Not cross-platform, limited IDE coverage, no safety features |
| Separate npm package for installer | Yes | Unnecessary indirection; installer is small enough to co-locate |
| Interactive TUI installer | Yes | Complexity not justified; CLI flags are sufficient |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `mcp-server/src/install.ts` | Multi-IDE auto-installer with detection, config generation, backup/rollback |
| `mcp-server/tests/install.test.ts` | Unit tests for installer logic |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `mcp-server/src/index.ts` | Add CLI routing: when first arg is `install`, delegate to installer |

### Files Unchanged

| File | Reason |
|------|--------|
| `mcp-server/install.sh` | Kept for backward compatibility |
| `mcp-server/install.ps1` | Kept for backward compatibility |
| `mcp-server/package.json` | No new dependencies required (uses Node.js built-ins) |

## 4. Design

### IDE Detection Matrix

| IDE | Detection Method | Config Path | Config Format |
|-----|-----------------|-------------|---------------|
| VS Code | `~/.vscode/` exists or `code --version` | `.vscode/mcp.json` or user settings | `{ "servers": { ... } }` |
| Cursor | `~/.cursor/` exists or `cursor --version` | `~/.cursor/mcp.json` | `{ "mcpServers": { ... } }` |
| Claude Desktop | Platform-specific app support dir | `claude_desktop_config.json` | `{ "mcpServers": { ... } }` |
| Copilot CLI | `gh copilot --version` | Print manual instructions | N/A |
| Claude Code | `claude --version` | `.claude/settings.json` or suggest `claude mcp add` | N/A |
| JetBrains | `~/Library/Application Support/JetBrains/` | Print manual instructions | N/A |

### CLI Options

- `--dry-run` -- Show what would be done without modifying files
- `--ide <name>` -- Install for a specific IDE only (vscode, cursor, claude-desktop, claude-code, copilot, jetbrains)
- `--skip-verify` -- Skip post-install verification
- `--local` -- Use local path instead of npx
- `--help` -- Show help text

### Safety Features

- Timestamped backup before any config modification
- JSON validation before and after write
- Rollback on write failure
- Idempotent: safe to run multiple times

## 5. Testing Strategy

Unit tests mock the filesystem and command execution to verify:
- IDE detection logic
- Config generation per IDE format
- Backup creation
- Dry-run mode produces no side effects
- Idempotent re-runs

## 6. Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Config file corruption | Timestamped backup + JSON validation + rollback |
| IDE not detected when installed | Multiple detection methods per IDE (dir + command) |
| Breaking existing configs | Merge strategy preserves existing entries |
