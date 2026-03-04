# Risks & Mitigation

Adding Dark Forge to an existing repo is low-risk by default — and zero-risk if you follow this guide before running `init.ps1`.

!!! success "Total effort to reach zero risk: under 15 minutes"
    There are exactly two risks worth knowing about. Both have trivial mitigations. Everything else the framework adds is either a symlink, a new folder, or a git submodule pointer — none of which can break your existing repo.

---

## Risk 1: CODEOWNERS Overwrite

`init.ps1` generates a fresh `CODEOWNERS` file — which **replaces yours** if it already exists.

!!! danger "What happens"
    The bootstrap script writes a new `CODEOWNERS` at the repo root defining ownership for `.ai/` and governance paths. If you already have a `CODEOWNERS` file with your team's path assignments, it gets silently replaced. PR review requirements tied to those rules stop working until you notice and fix it.

### Mitigation A: Back up → run init → merge (Recommended)

Save your existing file before init, then copy your rules back in. One-time, permanent fix.

```powershell
# Step 1 — before running init
Copy-Item CODEOWNERS CODEOWNERS.bak

# Step 2 — run init as normal
powershell -ExecutionPolicy Bypass -File .ai\bin\init.ps1 -InstallDeps

# Step 3 — merge your rules back (open both files, paste your entries in)
code CODEOWNERS CODEOWNERS.bak
```

### Mitigation B: Skip CODEOWNERS entirely

After init runs, restore your original file before committing. Dark Forge still works — it just won't auto-assign ownership for its own paths.

```powershell
# After init runs, before git add
Copy-Item CODEOWNERS.bak CODEOWNERS -Force
```

---

## Risk 2: 5 New CI Workflows Run on Every PR

Governance workflows are copied to `.github/workflows/` and trigger automatically once committed.

!!! warning "What happens"
    The five workflows — `dark-factory-governance.yml`, `plan-archival.yml`, `propagate-submodule.yml`, `issue-monitor.yml`, `jm-compliance.yml` — fire on PR and push events. They won't break your existing pipeline, but they **add CI runtime and GitHub Actions minutes** to every PR. On a high-frequency repo this adds up fast.

### Mitigation A: Disable workflows in GitHub UI (Easiest)

Commit them but keep them switched off. Enable one at a time as your team is ready. Fully reversible with one click.

1. Go to your repo → **Actions** tab
2. Click the workflow name in the left sidebar
3. Click **… → Disable workflow**
4. Repeat for each of the 5 workflows (30 sec total)

### Mitigation B: Stage everything except workflows

Use local mode until you're ready. Don't commit the workflow files yet — they only trigger once they're in the remote repo.

```powershell
# After init, exclude workflow files from your first commit
git add -A
git reset .github/workflows/dark-factory-governance.yml
git reset .github/workflows/plan-archival.yml
git reset .github/workflows/propagate-submodule.yml
git reset .github/workflows/issue-monitor.yml
git reset .github/workflows/jm-compliance.yml
git commit -m "chore: add .ai governance submodule (workflows pending)"
```

### Mitigation C: Scope workflows to a branch prefix

Edit each workflow's trigger so it only fires on `dark-factory/*` branches. Your main dev branches are untouched.

```yaml
# Add this to the `on:` block in each workflow YAML
on:
  pull_request:
    branches:
      - dark-factory/**   # only runs on DF feature branches
  push:
    branches:
      - dark-factory/**
```

---

## Zero-Risk Pre-Flight Checklist

Run through this *before* you touch `init.ps1`. Takes 5 minutes. Saves headaches.

- [ ] **Do you have a CODEOWNERS file?** Run `Get-Item CODEOWNERS`. If it exists → back it up now: `Copy-Item CODEOWNERS CODEOWNERS.bak`
- [ ] **Is this a high-frequency repo with active CI?** If yes → plan to disable the 5 new workflows in GitHub Actions UI right after your first push. Takes 30 seconds.
- [ ] **Do you already have branch protection rules tied to specific workflow names?** New workflows won't break them — but check your branch protection settings after committing so nothing is unexpectedly blocking merges.
- [ ] **Are you on a shared repo with teammates actively working?** Give them a heads-up: "I'm adding the Dark Forge submodule. You'll need to run `git submodule update --init --recursive` after pulling."
- [ ] **Windows without Developer Mode enabled?** Symlinks won't work — init falls back to file copies. Everything still works, but re-run `init.ps1` after each submodule update. Or enable Developer Mode: **Settings → System → For developers → Developer Mode → On**.

!!! success "After the checklist — you're good to go"
    Run `init.ps1 -InstallDeps`, commit, disable workflows in the UI if needed, merge your CODEOWNERS back. The rest of the framework adds **zero breaking changes** to anything you already have.

---

*Back to [Windows Onboarding](windows-onboarding.md) · [Architecture Visual](architecture-visual.md)*
