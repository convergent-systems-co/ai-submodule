# Migrating from Git Submodule to Binary CLI

This guide walks consumers through migrating from the `.ai/` git submodule to the standalone `dark-governance` binary. Expected time: 15–30 minutes.

## Overview

The `dark-governance` binary replaces the git submodule (`.ai/`) as the primary distribution method. Key changes:

| Aspect | Submodule (`.ai/`) | Binary (`dark-governance`) |
|--------|-------------------|---------------------------|
| Installation | `git submodule add` | `brew install` or `curl` |
| Updates | `git submodule update` | `brew upgrade` or re-download |
| Init | `bash .ai/bin/init.sh` | `dark-governance init` |
| Policy engine | `python -m governance.engine.policy_engine` | `dark-governance engine run` |
| Verify | `bash .ai/bin/init.sh --verify` | `dark-governance verify` |
| CI integration | Clone submodule in workflow | Download binary in workflow |

What stays the same:
- `project.yaml` configuration format
- `CLAUDE.md` instructions
- Governance emissions format and directory structure
- Policy profiles and schemas

## Prerequisites

1. Install the binary via Homebrew or direct download:

   ```bash
   # Homebrew (recommended)
   brew tap SET-Apps/tap
   brew install dark-governance

   # Or direct download
   curl -sSfL https://raw.githubusercontent.com/convergent-systems-co/dark-forge/main/src/scripts/install.sh | sh
   ```

2. Verify installation:

   ```bash
   dark-governance version
   ```

## Step 1: Back Up Current State

Save files you may have customized:

```bash
# Back up customized files
cp project.yaml project.yaml.bak
cp CLAUDE.md CLAUDE.md.bak

# Back up any custom CI workflows that reference .ai/
cp -r .github/workflows .github/workflows.bak
```

## Step 2: Remove the Git Submodule

```bash
# Deinitialize the submodule
git submodule deinit -f .ai

# Remove from git tracking
git rm -f .ai

# Clean up .gitmodules if empty
if [ ! -s .gitmodules ]; then
  git rm -f .gitmodules
fi

# Remove cached submodule data
rm -rf .git/modules/.ai

# Commit the removal
git commit -m "refactor: remove .ai git submodule in favor of dark-governance binary"
```

## Step 3: Initialize with Binary

```bash
# Initialize governance in your repo
dark-governance init --language <your-language>

# Available languages: go, csharp, python, node, java
```

This scaffolds:
- `project.yaml` (preserves existing if present)
- `CLAUDE.md` (preserves existing if present)
- `.governance/` directory for emissions
- GitHub Actions workflow for governance checks

## Step 4: Restore Customizations

If you had customizations in `project.yaml` or `CLAUDE.md`:

```bash
# Compare and merge your backups
diff project.yaml project.yaml.bak
diff CLAUDE.md CLAUDE.md.bak

# Restore your customizations
# (manually merge differences — the binary may have added new fields)
```

## Step 5: Emissions Directory

The binary uses `.governance/` as the default emissions directory (instead of `.artifacts/emissions/`).

To use a custom location:

```bash
dark-governance engine run --emissions-dir .artifacts/emissions/
```

Or set it in `project.yaml`:

```yaml
governance:
  emissions_dir: .artifacts/emissions/
```

## Step 6: CI Workflow Migration

Replace submodule-based CI steps with binary commands:

### Before (submodule)

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      submodules: recursive
      token: ${{ secrets.SUBMODULE_TOKEN }}

  - name: Run governance
    run: |
      bash .ai/bin/init.sh
      python -m governance.engine.policy_engine
```

### After (binary)

```yaml
steps:
  - uses: actions/checkout@v4

  - name: Install dark-governance
    run: |
      curl -sSfL https://raw.githubusercontent.com/convergent-systems-co/dark-forge/main/src/scripts/install.sh | sh
      echo "$HOME/.local/bin" >> "$GITHUB_PATH"

  - name: Run governance
    run: |
      dark-governance verify
      dark-governance engine run
```

### Command Reference

| Submodule Command | Binary Equivalent |
|-------------------|-------------------|
| `bash .ai/bin/init.sh` | `dark-governance init` |
| `bash .ai/bin/init.sh --refresh` | `dark-governance init` (idempotent) |
| `bash .ai/bin/init.sh --verify` | `dark-governance verify` |
| `bash .ai/bin/init.sh --check-branch-protection` | `dark-governance verify-environment` |
| `python -m governance.engine.policy_engine` | `dark-governance engine run` |
| `python -m governance.engine.orchestrator status` | `dark-governance engine status` |

## Step 7: Verify

```bash
# Check lockfile integrity
dark-governance verify

# Verify engine status
dark-governance engine status

# Run a dry-run policy evaluation
dark-governance engine run --dry-run
```

## Rollback

If you need to revert to the submodule:

```bash
# Re-add the submodule
git submodule add https://github.com/convergent-systems-co/dark-forge.git .ai
git submodule update --init --recursive

# Re-initialize
bash .ai/bin/init.sh
```

## FAQ

**Q: Do I need Python installed for the binary?**
A: No. The binary embeds the policy engine. Python is only needed for the legacy submodule approach.

**Q: Can I use both the submodule and binary simultaneously?**
A: Not recommended. The binary and submodule may conflict on governance configuration. Choose one.

**Q: What about custom policy profiles?**
A: Custom profiles in `governance/policy/` are preserved. The binary reads them from the same location.

**Q: Will my governance emissions history be preserved?**
A: Yes. Existing emissions in `.artifacts/` are not touched. Configure `emissions_dir` if you want to keep using that path.

**Q: What if `dark-governance init` overwrites my project.yaml?**
A: It won't. The init command preserves existing `project.yaml` and `CLAUDE.md` files, merging new defaults only for missing fields.
