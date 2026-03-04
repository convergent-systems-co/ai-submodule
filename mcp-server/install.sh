#!/usr/bin/env bash
# install.sh — Configure IDE MCP server entries for dark-forge-mcp
# Supports: Claude Code, VS Code, Cursor
# Usage: bash install.sh [--governance-root /path/to/root]

set -euo pipefail

GOVERNANCE_ROOT=""
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --governance-root)
      GOVERNANCE_ROOT="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: bash install.sh [--governance-root /path/to/root]"
      echo ""
      echo "Configures MCP server entries for Claude Code, VS Code, and Cursor."
      echo ""
      echo "Options:"
      echo "  --governance-root  Path to the governance root directory"
      echo "  -h, --help         Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Determine the node command path
NODE_CMD="$(which node 2>/dev/null || echo "node")"
SERVER_SCRIPT="${SCRIPT_DIR}/dist/index.js"

if [[ ! -f "$SERVER_SCRIPT" ]]; then
  echo "Error: dist/index.js not found. Run 'npm run build' first."
  exit 1
fi

# Build the MCP server args as a JSON array
# Prefer jq for JSON construction; fall back to node if jq is unavailable
build_args_json() {
  local args=("$@")
  if command -v jq &>/dev/null; then
    printf '%s\n' "${args[@]}" | jq -R . | jq -s .
  else
    "$NODE_CMD" -e "console.log(JSON.stringify(process.argv.slice(1)))" -- "${args[@]}"
  fi
}

MCP_ARGS=("${SERVER_SCRIPT}")
if [[ -n "$GOVERNANCE_ROOT" ]]; then
  MCP_ARGS+=("--governance-root" "$GOVERNANCE_ROOT")
fi

ARGS_JSON="$(build_args_json "${MCP_ARGS[@]}")"

echo "=== dark-forge-mcp installer ==="
echo "Server: ${SERVER_SCRIPT}"
echo ""

# --- Helper: merge MCP config into a JSON file ---
merge_mcp_config() {
  local config_file="$1"
  local servers_key="$2"

  "$NODE_CMD" -e "
    const fs = require('fs');
    const config = JSON.parse(fs.readFileSync(process.argv[1], 'utf-8'));
    const key = process.argv[2];
    if (!config[key]) config[key] = {};
    config[key]['dark-forge-mcp'] = {
      command: process.argv[3],
      args: JSON.parse(process.argv[4])
    };
    fs.writeFileSync(process.argv[1], JSON.stringify(config, null, 2) + '\n');
  " "$config_file" "$servers_key" "$NODE_CMD" "$ARGS_JSON"
}

# --- Claude Code ---
configure_claude_code() {
  local config_file="${HOME}/.claude.json"

  if [[ ! -f "$config_file" ]]; then
    echo '{}' > "$config_file"
  fi

  merge_mcp_config "$config_file" "mcpServers"
  echo "[OK] Claude Code: ${config_file}"
}

# --- VS Code ---
configure_vscode() {
  local settings_dir
  case "$(uname -s)" in
    Darwin) settings_dir="${HOME}/Library/Application Support/Code/User" ;;
    Linux)  settings_dir="${HOME}/.config/Code/User" ;;
    *)      echo "[SKIP] VS Code: unsupported platform"; return ;;
  esac

  local settings_file="${settings_dir}/settings.json"

  if [[ ! -d "$settings_dir" ]]; then
    echo "[SKIP] VS Code: settings directory not found at ${settings_dir}"
    return
  fi

  if [[ ! -f "$settings_file" ]]; then
    echo '{}' > "$settings_file"
  fi

  merge_mcp_config "$settings_file" "mcp.servers"
  echo "[OK] VS Code: ${settings_file}"
}

# --- Cursor ---
configure_cursor() {
  local config_file="${HOME}/.cursor/mcp.json"
  local config_dir="${HOME}/.cursor"

  if [[ ! -d "$config_dir" ]]; then
    echo "[SKIP] Cursor: ~/.cursor directory not found"
    return
  fi

  if [[ ! -f "$config_file" ]]; then
    echo '{}' > "$config_file"
  fi

  merge_mcp_config "$config_file" "mcpServers"
  echo "[OK] Cursor: ${config_file}"
}

configure_claude_code
configure_vscode
configure_cursor

echo ""
echo "Done. Restart your IDE to pick up the new MCP server configuration."
