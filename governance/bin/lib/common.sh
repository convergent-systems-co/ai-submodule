#!/bin/bash
# governance/bin/lib/common.sh — Shared functions for init modular scripts.
# Sourced by all governance/bin/*.sh scripts.

# Guard against double-sourcing
[ -n "${_COMMON_SH_LOADED:-}" ] && return 0
_COMMON_SH_LOADED=1

# --- Configuration ---
DRY_RUN="${DRY_RUN:-false}"
DEBUG="${DEBUG:-false}"

# --- Logging ---
log_ok()    { echo "  [OK] $*"; }
log_warn()  { echo "  [WARN] $*"; }
log_error() { echo "  [ERROR] $*"; }
log_skip()  { echo "  [SKIP] $*"; }
log_info()  { echo "  [INFO] $*"; }
log_debug() { [ "$DEBUG" = "true" ] && echo "  [DEBUG] $*" || true; }

# --- Path resolution ---
# Resolve the .ai directory from any governance/bin/ script.
# Sets AI_DIR, PROJECT_ROOT if not already set.
resolve_ai_dir() {
  if [ -z "$AI_DIR" ]; then
    # Detect: are we inside governance/bin/ or bin/?
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}")" && pwd)"
    if [[ "$script_dir" == */governance/bin ]]; then
      AI_DIR="$(cd "$script_dir/../.." && pwd)"
    elif [[ "$script_dir" == */governance/bin/lib ]]; then
      AI_DIR="$(cd "$script_dir/../../.." && pwd)"
    elif [[ "$script_dir" == */bin ]]; then
      AI_DIR="$(cd "$script_dir/.." && pwd)"
    else
      AI_DIR="$(cd "$script_dir" && pwd)"
    fi
  fi
  PROJECT_ROOT="${PROJECT_ROOT:-$(dirname "$AI_DIR")}"
  VENV_DIR="${VENV_DIR:-$AI_DIR/.venv}"

  log_debug "AI_DIR=$AI_DIR"
  log_debug "PROJECT_ROOT=$PROJECT_ROOT"
}

# --- Command check ---
check_command() {
  command -v "$1" &>/dev/null
}

# --- Dry-run wrapper ---
# Usage: run_cmd <description> <command...>
run_cmd() {
  local desc="$1"; shift
  if [ "$DRY_RUN" = "true" ]; then
    echo "  [DRY-RUN] $desc: $*"
    return 0
  fi
  log_debug "Running: $*"
  "$@"
}

# --- Python resolution ---
# Find a working Python command and validate version.
# Sets PYTHON_CMD and PYTHON_OK.
find_python() {
  for cmd in python3 python; do
    if check_command "$cmd"; then
      echo "$cmd"
      return 0
    fi
  done
  return 1
}

# --- File copy with diff-based staleness detection ---
# Replaces symlinks with copies; updates stale copies; skips unchanged files.
# Usage: copy_with_diff <source> <destination>
copy_with_diff() {
  local src="$1" dst="$2"
  if [ ! -f "$src" ]; then
    log_warn "Source file not found: $src"
    return 1
  fi
  if [ -L "$dst" ]; then
    if [ "$DRY_RUN" = "true" ]; then
      echo "  [DRY-RUN] Would replace symlink with copy: $dst"
      return 0
    fi
    rm "$dst"
    echo "  [MIGRATE] Replacing symlink with copy: $dst"
  fi
  if [ ! -f "$dst" ]; then
    if [ "$DRY_RUN" = "true" ]; then
      echo "  [DRY-RUN] Would copy: $src -> $dst"
      return 0
    fi
    cp "$src" "$dst"
    echo "  [COPY] $dst"
  elif ! diff -q "$src" "$dst" >/dev/null 2>&1; then
    if [ "$DRY_RUN" = "true" ]; then
      echo "  [DRY-RUN] Would update (content differs): $dst"
      return 0
    fi
    cp "$src" "$dst"
    echo "  [UPDATE] $dst"
  else
    echo "  [SKIP] $dst (unchanged)"
  fi
}

# Syncs a source directory to a destination directory using copy_with_diff.
# Replaces directory symlinks with real directories. Preserves user-added files.
# Usage: sync_dir_with_diff <source_dir> <destination_dir>
sync_dir_with_diff() {
  local src_dir="$1" dst_dir="$2"
  if [ ! -d "$src_dir" ]; then
    log_warn "Source directory not found: $src_dir"
    return 1
  fi
  if [ -L "$dst_dir" ]; then
    if [ "$DRY_RUN" = "true" ]; then
      echo "  [DRY-RUN] Would replace directory symlink with copy: $dst_dir"
      for src_file in "$src_dir"/*; do
        [ -f "$src_file" ] || continue
        local fname
        fname=$(basename "$src_file")
        echo "  [DRY-RUN] Would copy: $src_file -> $dst_dir/$fname"
      done
      return 0
    fi
    rm "$dst_dir"
    mkdir -p "$dst_dir"
    echo "  [MIGRATE] Replacing directory symlink with copy: $dst_dir"
  else
    mkdir -p "$dst_dir"
  fi
  for src_file in "$src_dir"/*; do
    [ -f "$src_file" ] || continue
    local fname
    fname=$(basename "$src_file")
    copy_with_diff "$src_file" "$dst_dir/$fname"
  done
}

# --- Config parsing helper ---
# Reads a YAML field from config files using Python.
# Usage: parse_yaml_field "repository.auto_merge" "true"
parse_yaml_field() {
  local field="$1"
  local default_value="$2"
  local python_cmd

  if [ -d "$VENV_DIR" ] && [ -x "$VENV_DIR/bin/python" ]; then
    python_cmd="$VENV_DIR/bin/python"
  elif [ -n "$PYTHON_CMD" ] && [ "$PYTHON_OK" = "true" ]; then
    python_cmd="$PYTHON_CMD"
  else
    echo "$default_value"
    return 0
  fi

  "$python_cmd" -c "
import yaml, sys, os

def deep_get(d, keys):
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d

def deep_merge(base, override):
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        elif k in result and isinstance(result[k], list) and isinstance(v, list):
            result[k] = result[k] + v
        else:
            result[k] = v
    return result

field = sys.argv[1]
default_value = sys.argv[2]
config_files = sys.argv[3:]

config = {}
for f in config_files:
    if os.path.exists(f):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
            config = deep_merge(config, data)

val = deep_get(config, field.split('.'))
if val is None:
    print(default_value)
else:
    print(str(val).lower() if isinstance(val, bool) else val)
" "$field" "$default_value" "$AI_DIR/config.yaml" "$AI_DIR/project.yaml" "$PROJECT_ROOT/project.yaml" 2>/dev/null || echo "$default_value"
}
