#!/bin/bash
# governance/bin/validate-project-yaml.sh — Validate project.yaml against schema.
#
# Uses python3 jsonschema if available; falls back to basic shell validation
# checking required fields and types.
#
# Usage:
#   bash .ai/governance/bin/validate-project-yaml.sh [PROJECT_YAML_PATH]
#
# Arguments:
#   PROJECT_YAML_PATH    Path to project.yaml (default: ./project.yaml or .ai/project.yaml)
#
# Exit codes:
#   0 — valid
#   1 — invalid or missing

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_DIR="${AI_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
PROJECT_ROOT="${PROJECT_ROOT:-$(dirname "$AI_DIR")}"

# Source common library if available
if [ -f "$SCRIPT_DIR/lib/common.sh" ]; then
  source "$SCRIPT_DIR/lib/common.sh"
fi

SCHEMA_FILE="$AI_DIR/governance/schemas/project.schema.json"

# --- Resolve project.yaml path ---
PROJECT_YAML="${1:-}"
if [ -z "$PROJECT_YAML" ]; then
  if [ -f "$PROJECT_ROOT/project.yaml" ]; then
    PROJECT_YAML="$PROJECT_ROOT/project.yaml"
  elif [ -f "$AI_DIR/project.yaml" ]; then
    PROJECT_YAML="$AI_DIR/project.yaml"
  else
    echo "ERROR: No project.yaml found" >&2
    echo "  Searched: $PROJECT_ROOT/project.yaml" >&2
    echo "  Searched: $AI_DIR/project.yaml" >&2
    exit 1
  fi
fi

if [ ! -f "$PROJECT_YAML" ]; then
  echo "ERROR: File not found: $PROJECT_YAML" >&2
  exit 1
fi

echo "Validating: $PROJECT_YAML"
echo "Schema: $SCHEMA_FILE"
echo ""

# --- Try Python jsonschema validation ---
try_python_validation() {
  local python_cmd=""

  # Find Python
  if [ -d "$AI_DIR/.venv" ] && [ -x "$AI_DIR/.venv/bin/python" ]; then
    python_cmd="$AI_DIR/.venv/bin/python"
  elif command -v python3 &>/dev/null; then
    python_cmd="python3"
  elif command -v python &>/dev/null; then
    python_cmd="python"
  else
    return 1  # No Python available
  fi

  # Check if required modules are available
  if ! "$python_cmd" -c "import yaml, jsonschema" 2>/dev/null; then
    return 1  # Missing modules
  fi

  "$python_cmd" -c "
import sys, json, yaml
from jsonschema import validate, ValidationError, SchemaError

schema_path = sys.argv[1]
yaml_path = sys.argv[2]

try:
    with open(schema_path) as f:
        schema = json.load(f)
except (json.JSONDecodeError, FileNotFoundError) as e:
    print(f'ERROR: Cannot load schema: {e}', file=sys.stderr)
    sys.exit(1)

try:
    with open(yaml_path) as f:
        data = yaml.safe_load(f)
except yaml.YAMLError as e:
    print(f'ERROR: Invalid YAML syntax: {e}', file=sys.stderr)
    sys.exit(1)

if data is None:
    print('ERROR: project.yaml is empty', file=sys.stderr)
    sys.exit(1)

errors = []
try:
    validate(instance=data, schema=schema)
except ValidationError as e:
    # Collect all errors
    from jsonschema import Draft202012Validator
    validator = Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = '.'.join(str(p) for p in error.path) if error.path else '(root)'
        errors.append(f'  - {path}: {error.message}')
except SchemaError as e:
    print(f'ERROR: Invalid schema: {e.message}', file=sys.stderr)
    sys.exit(1)

if errors:
    print('INVALID: project.yaml has validation errors:', file=sys.stderr)
    for err in errors:
        print(err, file=sys.stderr)
    sys.exit(1)
else:
    # Additional semantic checks
    warnings = []
    if 'name' not in data:
        warnings.append('  - Missing recommended field: name')
    if 'language' not in data and 'languages' not in data:
        warnings.append('  - Missing recommended field: language or languages')

    if warnings:
        print('VALID (with warnings):')
        for w in warnings:
            print(w)
    else:
        print('VALID: project.yaml passes schema validation')
    sys.exit(0)
" "$SCHEMA_FILE" "$PROJECT_YAML"
}

# --- Fallback: basic shell validation ---
shell_validation() {
  local errors=0

  echo "  [INFO] Python jsonschema not available; using basic shell validation"
  echo ""

  # Check YAML syntax (if python is available but jsonschema is not)
  local python_cmd=""
  if command -v python3 &>/dev/null; then
    python_cmd="python3"
  elif command -v python &>/dev/null; then
    python_cmd="python"
  fi

  if [ -n "$python_cmd" ]; then
    if ! "$python_cmd" -c "
import yaml, sys
try:
    with open(sys.argv[1]) as f:
        data = yaml.safe_load(f)
    if data is None:
        print('ERROR: File is empty', file=sys.stderr)
        sys.exit(1)
except yaml.YAMLError as e:
    print(f'ERROR: Invalid YAML: {e}', file=sys.stderr)
    sys.exit(1)
except ImportError:
    pass  # No yaml module; skip syntax check
" "$PROJECT_YAML" 2>&1; then
      errors=$((errors + 1))
    fi
  fi

  # Check for required fields using grep (basic)
  if ! grep -q "^name:" "$PROJECT_YAML" 2>/dev/null; then
    echo "  ERROR: Missing required field 'name'" >&2
    errors=$((errors + 1))
  fi

  if ! grep -q "^language:" "$PROJECT_YAML" 2>/dev/null && ! grep -q "^languages:" "$PROJECT_YAML" 2>/dev/null; then
    echo "  ERROR: Missing required field 'language' or 'languages'" >&2
    errors=$((errors + 1))
  fi

  # Check for common mistakes
  if grep -q "^  skip_panel_validation: true" "$PROJECT_YAML" 2>/dev/null; then
    echo "  WARNING: skip_panel_validation is set to true — governance panels will be skipped" >&2
  fi

  if [ "$errors" -gt 0 ]; then
    echo ""
    echo "INVALID: $errors error(s) found"
    return 1
  else
    echo ""
    echo "VALID: Basic validation passed (install jsonschema for full validation)"
    return 0
  fi
}

# --- Run validation ---
if try_python_validation; then
  exit 0
else
  exit_code=$?
  # If Python validation returned 1 because of validation errors, propagate that
  if [ $exit_code -eq 1 ] && command -v python3 &>/dev/null; then
    # Check if Python and jsonschema are available — if so, it was a real validation failure
    if python3 -c "import yaml, jsonschema" 2>/dev/null; then
      exit 1
    fi
  fi
  # Otherwise fall back to shell validation
  if shell_validation; then
    exit 0
  else
    exit 1
  fi
fi
