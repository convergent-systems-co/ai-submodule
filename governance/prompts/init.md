# Init: Agentic Bootstrap Prompt

Execute this prompt to bootstrap the `.ai` governance submodule in a consuming project. This is the agentic equivalent of `bash .ai/bin/init.sh` — it walks the user through setup interactively, asking about configuration options.

**When to use this:** After adding the `.ai` submodule to a project (`git submodule add git@github.com:SET-Apps/ai-submodule.git .ai`), run this prompt to configure the project.

**Canonical implementation:** `init.sh` (bash) and `init.ps1` (PowerShell) are the source of truth for bootstrap logic. This prompt mirrors their behavior but adds interactive configuration. If this prompt and the shell scripts diverge, the shell scripts are authoritative.

---

## Pre-flight Checks

Before starting, verify the environment:

1. **Confirm `.ai` submodule exists:**
   ```bash
   test -d .ai/governance && echo "OK" || echo "MISSING"
   ```
   If MISSING: The `.ai` submodule has not been added yet. Run:
   ```bash
   git submodule add git@github.com:SET-Apps/ai-submodule.git .ai
   git submodule update --init --recursive
   ```
   Then re-run this prompt.

2. **Check if already initialized** (symlinks exist):
   ```bash
   test -L CLAUDE.md && echo "CLAUDE.md symlink exists" || echo "Not initialized"
   test -L .cursorrules && echo ".cursorrules symlink exists" || echo "Not initialized"
   test -L .github/copilot-instructions.md && echo "copilot-instructions symlink exists" || echo "Not initialized"
   ```
   If all symlinks exist, skip to Step 3 (Repository Configuration) — the project may already be initialized but need configuration updates.

3. **Detect platform:**
   ```bash
   uname -s
   ```

---

## Step 1: Choose Language Template

Ask the user which language template to use for `project.yaml`. Available templates:

| Template | Path | Language | Defaults |
|----------|------|----------|----------|
| Python | `governance/templates/python/project.yaml` | Python | pytest, ruff, mypy, uv |
| Node | `governance/templates/node/project.yaml` | TypeScript/JS | jest, eslint, prettier |
| React | `governance/templates/react/project.yaml` | TypeScript/React | jest/vitest, eslint, prettier |
| Go | `governance/templates/go/project.yaml` | Go | go test, golangci-lint |
| C# | `governance/templates/csharp/project.yaml` | C# | xUnit, dotnet format |
| Generic | `governance/templates/project.yaml` | Any | Minimal defaults |
| Skip | — | — | Do not copy a template |

**Action:** Ask the user: "Which language template should I use for your project? (python, node, react, go, csharp, generic, or skip)"

If the user selects a template (not "skip"):
```bash
cp .ai/governance/templates/{selection}/project.yaml project.yaml
```
For "generic":
```bash
cp .ai/governance/templates/project.yaml project.yaml
```

Then tell the user: "I've copied the template to `project.yaml` (project root). You can customize it later — it controls which personas, panels, and conventions are active for your project."

---

## Step 2: Create Symlinks

Create the symlinks that connect the `.ai` submodule's instructions to each AI tool's expected location:

```bash
# CLAUDE.md -> .ai/instructions.md (Claude Code)
ln -sf .ai/instructions.md CLAUDE.md

# .cursorrules -> .ai/instructions.md (Cursor)
ln -sf .ai/instructions.md .cursorrules

# .github/copilot-instructions.md -> .ai/instructions.md (GitHub Copilot)
mkdir -p .github
ln -sf ../.ai/instructions.md .github/copilot-instructions.md
```

Verify each symlink was created:
```bash
ls -la CLAUDE.md .cursorrules .github/copilot-instructions.md
```

---

## Step 3: Repository Configuration

Ask the user about GitHub repository settings. These settings are applied via the GitHub API and affect how PRs are merged.

**Action:** Ask the user the following questions:

1. **"Should PRs auto-merge when all checks pass?"** (yes/no, default: no)
   - `yes` → `auto_merge: true` — PRs merge automatically after CI passes and approvals are met
   - `no` → `auto_merge: false` — PRs require manual merge (recommended for most teams)

2. **"Should branches be deleted after merge?"** (yes/no, default: yes)
   - `yes` → `delete_branch_on_merge: true` — keeps the branch list clean
   - `no` → `delete_branch_on_merge: false` — preserves branches after merge

3. **"Which merge strategies should be allowed?"** (squash, merge commit, rebase — select all that apply, default: all)

If the user chose a template in Step 1 and `project.yaml` exists, update it with the user's choices:

```bash
# Example: Update auto_merge in project.yaml
# The agent should edit the repository section of project.yaml (project root)
# to reflect the user's preferences, adding a repository section if missing:
#
# repository:
#   auto_merge: true
#   delete_branch_on_merge: true
#   allow_squash_merge: true
#   allow_merge_commit: true
#   allow_rebase_merge: true
```

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
.ai/.venv/bin/pip install --quiet -r .ai/governance/bin/requirements.txt

# Verify
.ai/.venv/bin/python -c "import jsonschema; import yaml; print('OK')"
```

If no: "Skipping Python dependencies. You can install later with `bash .ai/bin/init.sh --install-deps`."

---

## Post-flight: Verify & Summary

Run a final verification:

```bash
echo "=== Verification ==="
echo "Symlinks:"
ls -la CLAUDE.md .cursorrules .github/copilot-instructions.md 2>/dev/null
echo ""
echo "Project config:"
test -f project.yaml && echo "project.yaml: OK" || echo "project.yaml: not configured"
echo ""
echo "CODEOWNERS:"
test -s CODEOWNERS && echo "CODEOWNERS: OK" || echo "CODEOWNERS: not configured"
echo ""
echo "Python venv:"
test -d .ai/.venv && echo ".venv: OK" || echo ".venv: not installed"
```

Present a summary to the user:

```
Setup complete. Here's what was configured:

- [x/skip] Language template: {selection}
- [x/skip] Symlinks: CLAUDE.md, .cursorrules, copilot-instructions.md
- [x/skip] Repository settings: auto_merge={value}, delete_branch={value}
- [x/skip] Issue templates copied
- [x/skip] CODEOWNERS generated
- [x/skip] Python dependencies installed

Next steps:
1. Customize project.yaml for your project's personas and conventions
2. Review CODEOWNERS and adjust ownership rules
3. Commit the new files: git add . && git commit -m "chore: bootstrap .ai governance submodule"
```

---

## Re-running This Prompt

This prompt is idempotent. Running it again will:
- Skip symlinks that already exist
- Skip templates if `project.yaml` is already present (ask before overwriting)
- Re-apply repository settings (safe — PATCH is idempotent)
- Skip issue templates that already exist
- Skip CODEOWNERS if populated
- Skip Python venv if `.ai/.venv` exists
