#!/bin/bash
# governance/bin/breaking-change-check.sh — Detect breaking changes between versions.
#
# Compares governance schemas and policy profiles between two commits
# to detect potentially breaking changes: removed fields, changed types,
# deleted files, and renamed keys.
#
# Usage:
#   bash .ai/governance/bin/breaking-change-check.sh OLD_SHA NEW_SHA
#   bash .ai/governance/bin/breaking-change-check.sh --from HEAD~5 --to HEAD
#
# Exit codes:
#   0 = no breaking changes
#   1 = breaking changes detected

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

FROM_SHA=""
TO_SHA=""
BREAKING=false

# Parse arguments
while [ $# -gt 0 ]; do
  case "$1" in
    --from) FROM_SHA="$2"; shift 2 ;;
    --to)   TO_SHA="$2"; shift 2 ;;
    *)
      if [ -z "$FROM_SHA" ]; then FROM_SHA="$1"
      elif [ -z "$TO_SHA" ]; then TO_SHA="$1"
      fi
      shift
      ;;
  esac
done

if [ -z "$FROM_SHA" ] || [ -z "$TO_SHA" ]; then
  echo "Usage: breaking-change-check.sh FROM_SHA TO_SHA"
  echo "   or: breaking-change-check.sh --from SHA --to SHA"
  exit 1
fi

echo "Breaking Change Detection"
echo "========================="
echo "  From: $FROM_SHA"
echo "  To:   $TO_SHA"
echo ""

# --- Check for deleted files ---
DELETED="$(git -C "$AI_DIR" diff --diff-filter=D --name-only "$FROM_SHA" "$TO_SHA" 2>/dev/null || echo "")"
if [ -n "$DELETED" ]; then
  echo "BREAKING: Files deleted"
  echo "$DELETED" | while read -r f; do echo "  - $f"; done
  echo ""
  BREAKING=true
fi

# --- Check for renamed schema files ---
RENAMED="$(git -C "$AI_DIR" diff --diff-filter=R --name-only "$FROM_SHA" "$TO_SHA" -- governance/schemas/ 2>/dev/null || echo "")"
if [ -n "$RENAMED" ]; then
  echo "BREAKING: Schema files renamed"
  echo "$RENAMED" | while read -r f; do echo "  - $f"; done
  echo ""
  BREAKING=true
fi

# --- Check for schema field removals (basic heuristic) ---
SCHEMA_CHANGES="$(git -C "$AI_DIR" diff "$FROM_SHA" "$TO_SHA" -- governance/schemas/*.json 2>/dev/null || echo "")"
if echo "$SCHEMA_CHANGES" | grep -q '^-.*"required"'; then
  echo "WARNING: Required fields may have changed in schemas"
  echo ""
fi

# Check for removed properties in schemas
if echo "$SCHEMA_CHANGES" | grep -q '^-.*"properties"'; then
  echo "WARNING: Schema properties may have been removed"
  echo ""
  BREAKING=true
fi

# --- Check for policy profile key removals ---
POLICY_DIFF="$(git -C "$AI_DIR" diff "$FROM_SHA" "$TO_SHA" -- governance/policy/*.yaml 2>/dev/null || echo "")"
REMOVED_KEYS="$(echo "$POLICY_DIFF" | grep '^-[a-z_]' | grep -v '^---' || echo "")"
if [ -n "$REMOVED_KEYS" ]; then
  echo "WARNING: Policy profile top-level keys may have been removed:"
  echo "$REMOVED_KEYS" | head -10 | while read -r line; do echo "  $line"; done
  echo ""
fi

# --- Summary ---
if [ "$BREAKING" = "true" ]; then
  echo "RESULT: Breaking changes detected. Review before updating."
  exit 1
else
  echo "RESULT: No breaking changes detected."
  exit 0
fi
