#!/usr/bin/env bash
# governance-status.sh — Human-readable governance status dashboard
# Usage: bash .ai/bin/governance-status.sh [--verbose]
#
# Default: compact summary (< 10 lines)
# --verbose: full dashboard with all sections

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$AI_DIR")"

# --- Parse arguments ---
VERBOSE=false
for arg in "$@"; do
  case "$arg" in
    --verbose) VERBOSE=true ;;
    --help|-h)
      echo "Usage: bash .ai/bin/governance-status.sh [--verbose]"
      echo ""
      echo "  (no flags)   Compact summary"
      echo "  --verbose    Full dashboard with all sections"
      exit 0
      ;;
  esac
done

# Colors (disabled if not a terminal)
if [ -t 1 ]; then
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  RED='\033[0;31m'
  BLUE='\033[0;34m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  GREEN='' YELLOW='' RED='' BLUE='' BOLD='' NC=''
fi

# --- Check installation ---
install_ok=true
[ -d "$AI_DIR/governance" ] || install_ok=false
{ [ -L "$PROJECT_ROOT/CLAUDE.md" ] || [ -f "$PROJECT_ROOT/CLAUDE.md" ]; } || install_ok=false
[ -d "$PROJECT_ROOT/.governance" ] || install_ok=false
{ command -v python3 &>/dev/null || command -v python &>/dev/null; } || install_ok=false

# --- Extract policy profile ---
PROFILE="unknown"
PROJECT_YAML=""
if [ -f "$PROJECT_ROOT/project.yaml" ]; then
  PROJECT_YAML="$PROJECT_ROOT/project.yaml"
elif [ -f "$AI_DIR/project.yaml" ]; then
  PROJECT_YAML="$AI_DIR/project.yaml"
fi

if [ -n "$PROJECT_YAML" ]; then
  PYTHON_CMD=""
  if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
  elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
  fi
  if [ -n "$PYTHON_CMD" ]; then
    PROFILE=$($PYTHON_CMD -c "
import yaml, sys
try:
    with open('$PROJECT_YAML') as f:
        data = yaml.safe_load(f)
    print(data.get('governance', {}).get('policy_profile', 'default'))
except:
    print('unknown')
" 2>/dev/null || echo "unknown")
  fi
fi

# --- Count emissions ---
EMISSION_COUNT=0
EMISSIONS_DIR="$PROJECT_ROOT/.governance/panels"
if [ -d "$EMISSIONS_DIR" ]; then
  EMISSION_COUNT=$(find "$EMISSIONS_DIR" -name "*.json" -type f 2>/dev/null | wc -l | tr -d ' ')
fi

# ============================================================
# COMPACT MODE (default)
# ============================================================
if [ "$VERBOSE" = "false" ]; then
  echo ""
  echo -e "${BOLD}Dark Forge — Status${NC}"

  if [ "$install_ok" = true ]; then
    echo -e "  Installation:    ${GREEN}OK${NC}"
  else
    echo -e "  Installation:    ${YELLOW}incomplete${NC}"
  fi
  echo -e "  Policy profile:  $PROFILE"

  if [ "$EMISSION_COUNT" -gt 0 ]; then
    echo "  Panel emissions: $EMISSION_COUNT total"
  else
    echo "  Panel emissions: none yet"
  fi
  echo ""

  if [ "$install_ok" = true ]; then
    echo -e "${GREEN}Governance is active.${NC} Open a PR to see it in action."
  else
    echo -e "${YELLOW}Governance is partially configured.${NC} Run: bash .ai/bin/init.sh --quick"
  fi
  echo ""
  echo "  Run with --verbose for full dashboard."
  echo ""
  exit 0
fi

# ============================================================
# VERBOSE MODE (full dashboard — previous default behavior)
# ============================================================

echo ""
echo -e "${BOLD}Dark Forge — Status${NC}"
echo "================================="
echo ""

# --- Installation Status ---
echo -e "${BOLD}Installation${NC}"

check_item() {
  local label="$1"
  local condition="$2"
  if eval "$condition"; then
    echo -e "  ${GREEN}[ok]${NC} $label"
    return 0
  else
    echo -e "  ${RED}[--]${NC} $label"
    return 1
  fi
}

check_item "Submodule present (.ai/)" "[ -d '$AI_DIR/governance' ]" || true
check_item "CLAUDE.md symlink" "[ -L '$PROJECT_ROOT/CLAUDE.md' ] || [ -f '$PROJECT_ROOT/CLAUDE.md' ]" || true
check_item "Governance directories" "[ -d '$PROJECT_ROOT/.governance' ]" || true
check_item "Python available" "command -v python3 &>/dev/null || command -v python &>/dev/null" || true

# Check for virtual environment
if [ -d "$AI_DIR/.venv" ]; then
  check_item "Virtual environment" "true"
else
  echo -e "  ${YELLOW}[??]${NC} Virtual environment (not installed — run init.sh --install-deps)"
fi

echo ""

# --- Project Configuration ---
echo -e "${BOLD}Configuration${NC}"

if [ -f "$PROJECT_ROOT/project.yaml" ]; then
  echo -e "  ${GREEN}[ok]${NC} project.yaml (project root)"
elif [ -f "$AI_DIR/project.yaml" ]; then
  echo -e "  ${YELLOW}[!!]${NC} project.yaml (legacy location: .ai/project.yaml — move to project root)"
else
  echo -e "  ${RED}[--]${NC} project.yaml not found"
  echo "        Create one: cp .ai/governance/templates/python/project.yaml project.yaml"
fi

echo -e "  ${BLUE}Policy profile:${NC} $PROFILE"

echo ""

# --- Recent Emissions ---
echo -e "${BOLD}Recent Governance Activity${NC}"

if [ -d "$EMISSIONS_DIR" ]; then
  if [ "$EMISSION_COUNT" -gt 0 ]; then
    echo "  Panel emissions: $EMISSION_COUNT total"
    echo "  Latest:"
    find "$EMISSIONS_DIR" -name "*.json" -type f -exec stat -f "    %Sm  %N" -t "%Y-%m-%d %H:%M" {} \; 2>/dev/null | sort -r | head -5 || \
    find "$EMISSIONS_DIR" -name "*.json" -type f -printf "    %TY-%Tm-%Td %TH:%TM  %p\n" 2>/dev/null | sort -r | head -5 || \
    echo "    (unable to list — check $EMISSIONS_DIR)"
  else
    echo "  No panel emissions yet. Open a PR to trigger governance reviews."
  fi
else
  echo "  No governance activity directory. Run: bash .ai/bin/init.sh"
fi

echo ""

# --- Checkpoints ---
CHECKPOINT_DIR="$PROJECT_ROOT/.governance/checkpoints"
if [ -d "$CHECKPOINT_DIR" ]; then
  CHECKPOINT_COUNT=$(find "$CHECKPOINT_DIR" -name "*.json" -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "$CHECKPOINT_COUNT" -gt 0 ]; then
    echo -e "${BOLD}Session Checkpoints${NC}"
    echo "  Total: $CHECKPOINT_COUNT"
    LATEST=$(find "$CHECKPOINT_DIR" -name "*.json" -type f 2>/dev/null | sort -r | head -1)
    if [ -n "$LATEST" ]; then
      echo "  Latest: $(basename "$LATEST")"
    fi
    echo ""
  fi
fi

# --- Quick Actions ---
echo -e "${BOLD}Quick Actions${NC}"
echo "  Update governance:   git submodule update --remote .ai && bash .ai/bin/init.sh --refresh"
echo "  Install dependencies: bash .ai/bin/init.sh --install-deps"
echo "  Configure IDEs:      bash .ai/bin/init.sh --mcp"
echo "  Verify installation: bash .ai/bin/init.sh --verify"
echo ""

if [ "$install_ok" = true ]; then
  echo -e "${GREEN}Governance is active.${NC} Open a PR to see it in action."
else
  echo -e "${YELLOW}Governance is partially configured.${NC} Run: bash .ai/bin/init.sh --quick"
fi
echo ""
