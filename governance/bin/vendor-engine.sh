#!/bin/bash
# governance/bin/vendor-engine.sh — Vendor the policy engine into a consuming repo.
#
# Copies the policy engine, schemas, and policy profiles into .artifacts/engine/
# so that cross-org consuming repos can run the full policy engine in CI without
# needing to clone the dark-forge.
#
# Called by: init.sh (submodule context) or standalone.
#
# Usage:
#   bash .ai/governance/bin/vendor-engine.sh
#   bash .ai/governance/bin/vendor-engine.sh --force    # re-vendor even if up-to-date
#   bash .ai/governance/bin/vendor-engine.sh --check    # check staleness only (exit 0=fresh, 1=stale)
#   bash .ai/governance/bin/vendor-engine.sh --package  # create distributable tarball in .artifacts/dist/
#
# The vendored copy includes:
#   .artifacts/engine/policy-engine.py    — CLI entry point
#   .artifacts/engine/policy_engine.py    — Engine module
#   .artifacts/engine/policy/             — Policy profiles
#   .artifacts/engine/schemas/            — JSON schemas for validation
#   .artifacts/engine/requirements.txt    — Python dependencies
#   .artifacts/engine/VERSION             — Submodule commit SHA for staleness detection

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
resolve_ai_dir

FORCE=false
CHECK_ONLY=false
PACKAGE=false

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=true ;;
    --check) CHECK_ONLY=true ;;
    --package) PACKAGE=true ;;
  esac
done

# --- Paths ---
VENDOR_DIR="$PROJECT_ROOT/.artifacts/engine"
VERSION_FILE="$VENDOR_DIR/VERSION"

# Source directories (inside the submodule)
ENGINE_CLI="$AI_DIR/governance/bin/policy-engine.py"
ENGINE_MODULE="$AI_DIR/governance/engine/policy_engine.py"
POLICY_DIR="$AI_DIR/governance/policy"
SCHEMA_DIR="$AI_DIR/governance/schemas"
REQUIREMENTS="$AI_DIR/governance/bin/requirements.txt"

# Schemas needed for policy evaluation (shared by vendor and package modes)
SCHEMA_FILES=(
  "panel-output.schema.json"
  "run-manifest.schema.json"
  "panels.defaults.json"
  "panels.schema.json"
)

# --- Resolve current submodule version ---
get_submodule_version() {
  if git -C "$AI_DIR" rev-parse HEAD &>/dev/null; then
    git -C "$AI_DIR" rev-parse HEAD
  else
    echo "unknown"
  fi
}

CURRENT_VERSION="$(get_submodule_version)"

# --- Staleness check ---
is_stale() {
  if [ ! -f "$VERSION_FILE" ]; then
    return 0  # No version file = needs vendoring
  fi
  local vendored_version
  vendored_version="$(cat "$VERSION_FILE" 2>/dev/null || echo "")"
  if [ "$vendored_version" != "$CURRENT_VERSION" ]; then
    return 0  # Different version = stale
  fi
  # Also check that key files exist
  if [ ! -f "$VENDOR_DIR/policy-engine.py" ] || [ ! -f "$VENDOR_DIR/policy_engine.py" ]; then
    return 0  # Missing files = needs re-vendor
  fi
  return 1  # Up to date
}

# --- Check-only mode ---
if [ "$CHECK_ONLY" = "true" ]; then
  if is_stale; then
    echo "stale"
    exit 1
  else
    echo "fresh"
    exit 0
  fi
fi

# --- Package mode: create distributable tarball ---
if [ "$PACKAGE" = "true" ]; then
  if [ ! -f "$ENGINE_CLI" ]; then
    log_error "Policy engine CLI not found at $ENGINE_CLI — cannot package"
    exit 1
  fi

  DIST_DIR="$PROJECT_ROOT/.artifacts/dist"
  SHORT_VERSION="$(echo "$CURRENT_VERSION" | head -c 12)"
  TARBALL_NAME="governance-engine-${SHORT_VERSION}.tar.gz"
  STAGING_DIR="$(mktemp -d)"

  echo ""
  echo "  Packaging governance engine (${SHORT_VERSION}...)"

  # Create staging directory structure
  mkdir -p "$STAGING_DIR/engine/policy" "$STAGING_DIR/engine/schemas"

  # Copy engine files
  cp "$ENGINE_CLI" "$STAGING_DIR/engine/policy-engine.py"
  if [ -f "$ENGINE_MODULE" ]; then
    cp "$ENGINE_MODULE" "$STAGING_DIR/engine/policy_engine.py"
  fi

  # Copy policy profiles
  if [ -d "$POLICY_DIR" ]; then
    for profile in "$POLICY_DIR"/*.yaml; do
      [ -f "$profile" ] || continue
      cp "$profile" "$STAGING_DIR/engine/policy/$(basename "$profile")"
    done
  fi

  # Copy schemas
  for schema in "${SCHEMA_FILES[@]}"; do
    if [ -f "$SCHEMA_DIR/$schema" ]; then
      cp "$SCHEMA_DIR/$schema" "$STAGING_DIR/engine/schemas/$schema"
    fi
  done

  # Copy requirements
  if [ -f "$REQUIREMENTS" ]; then
    cp "$REQUIREMENTS" "$STAGING_DIR/engine/requirements.txt"
  fi

  # Write version file
  echo "$CURRENT_VERSION" > "$STAGING_DIR/engine/VERSION"

  # Create output directory and tarball
  mkdir -p "$DIST_DIR"
  tar -czf "$DIST_DIR/$TARBALL_NAME" -C "$STAGING_DIR" engine/

  # Clean up staging directory
  rm -rf "$STAGING_DIR"

  log_ok "Created $DIST_DIR/$TARBALL_NAME"
  echo "  Contents: policy-engine.py, policy_engine.py, policy/, schemas/, requirements.txt, VERSION"
  echo ""
  exit 0
fi

# --- Skip if up-to-date (unless --force) ---
if [ "$FORCE" != "true" ] && ! is_stale; then
  log_ok "Vendored policy engine is up-to-date ($(cat "$VERSION_FILE" | head -c 12)...)"
  return 0 2>/dev/null || exit 0
fi

# --- Validate source files exist ---
if [ ! -f "$ENGINE_CLI" ]; then
  log_warn "Policy engine CLI not found at $ENGINE_CLI — skipping vendoring"
  return 0 2>/dev/null || exit 0
fi

# --- Vendor the engine ---
echo ""
echo "  Vendoring policy engine into .artifacts/engine/"

# Create vendor directory structure
run_cmd "Create vendor directory" mkdir -p "$VENDOR_DIR/policy" "$VENDOR_DIR/schemas"

# Copy engine module (the actual implementation)
if [ -f "$ENGINE_MODULE" ]; then
  run_cmd "Copy policy_engine.py (module)" cp "$ENGINE_MODULE" "$VENDOR_DIR/policy_engine.py"
fi

# Create a standalone CLI wrapper that imports from the vendored module directly.
# The submodule's policy-engine.py uses `from governance.engine.policy_engine import main`
# which won't resolve in the vendored location. This wrapper uses a local import instead.
cat > "$VENDOR_DIR/policy-engine.py" << 'CLIEOF'
#!/usr/bin/env python3
"""Vendored policy engine entry point.

Auto-generated by vendor-engine.sh. Imports from the co-located policy_engine.py
module rather than from the governance.engine package path.
"""
import os
import sys

# Add the vendored directory to sys.path so policy_engine is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from policy_engine import main

if __name__ == '__main__':
    main()
CLIEOF
echo "  [OK] Created standalone policy-engine.py (CLI wrapper)"

# Copy policy profiles
if [ -d "$POLICY_DIR" ]; then
  for profile in "$POLICY_DIR"/*.yaml; do
    [ -f "$profile" ] || continue
    run_cmd "Copy policy $(basename "$profile")" cp "$profile" "$VENDOR_DIR/policy/$(basename "$profile")"
  done
  log_ok "Copied $(ls "$POLICY_DIR"/*.yaml 2>/dev/null | wc -l | tr -d ' ') policy profiles"
fi

# Copy schemas (only the ones needed for policy evaluation)
for schema in "${SCHEMA_FILES[@]}"; do
  if [ -f "$SCHEMA_DIR/$schema" ]; then
    run_cmd "Copy schema $schema" cp "$SCHEMA_DIR/$schema" "$VENDOR_DIR/schemas/$schema"
  fi
done

# Copy requirements
if [ -f "$REQUIREMENTS" ]; then
  run_cmd "Copy requirements.txt" cp "$REQUIREMENTS" "$VENDOR_DIR/requirements.txt"
fi

# Write version file
echo "$CURRENT_VERSION" > "$VERSION_FILE"

# Write .gitignore note
if [ ! -f "$VENDOR_DIR/.gitignore" ]; then
  cat > "$VENDOR_DIR/README.md" << 'VENDOREOF'
# Vendored Policy Engine

This directory contains a vendored copy of the Dark Forge policy engine
from the `dark-forge`. It is automatically maintained by `init.sh` and
`init.sh --refresh`.

**Do not edit files in this directory manually.** They will be overwritten
on the next refresh.

## Purpose

Cross-org consuming repos cannot clone the private `convergent-systems-co/dark-forge`
in CI. This vendored copy allows the full policy engine to run without
submodule access, providing Tier 1 evaluation instead of falling back to
the lightweight Tier 2 validator.

## Staleness

The `VERSION` file contains the submodule commit SHA used to produce this
copy. Running `bash .ai/bin/init.sh --refresh` will update the vendored
copy if the submodule has been updated.

To check staleness: `bash .ai/governance/bin/vendor-engine.sh --check`
VENDOREOF
fi

log_ok "Vendored policy engine at version $(echo "$CURRENT_VERSION" | head -c 12)..."
echo ""
