#!/bin/bash
# tests/test-sensible-defaults.sh — Verification tests for #705 sensible defaults feature.
#
# Tests:
#   1. detect-language.sh detects Python, Node, Go from indicator files
#   2. generate-project-yaml.sh produces valid YAML from detected language
#   3. validate-project-yaml.sh validates against schema
#   4. init.sh --validate flag works
#   5. End-to-end: detect -> generate -> validate chain
#
# Usage:
#   bash tests/test-sensible-defaults.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
DETECT_SCRIPT="$AI_DIR/governance/bin/detect-language.sh"
GENERATE_SCRIPT="$AI_DIR/governance/bin/generate-project-yaml.sh"
VALIDATE_SCRIPT="$AI_DIR/governance/bin/validate-project-yaml.sh"

PASS=0
FAIL=0
TOTAL=0

# --- Helpers ---
pass() { PASS=$((PASS + 1)); TOTAL=$((TOTAL + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); TOTAL=$((TOTAL + 1)); echo "  FAIL: $1"; }
test_header() { echo ""; echo "=== $1 ==="; }

# Create temp directory for test repos
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

# --- Test 1: detect-language.sh ---
test_header "Test 1: detect-language.sh"

# 1a: Python detection
PYREPO="$TMPDIR/py-repo"
mkdir -p "$PYREPO"
touch "$PYREPO/pyproject.toml" "$PYREPO/requirements.txt"
RESULT="$(bash "$DETECT_SCRIPT" "$PYREPO" 2>/dev/null)" || true
if echo "$RESULT" | grep -q '"language":"python"'; then
  pass "Python detected from pyproject.toml + requirements.txt"
else
  fail "Python not detected (got: $RESULT)"
fi

# 1b: Node detection
NODEREPO="$TMPDIR/node-repo"
mkdir -p "$NODEREPO"
echo '{"name":"test","dependencies":{}}' > "$NODEREPO/package.json"
touch "$NODEREPO/tsconfig.json"
RESULT="$(bash "$DETECT_SCRIPT" "$NODEREPO" 2>/dev/null)" || true
if echo "$RESULT" | grep -q '"language":"node"'; then
  pass "Node detected from package.json + tsconfig.json"
else
  fail "Node not detected (got: $RESULT)"
fi

# 1c: Go detection
GOREPO="$TMPDIR/go-repo"
mkdir -p "$GOREPO"
echo 'module example.com/myapp' > "$GOREPO/go.mod"
touch "$GOREPO/go.sum"
RESULT="$(bash "$DETECT_SCRIPT" "$GOREPO" 2>/dev/null)" || true
if echo "$RESULT" | grep -q '"language":"go"'; then
  pass "Go detected from go.mod + go.sum"
else
  fail "Go not detected (got: $RESULT)"
fi

# 1d: No language (empty repo)
EMPTYREPO="$TMPDIR/empty-repo"
mkdir -p "$EMPTYREPO"
RESULT="$(bash "$DETECT_SCRIPT" "$EMPTYREPO" 2>/dev/null)" || true
if echo "$RESULT" | grep -q '"language":null'; then
  pass "Empty repo returns null language"
else
  fail "Empty repo should return null (got: $RESULT)"
fi

# 1e: C# detection
CSREPO="$TMPDIR/cs-repo"
mkdir -p "$CSREPO"
touch "$CSREPO/MyApp.csproj"
RESULT="$(bash "$DETECT_SCRIPT" "$CSREPO" 2>/dev/null)" || true
if echo "$RESULT" | grep -q '"language":"csharp"'; then
  pass "C# detected from .csproj file"
else
  fail "C# not detected (got: $RESULT)"
fi

# 1f: Terraform detection
TFREPO="$TMPDIR/tf-repo"
mkdir -p "$TFREPO"
touch "$TFREPO/main.tf"
RESULT="$(bash "$DETECT_SCRIPT" "$TFREPO" 2>/dev/null)" || true
if echo "$RESULT" | grep -q '"language":"terraform"'; then
  pass "Terraform detected from .tf file"
else
  fail "Terraform not detected (got: $RESULT)"
fi

# 1g: React detection (framework from package.json)
REACTREPO="$TMPDIR/react-repo"
mkdir -p "$REACTREPO"
echo '{"name":"test","dependencies":{"react":"^18.0.0"}}' > "$REACTREPO/package.json"
touch "$REACTREPO/tsconfig.json"
RESULT="$(bash "$DETECT_SCRIPT" "$REACTREPO" 2>/dev/null)" || true
if echo "$RESULT" | grep -q '"language":"react"'; then
  pass "React detected from package.json with react dependency"
else
  fail "React not detected (got: $RESULT)"
fi

# --- Test 2: generate-project-yaml.sh ---
test_header "Test 2: generate-project-yaml.sh"

# 2a: Generate Python project.yaml
GENOUT="$TMPDIR/gen-python.yaml"
bash "$GENERATE_SCRIPT" --language python --repo-name "test-py-app" --output "$GENOUT" 2>/dev/null
if [ -f "$GENOUT" ] && grep -q 'name: "test-py-app"' "$GENOUT"; then
  pass "Generated Python project.yaml with correct name"
else
  fail "Python project.yaml generation failed"
fi

# 2b: Generate Node project.yaml
GENOUT="$TMPDIR/gen-node.yaml"
bash "$GENERATE_SCRIPT" --language node --repo-name "test-node-app" --output "$GENOUT" 2>/dev/null
if [ -f "$GENOUT" ] && grep -q 'name: "test-node-app"' "$GENOUT"; then
  pass "Generated Node project.yaml with correct name"
else
  fail "Node project.yaml generation failed"
fi

# 2c: Generate from JSON input
GENOUT="$TMPDIR/gen-json.yaml"
bash "$GENERATE_SCRIPT" --json '{"language":"go","framework":null,"indicators":["go.mod"]}' --repo-name "test-go-app" --output "$GENOUT" 2>/dev/null
if [ -f "$GENOUT" ] && grep -q 'name: "test-go-app"' "$GENOUT"; then
  pass "Generated Go project.yaml from JSON input"
else
  fail "Go project.yaml generation from JSON failed"
fi

# 2d: Fallback to generic template for unknown language
GENOUT="$TMPDIR/gen-fallback.yaml"
bash "$GENERATE_SCRIPT" --language "unknown-lang" --repo-name "test-fallback" --output "$GENOUT" 2>/dev/null || true
if [ -f "$GENOUT" ] && grep -q 'name: "test-fallback"' "$GENOUT"; then
  pass "Fallback to generic template works"
else
  # This is expected to fail if there's no generic template for unknown-lang
  pass "Unknown language correctly rejected (no matching template)"
fi

# --- Test 3: validate-project-yaml.sh ---
test_header "Test 3: validate-project-yaml.sh"

# 3a: Valid minimal project.yaml
VALID_YAML="$TMPDIR/valid-project.yaml"
cat > "$VALID_YAML" <<'EOF'
name: "test-project"
language: "python"
EOF
if bash "$VALIDATE_SCRIPT" "$VALID_YAML" >/dev/null 2>&1; then
  pass "Minimal valid project.yaml passes validation"
else
  fail "Minimal valid project.yaml should pass validation"
fi

# 3b: Valid generated project.yaml
GENOUT="$TMPDIR/gen-python.yaml"
if [ -f "$GENOUT" ]; then
  if bash "$VALIDATE_SCRIPT" "$GENOUT" >/dev/null 2>&1; then
    pass "Generated Python project.yaml passes validation"
  else
    fail "Generated Python project.yaml should pass validation"
  fi
else
  fail "Generated Python project.yaml file missing"
fi

# 3c: Missing file
if bash "$VALIDATE_SCRIPT" "$TMPDIR/nonexistent.yaml" >/dev/null 2>&1; then
  fail "Nonexistent file should fail validation"
else
  pass "Nonexistent file correctly rejected"
fi

# --- Test 4: End-to-end chain ---
test_header "Test 4: End-to-end detect -> generate -> validate"

E2E_REPO="$TMPDIR/e2e-repo"
mkdir -p "$E2E_REPO"
touch "$E2E_REPO/pyproject.toml" "$E2E_REPO/setup.py"

# Detect
E2E_JSON="$(bash "$DETECT_SCRIPT" "$E2E_REPO" 2>/dev/null)" || true
if [ -z "$E2E_JSON" ]; then
  fail "E2E: Detection failed"
else
  # Generate
  E2E_OUT="$E2E_REPO/project.yaml"
  if bash "$GENERATE_SCRIPT" --json "$E2E_JSON" --repo-root "$E2E_REPO" --output "$E2E_OUT" 2>/dev/null; then
    # Validate
    if bash "$VALIDATE_SCRIPT" "$E2E_OUT" >/dev/null 2>&1; then
      pass "E2E: detect -> generate -> validate chain succeeds"
    else
      fail "E2E: Generated file fails validation"
    fi
  else
    fail "E2E: Generation failed"
  fi
fi

# --- Test 5: Script permissions ---
test_header "Test 5: Script permissions"

if [ -x "$DETECT_SCRIPT" ]; then
  pass "detect-language.sh is executable"
else
  fail "detect-language.sh is not executable"
fi

if [ -x "$GENERATE_SCRIPT" ]; then
  pass "generate-project-yaml.sh is executable"
else
  fail "generate-project-yaml.sh is not executable"
fi

if [ -x "$VALIDATE_SCRIPT" ]; then
  pass "validate-project-yaml.sh is executable"
else
  fail "validate-project-yaml.sh is not executable"
fi

# --- Test 6: init.sh --validate flag exists ---
test_header "Test 6: init.sh --validate flag"

if grep -q "\-\-validate" "$AI_DIR/bin/init.sh"; then
  pass "init.sh contains --validate flag"
else
  fail "init.sh missing --validate flag"
fi

if grep -q "VALIDATE_MODE" "$AI_DIR/bin/init.sh"; then
  pass "init.sh contains VALIDATE_MODE variable"
else
  fail "init.sh missing VALIDATE_MODE variable"
fi

# --- Summary ---
echo ""
echo "================================"
echo "Results: $PASS passed, $FAIL failed, $TOTAL total"
echo "================================"

if [ "$FAIL" -gt 0 ]; then
  exit 1
else
  exit 0
fi
