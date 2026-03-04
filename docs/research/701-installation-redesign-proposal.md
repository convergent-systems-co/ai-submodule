# Installation Redesign Proposal: AI-Submodule

**Issue:** #701 — UX Review: installation experience for consuming repos
**Date:** 2026-03-02
**Author:** Coder (automated)

---

## Executive Summary

This proposal redesigns the AI-Submodule installation experience to achieve:
- **Same-org install: 1 command, under 1 minute**
- **Cross-org install: 1 command, zero submodule dependency**
- **First value: visible within the install command itself**

---

## 1. Proposed Same-Org Installation

### New Flow

```bash
# One command — does everything
bash <(curl -s https://raw.githubusercontent.com/convergent-systems-co/dark-forge/main/bin/quick-install.sh)
```

Or if already in a repo:
```bash
git submodule add https://github.com/convergent-systems-co/dark-forge.git .ai && bash .ai/bin/init.sh --quick
```

### What `--quick` Does (Redesigned)

```
$ bash .ai/bin/init.sh --quick

  AI Governance — installing...

  [1/4] Setting up governance.............. done
  [2/4] Detecting project.................. Python (requirements.txt found)
  [3/4] Configuring IDEs................... VS Code, Claude Code (2 found)
  [4/4] Verifying installation............. passed

  Governance is active. Your PRs will be automatically reviewed.

  Quick links:
    Governance status:   bash .ai/bin/governance-status.sh
    Your first PR guide: https://set-apps.github.io/dark-forge/quickstart/first-governed-pr/
    Customize settings:  project.yaml (auto-generated)
```

### Key Changes from Current

| Current | Proposed | Impact |
|---------|----------|--------|
| 9-step verbose output | 4-step progress bar | Cognitive load: less output to parse |
| Manual template copy for project.yaml | Auto-detect language, generate project.yaml | Post-install steps: 4 to 0 |
| MCP requires separate `--mcp` flag | Auto-detect IDEs and configure (skip silently if npm missing) | IDE setup: automatic |
| Prerequisites not checked upfront | Check Python, git at start; install guidance if missing | Fail-fast with clear fix |
| No immediate value visible | Show "governance is active" + quick links | First value visible at install time |

### Prerequisite Handling

```
$ bash .ai/bin/init.sh --quick

  Checking prerequisites...
  [x] git 2.39.0
  [x] Python 3.11.4
  [ ] gh CLI — not found (optional, needed for PR governance)
      Install: brew install gh

  Continue without gh CLI? [Y/n]
```

### Auto-Detection: Project Language

Scan in priority order:
1. `package.json` or `package-lock.json` -> Node.js template
2. `requirements.txt` or `pyproject.toml` or `setup.py` -> Python template
3. `go.mod` -> Go template
4. `*.csproj` or `*.sln` -> C# template
5. `*.tf` or `*.bicep` -> Infrastructure template
6. `Gemfile` -> Ruby template
7. Fallback -> minimal template with language-agnostic defaults

---

## 2. Proposed Cross-Org Installation

### Strategy: Vendored Release Package

For repos outside SET-Apps that cannot clone the private submodule:

```bash
# Cross-org install via release tarball
bash <(curl -s https://github.com/convergent-systems-co/dark-forge/releases/latest/download/install.sh)
```

### What This Does

1. Downloads the latest release tarball (governance engine + schemas + workflows only)
2. Extracts to `.ai-governance/` (not a submodule — a regular directory)
3. Creates the same symlinks as the submodule install
4. Runs at Tier 2 (lightweight emission validation) — no submodule updates needed
5. Provides an update command: `bash .ai-governance/bin/update.sh`

### Tier 2 vs Tier 1

| Capability | Tier 1 (Submodule) | Tier 2 (Vendored) |
|-----------|:------------------:|:-----------------:|
| Policy engine | Full | Lightweight |
| Schema validation | Full | Full |
| GitHub Actions workflows | Full | Full |
| MCP server | Full | Full |
| Auto-update | `git submodule update` | `bash update.sh` |
| Persona definitions | Full | Included (read-only) |
| Orchestrator CLI | Full | Not available |

### Future: npm Package

Phase 2 of cross-org distribution:
```bash
npx @set-apps/ai-governance install
```

This would combine the tarball approach with npm's distribution infrastructure, matching DACH's install experience exactly.

---

## 3. Cognitive Load Reduction

### Install-Time Information Budget

**Current:** 30+ concepts exposed at install time
**Proposed:** 3 concepts exposed at install time

| Tier | When | Concepts Introduced | User Sees |
|------|------|--------------------|-----------|
| Install | `init.sh --quick` | Governance is active, status command, first PR guide | 3 things |
| First PR | User opens a PR | Panels that ran, findings summary, how to fix | +3 things |
| Customization | User edits project.yaml | Policy profiles, persona overrides | +2 things |
| Advanced | User runs `/startup` | Orchestrator, multi-agent dispatch, containment | +5 things |

### Post-Install: Zero Required Steps

Instead of showing 4 next steps, the install generates everything automatically:
- `project.yaml` is auto-generated with detected language defaults
- IDE configs are auto-written for detected IDEs
- Governance workflows are auto-copied
- CODEOWNERS is auto-generated

The only "next step" shown is: **"Open a PR to see governance in action."**

---

## 4. Implementation Roadmap

### Phase 1: Same-Org UX Overhaul (Issues #701-#704)

| Task | Issue | Effort | Impact |
|------|-------|--------|--------|
| Auto-detect project language | #701 | Medium | High |
| Quiet-by-default init.sh output | #702 | Low | High |
| Auto-detect and configure IDEs | #703 | Medium | High |
| Quickstart guides | #704 | Medium | High |
| Consolidate --quick to full setup | #701 | Low | Medium |
| Prerequisite check at init start | #701 | Low | Medium |

### Phase 2: Cross-Org Distribution

| Task | Effort | Impact |
|------|--------|--------|
| Create release tarball workflow | Medium | High |
| Build vendored installer script | Medium | High |
| Create update mechanism | Medium | Medium |

### Phase 3: npm Distribution

| Task | Effort | Impact |
|------|--------|--------|
| Create npm package structure | High | High |
| Publish to npm registry | Medium | High |
| npx install experience | Medium | High |

---

## 5. Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Time-to-first-value (same-org) | 5-10 min | < 1 min | Time from `init.sh` to "governance active" message |
| Time-to-first-value (cross-org) | Broken | < 2 min | Time from curl to "governance active" message |
| Post-install required steps | 4 | 0 | Count of manual steps shown |
| Concepts at install | 30+ | 3 | Count of governance concepts in install output |
| IDE auto-detection coverage | 3 IDEs | 5+ IDEs | Count of auto-detected IDE types |
| Cross-org install success rate | 0% | 95%+ | Successful installs without submodule access |

---

## 6. Proposed `init.sh --quick` Output (Mockup)

### Success Case
```
$ bash .ai/bin/init.sh --quick

  Dark Forge v4.2.0

  Setting up governance.............. done
  Detecting project.................. Python 3.11 (pyproject.toml)
  Configuring IDEs................... VS Code, Claude Code
  Verifying installation............. 12/12 checks passed

  Governance is active.
  Your PRs will be automatically reviewed for security, code quality, and compliance.

  Next: Open a PR to see governance in action.
        Run 'bash .ai/bin/governance-status.sh' to see current status.
```

### Prerequisite Missing
```
$ bash .ai/bin/init.sh --quick

  Dark Forge v4.2.0

  Checking prerequisites...
    git 2.39.0 ...................... ok
    Python .......................... not found

  Python 3.9+ is required for full governance.
  Install: brew install python3 (macOS) or apt install python3 (Linux)

  Install basic governance without Python? [Y/n]
  (Basic mode: schema validation + PR workflows. No policy engine.)
```

### Cross-Org
```
$ bash <(curl -s .../install.sh)

  Dark Forge v4.2.0 (vendored)

  Downloading governance package..... done
  Setting up governance.............. done
  Detecting project.................. Node.js (package.json)
  Configuring IDEs................... Cursor, Claude Code
  Verifying installation............. 10/12 checks passed
                                      (2 skipped: submodule-only features)

  Governance is active (Tier 2 — lightweight mode).
  Your PRs will be reviewed for security and code quality.

  To upgrade to full governance (Tier 1):
    git submodule add https://github.com/convergent-systems-co/dark-forge.git .ai
    bash .ai/bin/init.sh --refresh
```
