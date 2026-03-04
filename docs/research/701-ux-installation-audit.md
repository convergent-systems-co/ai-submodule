# UX Installation Audit: AI-Submodule

**Issue:** #701 — UX Review: installation experience for consuming repos
**Date:** 2026-03-02
**Author:** Coder (automated)

---

## Executive Summary

The AI-Submodule installation experience requires 5-10 minutes and substantial pre-existing knowledge for same-org installation, and is effectively **broken** for cross-org installation. This audit identifies specific friction points in each step and proposes measurable improvements.

---

## 1. Same-Org Installation Audit (`init.sh`)

### Current Flow

```
Step 1: git submodule add https://github.com/convergent-systems-co/dark-forge.git .ai
Step 2: bash .ai/bin/init.sh
```

Or with `--quick`:
```
Step 1: bash .ai/bin/init.sh --quick
```

### Step-by-Step Analysis

| Step | Action | Time | Friction |
|------|--------|------|----------|
| 0 | Prerequisites: Python 3.9+, gh CLI | 2-10 min | **HIGH** — users may not have Python 3.9+ or gh CLI installed; no upfront check |
| 1 | Python detection (`check-python.sh`) | 2s | Low — auto-detects python3/python |
| 2 | Submodule freshness (`update-submodule.sh`) | 3s | Low — transparent |
| 3 | Symlink creation (`create-symlinks.sh`) | 1s | **MEDIUM** — creates CLAUDE.md, copilot-instructions.md, .claude/commands; user doesn't know what these are |
| 4 | Workflow setup (`setup-workflows.sh`) | 2s | **MEDIUM** — copies GitHub Actions workflows; user doesn't understand governance workflows |
| 5 | Emission validation (`validate-emissions.sh`) | 1s | **HIGH** — concept of "emissions" is not self-explanatory |
| 6 | Directory setup (`setup-directories.sh`) | 1s | Low — creates `.artifacts/` subdirectories |
| 7 | Dependency installation (optional `--install-deps`) | 30-60s | **MEDIUM** — separate flag required; not part of default flow |
| 8 | Repository configuration (`setup-repo-config.sh`, `setup-codeowners.sh`) | 3s | **MEDIUM** — CODEOWNERS generation is opaque |
| 9 | MCP server (optional `--mcp`) | 30-60s | **HIGH** — separate flag, requires npm, requires manual IDE restart |

### Time-to-First-Value

| Scenario | Time | Notes |
|----------|------|-------|
| Experienced user (has prerequisites) | 2-3 min | git submodule add + init.sh + template copy |
| New user (needs prerequisites) | 5-15 min | Install Python, gh CLI, then the above |
| Full setup (deps + MCP) | 5-10 min | Add --install-deps and --mcp flags |

### Post-Install Next Steps (Currently Required)

```
1. Copy a language template:  cp .ai/governance/templates/python/project.yaml project.yaml
2. Customize personas and conventions in project.yaml
3. Set governance profile:    governance.policy_profile: default
4. Install MCP server:       bash .ai/bin/init.sh --mcp
```

**Problem:** These next steps require understanding templates, personas, conventions, policy profiles, and MCP servers. A new user has zero context for any of these.

### Friction Summary

| Category | Score (1-5) | Notes |
|----------|:-----------:|-------|
| Number of commands | 2/5 | 2-4 commands minimum |
| Prerequisites transparency | 1/5 | No upfront dependency check |
| Concept introduction | 1/5 | Immediately shows 30+ concepts |
| Error messaging | 3/5 | init.sh reports errors but doesn't guide fixes |
| Idempotency | 5/5 | Safe to re-run |
| Post-install guidance | 2/5 | Shows next steps but doesn't explain them |

---

## 2. Cross-Org Installation Audit

### Current State: Broken

Cross-org repos (outside SET-Apps) cannot clone the private submodule without explicit credential configuration. This means:

1. `git submodule add` fails with authentication error
2. CI/CD pipelines fail because they lack submodule access tokens
3. No documented workaround for cross-org consumers

### Fallback: Tier 2 Lightweight Validation

The vendored engine (`governance/bin/vendor-engine.sh`) partially addresses this by copying the policy engine into consuming repos. However:

- Requires running `init.sh` first (chicken-and-egg: can't run init.sh without the submodule)
- Massively reduced governance (emission validation only, no full policy engine)
- No documentation on how to use Tier 2 independently

### Cross-Org Distribution Options

| Method | Feasibility | Pros | Cons |
|--------|:----------:|------|------|
| Public submodule | Low | Zero friction | Exposes proprietary governance |
| npm package | High | `npx` one-command install | Requires npm registry; governance split across package + repo |
| GitHub template repo | Medium | Fork-and-customize | No automatic updates; drift |
| Vendored release tarball | Medium | No submodule dependency | Manual updates; version drift |
| GitHub App installation | High | Automated, cross-org | Significant engineering effort |

---

## 3. First-Run Experience Comparison

### DACH Awesome Copilot

| Time | Action | User sees |
|------|--------|-----------|
| 0:00 | Browse catalog at catalog.html | Organized prompts by namespace |
| 0:30 | `npx @jm-packages/dach-prompts install` | Auto-detection of 6 IDEs |
| 1:00 | Done | Prompts available in IDE |

**Key insight:** DACH's install does ONE thing (configure IDE prompts). User understands immediately what they got.

### AI-Submodule

| Time | Action | User sees |
|------|--------|-----------|
| 0:00 | Read README (524 lines) | 7 personas, 21 panels, 6 policy profiles, orchestrator CLI |
| 2:00 | `git submodule add ... && bash .ai/bin/init.sh` | 9-step pipeline output |
| 3:00 | Read "Next steps" | Copy template, customize personas, set profile, install MCP |
| 5:00 | Copy template, edit project.yaml | Must understand personas, conventions, profiles |
| 10:00 | Maybe done | Still unclear what governance "does" for them |

**Key insight:** AI-Submodule's install does MANY things and requires understanding of the governance model before first value.

### What Is Our "Browse the Catalog" Equivalent?

**We don't have one.** The closest equivalent would be a web page showing:
- "Here's what governance does for your PRs" (3 bullet points)
- "Here's how to add it to your repo" (1 command)
- "Here's what a governed PR looks like" (screenshot/example)

---

## 4. Specific Recommendations

### Immediate (Low Effort)

1. **Add prerequisite check at top of init.sh** — check for Python, gh CLI, git before proceeding; show install commands for missing tools
2. **Reduce post-install "Next steps" to 1 step** — auto-detect language and create project.yaml with sensible defaults
3. **Add `--everything` flag** — combines `--install-deps --mcp` for users who want full setup in one command

### Medium Effort

4. **Auto-detect project language** — scan for package.json, requirements.txt, go.mod, *.csproj to auto-select the right project.yaml template
5. **Silent mode by default** — show a progress bar instead of 9 steps of output; use `--verbose` for details
6. **Consolidate MCP into default install** — if npm is available, install MCP server by default (skip silently if npm missing)

### High Effort

7. **npm distribution package** — `npx @set-apps/ai-governance install` for cross-org consumers
8. **GitHub App** — one-click installation from GitHub Marketplace for org-wide deployment
9. **Web-based quickstart** — interactive page that generates the install command with pre-configured options
