#!/bin/bash
# governance/bin/detect-language.sh — Detect primary language of a consuming repo.
#
# Scans the repo root (not .ai/) for language indicator files and outputs
# a JSON object with the detected language, framework hint, and indicators found.
#
# Compatible with Bash 3.2+ (macOS default).
#
# Usage:
#   bash .ai/governance/bin/detect-language.sh [REPO_ROOT]
#
# Output (stdout):
#   {"language":"python","framework":null,"indicators":["pyproject.toml","requirements.txt"]}
#
# Exit codes:
#   0 — language detected
#   1 — no language detected

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source common library if available (for logging)
if [ -f "$SCRIPT_DIR/lib/common.sh" ]; then
  source "$SCRIPT_DIR/lib/common.sh"
fi

# --- Resolve repo root ---
REPO_ROOT="${1:-}"
if [ -z "$REPO_ROOT" ]; then
  if [ -n "${AI_DIR:-}" ]; then
    REPO_ROOT="$(dirname "$AI_DIR")"
  elif git rev-parse --is-inside-work-tree &>/dev/null; then
    REPO_ROOT="$(git rev-parse --show-toplevel)"
  else
    echo '{"language":null,"framework":null,"indicators":[],"error":"not a git repository"}' >&2
    exit 1
  fi
fi

# --- Per-language score tracking (Bash 3.2 compatible) ---
# Instead of associative arrays, use individual variables per language.
score_node=0;    indicators_node="";    framework_node=""
score_python=0;  indicators_python="";  framework_python=""
score_go=0;      indicators_go="";      framework_go=""
score_java=0;    indicators_java="";    framework_java=""
score_csharp=0;  indicators_csharp="";  framework_csharp=""
score_bicep=0;   indicators_bicep="";   framework_bicep=""
score_terraform=0; indicators_terraform=""; framework_terraform=""
score_html=0;    indicators_html="";    framework_html=""
score_markdownjson=0; indicators_markdownjson=""; framework_markdownjson=""

# Add an indicator to a language's score
# Usage: add_score <varprefix> <indicator_file>
add_score() {
  local prefix="$1"
  local file="$2"
  local cur_score cur_ind
  eval "cur_score=\${score_${prefix}}"
  eval "cur_ind=\${indicators_${prefix}}"
  eval "score_${prefix}=$(( cur_score + 1 ))"
  if [ -n "$cur_ind" ]; then
    eval "indicators_${prefix}=\"${cur_ind},${file}\""
  else
    eval "indicators_${prefix}=\"${file}\""
  fi
}

set_fw() {
  local prefix="$1"
  local fw="$2"
  eval "framework_${prefix}=\"${fw}\""
}

check_file() {
  local prefix="$1"
  local file="$2"
  if [ -f "$REPO_ROOT/$file" ]; then
    add_score "$prefix" "$file"
  fi
}

check_glob() {
  local prefix="$1"
  local pattern="$2"
  local match
  match=$(find "$REPO_ROOT" -maxdepth 2 -name "$pattern" \
    -not -path "*/.ai/*" -not -path "*/node_modules/*" -not -path "*/.git/*" \
    2>/dev/null | head -1) || true
  if [ -n "$match" ]; then
    add_score "$prefix" "$(basename "$match")"
  fi
}

# --- Node / TypeScript ---
check_file "node" "package.json"
check_file "node" "tsconfig.json"
check_file "node" "package-lock.json"
check_file "node" "pnpm-lock.yaml"
check_file "node" "yarn.lock"

# React / Next.js / Express detection
if [ -f "$REPO_ROOT/package.json" ]; then
  if grep -q '"react"' "$REPO_ROOT/package.json" 2>/dev/null; then
    set_fw "node" "react"
  elif grep -q '"next"' "$REPO_ROOT/package.json" 2>/dev/null; then
    set_fw "node" "nextjs"
  elif grep -q '"express"' "$REPO_ROOT/package.json" 2>/dev/null; then
    set_fw "node" "express"
  fi
fi

# --- Python ---
check_file "python" "requirements.txt"
check_file "python" "pyproject.toml"
check_file "python" "setup.py"
check_file "python" "setup.cfg"
check_file "python" "Pipfile"
check_file "python" "poetry.lock"

# Python framework detection
if [ -f "$REPO_ROOT/pyproject.toml" ]; then
  if grep -q 'django' "$REPO_ROOT/pyproject.toml" 2>/dev/null; then
    set_fw "python" "django"
  elif grep -q 'fastapi' "$REPO_ROOT/pyproject.toml" 2>/dev/null; then
    set_fw "python" "fastapi"
  elif grep -q 'flask' "$REPO_ROOT/pyproject.toml" 2>/dev/null; then
    set_fw "python" "flask"
  fi
fi

# --- Go ---
check_file "go" "go.mod"
check_file "go" "go.sum"

# --- Java ---
check_file "java" "pom.xml"
check_file "java" "build.gradle"
check_file "java" "build.gradle.kts"
check_file "java" "gradlew"

# Java framework detection
if [ -f "$REPO_ROOT/pom.xml" ]; then
  if grep -q 'spring-boot' "$REPO_ROOT/pom.xml" 2>/dev/null; then
    set_fw "java" "spring-boot"
  fi
elif [ -f "$REPO_ROOT/build.gradle" ]; then
  if grep -q 'spring-boot' "$REPO_ROOT/build.gradle" 2>/dev/null; then
    set_fw "java" "spring-boot"
  fi
fi

# --- C# / .NET ---
check_glob "csharp" "*.csproj"
check_glob "csharp" "*.sln"
check_file "csharp" "global.json"
check_file "csharp" "Directory.Build.props"

# --- Bicep ---
check_glob "bicep" "*.bicep"
check_file "bicep" "bicepconfig.json"

# --- Terraform ---
check_glob "terraform" "*.tf"
check_file "terraform" ".terraform.lock.hcl"

# --- HTML (static site) ---
check_file "html" "index.html"

# --- Markdown/JSON (docs-only / governance) ---
if [ -f "$REPO_ROOT/mkdocs.yml" ] || [ -f "$REPO_ROOT/docusaurus.config.js" ]; then
  add_score "markdownjson" "mkdocs.yml"
fi

# --- Pick primary language (highest score) ---
best_lang=""
best_score=0
best_prefix=""

for entry in \
  "node:$score_node" \
  "python:$score_python" \
  "go:$score_go" \
  "java:$score_java" \
  "csharp:$score_csharp" \
  "bicep:$score_bicep" \
  "terraform:$score_terraform" \
  "html:$score_html" \
  "markdown-json:$score_markdownjson"; do
  lang="${entry%%:*}"
  score="${entry##*:}"
  if [ "$score" -gt "$best_score" ]; then
    best_score=$score
    best_lang=$lang
    # Map lang name to variable prefix
    case "$lang" in
      markdown-json) best_prefix="markdownjson" ;;
      *) best_prefix="$lang" ;;
    esac
  fi
done

# --- Map node to react template if React detected ---
template_lang="$best_lang"
if [ "$best_lang" = "node" ]; then
  if [ "$framework_node" = "react" ] || [ "$framework_node" = "nextjs" ]; then
    template_lang="react"
  fi
fi

# --- Output JSON ---
if [ -z "$best_lang" ]; then
  echo '{"language":null,"framework":null,"indicators":[]}'
  exit 1
fi

# Get framework and indicators for best language
eval "framework=\${framework_${best_prefix}}"
eval "raw_indicators=\${indicators_${best_prefix}}"

if [ -n "$framework" ]; then
  framework_json="\"$framework\""
else
  framework_json="null"
fi

# Build indicators JSON array
indicators_json=""
IFS=',' read -r -a indicator_arr <<< "$raw_indicators"
for ind in "${indicator_arr[@]}"; do
  if [ -n "$indicators_json" ]; then
    indicators_json="$indicators_json,\"$ind\""
  else
    indicators_json="\"$ind\""
  fi
done

echo "{\"language\":\"$template_lang\",\"framework\":$framework_json,\"indicators\":[$indicators_json]}"
exit 0
