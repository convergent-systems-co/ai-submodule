# Competitive Teardown: DACH Awesome Copilot Install Experience

**Issue:** #701 — UX Review: installation experience for consuming repos
**Date:** 2026-03-02
**Author:** Coder (automated)

---

## Executive Summary

DACH Awesome Copilot achieves superior developer experience scores through three key strategies: (1) single-purpose install command, (2) zero-config IDE auto-detection, and (3) catalog-first discovery. This teardown documents exactly what DACH does and identifies which patterns are transferable to AI-Submodule's submodule architecture.

---

## 1. DACH Install Flow Analysis

### Command

```bash
gh auth login --scopes read:packages
npx @jm-packages/dach-prompts install
```

### What `npx install` Does (Inferred from Evaluation)

1. **Detects installed IDEs** — scans for VS Code, Cursor, Claude Desktop, Copilot CLI, Claude Code, JetBrains config directories
2. **Downloads prompt catalog** — fetches `catalog.json` from npm package
3. **Installs prompts per IDE** — writes prompts to each detected IDE's config location
4. **Reports results** — shows which IDEs were configured and how to access prompts

### Time Budget

| Phase | Duration | Notes |
|-------|----------|-------|
| gh auth | 30s | One-time; may already be done |
| npx download | 5-10s | npm package cached after first run |
| IDE detection | 1-2s | File system checks only |
| Prompt installation | 1-2s | Write JSON/YAML configs |
| **Total** | **~15s** (after auth) | |

### Key Design Decisions

1. **npm as distribution channel** — no git submodule dependency; works cross-org via npm registry
2. **`npx` for zero-install execution** — no local setup required beyond Node.js
3. **No configuration required** — auto-detects everything; no project.yaml equivalent
4. **Catalog-first** — users can browse prompts before installing
5. **IDE-native integration** — prompts appear in IDE's native prompt UI, not a separate tool

---

## 2. UX Pattern Analysis

### Pattern 1: Single-Purpose Command

**DACH:** `npx @jm-packages/dach-prompts install` does ONE thing — installs prompts into IDEs.

**AI-Submodule:** `bash .ai/bin/init.sh` does 9 things — symlinks, workflows, emissions, directories, config, CODEOWNERS, deps, MCP.

**Transferable?** Yes. Create a single-purpose entry point: `bash .ai/bin/init.sh --quick` already exists but still runs the full 9-step pipeline. Refactor to do only the essential steps by default.

### Pattern 2: Zero-Config Auto-Detection

**DACH:** Detects 6 IDEs without any user input. No config files, no flags, no questions.

**AI-Submodule:** MCP installer (`mcp-server/install.sh`) detects 3 IDEs (Claude Code, VS Code, Cursor). Missing: Claude Desktop, JetBrains.

**Transferable?** Yes. Extend IDE detection to match DACH's 6-IDE coverage. Add Claude Desktop and JetBrains.

### Pattern 3: Catalog-First Discovery

**DACH:** `catalog.json` provides browsable prompt inventory. Users can see what they're getting before installing.

**AI-Submodule:** No equivalent. Users must read the 524-line README or browse `governance/prompts/` directory.

**Transferable?** Yes. Create a `docs/catalog.html` (already exists at `docs/catalog.html`) or enhance it to be the primary entry point. Interactive prompt/panel/persona browser.

### Pattern 4: Progressive Disclosure

**DACH:** Install shows only success/failure. Details available via `--verbose`. Prompts are organized by namespace (security, code-review, testing) — user discovers as needed.

**AI-Submodule:** Install outputs all 9 steps. Post-install shows 4 next-steps requiring concept understanding.

**Transferable?** Yes. Default to quiet output with progress indicator. Show "Governance active. Run `governance status` for details."

### Pattern 5: npm Distribution (Cross-Org)

**DACH:** npm registry means any repo can install, regardless of GitHub org. `read:packages` scope is the only auth requirement.

**AI-Submodule:** Private git submodule means only same-org repos can install. Cross-org is broken.

**Transferable?** Partially. We could publish a governance npm package for cross-org distribution, but our governance is deeper than prompt installation — it includes workflows, schemas, policy engine. A hybrid approach (npm for lightweight, submodule for full) may be needed.

---

## 3. Score Gap Analysis

### Ease of Adoption (AI-Sub: 3/5, DACH: 4/5)

| Factor | DACH | AI-Submodule | Gap Cause |
|--------|------|-------------|-----------|
| Install commands | 2 | 2-4 | More flags needed for full setup |
| Prerequisites | Node.js only | Python 3.9+, gh CLI, git | More dependencies |
| Post-install steps | 0 | 4 | Template copy, persona config, profile, MCP |
| Works cross-org | Yes | No | Private submodule |

### Cognitive Load (AI-Sub: 2/5, DACH: 4/5)

| Factor | DACH | AI-Submodule | Gap Cause |
|--------|------|-------------|-----------|
| Concepts at install | 1 (prompts) | 30+ (personas, panels, profiles, schemas, emissions...) | No progressive disclosure |
| Documentation entry point | Catalog (browsable) | README (524 lines) | No guided path |
| Mental model required | "prompts for your IDE" | "governance platform with 5 layers" | Scope difference |

### Time-to-First-Value (AI-Sub: 4/5, DACH: 5/5)

| Factor | DACH | AI-Submodule | Gap Cause |
|--------|------|-------------|-----------|
| Time to install | ~15s | 2-3 min | Multi-step pipeline |
| Time to first use | 0 (prompts immediately available) | 5+ min (needs project.yaml) | Configuration required |
| Time to understand value | Immediate (see prompts in IDE) | Days (must submit PR to see governance) | Value not visible until PR |

---

## 4. Transferable UX Patterns (Ranked by Impact)

### Must Adopt

1. **Auto-detect project and create project.yaml automatically** — eliminate the manual template copy step entirely
2. **Quiet-by-default output** — show only success/failure; `--verbose` for details
3. **Consolidate to one command** — `bash .ai/bin/init.sh --quick` should do everything including deps and MCP
4. **Match 6-IDE auto-detection** — add Claude Desktop and JetBrains to MCP installer

### Should Adopt

5. **Cross-org distribution via npm** — publish `@set-apps/ai-governance` for npx install
6. **Interactive catalog page** — enhance `docs/catalog.html` as the primary discovery interface
7. **Show governance value immediately** — after install, run a demo governance check on the repo

### Consider

8. **GitHub App for org-wide deployment** — significant effort but highest cross-org impact
9. **VS Code extension** — one-click marketplace install for IDE integration

---

## 5. Architecture Constraints

Unlike DACH (which distributes prompt files), AI-Submodule distributes a **governance platform**:

| Component | DACH | AI-Submodule |
|-----------|------|-------------|
| What's distributed | Prompt markdown files | Policy engine, schemas, workflows, prompts, personas, MCP server |
| Runtime dependency | None (prompts are static) | Python 3.9+, policy engine |
| CI integration | None | GitHub Actions workflows |
| Config required | None | project.yaml (language, personas, policy profile) |

This means we cannot achieve DACH's zero-config simplicity for the **full** governance experience. But we can:
1. **Tier the experience** — basic governance (Tier 2: emission validation only) needs zero config; full governance (Tier 1: policy engine) needs project.yaml
2. **Generate defaults** — auto-detect language and create project.yaml with sensible defaults
3. **Defer complexity** — install the platform silently; introduce concepts as the user encounters them (progressive disclosure)
