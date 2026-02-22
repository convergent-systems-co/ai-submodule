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
else
  echo "  Skipping issue template copy (not a submodule context)"
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
