#!/bin/bash
# governance/bin/verify-installation.sh — Read-only installation verification
# Validates that the dark-forge is correctly installed regardless of installation method.
# Called by: bash .ai/bin/init.sh --verify (or standalone)
#
# Exit codes:
#   0 — all checks passed
#   1 — one or more checks failed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure AI_DIR and PROJECT_ROOT are set before sourcing common.sh (which uses set -u guards)
export AI_DIR="${AI_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
export PROJECT_ROOT="${PROJECT_ROOT:-$(dirname "$AI_DIR")}"

source "$SCRIPT_DIR/lib/common.sh"
resolve_ai_dir

# --- Context detection ---
# Detect if we're running inside the governance repo itself (not as a submodule).
# When AI_DIR IS the git repo root, use AI_DIR as the effective project root.
IS_SUBMODULE=false
IS_GOVERNANCE_REPO=false

if [ -f "$PROJECT_ROOT/.gitmodules" ] && grep -q '\.ai' "$PROJECT_ROOT/.gitmodules" 2>/dev/null; then
  IS_SUBMODULE=true
elif git -C "$AI_DIR" rev-parse --show-toplevel &>/dev/null; then
  GIT_ROOT="$(cd "$(git -C "$AI_DIR" rev-parse --show-toplevel)" && pwd)"
  AI_DIR_REAL="$(cd "$AI_DIR" && pwd)"
  if [ "$GIT_ROOT" = "$AI_DIR_REAL" ]; then
    IS_GOVERNANCE_REPO=true
    PROJECT_ROOT="$AI_DIR"
  fi
fi

# Determine the correct base path for governance sources
if [ "$IS_SUBMODULE" = "true" ]; then
  GOV_BASE="$PROJECT_ROOT/.ai"
else
  GOV_BASE="$AI_DIR"
fi

# --- Counters ---
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# --- Helpers ---
record_pass() {
  echo "  [PASS] $*"
  PASS_COUNT=$((PASS_COUNT + 1))
}

record_fail() {
  echo "  [FAIL] $*"
  FAIL_COUNT=$((FAIL_COUNT + 1))
}

record_warn() {
  echo "  [WARN] $*"
  WARN_COUNT=$((WARN_COUNT + 1))
}

echo ""
echo "Installation Verification Report"
echo "================================"
echo ""

# --- Check 1: Git repository ---
if git -C "$PROJECT_ROOT" rev-parse --is-inside-work-tree &>/dev/null; then
  record_pass "Git repository detected"
else
  record_fail "Not inside a git repository"
fi

# --- Check 2: Submodule presence (submodule context only) ---
if [ "$IS_SUBMODULE" = "true" ]; then
  if [ -d "$PROJECT_ROOT/.ai/.git" ] || [ -f "$PROJECT_ROOT/.ai/.git" ]; then
    record_pass "Submodule .ai is present"
  else
    record_fail "Submodule .ai entry in .gitmodules but directory missing — run: git submodule update --init .ai"
  fi
fi

# --- Check 3: project.yaml ---
if [ -f "$PROJECT_ROOT/project.yaml" ]; then
  # Validate required keys using grep (zero-dependency)
  MISSING_KEYS=""
  for key in name language governance; do
    if ! grep -q "^${key}:" "$PROJECT_ROOT/project.yaml" 2>/dev/null; then
      MISSING_KEYS="$MISSING_KEYS $key"
    fi
  done
  if [ -z "$MISSING_KEYS" ]; then
    record_pass "project.yaml found at project root with required keys (name, language, governance)"
  else
    record_warn "project.yaml found at project root but missing keys:$MISSING_KEYS"
  fi
elif [ -f "$GOV_BASE/project.yaml" ]; then
  record_warn "project.yaml found at .ai/project.yaml (legacy location) — move to project root: mv .ai/project.yaml project.yaml"
else
  record_fail "project.yaml not found — copy a template: cp .ai/governance/templates/<lang>/project.yaml project.yaml"
fi

# --- Check 4: Symlinks / copies ---
# CLAUDE.md — either a symlink (legacy) or a copy (preferred) is acceptable
if [ -L "$PROJECT_ROOT/CLAUDE.md" ]; then
  LINK_TARGET="$(readlink "$PROJECT_ROOT/CLAUDE.md")"
  if [[ "$LINK_TARGET" == *"instructions.md"* ]]; then
    record_warn "CLAUDE.md is a symlink (works locally but breaks cross-org CI) — run: bash .ai/bin/init.sh --refresh to convert to copy"
  else
    record_warn "CLAUDE.md is a symlink but points to unexpected target: $LINK_TARGET"
  fi
elif [ -f "$PROJECT_ROOT/CLAUDE.md" ]; then
  record_pass "CLAUDE.md present (regular file)"
else
  record_fail "CLAUDE.md missing — run: bash .ai/bin/init.sh"
fi

# .github/copilot-instructions.md — either a symlink (legacy) or a copy (preferred) is acceptable
if [ -L "$PROJECT_ROOT/.github/copilot-instructions.md" ]; then
  LINK_TARGET="$(readlink "$PROJECT_ROOT/.github/copilot-instructions.md")"
  if [[ "$LINK_TARGET" == *"instructions.md"* ]]; then
    record_warn ".github/copilot-instructions.md is a symlink (works locally but breaks cross-org CI) — run: bash .ai/bin/init.sh --refresh to convert to copy"
  else
    record_warn ".github/copilot-instructions.md is a symlink but points to unexpected target: $LINK_TARGET"
  fi
elif [ -f "$PROJECT_ROOT/.github/copilot-instructions.md" ]; then
  record_pass ".github/copilot-instructions.md present (regular file)"
else
  record_fail ".github/copilot-instructions.md missing — run: bash .ai/bin/init.sh"
fi

# --- Check 5: Slash commands ---
COMMANDS_DIR="$PROJECT_ROOT/.claude/commands"
EXPECTED_COMMANDS="startup.md checkpoint.md threat-model.md"

if [ -d "$COMMANDS_DIR" ]; then
  if [ -L "$COMMANDS_DIR" ]; then
    COMMANDS_STATUS="symlink"
  else
    COMMANDS_STATUS="directory"
  fi

  MISSING_CMDS=""
  for cmd in $EXPECTED_COMMANDS; do
    if [ ! -f "$COMMANDS_DIR/$cmd" ]; then
      MISSING_CMDS="$MISSING_CMDS $cmd"
    fi
  done

  if [ -z "$MISSING_CMDS" ]; then
    record_pass "Slash commands present: startup.md, checkpoint.md, threat-model.md"
  else
    record_fail "Slash commands missing:$MISSING_CMDS — run: bash .ai/bin/init.sh"
  fi

  if [ "$COMMANDS_STATUS" = "directory" ] && [ "$IS_SUBMODULE" = "true" ]; then
    record_warn ".claude/commands/ is a regular directory (not a symlink to .ai/.claude/commands/)"
  fi
else
  record_fail ".claude/commands/ directory missing — run: bash .ai/bin/init.sh"
fi

# --- Check 6: Governance directories ---
GOV_DIRS=".artifacts/plans .artifacts/panels .artifacts/checkpoints .artifacts/state .artifacts/state/agent-log"
MISSING_DIRS=""
for dir in $GOV_DIRS; do
  if [ ! -d "$PROJECT_ROOT/$dir" ]; then
    MISSING_DIRS="$MISSING_DIRS $dir"
  fi
done

if [ -z "$MISSING_DIRS" ]; then
  record_pass "Governance directories present (.artifacts/plans, panels, checkpoints, state, state/agent-log)"
else
  record_fail "Governance directories missing:$MISSING_DIRS — run: bash .ai/bin/init.sh"
fi

# --- Check 7: Governance workflow (submodule context only) ---
if [ "$IS_SUBMODULE" = "true" ]; then
  WF_PATH="$PROJECT_ROOT/.github/workflows/dark-factory-governance.yml"
  if [ -L "$WF_PATH" ]; then
    record_warn "Governance workflow is a symlink (breaks CI in cross-org repos) — run: bash .ai/bin/init.sh --refresh"
  elif [ -f "$WF_PATH" ]; then
    record_pass "Governance workflow present (dark-factory-governance.yml)"
  else
    record_fail "Governance workflow missing — run: bash .ai/bin/init.sh"
  fi
fi

# --- Check 7b: Vendored policy engine (submodule context only) ---
if [ "$IS_SUBMODULE" = "true" ]; then
  VENDOR_DIR="$PROJECT_ROOT/.artifacts/engine"
  if [ -f "$VENDOR_DIR/policy-engine.py" ] && [ -f "$VENDOR_DIR/VERSION" ]; then
    # Check staleness
    VENDOR_VERSION="$(cat "$VENDOR_DIR/VERSION" 2>/dev/null || echo "")"
    if [ -n "$VENDOR_VERSION" ]; then
      CURRENT_VERSION=""
      if git -C "$GOV_BASE" rev-parse HEAD &>/dev/null; then
        CURRENT_VERSION="$(git -C "$GOV_BASE" rev-parse HEAD)"
      fi
      if [ -n "$CURRENT_VERSION" ] && [ "$VENDOR_VERSION" != "$CURRENT_VERSION" ]; then
        record_warn "Vendored policy engine is stale (vendored: ${VENDOR_VERSION:0:12}, current: ${CURRENT_VERSION:0:12}) — run: bash .ai/bin/init.sh --refresh"
      else
        record_pass "Vendored policy engine present and up-to-date"
      fi
    else
      record_warn "Vendored policy engine VERSION file is empty"
    fi
  else
    record_warn "Vendored policy engine not found — cross-org CI will use lightweight fallback. Run: bash .ai/bin/init.sh --refresh"
  fi
fi

# --- Check 7c: Cross-org CI readiness (submodule context only) ---
if [ "$IS_SUBMODULE" = "true" ]; then
  VENDOR_DIR="$PROJECT_ROOT/.artifacts/engine"

  # Check vendored engine completeness — all files needed for standalone CI
  if [ -d "$VENDOR_DIR" ]; then
    VENDOR_MISSING=""
    for required_file in "policy-engine.py" "VERSION" "policy/default.yaml"; do
      if [ ! -f "$VENDOR_DIR/$required_file" ]; then
        VENDOR_MISSING="$VENDOR_MISSING $required_file"
      fi
    done

    if [ -z "$VENDOR_MISSING" ]; then
      record_pass "Vendored engine has all required files for standalone CI"
    else
      record_warn "Vendored engine incomplete — missing:$VENDOR_MISSING — run: bash .ai/bin/init.sh --refresh"
    fi

    # Check that vendored schemas include panel-output.schema.json
    if [ -f "$VENDOR_DIR/schemas/panel-output.schema.json" ]; then
      record_pass "Vendored engine includes panel-output schema"
    else
      record_warn "Vendored engine missing panel-output.schema.json — validation may be limited"
    fi
  fi

  # Check for symlinks that break cross-org CI
  BROKEN_SYMLINKS=""
  for check_path in "$PROJECT_ROOT/.github/workflows/dark-factory-governance.yml" \
                     "$PROJECT_ROOT/CLAUDE.md" \
                     "$PROJECT_ROOT/.github/copilot-instructions.md"; do
    if [ -L "$check_path" ]; then
      BROKEN_SYMLINKS="$BROKEN_SYMLINKS $(basename "$check_path")"
    fi
  done

  if [ -z "$BROKEN_SYMLINKS" ]; then
    record_pass "No symlinks found in CI-critical paths (cross-org compatible)"
  else
    record_warn "Symlinks detected in CI-critical paths:$BROKEN_SYMLINKS — these break cross-org CI. Run: bash .ai/bin/init.sh --refresh"
  fi

  # Verify CI can run policy engine without submodule
  # (vendored engine + local emissions = CI-ready)
  if [ -f "$VENDOR_DIR/policy-engine.py" ] && [ -s "$VENDOR_DIR/VERSION" ]; then
    if [ -d "$PROJECT_ROOT/.artifacts/panels" ] || [ -d "$PROJECT_ROOT/governance/emissions" ]; then
      record_pass "Cross-org CI ready: vendored engine + emissions directory present"
    else
      record_warn "Vendored engine present but no emissions directory — CI will require panel emissions to evaluate"
    fi
  fi
fi

# --- Check 8: CODEOWNERS ---
# Check multiple valid locations
CODEOWNERS_FOUND=false
for loc in "$PROJECT_ROOT/CODEOWNERS" "$PROJECT_ROOT/.github/CODEOWNERS" "$PROJECT_ROOT/docs/CODEOWNERS"; do
  if [ -f "$loc" ] && [ -s "$loc" ]; then
    CODEOWNERS_FOUND=true
    break
  fi
done

if [ "$CODEOWNERS_FOUND" = "true" ]; then
  record_pass "CODEOWNERS file present and non-empty"
else
  record_warn "CODEOWNERS file missing or empty — run: bash .ai/bin/init.sh"
fi

# --- Check 9: instructions.md source ---
if [ "$IS_SUBMODULE" = "true" ]; then
  INSTRUCTIONS_PATH="$PROJECT_ROOT/.ai/instructions.md"
else
  INSTRUCTIONS_PATH="$AI_DIR/instructions.md"
fi

if [ -f "$INSTRUCTIONS_PATH" ]; then
  record_pass "instructions.md source file present"
else
  record_fail "instructions.md source file missing at $INSTRUCTIONS_PATH"
fi

# --- Summary ---
echo ""
echo "Summary: $PASS_COUNT passed, $FAIL_COUNT failed, $WARN_COUNT warning(s)"

if [ "$FAIL_COUNT" -gt 0 ]; then
  echo ""
  echo "Remediation: run 'bash .ai/bin/init.sh' to fix most issues."
  exit 1
else
  exit 0
fi
