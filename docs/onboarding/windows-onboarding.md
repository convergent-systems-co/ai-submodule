# Windows Onboarding — Team Starter Guide

Get your first AI-governed project running in under 10 minutes. No prior experience needed.

!!! info "This is the on-ramp, not the manual"
    **This page** gets you running in 10 minutes on Windows. It's opinionated on purpose.
    **Everything else** — consolidated review prompts, policy profiles, compliance rules, CI pipeline, runtime feedback, and advanced config — lives in the full [Documentation Site](../index.md).

---

## What Is This?

| Feature | Description |
|---------|-------------|
| **A Virtual Engineering Team** | Drop a `.ai` submodule into any repo and get a full AI team: planner, coder, security reviewer, data governance reviewer, and more — all automated. |
| **Governed by Panels** | Every code change goes through review panels. If panels pass, it auto-merges. If they fail, it fixes itself and tries again. |
| **Plans as Audit Trail** | Every decision is written to `.governance/plans/`. Team members can see exactly why a change was made and how it evolved. |
| **Local or GitHub** | Works offline with no GitHub remote (local mode) or fully connected with issue tracking, PRs, and auto-merge (remote mode). |

---

## Before You Start

| Prerequisite | Details |
|-------------|---------|
| **Python 3.12+** | Required for the governance policy engine. [Download from python.org](https://www.python.org/downloads/) and make sure it's in your PATH. Verify: `python --version` |
| **Git** | Standard git installation. Verify: `git --version` |
| **AI Tool** | Claude Code or GitHub Copilot. The framework works with both. Instructions are shared automatically via symlinks. |
| **GitHub access** | Needed to clone the submodule. Use SSH: `git@github.com:SET-Apps/ai-submodule.git` |

!!! warning "Windows Symlink Tip"
    For symlinks to work (so `.github/copilot-instructions.md` and `CLAUDE.md` stay in sync automatically), enable **Developer Mode**: Settings → System → For developers → Developer Mode → On. Otherwise the script falls back to file copies — everything still works, but you'll need to re-run `init.ps1` after submodule updates.

---

## Quick Start (Windows)

### Step 1 — Create your project folder

Start a new folder for your project and initialize git.

```powershell
mkdir my-project
cd my-project
git init
```

### Step 2 — Add the .ai governance submodule

This pulls the entire governance framework into your repo as a `.ai` folder.

```powershell
git submodule add git@github.com:SET-Apps/ai-submodule.git .ai
```

### Step 3 — Bootstrap the framework

Run the init script. It creates symlinks for all AI tools, sets up `.governance/plans/` and `.governance/panels/` folders, copies governance workflows, and generates CODEOWNERS.

```powershell
powershell -ExecutionPolicy Bypass -File .ai\bin\init.ps1 -InstallDeps
```

!!! tip
    `-InstallDeps` creates a Python venv and installs `jsonschema` + `pyyaml` automatically.

### Step 4 — Pick your language template (optional)

Copy a template for your stack, or skip this — the Code Manager will auto-detect your codebase and generate `project.yaml` during the first agentic session.

```powershell
# Optional: choose one: python / node / go / csharp / react
Copy-Item .ai\governance\templates\node\project.yaml project.yaml
# Or skip this — /startup will auto-generate it
```

### Step 5 — Commit the setup

```powershell
git add -A
git commit -m "chore: add .ai governance submodule"
```

### Step 6 — Start the agentic loop

Open your AI tool (Claude Code or GitHub Copilot) in this folder and type:

```
/startup
```

!!! note "What happens next"
    Five AI personas activate: DevOps Engineer (triage) → Code Manager (plan) → Coder (implement) → Tester (evaluate) → Security Review → Merge. If no `project.yaml` exists, the Code Manager creates one first.

---

## What It Adds to Your Repo

| What's Added | Impact | Concern |
|-------------|--------|---------|
| `.ai/` | Submodule — git tracks it as **one commit pointer**. Won't clutter `git status` or diffs. | **Low** |
| `CLAUDE.md` | Symlink at root (or file copy on Windows without Developer Mode). Visible but inert. | **Low** |
| `project.yaml` | Single config file you own. Name your project, set policy profile. | **Low** |
| `.governance/plans/` / `.governance/checkpoints/` | New folders for audit trail and session state. | **Low** |
| `.github/workflows/` (5 new YAMLs) | Governance CI runs on every PR. Won't break existing workflows but **adds CI time**. | **Medium** |
| `CODEOWNERS` | Generated fresh. **Will overwrite** your existing CODEOWNERS if you have one. | **Check first** |

!!! warning "Before running init"
    Do you have a `CODEOWNERS` file? Back it up. Do you have existing CI workflows you care about? Review the 5 new YAMLs before they go live. See the [Risks & Mitigation](risks-mitigation.md) guide for step-by-step commands.

---

## Local Mode vs. Remote Mode

The framework auto-detects whether you have a GitHub remote. Both modes run the full governance pipeline.

=== "Local Mode"

    - Plans written to `.governance/plans/`
    - Panels run and evaluate code
    - Code generated and tested
    - No GitHub issues created
    - No PRs or auto-merge

    *Perfect for learning and POC. Start here.*

=== "Remote Mode"

    - Plans written to `.governance/plans/`
    - Panels run and evaluate code
    - Code generated and tested
    - GitHub issues created automatically
    - PRs created and auto-merged if panels pass

    *Production workflow. Add `git remote add origin` to activate.*

---

## How It Works (The Mental Model)

!!! success "Real developer feedback"
    **"Keyboard Karen" (a real dev, first day with the framework):** "What I basically created was not an app, but was the app *and* the ecosystem that I can talk to — to create new issues, add new features, document something, test something, add new code. It's an ecosystem. It's like I created a virtual team."

| You say | What happens |
|---------|-------------|
| "Build me a theme switcher" | DevOps Engineer triages → Code Manager plans → Coder implements → Tester evaluates → Security review → merge |
| "Add Nord and Solarized themes" | Same 5-phase pipeline, scoped to the new request. Plans updated. |
| "Update GOALS.md" | Framework reads what was implemented and rewrites GOALS.md in standard format |
| `/startup` | DevOps Engineer scans open PRs → triages issues → Code Manager orchestrates → Coder + Tester loop → merge |

---

## Understanding the Plans Folder

Every non-trivial action creates a plan file. This is your audit trail.

| Question | Answer |
|----------|--------|
| **What's in a plan?** | What was asked, what was decided, what was implemented, and why. Each plan = one session or one feature. |
| **Who reads them?** | New team members who need to understand *why* the code looks the way it does. Plans are the "how did we get here" trail. |
| **Can we delete them?** | Yes, once the team is comfortable. Plans can be disabled in `project.yaml`. |
| **Where do they go?** | Archived to GitHub Releases automatically when a PR merges (via `plan-archival.yml` workflow). |

---

## Keeping the Framework Updated

```powershell
# Pull latest governance updates from SET-Apps/ai-submodule
git submodule update --remote .ai
git add .ai
git commit -m "chore: update .ai submodule"
```

!!! info
    The startup loop auto-runs this check at the start of every session. You usually don't need to do this manually.

---

## When Things Get Stuck

| Situation | What to do |
|-----------|-----------|
| Agent stopped mid-session | `/startup` — it resumes from the most recent checkpoint or open PR |
| Context is full / agent repeating itself | Say: *"Write a checkpoint and stop"* → `/clear` → *"Resume from checkpoint"* |
| Dirty git state | `git add -A && git commit -m "wip: recovery"` then `/startup` |
| PR stuck / CI failing | Say: *"Resume PR #N"* — agent re-enters the review loop |
| Don't know where you are | `git status` · `git branch --show-current` · `ls .governance/checkpoints/` |

---

## Key Links

| Resource | Description |
|----------|-------------|
| [Architecture Visual](architecture-visual.md) | High-level flow — how your request becomes governed, tested, and merged code |
| [Risks & Mitigation](risks-mitigation.md) | Two risks, five mitigations, zero-risk pre-flight checklist |
| [AI-Assisted Install](ai-assisted-install.md) | Install with Copilot CLI or Claude Code in one command |
| [Developer Guide](developer-guide.md) | Quick-start onboarding, recovery, diagnostics |
| [Simple Explainer](eli5.md) | Plain-language overview — what this is and why it exists |
