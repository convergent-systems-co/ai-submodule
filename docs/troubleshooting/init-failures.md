# Troubleshooting: init.sh Failures

This guide covers common failures when running `bash .ai/bin/init.sh` and how to resolve them.

## Diagnostic Flags

### `--debug`

Enables verbose output showing every resolved path and executed command:

```bash
bash .ai/bin/init.sh --debug
```

### `--dry-run`

Shows what the script would do without making any changes:

```bash
bash .ai/bin/init.sh --dry-run
```

Both flags can be combined: `bash .ai/bin/init.sh --debug --dry-run`.

## Common Failures

### Python Not Found

**Symptom:**
```
  [WARN] Python is not installed or not in PATH
```

**Resolution:**
1. Install Python 3.12+ from [python.org](https://www.python.org/downloads/)
2. Verify: `python3 --version`
3. Re-run init.sh

On macOS with Homebrew: `brew install python@3.12`

### Python Version Too Old

**Symptom:**
```
  [WARN] Python 3.9.7 found, but 3.12+ required
```

**Resolution:**
1. Install Python 3.12+ alongside the existing version
2. Ensure `python3` on your PATH points to the new version, or update your shell profile

### GitHub CLI (gh) Missing

**Symptom:**
```
  [SKIP] GitHub CLI (gh) not found. Skipping repository configuration.
```

**Resolution:**
1. Install from [cli.github.com](https://cli.github.com/)
2. Authenticate: `gh auth login`
3. Re-run init.sh

Repository settings and CODEOWNERS generation require gh CLI. Other init steps work without it.

### GitHub CLI Not Authenticated

**Symptom:**
```
  [SKIP] Not authenticated with GitHub CLI. Run: gh auth login
```

**Resolution:**
```bash
gh auth login
# Follow the prompts to authenticate
bash .ai/bin/init.sh
```

### Submodule Has Uncommitted Changes

**Symptom:**
```
  [WARN] .ai submodule has uncommitted changes; skipping automatic update
```

**Resolution:**
```bash
cd .ai
git stash        # or: git checkout .
cd ..
bash .ai/bin/init.sh
```

### Submodule Fetch Fails (Network Error)

**Symptom:**
```
  [WARN] Could not fetch .ai remote (network error or no remote configured)
```

**Resolution:**
1. Check network connectivity
2. Verify the remote URL: `git -C .ai remote -v`
3. If behind a proxy, configure git: `git config --global http.proxy http://proxy:port`

### Permission Denied on Symlink Creation

**Symptom:**
```
ln: .../CLAUDE.md: Permission denied
```

**Resolution:**
1. Check file ownership: `ls -la CLAUDE.md`
2. Remove the existing file if it's not a symlink: `rm CLAUDE.md`
3. Re-run init.sh

On Windows (Git Bash), symlinks may require developer mode or administrator privileges.

### Integrity Verification Failures

**Symptom:**
```
  [WARN] Integrity verification found issues (3/5 passed):
  MISMATCH: governance/policy/default.yaml (expected: a1b2c3d4..., actual: e5f6g7h8...)
```

**Resolution:**
1. Review the mismatched files for unauthorized modifications
2. If changes are intentional, update the manifest: `governance/integrity/critical-files.sha256`
3. If changes are unexpected, re-clone the submodule: `git submodule update --force .ai`

### Missing Panel Emissions

**Symptom:**
```
  [WARN] Missing required panel emissions: security-review threat-modeling
```

**Resolution:**
Panel emissions are created during governance reviews. This warning is expected for new projects. The governance workflow will block PRs until these panels have been run. See `governance/policy/default.yaml` for required panel definitions.

### Dependency Installation Fails

**Symptom:**
```
  [ERROR] No pyproject.toml or requirements.txt found
```

**Resolution:**
1. Verify the submodule is properly initialized: `git submodule update --init .ai`
2. Check that `governance/engine/pyproject.toml` exists in the .ai directory

## Running Individual Modular Scripts

Each init step can be run independently for debugging. Scripts are in `governance/bin/`:

```bash
# Check Python version
source .ai/governance/bin/check-python.sh

# Only update submodule
AI_DIR=.ai PROJECT_ROOT=. bash .ai/governance/bin/update-submodule.sh

# Only create symlinks
AI_DIR=.ai PROJECT_ROOT=. bash .ai/governance/bin/create-symlinks.sh

# Only set up workflows
AI_DIR=.ai PROJECT_ROOT=. PYTHON_CMD=python3 bash .ai/governance/bin/setup-workflows.sh

# Only validate emissions
AI_DIR=.ai PROJECT_ROOT=. PYTHON_CMD=python3 bash .ai/governance/bin/validate-emissions.sh

# Only create directories
AI_DIR=.ai PROJECT_ROOT=. PYTHON_CMD=python3 bash .ai/governance/bin/setup-directories.sh

# Only configure repository
AI_DIR=.ai PROJECT_ROOT=. PYTHON_CMD=python3 PYTHON_OK=true bash .ai/governance/bin/setup-repo-config.sh

# Only set up CODEOWNERS
AI_DIR=.ai PROJECT_ROOT=. PYTHON_CMD=python3 PYTHON_OK=true bash .ai/governance/bin/setup-codeowners.sh

# Only install dependencies
AI_DIR=.ai PROJECT_ROOT=. PYTHON_CMD=python3 PYTHON_OK=true bash .ai/governance/bin/install-deps.sh
```

All scripts support `DRY_RUN=true` and `DEBUG=true` environment variables:

```bash
DRY_RUN=true DEBUG=true AI_DIR=.ai PROJECT_ROOT=. bash .ai/governance/bin/create-symlinks.sh
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DRY_RUN` | `false` | Show actions without executing them |
| `DEBUG` | `false` | Enable verbose debug output |
| `AI_DIR` | Auto-detected | Path to the .ai submodule |
| `PROJECT_ROOT` | Parent of AI_DIR | Path to the project root |
| `PYTHON_CMD` | Auto-detected | Python executable to use |
| `PYTHON_OK` | Auto-detected | Whether Python meets version requirements |
| `PYTHON_MIN_MAJOR` | `3` | Minimum Python major version |
| `PYTHON_MIN_MINOR` | `12` | Minimum Python minor version |
| `REFRESH_MODE` | `false` | Skip submodule freshness check |
