#!/bin/bash
# .ai/bin/init.sh — Run once after adding the .ai submodule to a project.
# Creates symlinks, detects platform, and optionally installs all dependencies.
#
# Two installation paths:
#   Path 1 (Primary):   init.md — interactive, AI-assisted (agentic bootstrap)
#   Path 2 (Fallback):  init.sh — non-interactive, CI/script (this file)
#
# Usage:
#   bash .ai/bin/init.sh                          # Symlinks only (existing behavior)
#   bash .ai/bin/init.sh --quick                  # Add submodule (HTTPS) + full init (replaces quick-install.sh)
#   bash .ai/bin/init.sh --install-deps           # Symlinks + Python venv + dependencies
#   bash .ai/bin/init.sh --mcp                    # Also install MCP server for IDE integration
#   bash .ai/bin/init.sh --ci                     # Minimal CI-only setup (vendor engine, validate, directories)
#   bash .ai/bin/init.sh --refresh                # Re-apply structural setup after submodule update
#   bash .ai/bin/init.sh --uninstall              # Clean removal of governance artifacts
#   bash .ai/bin/init.sh --check-branch-protection  # Query branch protection status (machine-readable)
#   bash .ai/bin/init.sh --verify                 # Verify installation is complete and correct
#   bash .ai/bin/init.sh --validate               # Validate project.yaml against schema
#   bash .ai/bin/init.sh --quiet                  # Errors only — zero output on success
#   bash .ai/bin/init.sh --verbose                # Per-step detail (restores pre-v1 output)
#   bash .ai/bin/init.sh --dry-run                # Show what would be done without making changes
#   bash .ai/bin/init.sh --debug                  # Full debug trace for troubleshooting
#
# This script is idempotent — safe to run multiple times.
# Modular scripts live in governance/bin/; this file orchestrates them.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"  # .ai/bin/
AI_DIR="$(dirname "$SCRIPT_DIR")"                             # .ai/
PROJECT_ROOT="$(dirname "$AI_DIR")"                           # project root
VENV_DIR="$AI_DIR/.venv"
INSTALL_DEPS=false
REFRESH_MODE=false
CHECK_BRANCH_PROTECTION=false
VERIFY_MODE=false
VALIDATE_MODE=false
QUICK_MODE=false
INSTALL_MCP=false
UNINSTALL_MODE=false
CI_MODE=false
GUIDED_MODE=false
export DRY_RUN="${DRY_RUN:-false}"
export DEBUG="${DEBUG:-false}"
export VERBOSITY="${VERBOSITY:-1}"
export PYTHON_MIN_MAJOR=3
export PYTHON_MIN_MINOR=9

LIB_DIR="$AI_DIR/governance/bin"

# Default submodule URL (HTTPS — works across orgs without SSH key setup)
SUBMODULE_URL="https://github.com/convergent-systems-co/dark-forge.git"
SUBMODULE_PATH=".ai"

# --- Parse arguments ---

for arg in "$@"; do
  case "$arg" in
    --install-deps) INSTALL_DEPS=true ;;
    --refresh) REFRESH_MODE=true ;;
    --check-branch-protection) CHECK_BRANCH_PROTECTION=true ;;
    --verify) VERIFY_MODE=true ;;
    --validate) VALIDATE_MODE=true ;;
    --quick) QUICK_MODE=true ;;
    --mcp) INSTALL_MCP=true ;;
    --ci) CI_MODE=true ;;
    --uninstall) UNINSTALL_MODE=true ;;
    --guided) GUIDED_MODE=true ;;
    --quiet) VERBOSITY=0 ;;
    --verbose) VERBOSITY=2 ;;
    --dry-run) DRY_RUN=true ;;
    --debug) DEBUG=true; VERBOSITY=3 ;;
    --help|-h)
      echo "Usage: bash .ai/bin/init.sh [OPTIONS]"
      echo ""
      echo "Installation paths:"
      echo "  (no flags)                  Standard init — symlinks, workflows, directories"
      echo "  --quick                     Add submodule (HTTPS) + full init (replaces quick-install.sh)"
      echo "  --guided                    Interactive walkthrough with explanations at each step"
      echo "  --install-deps              Also install Python virtual environment and dependencies"
      echo "  --mcp                       Also install MCP server for IDE integration"
      echo "  --ci                        Minimal CI-only setup (vendor engine, validate, directories)"
      echo ""
      echo "Maintenance:"
      echo "  --refresh                   Re-apply structural setup (skip submodule check)"
      echo "  --verify                    Verify installation is complete and correct"
      echo "  --validate                  Validate project.yaml against governance schema"
      echo "  --uninstall                 Clean removal of governance artifacts from project"
      echo ""
      echo "Diagnostics:"
      echo "  --check-branch-protection   Query if default branch requires PRs"
      echo "  --quiet                     Errors only — zero output on success"
      echo "  --verbose                   Per-step detail (restores pre-v1 output)"
      echo "  --dry-run                   Show what would be done without making changes"
      echo "  --debug                     Full debug trace for troubleshooting"
      echo "  --help, -h                  Show this help message"
      echo ""
      echo "For interactive AI-assisted setup, tell your assistant:"
      echo "  \"Read and execute .ai/governance/prompts/init.md\""
      exit 0
      ;;
    *)
      echo "Unknown argument: $arg"
      echo "Usage: bash .ai/bin/init.sh [--quick] [--guided] [--install-deps] [--mcp] [--ci] [--refresh] [--uninstall] [--verify] [--validate] [--quiet] [--verbose] [--dry-run] [--debug]"
      exit 1
      ;;
  esac
done

# Export shared variables for modular scripts
export AI_DIR PROJECT_ROOT VENV_DIR DRY_RUN DEBUG VERBOSITY

# --- Early exit: --check-branch-protection ---

if [ "$CHECK_BRANCH_PROTECTION" = "true" ]; then
  exec bash "$LIB_DIR/check-branch-protection.sh"
fi

# --- Early exit: --verify ---

if [ "$VERIFY_MODE" = "true" ]; then
  exec bash "$LIB_DIR/verify-installation.sh"
fi

# --- Early exit: --validate ---

if [ "$VALIDATE_MODE" = "true" ]; then
  exec bash "$LIB_DIR/validate-project-yaml.sh"
fi

# --- Early exit: --uninstall ---

if [ "$UNINSTALL_MODE" = "true" ]; then
  echo "Uninstalling Dark Forge governance artifacts..."
  echo ""

  # Remove symlinks
  for link in "$PROJECT_ROOT/CLAUDE.md" "$PROJECT_ROOT/.github/copilot-instructions.md"; do
    if [ -L "$link" ]; then
      if [ "$DRY_RUN" = "true" ]; then
        echo "  [DRY-RUN] Would remove symlink: $link"
      else
        rm "$link"
        echo "  [OK] Removed symlink: $link"
      fi
    fi
  done

  # Remove .claude/commands symlink or directory
  COMMANDS_DIR="$PROJECT_ROOT/.claude/commands"
  if [ -L "$COMMANDS_DIR" ]; then
    if [ "$DRY_RUN" = "true" ]; then
      echo "  [DRY-RUN] Would remove symlink: $COMMANDS_DIR"
    else
      rm "$COMMANDS_DIR"
      echo "  [OK] Removed symlink: $COMMANDS_DIR"
    fi
  fi

  # Remove governance directories
  for dir in "$PROJECT_ROOT/.governance"; do
    if [ -d "$dir" ]; then
      if [ "$DRY_RUN" = "true" ]; then
        echo "  [DRY-RUN] Would remove directory: $dir"
      else
        echo "  [WARN] .artifacts/ directory preserved (contains state). Remove manually if desired:"
        echo "         rm -rf $dir"
      fi
    fi
  done

  # Remove venv
  if [ -d "$VENV_DIR" ]; then
    if [ "$DRY_RUN" = "true" ]; then
      echo "  [DRY-RUN] Would remove virtual environment: $VENV_DIR"
    else
      rm -rf "$VENV_DIR"
      echo "  [OK] Removed virtual environment: $VENV_DIR"
    fi
  fi

  echo ""
  echo "Uninstall complete."
  echo ""
  echo "To fully remove the submodule:"
  echo "  git submodule deinit .ai"
  echo "  git rm .ai"
  echo "  rm -rf .git/modules/.ai"
  exit 0
fi

# --- Early exit: --ci (minimal CI-only setup) ---

if [ "$CI_MODE" = "true" ]; then
  echo "CI mode: minimal governance setup for CI environments"
  echo ""

  # Source shared library
  source "$LIB_DIR/lib/common.sh"

  # Step 1: Python detection (needed for policy engine)
  export PYTHON_CMD="" PYTHON_OK=false
  source "$LIB_DIR/check-python.sh"
  export PYTHON_CMD PYTHON_OK

  # Step 2: Setup governance directories (always needed)
  IS_SUBMODULE=false
  if [ -f "$PROJECT_ROOT/.gitmodules" ] && grep -q '\.ai' "$PROJECT_ROOT/.gitmodules" 2>/dev/null; then
    IS_SUBMODULE=true
  fi

  if [ "$IS_SUBMODULE" = "true" ]; then
    source "$LIB_DIR/setup-directories.sh"
    # Step 3: Validate emissions structure
    source "$LIB_DIR/validate-emissions.sh"
    # Step 4: Vendor engine for cross-org CI
    source "$LIB_DIR/vendor-engine.sh"
  else
    # Not a submodule context — just ensure directories exist
    for dir in "$PROJECT_ROOT/.artifacts/plans" "$PROJECT_ROOT/.artifacts/panels" \
               "$PROJECT_ROOT/.artifacts/checkpoints" "$PROJECT_ROOT/.artifacts/state"; do
      mkdir -p "$dir" 2>/dev/null || true
    done
    log_ok "Governance directories created"
  fi

  echo ""
  echo "CI setup complete."
  exit 0
fi

# --- Quick mode: add submodule first ---

if [ "$QUICK_MODE" = "true" ]; then
  # Must be in a git repository
  if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo "[ERROR] Not inside a git repository. Run 'git init' first."
    exit 1
  fi

  # Re-resolve PROJECT_ROOT for quick mode (we're in the project root, not .ai/)
  if [ ! -d "$SUBMODULE_PATH" ]; then
    echo "Adding $SUBMODULE_PATH as git submodule (HTTPS)..."
    if [ "$DRY_RUN" = "true" ]; then
      echo "  [DRY-RUN] Would run: git submodule add $SUBMODULE_URL $SUBMODULE_PATH"
    else
      git submodule add "$SUBMODULE_URL" "$SUBMODULE_PATH"
      echo "[OK] Submodule added."
    fi
  else
    echo "[OK] $SUBMODULE_PATH already exists."
  fi

  # After adding submodule, re-resolve paths
  if [ -d "$SUBMODULE_PATH" ]; then
    AI_DIR="$(cd "$SUBMODULE_PATH" && pwd)"
    LIB_DIR="$AI_DIR/governance/bin"
    VENV_DIR="$AI_DIR/.venv"
    export AI_DIR VENV_DIR
  fi

  echo ""
  # Fall through to normal init
fi

# --- Guided mode: interactive walkthrough ---

if [ "$GUIDED_MODE" = "true" ]; then
  echo ""
  echo "=== Dark Forge — Guided Setup ==="
  echo ""
  echo "This will walk you through setting up governance for your repository."
  echo "Each step will be explained before it runs."
  echo ""

  # Step 1: Prerequisites
  echo "--- Step 1 of 5: Check Prerequisites ---"
  echo "Governance needs Python 3.9+ for the policy engine and git for version control."
  echo ""
  PREREQ_OK=true
  if command -v python3 &>/dev/null; then
    echo "  [ok] Python: $(python3 --version 2>&1)"
  elif command -v python &>/dev/null; then
    echo "  [ok] Python: $(python --version 2>&1)"
  else
    echo "  [--] Python: not found"
    echo "       Install: brew install python3 (macOS) or apt install python3 (Linux)"
    PREREQ_OK=false
  fi
  if command -v git &>/dev/null; then
    echo "  [ok] git: $(git --version 2>&1 | head -1)"
  else
    echo "  [--] git: not found"
    PREREQ_OK=false
  fi
  if command -v gh &>/dev/null; then
    echo "  [ok] gh CLI: $(gh --version 2>&1 | head -1)"
  else
    echo "  [..] gh CLI: not found (optional — needed for PR governance)"
  fi
  echo ""

  if [ "$PREREQ_OK" = "false" ]; then
    read -rp "Some prerequisites are missing. Continue anyway? [y/N] " PREREQ_ANSWER
    if [[ ! "$PREREQ_ANSWER" =~ ^[Yy] ]]; then
      echo "Setup cancelled. Install missing prerequisites and try again."
      exit 0
    fi
  fi

  # Step 2: Explain what will happen
  echo "--- Step 2 of 5: What Gets Installed ---"
  echo "The setup will:"
  echo "  1. Create symlinks for AI assistant instructions (CLAUDE.md, copilot-instructions.md)"
  echo "  2. Copy GitHub Actions workflows for automated PR governance"
  echo "  3. Create .governance/ directories for plans, panels, and checkpoints"
  echo "  4. Generate repository configuration (CODEOWNERS)"
  echo ""
  echo "Your existing files will NOT be overwritten."
  echo ""
  read -rp "Continue? [Y/n] " SETUP_ANSWER
  if [[ "$SETUP_ANSWER" =~ ^[Nn] ]]; then
    echo "Setup cancelled."
    exit 0
  fi

  # Step 3: Deps
  echo ""
  echo "--- Step 3 of 5: Python Dependencies ---"
  echo "The policy engine needs Python packages (PyYAML, jsonschema, etc.)."
  echo "These are installed in an isolated virtual environment at .ai/.venv/"
  echo ""
  read -rp "Install Python dependencies? [Y/n] " DEPS_ANSWER
  if [[ ! "$DEPS_ANSWER" =~ ^[Nn] ]]; then
    INSTALL_DEPS=true
  fi

  # Step 4: MCP
  echo ""
  echo "--- Step 4 of 5: IDE Integration ---"
  echo "The MCP server integrates governance tools into your IDE (VS Code, Cursor, Claude Code)."
  echo "This requires Node.js and npm."
  echo ""
  if command -v npm &>/dev/null; then
    read -rp "Configure IDE integration? [Y/n] " MCP_ANSWER
    if [[ ! "$MCP_ANSWER" =~ ^[Nn] ]]; then
      INSTALL_MCP=true
    fi
  else
    echo "  [skip] npm not found — IDE integration requires Node.js."
    echo "         Install Node.js later and run: bash .ai/bin/init.sh --mcp"
  fi

  # Step 5: Confirm
  echo ""
  echo "--- Step 5 of 5: Confirm ---"
  echo "Ready to install with these options:"
  echo "  Python dependencies: $([ "$INSTALL_DEPS" = "true" ] && echo "yes" || echo "no")"
  echo "  IDE integration:     $([ "$INSTALL_MCP" = "true" ] && echo "yes" || echo "no")"
  echo ""
  read -rp "Start installation? [Y/n] " FINAL_ANSWER
  if [[ "$FINAL_ANSWER" =~ ^[Nn] ]]; then
    echo "Setup cancelled."
    exit 0
  fi
  echo ""
  echo "Installing..."
  echo ""
  # Fall through to normal init with the selected options
fi

# --- Platform detection ---

detect_platform() {
  local os; os="$(uname -s)"
  case "$os" in
    Darwin) echo "macOS" ;; Linux) echo "Linux" ;; *) echo "$os" ;;
  esac
}

PLATFORM="$(detect_platform)"

# --- Source shared library (includes output.sh for verbosity control) ---
source "$LIB_DIR/lib/common.sh"

# Start summary collection
output_summary_start

out_verbose "Platform: $PLATFORM"
out_verbose ""

# --- Step 1: Python detection ---
export PYTHON_CMD="" PYTHON_OK=false
source "$LIB_DIR/check-python.sh"
export PYTHON_CMD PYTHON_OK

# --- Step 2: Submodule freshness + integrity ---
export REFRESH_MODE
source "$LIB_DIR/update-submodule.sh"

# --- Step 3: Symlinks ---
source "$LIB_DIR/create-symlinks.sh"

# --- Step 4-6: Submodule-context setup (workflows, emissions, directories) ---
IS_SUBMODULE=false
if [ -f "$PROJECT_ROOT/.gitmodules" ] && grep -q '\.ai' "$PROJECT_ROOT/.gitmodules" 2>/dev/null; then
  IS_SUBMODULE=true
fi

if [ "$IS_SUBMODULE" = "true" ]; then
  source "$LIB_DIR/setup-workflows.sh"
  source "$LIB_DIR/validate-emissions.sh"
  source "$LIB_DIR/setup-directories.sh"
  # Vendor policy engine for cross-org CI (consuming repos can't clone submodule)
  source "$LIB_DIR/vendor-engine.sh"
else
  out_verbose "Skipping template/workflow/directory setup (not a submodule context)"
fi

# --- Ensure project.yaml exists (auto-detect if missing) ---
if [ ! -f "$PROJECT_ROOT/project.yaml" ] && [ ! -f "$AI_DIR/project.yaml" ]; then
  out_verbose ""
  out_verbose "[AUTO] No project.yaml found — auto-detecting language..."
  DETECT_JSON=""
  if [ -f "$LIB_DIR/detect-language.sh" ]; then
    DETECT_JSON="$(bash "$LIB_DIR/detect-language.sh" "$PROJECT_ROOT" 2>/dev/null)" || true
  fi

  if [ -n "$DETECT_JSON" ] && echo "$DETECT_JSON" | grep -q '"language"' 2>/dev/null; then
    DETECTED_LANG="$(echo "$DETECT_JSON" | sed -n 's/.*"language":"\([^"]*\)".*/\1/p')"
    if [ -n "$DETECTED_LANG" ] && [ "$DETECTED_LANG" != "null" ]; then
      out_verbose "[AUTO] Detected language: $DETECTED_LANG"
      if [ -f "$LIB_DIR/generate-project-yaml.sh" ]; then
        if [ "$DRY_RUN" = "true" ]; then
          out_verbose "[DRY-RUN] Would generate project.yaml from $DETECTED_LANG template"
        else
          bash "$LIB_DIR/generate-project-yaml.sh" \
            --json "$DETECT_JSON" \
            --repo-root "$PROJECT_ROOT" \
            --output "$PROJECT_ROOT/project.yaml"
          # Validate the generated file
          if [ -f "$LIB_DIR/validate-project-yaml.sh" ] && [ -f "$PROJECT_ROOT/project.yaml" ]; then
            out_verbose ""
            bash "$LIB_DIR/validate-project-yaml.sh" "$PROJECT_ROOT/project.yaml" || true
          fi
        fi
      else
        out_warn "generate-project-yaml.sh not found — cannot auto-generate"
      fi
    else
      out_verbose "[INFO] Could not detect language. Create project.yaml manually:"
      out_verbose "       cp .ai/governance/templates/<language>/project.yaml project.yaml"
    fi
  else
    out_verbose "[INFO] Language detection unavailable. Create project.yaml manually:"
    out_verbose "       cp .ai/governance/templates/<language>/project.yaml project.yaml"
  fi
elif [ -f "$AI_DIR/project.yaml" ] && [ ! -f "$PROJECT_ROOT/project.yaml" ]; then
  out_warn "project.yaml found at .ai/project.yaml (legacy location) — move to project root"
  out_verbose "       Move it with: mv .ai/project.yaml project.yaml"
  out_verbose "       Both locations are read; root takes precedence."
fi

# --- Deprecation warning: config.yaml without project.yaml ---
if [ -f "$AI_DIR/config.yaml" ] && [ ! -f "$PROJECT_ROOT/project.yaml" ] && [ ! -f "$AI_DIR/project.yaml" ]; then
  out_warn "config.yaml detected without project.yaml — consolidate to project.yaml"
fi
out_verbose ""

# --- Step 7: Dependency installation ---
if [ "$INSTALL_DEPS" = "true" ]; then
  source "$LIB_DIR/install-deps.sh"
else
  if [ "$PYTHON_OK" = "true" ]; then
    if [ -d "$VENV_DIR" ]; then
      log_ok "Virtual environment exists at .ai/.venv"
    else
      out_verbose "[INFO] No virtual environment found. Run with --install-deps to create one."
    fi
  fi
fi

# --- Step 8: Repository configuration ---
if [ "$PYTHON_OK" = "true" ]; then
  source "$LIB_DIR/setup-repo-config.sh"
  source "$LIB_DIR/setup-codeowners.sh"
else
  log_skip "Repository configuration requires Python for YAML parsing"
fi

# --- Step 9: MCP server / IDE configuration (opt-in) ---
if [ "$INSTALL_MCP" = "true" ]; then
  echo ""
  # Prefer the unified IDE installer (auto-detects all IDEs including Claude Desktop and JetBrains)
  IDE_INSTALL_SCRIPT="$AI_DIR/bin/install-ide.sh"
  if [ -f "$IDE_INSTALL_SCRIPT" ]; then
    echo "Configuring IDE integration (auto-detecting installed IDEs)..."
    bash "$IDE_INSTALL_SCRIPT" --governance-root "$PROJECT_ROOT"
  else
    # Fallback to legacy MCP installer (VS Code, Cursor, Claude Code only)
    MCP_INSTALL_SCRIPT="$AI_DIR/mcp-server/install.sh"
    if [ -f "$MCP_INSTALL_SCRIPT" ]; then
      echo "Installing MCP server for IDE integration..."
      if [ -f "$AI_DIR/mcp-server/dist/index.js" ]; then
        bash "$MCP_INSTALL_SCRIPT" --governance-root "$PROJECT_ROOT"
      else
        echo "  [INFO] MCP server not built. Building..."
        if command -v npm &>/dev/null; then
          (cd "$AI_DIR/mcp-server" && npm install --silent && npm run build --silent)
          bash "$MCP_INSTALL_SCRIPT" --governance-root "$PROJECT_ROOT"
        else
          echo "  [SKIP] npm not found. Install Node.js to use the MCP server."
          echo "         Then run: cd .ai/mcp-server && npm install && npm run build"
          echo "         Then run: bash .ai/mcp-server/install.sh --governance-root ."
        fi
      fi
    else
      echo "  [SKIP] MCP server install script not found"
    fi
  fi
fi

# --- Done ---
if [ "$REFRESH_MODE" = "true" ]; then
  output_summary_end
  out_summary "Refresh complete."
else
  output_summary_end
  # Compact post-install message (default verbosity)
  if [ "${VERBOSITY:-1}" -le 1 ]; then
    echo ""
    echo "Done. Governance is active."
    echo ""
    echo "  Verify:  bash .ai/bin/init.sh --verify"
    echo "  Guide:   docs/guides/developer-quickstart.md"
    echo ""
    echo "  Open a PR to see governance in action."
  else
    # Verbose next-steps (--verbose or --debug)
    echo ""
    echo "Done."
    echo ""
    echo "Next steps:"
    if [ "$INSTALL_DEPS" = "false" ] && [ ! -d "$VENV_DIR" ]; then
      echo "  0. Install dependencies:     bash .ai/bin/init.sh --install-deps"
    fi
    if [ -f "$PROJECT_ROOT/project.yaml" ]; then
      echo "  1. Review generated project.yaml and customize for your project"
      echo "  2. Validate configuration:   bash .ai/bin/init.sh --validate"
    else
      echo "  1. Copy a language template:  cp .ai/governance/templates/<language>/project.yaml project.yaml"
      echo "     Or re-run init.sh — it will auto-detect your language and generate one"
      echo "  2. Customize personas and conventions in project.yaml"
    fi
    echo "  3. Set governance profile:    governance.policy_profile: default"
    if [ "$INSTALL_MCP" = "false" ]; then
      echo "  4. Install MCP server:       bash .ai/bin/init.sh --mcp"
    fi
    if [ -d "$VENV_DIR" ]; then
      echo ""
      echo "To activate the virtual environment:"
      echo "  source .ai/.venv/bin/activate"
    fi
  fi
fi
