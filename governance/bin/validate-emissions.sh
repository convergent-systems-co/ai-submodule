#!/bin/bash
# governance/bin/validate-emissions.sh — Validate required panel emissions have baseline files.
# Only runs in submodule context.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
resolve_ai_dir

PYTHON_CMD="${PYTHON_CMD:-}"

echo ""
echo "Validating panel emissions..."
EMISSIONS_DIR="$AI_DIR/governance/emissions"

# Read required panels from active policy profile
if [ -n "$PYTHON_CMD" ]; then
  DYNAMIC_PANELS=$("$PYTHON_CMD" -c "
import yaml, os, sys

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

config = {}
for f in sys.argv[1:]:
    if os.path.exists(f):
        with open(f) as fh:
            data = yaml.safe_load(fh) or {}
            config = deep_merge(config, data)

profile_name = config.get('governance', {}).get('policy_profile', 'default')
ai_dir = sys.argv[1].rsplit('/', 1)[0]
profile_path = os.path.join(ai_dir, 'governance', 'policy', profile_name + '.yaml')
if os.path.exists(profile_path):
    with open(profile_path) as fh:
        profile = yaml.safe_load(fh) or {}
    panels = profile.get('required_panels', [])
    if panels:
        print(' '.join(panels))
        sys.exit(0)
print('code-review security-review threat-modeling cost-analysis documentation-review data-governance-review')
" "$AI_DIR/config.yaml" "$AI_DIR/project.yaml" "$PROJECT_ROOT/project.yaml" 2>&1)
  PANEL_EXIT=$?
  if [ $PANEL_EXIT -eq 0 ] && [ -n "$DYNAMIC_PANELS" ]; then
    REQUIRED_PANELS="$DYNAMIC_PANELS"
  else
    log_warn "Could not read panels from policy profile, using defaults"
    if [ -n "$DYNAMIC_PANELS" ]; then
      echo "  $DYNAMIC_PANELS" >&2
    fi
    REQUIRED_PANELS="code-review security-review threat-modeling cost-analysis documentation-review data-governance-review"
  fi
else
  REQUIRED_PANELS="code-review security-review threat-modeling cost-analysis documentation-review data-governance-review"
fi

MISSING_PANELS=""
for panel in $REQUIRED_PANELS; do
  if [ ! -f "$EMISSIONS_DIR/${panel}.json" ]; then
    MISSING_PANELS="$MISSING_PANELS $panel"
  fi
done

if [ -n "$MISSING_PANELS" ]; then
  log_warn "Missing required panel emissions:$MISSING_PANELS"
  echo "         The governance workflow will block PRs until these panels have emissions."
  echo "         See governance/policy/default.yaml for required panel definitions."
else
  log_ok "All required panel emissions present"
fi
