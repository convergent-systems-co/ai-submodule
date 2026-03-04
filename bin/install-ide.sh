#!/usr/bin/env bash
# install-ide.sh — Unified IDE auto-detection and MCP server configuration
# Detects installed IDEs and configures the governance MCP server for each.
#
# Supported IDEs: VS Code, Cursor, Claude Desktop, Claude Code, JetBrains
#
# Usage:
#   bash .ai/bin/install-ide.sh                    # Auto-detect and configure all IDEs
#   bash .ai/bin/install-ide.sh --check            # Show detected IDEs without configuring
#   bash .ai/bin/install-ide.sh --fix              # Detect and fix stale configurations
#   bash .ai/bin/install-ide.sh --ide vscode       # Configure only VS Code
#   bash .ai/bin/install-ide.sh --governance-root . # Specify governance root path

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$AI_DIR")"
MCP_SERVER_DIR="$AI_DIR/mcp-server"
SERVER_SCRIPT="$MCP_SERVER_DIR/dist/index.js"

CHECK_ONLY=false
FIX_MODE=false
SPECIFIC_IDE=""
GOVERNANCE_ROOT=""

# Colors (disabled if not a terminal)
if [ -t 1 ]; then
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  RED='\033[0;31m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  GREEN='' YELLOW='' RED='' BOLD='' NC=''
fi

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) CHECK_ONLY=true; shift ;;
    --fix) FIX_MODE=true; shift ;;
    --ide) SPECIFIC_IDE="$2"; shift 2 ;;
    --governance-root) GOVERNANCE_ROOT="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash .ai/bin/install-ide.sh [OPTIONS]"
      echo ""
      echo "Auto-detect installed IDEs and configure the governance MCP server."
      echo ""
      echo "Options:"
      echo "  --check              Show detected IDEs without configuring"
      echo "  --fix                Detect and fix stale configurations"
      echo "  --ide <name>         Configure only the specified IDE"
      echo "                       (vscode, cursor, claude-desktop, claude-code, jetbrains)"
      echo "  --governance-root    Path to governance root directory"
      echo "  -h, --help           Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Run with --help for usage."
      exit 1
      ;;
  esac
done

if [ -z "$GOVERNANCE_ROOT" ]; then
  GOVERNANCE_ROOT="$PROJECT_ROOT"
fi

# --- IDE Detection Functions ---

OS="$(uname -s)"

detect_vscode() {
  local settings_dir=""
  case "$OS" in
    Darwin) settings_dir="$HOME/Library/Application Support/Code/User" ;;
    Linux)  settings_dir="$HOME/.config/Code/User" ;;
    MINGW*|MSYS*|CYGWIN*) settings_dir="$APPDATA/Code/User" ;;
  esac
  [ -n "$settings_dir" ] && [ -d "$settings_dir" ] && echo "$settings_dir"
}

detect_cursor() {
  local config_dir="$HOME/.cursor"
  [ -d "$config_dir" ] && echo "$config_dir"
}

detect_claude_desktop() {
  local config_dir=""
  case "$OS" in
    Darwin) config_dir="$HOME/Library/Application Support/Claude" ;;
    Linux)  config_dir="$HOME/.config/Claude" ;;
    MINGW*|MSYS*|CYGWIN*) config_dir="$APPDATA/Claude" ;;
  esac
  [ -n "$config_dir" ] && [ -d "$config_dir" ] && echo "$config_dir"
}

detect_claude_code() {
  local config_file="$HOME/.claude.json"
  # Claude Code is present if the config file exists or the CLI is installed
  if [ -f "$config_file" ] || command -v claude &>/dev/null; then
    echo "$HOME"
  fi
}

detect_jetbrains() {
  # Detect any JetBrains IDE by checking for their config directories
  local found=""
  local jetbrains_dirs=()

  case "$OS" in
    Darwin)
      # macOS: ~/Library/Application Support/JetBrains/<IDE><version>
      if [ -d "$HOME/Library/Application Support/JetBrains" ]; then
        while IFS= read -r dir; do
          jetbrains_dirs+=("$dir")
        done < <(find "$HOME/Library/Application Support/JetBrains" -maxdepth 1 -type d -name "IntelliJ*" -o -name "WebStorm*" -o -name "PyCharm*" -o -name "GoLand*" -o -name "Rider*" -o -name "RubyMine*" -o -name "PhpStorm*" -o -name "CLion*" 2>/dev/null)
      fi
      ;;
    Linux)
      # Linux: ~/.config/JetBrains/<IDE><version>
      if [ -d "$HOME/.config/JetBrains" ]; then
        while IFS= read -r dir; do
          jetbrains_dirs+=("$dir")
        done < <(find "$HOME/.config/JetBrains" -maxdepth 1 -type d -name "IntelliJ*" -o -name "WebStorm*" -o -name "PyCharm*" -o -name "GoLand*" -o -name "Rider*" -o -name "RubyMine*" -o -name "PhpStorm*" -o -name "CLion*" 2>/dev/null)
      fi
      ;;
  esac

  if [ ${#jetbrains_dirs[@]} -gt 0 ]; then
    # Return the most recent (highest version) JetBrains config dir
    printf '%s\n' "${jetbrains_dirs[@]}" | sort -V | tail -1
  fi
}

# --- MCP Server Build Check ---

ensure_mcp_built() {
  if [ -f "$SERVER_SCRIPT" ]; then
    return 0
  fi

  echo -e "  ${YELLOW}MCP server not built. Building...${NC}"
  if ! command -v npm &>/dev/null; then
    echo -e "  ${RED}npm not found. Install Node.js to use IDE integration.${NC}"
    return 1
  fi

  if (cd "$MCP_SERVER_DIR" && npm install --silent 2>/dev/null && npm run build --silent 2>/dev/null); then
    echo -e "  ${GREEN}MCP server built successfully.${NC}"
    return 0
  else
    echo -e "  ${RED}Failed to build MCP server. Run manually:${NC}"
    echo "    cd .ai/mcp-server && npm install && npm run build"
    return 1
  fi
}

# --- Configuration Functions ---

# Build JSON args for MCP server
build_mcp_args() {
  local args=("$SERVER_SCRIPT")
  if [ -n "$GOVERNANCE_ROOT" ]; then
    args+=("--governance-root" "$GOVERNANCE_ROOT")
  fi

  # Use node for reliable JSON construction
  local node_cmd
  node_cmd="$(command -v node 2>/dev/null || echo "")"
  if [ -n "$node_cmd" ]; then
    "$node_cmd" -e "console.log(JSON.stringify(process.argv.slice(1)))" -- "${args[@]}"
  elif command -v jq &>/dev/null; then
    printf '%s\n' "${args[@]}" | jq -R . | jq -s .
  else
    # Fallback: manual JSON array
    local json="["
    local first=true
    for arg in "${args[@]}"; do
      [ "$first" = "true" ] && first=false || json+=","
      json+="\"$arg\""
    done
    json+="]"
    echo "$json"
  fi
}

configure_ide_json() {
  local config_file="$1"
  local servers_key="$2"
  local args_json="$3"

  local node_cmd
  node_cmd="$(command -v node 2>/dev/null || echo "")"

  if [ -z "$node_cmd" ]; then
    echo -e "  ${RED}Node.js required for JSON configuration. Skipping.${NC}"
    return 1
  fi

  if [ ! -f "$config_file" ]; then
    echo '{}' > "$config_file"
  fi

  "$node_cmd" -e "
    const fs = require('fs');
    const config = JSON.parse(fs.readFileSync(process.argv[1], 'utf-8'));
    const key = process.argv[2];
    if (!config[key]) config[key] = {};
    config[key]['dark-forge-mcp'] = {
      command: process.argv[3],
      args: JSON.parse(process.argv[4])
    };
    fs.writeFileSync(process.argv[1], JSON.stringify(config, null, 2) + '\n');
  " "$config_file" "$servers_key" "$(command -v node)" "$args_json"
}

# --- Stale Config Detection ---

check_stale_config() {
  local config_file="$1"
  local servers_key="$2"

  if [ ! -f "$config_file" ]; then
    return 1  # No config to check
  fi

  local node_cmd
  node_cmd="$(command -v node 2>/dev/null || echo "")"
  if [ -z "$node_cmd" ]; then
    return 1
  fi

  local result
  result=$("$node_cmd" -e "
    const fs = require('fs');
    try {
      const config = JSON.parse(fs.readFileSync(process.argv[1], 'utf-8'));
      const key = process.argv[2];
      const entry = (config[key] || {})['dark-forge-mcp'];
      if (!entry) { console.log('missing'); process.exit(0); }
      const args = entry.args || [];
      const serverPath = args[0] || '';
      if (!fs.existsSync(serverPath)) { console.log('stale'); process.exit(0); }
      console.log('ok');
    } catch { console.log('error'); }
  " "$config_file" "$servers_key" 2>/dev/null || echo "error")

  echo "$result"
}

# --- Main Logic ---

echo ""
echo -e "${BOLD}IDE Configuration — Dark Forge${NC}"
echo ""

# Detect all IDEs
declare -A DETECTED_IDES

VSCODE_DIR=$(detect_vscode || true)
CURSOR_DIR=$(detect_cursor || true)
CLAUDE_DESKTOP_DIR=$(detect_claude_desktop || true)
CLAUDE_CODE_DIR=$(detect_claude_code || true)
JETBRAINS_DIR=$(detect_jetbrains || true)

[ -n "$VSCODE_DIR" ] && DETECTED_IDES[vscode]="$VSCODE_DIR"
[ -n "$CURSOR_DIR" ] && DETECTED_IDES[cursor]="$CURSOR_DIR"
[ -n "$CLAUDE_DESKTOP_DIR" ] && DETECTED_IDES[claude-desktop]="$CLAUDE_DESKTOP_DIR"
[ -n "$CLAUDE_CODE_DIR" ] && DETECTED_IDES[claude-code]="$CLAUDE_CODE_DIR"
[ -n "$JETBRAINS_DIR" ] && DETECTED_IDES[jetbrains]="$JETBRAINS_DIR"

IDE_COUNT=${#DETECTED_IDES[@]}

echo "Detected IDEs: $IDE_COUNT"
for ide in "${!DETECTED_IDES[@]}"; do
  echo -e "  ${GREEN}[found]${NC} $ide — ${DETECTED_IDES[$ide]}"
done

if [ "$IDE_COUNT" -eq 0 ]; then
  echo ""
  echo "No supported IDEs detected. Supported IDEs:"
  echo "  - VS Code        (https://code.visualstudio.com)"
  echo "  - Cursor          (https://cursor.sh)"
  echo "  - Claude Desktop  (https://claude.ai/desktop)"
  echo "  - Claude Code     (https://claude.ai/code)"
  echo "  - JetBrains IDEs  (https://www.jetbrains.com)"
  exit 0
fi

# Check-only mode
if [ "$CHECK_ONLY" = "true" ]; then
  echo ""
  echo "Run without --check to configure these IDEs."
  exit 0
fi

echo ""

# Ensure MCP server is built
if ! ensure_mcp_built; then
  echo ""
  echo -e "${RED}Cannot configure IDEs without a built MCP server.${NC}"
  exit 1
fi

# Build args JSON
ARGS_JSON=$(build_mcp_args)
NODE_CMD="$(command -v node 2>/dev/null || echo "node")"

CONFIGURED=0
SKIPPED=0

# Configure each detected IDE
for ide in "${!DETECTED_IDES[@]}"; do
  # Skip if --ide was specified and this isn't the one
  if [ -n "$SPECIFIC_IDE" ] && [ "$ide" != "$SPECIFIC_IDE" ]; then
    continue
  fi

  case "$ide" in
    vscode)
      local_config="${DETECTED_IDES[$ide]}/settings.json"
      if [ "$FIX_MODE" = "true" ]; then
        status=$(check_stale_config "$local_config" "mcp.servers")
        if [ "$status" = "ok" ]; then
          echo -e "  ${GREEN}[ok]${NC} VS Code — config is current"
          continue
        fi
        echo -e "  ${YELLOW}[fix]${NC} VS Code — updating stale config"
      fi
      if configure_ide_json "$local_config" "mcp.servers" "$ARGS_JSON"; then
        echo -e "  ${GREEN}[ok]${NC} VS Code — $local_config"
        CONFIGURED=$((CONFIGURED + 1))
      fi
      ;;
    cursor)
      local_config="${DETECTED_IDES[$ide]}/mcp.json"
      if [ "$FIX_MODE" = "true" ]; then
        status=$(check_stale_config "$local_config" "mcpServers")
        if [ "$status" = "ok" ]; then
          echo -e "  ${GREEN}[ok]${NC} Cursor — config is current"
          continue
        fi
        echo -e "  ${YELLOW}[fix]${NC} Cursor — updating stale config"
      fi
      if configure_ide_json "$local_config" "mcpServers" "$ARGS_JSON"; then
        echo -e "  ${GREEN}[ok]${NC} Cursor — $local_config"
        CONFIGURED=$((CONFIGURED + 1))
      fi
      ;;
    claude-desktop)
      local_config="${DETECTED_IDES[$ide]}/claude_desktop_config.json"
      if [ "$FIX_MODE" = "true" ]; then
        status=$(check_stale_config "$local_config" "mcpServers")
        if [ "$status" = "ok" ]; then
          echo -e "  ${GREEN}[ok]${NC} Claude Desktop — config is current"
          continue
        fi
        echo -e "  ${YELLOW}[fix]${NC} Claude Desktop — updating stale config"
      fi
      if configure_ide_json "$local_config" "mcpServers" "$ARGS_JSON"; then
        echo -e "  ${GREEN}[ok]${NC} Claude Desktop — $local_config"
        CONFIGURED=$((CONFIGURED + 1))
      fi
      ;;
    claude-code)
      local_config="$HOME/.claude.json"
      if [ "$FIX_MODE" = "true" ]; then
        status=$(check_stale_config "$local_config" "mcpServers")
        if [ "$status" = "ok" ]; then
          echo -e "  ${GREEN}[ok]${NC} Claude Code — config is current"
          continue
        fi
        echo -e "  ${YELLOW}[fix]${NC} Claude Code — updating stale config"
      fi
      if configure_ide_json "$local_config" "mcpServers" "$ARGS_JSON"; then
        echo -e "  ${GREEN}[ok]${NC} Claude Code — $local_config"
        CONFIGURED=$((CONFIGURED + 1))
      fi
      ;;
    jetbrains)
      # JetBrains MCP configuration is IDE-version specific
      local jb_dir="${DETECTED_IDES[$ide]}"
      local jb_name
      jb_name=$(basename "$jb_dir")
      local_config="$jb_dir/options/mcp.json"
      mkdir -p "$jb_dir/options" 2>/dev/null || true
      if [ "$FIX_MODE" = "true" ]; then
        status=$(check_stale_config "$local_config" "mcpServers")
        if [ "$status" = "ok" ]; then
          echo -e "  ${GREEN}[ok]${NC} JetBrains ($jb_name) — config is current"
          continue
        fi
        echo -e "  ${YELLOW}[fix]${NC} JetBrains ($jb_name) — updating stale config"
      fi
      if configure_ide_json "$local_config" "mcpServers" "$ARGS_JSON"; then
        echo -e "  ${GREEN}[ok]${NC} JetBrains ($jb_name) — $local_config"
        CONFIGURED=$((CONFIGURED + 1))
      fi
      ;;
  esac
done

echo ""
echo -e "${BOLD}Summary:${NC} $CONFIGURED IDE(s) configured."
if [ "$CONFIGURED" -gt 0 ]; then
  echo ""
  echo "Restart your IDE(s) to activate the governance MCP server."
fi
echo ""
