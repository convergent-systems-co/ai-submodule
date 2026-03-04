#!/bin/bash
# .ai/bin/quick-install.sh — DEPRECATED: use init.sh --quick instead.
#
# This script is preserved for backward compatibility. It delegates to init.sh --quick.
#
# New usage:
#   bash .ai/bin/init.sh --quick                      # Add submodule + init
#   bash .ai/bin/init.sh --quick --install-deps       # Add submodule + init + Python deps
#   bash .ai/bin/init.sh --quick --mcp                # Add submodule + init + MCP server

set -euo pipefail

echo "[DEPRECATED] quick-install.sh is deprecated. Use 'bash .ai/bin/init.sh --quick' instead."
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Forward all arguments plus --quick to init.sh
exec bash "$SCRIPT_DIR/init.sh" --quick "$@"
