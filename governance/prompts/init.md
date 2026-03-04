# Init: Agentic Bootstrap Prompt

Execute this prompt to bootstrap the `.ai` governance submodule in a consuming project. This is the agentic equivalent of `bash .ai/bin/init.sh` — it walks the user through setup interactively, asking about configuration options.

**When to use this:** After adding the Dark Forge submodule to a project (`git submodule add git@github.com:convergent-systems-co/dark-forge.git .ai`), run this prompt to configure the project.

**Canonical implementation:** This prompt is the primary bootstrap method. Shell scripts in `bin/` are utilities for specific operations (e.g., `--check-branch-protection`, `--verify`). If this prompt and the shell scripts diverge, this prompt is authoritative for interactive setup.

---

## Pre-flight Checks

Before starting, verify the environment:

1. **Confirm `.ai` submodule exists:**
   ```bash
   test -d .ai/governance && echo "OK" || echo "MISSING"
   ```
   If MISSING: The `.ai` submodule has not been added yet. Run:
   ```bash
   git submodule add git@github.com:convergent-systems-co/dark-forge.git .ai
   git submodule update --init --recursive
   ```
   Then re-run this prompt.

2. **Check if already initialized** (instruction files exist):
   ```bash
   test -s CLAUDE.md && echo "CLAUDE.md exists" || echo "Not initialized"
   test -s .github/copilot-instructions.md && echo "copilot-instructions exists" || echo "Not initialized"
   ```
   If both files exist and contain the ANCHOR marker, skip to Step 3 (Repository Configuration) — the project may already be initialized but need configuration updates.

3. **Detect platform:**
   ```bash
   uname -s
   ```

---

## Step 1: Interactive Project Configuration

If `project.yaml` already exists in the project root, ask: "A `project.yaml` already exists. Do you want to reconfigure it? (yes/no, default: no)". If no, skip to Step 2.

Otherwise, walk the user through the following 5-group questionnaire. Present one group at a time and wait for answers before proceeding. For each question, show the default in parentheses — if the user presses Enter or says "default", use the default value.

### Group 1 — Project Identity

Ask the user these questions:

1. **Project name** — "What is the project name?" (default: the repository name, detected via `basename $(git rev-parse --show-toplevel)`)
2. **Primary language** — "What is the primary language?"
   - `python` | `typescript` | `go` | `java` | `csharp` | `rust` | `bicep` | `terraform`
   - (default: detect from files — `pyproject.toml` / `setup.py` → python, `package.json` → typescript, `go.mod` → go, `*.csproj` / `*.sln` → csharp, `main.bicep` → bicep, `main.tf` → terraform)
3. **Framework** — "What framework are you using, if any?"
   - Language-specific suggestions:
     - Python: `fastapi`, `django`, `flask`, `cli`, or `none`
     - TypeScript: `express`, `fastify`, `nestjs`, `hono`, or `none`
     - React/TypeScript: `react`, `nextjs`, `remix`, or `none`
     - Go: `chi`, `gin`, `echo`, `stdlib`, or `none`
     - C#: `aspnetcore`, `minimal-api`, `blazor`, `console`, or `none`
     - Bicep: `standalone`, `aks`, `app-service`, `container-apps`, or `none`
     - Terraform: `azure`, `aws`, `gcp`, `multi-cloud`, or `none`
   - (default: `none`)

### Group 2 — Governance

Ask the user these questions:

1. **Policy profile** — "Which policy profile should this project use?"
   - `default` — Balanced automation with human oversight; suitable for most internal applications
   - `fast-track` — Lightweight profile for trivial changes (docs, typos, chores); reduced ceremony
   - `fin_pii_high` — Strict compliance for financial/PII data; SOC2, PCI-DSS, HIPAA, GDPR contexts
   - `infrastructure_critical` — Emphasizes production stability and blast radius for IaC/platform repos
   - `reduced_touchpoint` — Near-full autonomy; human review only for overrides and security-critical findings
   - (default: `default`)
2. **Parallel coders** — "How many parallel Coder agents should run during dispatch?" (1-10, or -1 for unlimited; default: `5`)
3. **Project Manager mode** — "Enable Project Manager mode? PM orchestrates Tech Leads who each manage Coders." (yes/no; default: `no`)
4. **If PM mode is yes** — "How many parallel Tech Leads?" (1-5; default: `3`)

### Group 3 — Conventions

Ask the user these questions:

1. **Commit style** — "What commit message style?"
   - `conventional` — e.g., `feat:`, `fix:`, `refactor:`, `docs:` (recommended)
   - `freeform` — No enforced format
   - (default: `conventional`)
2. **PR template** — "Generate a PR template?" (yes/no; default: `yes`)

### Group 4 — Git

Ask the user this question:

1. **Branch naming pattern** — "What branch naming pattern should be used?"
   - Placeholders: `{network_id}` = your network ID, `{type}` = feat/fix/chore, `{number}` = issue number, `{name}` = short description
   - (default: `{network_id}/{type}/{number}/{name}`)

### Group 5 — Repository

Ask the user these questions:

1. **Auto-merge** — "Enable auto-merge? PRs merge automatically when all checks pass." (yes/no; default: `no`)
2. **CODEOWNERS** — "Generate a CODEOWNERS file?" (yes/no; default: `no`)
   - If yes: "Who should be the default code owner? (e.g., `@your-org/your-team`)"

---

### Language-Specific Convention Defaults

After collecting answers, apply language-specific convention defaults based on the primary language selected in Group 1. Use these as the `conventions` section of `project.yaml`. The user does not need to answer these — they come from the language template.

**Python:**
```yaml
conventions:
  testing:
    framework: "pytest"
    naming: "test_*"
    coverage_target: 80
  style:
    max_line_length: 100
    indent: "spaces"
    indent_size: 4
    linter: "ruff"
    formatter: "ruff format"
    type_checker: "mypy"
  tooling:
    package_manager: "uv"
    min_python: "3.11"
```

**TypeScript / Node:**
```yaml
conventions:
  testing:
    framework: "vitest"
    naming: "describe/it"
    coverage_target: 80
  style:
    max_line_length: 100
    indent: "spaces"
    indent_size: 2
    linter: "eslint"
    formatter: "prettier"
    module_system: "esm"
  tooling:
    package_manager: "pnpm"
    runtime: "node22"
```

**Go:**
```yaml
conventions:
  testing:
    framework: "go test"
    naming: "TestFunctionName_Scenario"
    pattern: "table-driven"
    coverage_target: 80
  style:
    formatter: "gofmt"
    linter: "golangci-lint"
    indent: "tabs"
```

**C#:**
```yaml
conventions:
  testing:
    framework: "xunit"
    assertions: "fluentassertions"
    naming: "MethodName_Scenario_Expected"
    coverage_target: 80
  style:
    max_line_length: 120
    indent: "spaces"
    indent_size: 4
    nullable: true
```

**Java:**
```yaml
conventions:
  testing:
    framework: "junit5"
    naming: "shouldDoSomething_whenCondition"
    coverage_target: 80
  style:
    max_line_length: 120
    indent: "spaces"
    indent_size: 4
    linter: "checkstyle"
    formatter: "google-java-format"
```

**Rust:**
```yaml
conventions:
  testing:
    framework: "cargo test"
    naming: "test_function_name"
    coverage_target: 80
  style:
    formatter: "rustfmt"
    linter: "clippy"
    indent: "spaces"
    indent_size: 4
```

**Bicep:**
```yaml
conventions:
  style:
    indent: "spaces"
    indent_size: 2
    naming: "camelCase"
    resource_naming: "kebab-case"
  testing:
    framework: "bicep-test"
    what_if: true
    linter: "bicep linter"
```

**Terraform:**
```yaml
conventions:
  style:
    indent: "spaces"
    indent_size: 2
    naming: "snake_case"
    resource_naming: "kebab-case"
  testing:
    framework: "terraform test"
    validate: true
    linter: "tflint"
    security_scanner: "tfsec"
```

For languages not listed above, use minimal defaults:
```yaml
conventions:
  testing:
    coverage_target: 80
  style:
    indent: "spaces"
    indent_size: 2
  git:
    commit_style: "conventional"
    pr_template: true
```

---

### Validation and Output

After collecting all answers:

1. **Validate** — Check answers against schema constraints:
   - `governance.parallel_coders` must be an integer, -1 to 10
   - `governance.parallel_tech_leads` must be an integer, 1 to 5
   - `governance.policy_profile` must be one of: `default`, `fast-track`, `fin_pii_high`, `infrastructure_critical`, `reduced_touchpoint`
   - `conventions.git.commit_style` must be `conventional` or `freeform`
   - If any answer is invalid, tell the user and re-ask that specific question

2. **Write `project.yaml`** — Generate the complete file in the project root using the collected answers and language-specific defaults. Structure:
   ```yaml
   # Project AI Configuration — generated by init.md

   name: "<project_name>"
   language: "<language>"
   framework: <framework_or_null>

   governance:
     policy_profile: "<profile>"
     parallel_coders: <N>
     use_project_manager: <true|false>
     # parallel_tech_leads: <N>  # only include if use_project_manager is true

   repository:
     auto_merge: <true|false>
     codeowners:
       enabled: <true|false>
       # default_owner: "<owner>"  # only include if codeowners enabled

   conventions:
     # ... language-specific defaults from above ...
     git:
       branch_pattern: "<pattern>"
       commit_style: "<style>"
       pr_template: <true|false>
   ```

3. **Run installation** — After writing `project.yaml`:
   ```bash
   bash .ai/bin/init.sh --install-deps
   ```

4. **Verify** — Confirm the installation:
   ```bash
   bash .ai/bin/init.sh --verify
   ```

5. **Print summary** — Show the user what was configured:
   ```
   project.yaml generated with:
     - Project: <name> (<language>/<framework>)
     - Policy profile: <profile>
     - Parallel coders: <N>
     - PM mode: <enabled/disabled>
     - Commit style: <style>
     - Branch pattern: <pattern>
     - Auto-merge: <yes/no>
     - CODEOWNERS: <yes/no>
   ```

---

## Step 2: Install Instructions

Write instruction files directly (not symlinks) to each AI tool's expected location. Direct files are more portable across platforms and avoid symlink resolution issues.

1. **Read the source content:**
   ```bash
   cat .ai/instructions.md
   ```

2. **Write CLAUDE.md** (Claude Code):
   - If `CLAUDE.md` is a symlink, migrate it: read the target content, remove the symlink, write the file
     ```bash
     if [ -L CLAUDE.md ]; then
       content=$(cat CLAUDE.md)
       rm CLAUDE.md
       echo "$content" > CLAUDE.md
       echo "Migrated CLAUDE.md from symlink to file"
     fi
     ```
   - If `CLAUDE.md` does not exist or is empty, write the content from `.ai/instructions.md`
   - If `CLAUDE.md` exists as a regular file with content, check if it matches source; update if stale

3. **Write .github/copilot-instructions.md** (GitHub Copilot):
   ```bash
   mkdir -p .github
   ```
   - Apply the same symlink migration and content write logic as CLAUDE.md
   - If a symlink, migrate: read target, remove symlink, write file
   - If missing or empty, write from `.ai/instructions.md`

4. **Verify both files exist and have content:**
   ```bash
   test -s CLAUDE.md && echo "CLAUDE.md: OK" || echo "CLAUDE.md: MISSING"
   test -s .github/copilot-instructions.md && echo "copilot-instructions.md: OK" || echo "copilot-instructions.md: MISSING"
   ```

---

## Step 3: Repository Configuration

Apply the repository settings collected during the Step 1 questionnaire (Group 5) via the GitHub API.

The `auto_merge` and `codeowners` values are already written to `project.yaml` in Step 1. This step applies them to the GitHub repository.

**Action:** Ask the user two additional questions not covered by the questionnaire:

1. **"Should branches be deleted after merge?"** (yes/no, default: yes)
   - `yes` → `delete_branch_on_merge: true` — keeps the branch list clean
   - `no` → `delete_branch_on_merge: false` — preserves branches after merge

2. **"Which merge strategies should be allowed?"** (squash, merge commit, rebase — select all that apply, default: all)

Update `project.yaml` with these additional settings (add them to the `repository` section).

Then apply settings immediately if `gh` is authenticated:

```bash
# Check gh auth
gh auth status

# Apply settings
gh api repos/{owner}/{repo} -X PATCH \
  --input <(cat <<EOF
{
  "allow_auto_merge": <auto_merge>,
  "delete_branch_on_merge": <delete_branch>,
  "allow_squash_merge": <squash>,
  "allow_merge_commit": <merge>,
  "allow_rebase_merge": <rebase>
}
EOF
)
```

If `gh` is not installed or not authenticated, tell the user: "GitHub CLI is not available. Repository settings were saved to `project.yaml` but not applied. Run `bash .ai/bin/init.sh` or configure manually in GitHub Settings > General."

---

## Step 4: Issue Templates

If this is a submodule context (consuming repo has `.ai` as a submodule), copy issue templates:

```bash
# Check if .ai is referenced in .gitmodules
grep -q '\.ai' .gitmodules 2>/dev/null && echo "submodule" || echo "standalone"
```

If submodule context:
```bash
mkdir -p .github/ISSUE_TEMPLATE
for tmpl in .ai/.github/ISSUE_TEMPLATE/*.yml; do
  name=$(basename "$tmpl")
  if [ ! -f ".github/ISSUE_TEMPLATE/$name" ]; then
    cp "$tmpl" ".github/ISSUE_TEMPLATE/$name"
    echo "Copied $name"
  else
    echo "$name already exists, skipping"
  fi
done
```

---

## Step 5: CODEOWNERS

Generate a CODEOWNERS file if one doesn't exist:

```bash
test -s CODEOWNERS && echo "CODEOWNERS already exists" || echo "No CODEOWNERS"
```

If no CODEOWNERS exists, ask the user: "Who should be the default code owner? (e.g., @your-org/your-team, or skip)"

If not skipped, create CODEOWNERS:
```
# CODEOWNERS — generated by init.md
# Edit as needed for your project.

* <default_owner>

/.github/workflows/ <default_owner>
/.ai @SET-Apps/approvers
```

---

## Step 6: Python Dependencies (Optional)

Ask the user: "Do you want to install Python dependencies for the governance policy engine? (Requires Python 3.12+)"

If yes:
```bash
# Check Python version
python3 --version

# Create venv
python3 -m venv .ai/.venv

# Install dependencies
.ai/.venv/bin/pip install --quiet --upgrade pip
.ai/.venv/bin/pip install --quiet -e .ai/governance/engine[dev]

# Verify
.ai/.venv/bin/python -c "import jsonschema; import yaml; print('OK')"
```

If no: "Skipping Python dependencies. You can install later with `bash .ai/bin/init.sh --install-deps`."

---

## Step 7: Install Hooks

Configure the PreCompact hook to auto-checkpoint before context compaction. This prevents losing work when context windows fill up.

1. **Check for existing settings:**
   ```bash
   test -f .claude/settings.json && echo "EXISTS" || echo "NEW"
   ```

2. **If `.claude/settings.json` does not exist**, create it:
   ```bash
   mkdir -p .claude
   ```
   Write `.claude/settings.json`:
   ```json
   {
     "hooks": {
       "PreCompact": [
         {
           "type": "command",
           "command": "bash .ai/governance/bin/pre-compact-checkpoint.sh"
         }
       ]
     }
   }
   ```

3. **If `.claude/settings.json` exists**, merge the hooks section:
   - Read the existing file
   - If it already has a `hooks.PreCompact` entry, skip (already installed)
   - If it has a `hooks` section but no `PreCompact`, add the PreCompact entry
   - If it has no `hooks` section, add the entire hooks block

4. **Verify hook installation:**
   ```bash
   grep -q "PreCompact" .claude/settings.json 2>/dev/null && echo "HOOKS_OK" || echo "HOOKS_MISSING"
   ```

---

## Post-flight: Verify & Summary

Run a final verification:

```bash
echo "=== Verification ==="
echo "Instruction files:"
test -s CLAUDE.md && echo "CLAUDE.md: OK" || echo "CLAUDE.md: MISSING"
test -s .github/copilot-instructions.md && echo "copilot-instructions.md: OK" || echo "copilot-instructions.md: MISSING"
echo ""
echo "Project config:"
test -f project.yaml && echo "project.yaml: OK" || echo "project.yaml: not configured"
echo ""
echo "CODEOWNERS:"
test -s CODEOWNERS && echo "CODEOWNERS: OK" || echo "CODEOWNERS: not configured"
echo ""
echo "Hooks:"
grep -q "PreCompact" .claude/settings.json 2>/dev/null && echo "PreCompact hook: OK" || echo "PreCompact hook: not installed"
echo ""
echo "Python venv:"
test -d .ai/.venv && echo ".venv: OK" || echo ".venv: not installed"
```

Present a summary to the user:

```
Setup complete. Here's what was configured:

- [x/skip] Language template: {selection}
- [x/skip] Instruction files: CLAUDE.md, copilot-instructions.md
- [x/skip] Repository settings: auto_merge={value}, delete_branch={value}
- [x/skip] Issue templates copied
- [x/skip] CODEOWNERS generated
- [x/skip] PreCompact hook installed
- [x/skip] Python dependencies installed

Next steps:
1. Customize project.yaml for your project's personas and conventions
2. Review CODEOWNERS and adjust ownership rules
3. Commit the new files: git add . && git commit -m "chore: bootstrap .ai governance submodule"
```

---

## Re-running This Prompt

This prompt is idempotent. Running it again will:
- Update instruction files if source has changed (content comparison)
- Skip templates if `project.yaml` is already present (ask before overwriting)
- Re-apply repository settings (safe — PATCH is idempotent)
- Skip issue templates that already exist
- Skip CODEOWNERS if populated
- Skip hooks if already installed
- Skip Python venv if `.ai/.venv` exists

**After a submodule update**, re-run this prompt or run `bash .ai/bin/init.sh --refresh` to re-apply structural setup. The agentic startup loop auto-repairs instruction files and hooks on every session (see below).

---

## Self-Repair

This prompt auto-repairs on `/startup`. The agentic startup loop (Phase 1a-bis) checks instruction file freshness and hook installation on every session. Specifically:

1. **Instruction files** — verifies `CLAUDE.md` and `.github/copilot-instructions.md` exist, have content, and contain the ANCHOR marker. Rewrites from `.ai/instructions.md` if stale or missing.
2. **PreCompact hook** — verifies `.claude/settings.json` contains the PreCompact hook. Installs if missing.
3. **Governance directories** — verifies `.artifacts/plans/`, `.artifacts/panels/`, `.artifacts/checkpoints/`, and `.artifacts/state/` exist. Creates if missing.

All repairs are non-blocking — the startup loop warns and continues if any repair fails.
