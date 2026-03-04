#!/bin/bash
# governance/bin/update-submodule.sh — Submodule freshness check, SSH-to-HTTPS conversion, integrity verification.
# Skipped when REFRESH_MODE=true (handled by the caller).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
resolve_ai_dir

REFRESH_MODE="${REFRESH_MODE:-false}"

# --- Submodule freshness check (skipped in refresh mode) ---

if [ "$REFRESH_MODE" = "false" ]; then
  # If running in a consuming repo (submodule context), check if .ai is up to date
  if [ -f "$PROJECT_ROOT/.gitmodules" ] && grep -q '\.ai' "$PROJECT_ROOT/.gitmodules" 2>/dev/null; then
    echo "Checking .ai submodule freshness..."
    # Check for dirty state before attempting update
    if ! git -C "$AI_DIR" diff-index --quiet HEAD -- 2>/dev/null; then
      log_warn ".ai submodule has uncommitted changes; skipping automatic update"
      echo "         Commit, stash, or discard local changes in .ai, then re-run init.sh"
    elif git -C "$AI_DIR" fetch origin main --quiet 2>/dev/null; then
      LOCAL_SHA=$(git -C "$AI_DIR" rev-parse HEAD 2>/dev/null)
      REMOTE_SHA=$(git -C "$AI_DIR" rev-parse origin/main 2>/dev/null)
      if [ -n "$LOCAL_SHA" ] && [ -n "$REMOTE_SHA" ]; then
        if [ "$LOCAL_SHA" = "$REMOTE_SHA" ]; then
          log_ok ".ai submodule is up to date (${LOCAL_SHA:0:8})"
        else
          echo "  [UPDATE] .ai submodule is behind (local: ${LOCAL_SHA:0:8}, remote: ${REMOTE_SHA:0:8})"
          if run_cmd "Update submodule" git -C "$PROJECT_ROOT" submodule update --remote .ai 2>/dev/null; then
            NEW_SHA=$(git -C "$AI_DIR" rev-parse HEAD 2>/dev/null)
            log_ok ".ai submodule updated to ${NEW_SHA:0:8}"
            echo "  Run 'git add .ai && git commit -m \"chore: update .ai submodule\"' to save the update"
          else
            log_warn "Could not update .ai submodule automatically"
            echo "         Run: git submodule update --remote .ai"
          fi
        fi
      fi
    else
      log_warn "Could not fetch .ai remote (network error or no remote configured)"
      echo "         Continuing with current version"
    fi
    echo ""
  fi

  # --- SSH to HTTPS URL conversion for CI compatibility ---

  # GitHub Actions uses GITHUB_TOKEN with HTTPS; SSH URLs fail in CI.
  # Only convert the .ai submodule entry to avoid affecting other submodules.
  if [ -f "$PROJECT_ROOT/.gitmodules" ]; then
    if grep -q 'git@github\.com:' "$PROJECT_ROOT/.gitmodules" 2>/dev/null; then
      echo "Converting .ai submodule SSH URL to HTTPS for CI compatibility..."
      if [ "$DRY_RUN" = "true" ]; then
        echo "  [DRY-RUN] Would convert SSH to HTTPS in .gitmodules"
      else
        awk '
          BEGIN { in_ai = 0 }
          /^\[submodule ".ai"\]$/ { in_ai = 1 }
          /^\[submodule / && $0 !~ /^\[submodule ".ai"\]$/ { in_ai = 0 }
          {
            if (in_ai && $0 ~ /^[[:space:]]*url[[:space:]]*=[[:space:]]*git@github\.com:/) {
              sub(/git@github\.com:/, "https://github.com/")
            }
            print
          }
        ' "$PROJECT_ROOT/.gitmodules" > "$PROJECT_ROOT/.gitmodules.tmp"
        mv "$PROJECT_ROOT/.gitmodules.tmp" "$PROJECT_ROOT/.gitmodules"
        # Validate converted URL
        if ! grep -q 'url.*=.*https://github.com/' "$PROJECT_ROOT/.gitmodules"; then
          log_warn "SSH-to-HTTPS conversion may have produced an invalid URL"
          echo "         Check .gitmodules and verify the .ai submodule URL"
        fi
        log_ok "Converted SSH URL to HTTPS in .gitmodules (.ai submodule only)"
        # Sync .git/config so existing clones use the updated URL immediately
        if git -C "$PROJECT_ROOT" submodule sync .ai 2>/dev/null; then
          log_ok "Synchronized .ai submodule URL in .git/config"
        else
          log_warn "Could not sync submodule URL. Run: git submodule sync .ai" >&2
        fi
        echo "  Run 'git add .gitmodules && git commit -m \"chore: use HTTPS URL for .ai submodule\"' to save"
      fi
    fi
    echo ""
  fi
fi  # end REFRESH_MODE gate

# --- Submodule integrity verification ---
# Verify critical governance files against known-good SHA-256 hashes.

INTEGRITY_MANIFEST="$AI_DIR/governance/integrity/critical-files.sha256"
if [ -f "$INTEGRITY_MANIFEST" ]; then
  echo "Verifying submodule integrity..."

  # Portable SHA-256 check: prefer sha256sum (Linux), fall back to shasum -a 256 (macOS)
  SHA_CMD=""
  if check_command sha256sum; then
    SHA_CMD="sha256sum"
  elif check_command shasum; then
    SHA_CMD="shasum -a 256"
  fi

  if [ -n "$SHA_CMD" ]; then
    INTEGRITY_FAILURES=""
    INTEGRITY_CHECKED=0
    INTEGRITY_PASSED=0
    while IFS= read -r line; do
      # Skip empty lines and comments
      [ -z "$line" ] && continue
      [[ "$line" =~ ^# ]] && continue

      expected_hash="${line%%  *}"
      file_path="${line#*  }"
      full_path="$AI_DIR/$file_path"
      if [ ! -f "$full_path" ]; then
        INTEGRITY_FAILURES="${INTEGRITY_FAILURES}\n  MISSING: $file_path"
        INTEGRITY_CHECKED=$((INTEGRITY_CHECKED + 1))
        continue
      fi

      actual_hash=$($SHA_CMD "$full_path" | awk '{print $1}')
      INTEGRITY_CHECKED=$((INTEGRITY_CHECKED + 1))
      if [ "$actual_hash" = "$expected_hash" ]; then
        INTEGRITY_PASSED=$((INTEGRITY_PASSED + 1))
      else
        INTEGRITY_FAILURES="${INTEGRITY_FAILURES}\n  MISMATCH: $file_path (expected: ${expected_hash:0:16}..., actual: ${actual_hash:0:16}...)"
      fi
    done < "$INTEGRITY_MANIFEST"

    if [ -z "$INTEGRITY_FAILURES" ]; then
      log_ok "All $INTEGRITY_CHECKED critical files verified ($INTEGRITY_PASSED/$INTEGRITY_CHECKED)"
    else
      log_warn "Integrity verification found issues ($INTEGRITY_PASSED/$INTEGRITY_CHECKED passed):"
      echo -e "$INTEGRITY_FAILURES"
      echo "  This may indicate unauthorized modification of governance files."
      echo "  Review changes carefully before proceeding."
    fi
  else
    log_skip "No SHA-256 tool available (install sha256sum or shasum)"
  fi
  echo ""
fi
