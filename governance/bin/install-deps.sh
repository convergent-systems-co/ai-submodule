#!/bin/bash
# governance/bin/install-deps.sh — Python venv creation and pip dependency installation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
resolve_ai_dir

PYTHON_CMD="${PYTHON_CMD:-}"
PYTHON_OK="${PYTHON_OK:-false}"
PYTHON_MIN_MAJOR="${PYTHON_MIN_MAJOR:-3}"
PYTHON_MIN_MINOR="${PYTHON_MIN_MINOR:-9}"
REQUIREMENTS="$AI_DIR/governance/bin/requirements.txt"
PYPROJECT="$AI_DIR/governance/engine/pyproject.toml"

echo ""
echo "Installing dependencies..."

if [ "$PYTHON_OK" = "false" ]; then
  log_error "Cannot install dependencies: Python ${PYTHON_MIN_MAJOR}.${PYTHON_MIN_MINOR}+ is required but not found."
  echo "          Install Python from https://www.python.org/downloads/ and re-run with --install-deps."
  exit 1
fi

# Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
  echo "  Creating virtual environment at .ai/.venv ..."
  run_cmd "Create venv" "$PYTHON_CMD" -m venv "$VENV_DIR"
  log_ok "Virtual environment created"
else
  log_ok "Virtual environment already exists at .ai/.venv"
fi

# Install requirements
run_cmd "Upgrade pip" "$VENV_DIR/bin/pip" install --quiet --upgrade pip
if [ -f "$PYPROJECT" ]; then
  echo "  Installing packages from governance/engine/pyproject.toml ..."
  run_cmd "Install pyproject" "$VENV_DIR/bin/pip" install --quiet -e "$AI_DIR/governance/engine[dev]"
  log_ok "Packages installed (pyproject.toml)"
elif [ -f "$REQUIREMENTS" ]; then
  echo "  Installing packages from requirements.txt (legacy fallback) ..."
  run_cmd "Install requirements" "$VENV_DIR/bin/pip" install --quiet -r "$REQUIREMENTS"
  log_ok "Packages installed (requirements.txt)"
else
  log_error "No pyproject.toml or requirements.txt found"
  echo "          Expected: $PYPROJECT or $REQUIREMENTS"
  exit 1
fi

# Verify installation
echo ""
echo "Verifying installation..."
if "$VENV_DIR/bin/python" -c "import jsonschema; import yaml; print('  [OK] jsonschema and pyyaml verified')" 2>/dev/null; then
  :
else
  log_error "Package verification failed. Check the install output above."
  exit 1
fi
