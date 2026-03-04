"""Centralized path constants for the governance platform.

All transient runtime outputs go under ARTIFACTS_DIR (.artifacts/).
All committed source lives under governance/.
Every module that needs paths should import from here.
"""

# --- Artifacts (transient runtime outputs) ---
ARTIFACTS_DIR = ".artifacts"
PLANS_DIR = f"{ARTIFACTS_DIR}/plans"
PANELS_DIR = f"{ARTIFACTS_DIR}/panels"
EMISSIONS_DIR = f"{ARTIFACTS_DIR}/emissions"
CHECKPOINTS_DIR = f"{ARTIFACTS_DIR}/checkpoints"
STATE_DIR = f"{ARTIFACTS_DIR}/state"
SESSION_DIR = f"{STATE_DIR}/sessions"
LOGS_DIR = f"{ARTIFACTS_DIR}/logs"
WORKTREES_DIR = f"{ARTIFACTS_DIR}/worktrees"
VENDOR_ENGINE_DIR = f"{ARTIFACTS_DIR}/engine"

# --- Legacy paths (for migration support) ---
LEGACY_ARTIFACTS_DIR = ".governance"
LEGACY_WORKTREES_DIR = ".claude/worktrees"

# --- Governance source ---
TEMPLATES_DIR = "governance/templates"
LANGUAGE_TEMPLATES_DIR = f"{TEMPLATES_DIR}/languages"
PROMPT_TEMPLATES_DIR = f"{TEMPLATES_DIR}/prompts"
COMMANDS_DIR = "governance/commands"
