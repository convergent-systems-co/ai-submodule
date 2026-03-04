#!/usr/bin/env bash
set -euo pipefail
# sync-paved-roads.sh — Regenerate paved-roads-catalog.yaml from GitHub API
# Usage: bash bin/sync-paved-roads.sh [--dry-run]

echo "Fetching repos from JM-Paved-Roads org..."
gh repo list JM-Paved-Roads --json name,description,updatedAt --limit 200 --jq '.[] | "\(.name)\t\(.description // "")\t\(.updatedAt)"'
echo "Done. Manual curation needed to update governance/paved-roads-catalog.yaml"
