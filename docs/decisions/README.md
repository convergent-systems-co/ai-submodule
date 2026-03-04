# Architectural Decision Records

**Repository:** convergent-systems-co/dark-forge (Dark Forge)
**Purpose:** Trace every significant architectural decision — what was decided, why, what alternatives were rejected, and what constraints bind future work.

---

## Table of Contents

### Standalone ADRs (Retroactive)

- [ADR Template](000-template.md)
- [ADR-001: Deterministic Policy Engine](001-deterministic-policy-engine.md)
- [ADR-002: Panel-Based Review System](002-panel-based-review-system.md)
- [ADR-003: Agent Persona Model](003-agent-persona-model.md)
- [ADR-004: Git Submodule Distribution](004-submodule-distribution.md)
- [ADR-005: JIT Context Management](005-jit-context-management.md)

### Inline ADRs

1. [ADR-001: Governance-Only Repository](#adr-001-governance-only-repository)
2. [ADR-002: Three Artifact Types](#adr-002-three-artifact-types)
3. [ADR-003: Remove MCP Server Directories](#adr-003-remove-mcp-server-directories)
4. [ADR-004: Collapse Filesystem Under governance/](#adr-004-collapse-filesystem-under-governance)
5. [ADR-005: Personas as Reasoning Roles, Not Agents](#adr-005-personas-as-reasoning-roles-not-agents)
6. [ADR-006: Mandatory Panels Across All Policy Profiles](#adr-006-mandatory-panels-across-all-policy-profiles)
7. [ADR-007: Structured Emissions with Schema Validation](#adr-007-structured-emissions-with-schema-validation)
8. [ADR-008: Panel Pass/Fail Criteria and Scoring System](#adr-008-panel-passfail-criteria-and-scoring-system)
9. [ADR-009: Phase 5 as Governance Artifacts First](#adr-009-phase-5-as-governance-artifacts-first)
10. [ADR-010: Self-Contained Review Prompts over MCP Skills](#adr-010-self-contained-review-prompts-over-mcp-skills)
11. [ADR-011: Persona Consolidation into Review Prompts](#adr-011-persona-consolidation-into-review-prompts)

---

## ADR-001: Governance-Only Repository

**Date:** 2026-02-21
**Status:** Active
**Commit:** Initial repository creation

### Context

Dark Forge needed a distribution model for governance artifacts across consuming repositories.

### Decision

The repository contains zero application code. It is entirely configuration, policy, schemas, and documentation — distributed as a git submodule to consuming repos.

### Rationale

- Clean separation between governance framework and application code
- Single `git submodule update --remote .ai` pulls all governance updates
- No build system, test runner, or linter needed in the governance repo itself
- Consuming repos get the full governance stack without copying files

### Consequences

- All governance changes propagate automatically to consuming repos
- The repo cannot contain runtime code (policy engine is the single exception, evaluated deterministically)
- Framework bugs cascade to every consuming repo simultaneously

---

## ADR-002: Three Artifact Types

**Date:** 2026-02-21
**Status:** Active

### Context

The governance framework needed clear boundaries between AI-interpreted content and programmatic evaluation.

### Decision

Three artifact types with distinct properties:

| Type | Format | Purpose | Mutability |
|------|--------|---------|------------|
| **Cognitive** | Markdown | Personas, prompts, workflows — interpreted by AI | Editable |
| **Enforcement** | JSON Schema / YAML | Policies, schemas — evaluated programmatically, never by AI | Versioned |
| **Audit** | JSON + Markdown | Run manifests — immutable decision records | Append-only |

### Rationale

- AI models should never interpret policy rules — hallucination risk
- Enforcement artifacts use semantic versioning; cognitive artifacts version by git SHA
- Audit trail must be immutable for compliance (SOC2, PCI-DSS)

### Consequences

- Clear ownership: cognitive artifacts evolve with the submodule, enforcement artifacts require version bumps
- The cognitive/enforcement boundary determines what can safely migrate to external systems (see ADR-010)

---

## ADR-003: Remove MCP Server Directories

**Date:** 2026-02-21
**Status:** Active
**Commit:** `b636ebd` — `refactor: remove MCP server directories (#14)`

### Context

MCP server configs (gitignore, ServiceNow) were preset in the governance repo for easy installation.

### Decision

Remove `mcp/` directory and all MCP server references. MCP configs belong in consuming repos, not the governance framework.

### Rationale

- Governance framework defines what to evaluate, not how to connect to external services
- MCP server configurations are project-specific (different ServiceNow instances, different git providers)
- Keeping them in the submodule creates false coupling

### Consequences

- Dark Forge has zero MCP infrastructure
- Any future MCP integration must be opt-in from consuming repos or external systems
- **This decision is revisitable** — see ADR-010 for the MCP skills evaluation

---

## ADR-004: Collapse Filesystem Under governance/

**Date:** 2026-02-21
**Status:** Active
**Commit:** `75f9cca` — `refactor: collapse filesystem structure under governance/ directory (#46)`

### Context

The repo had 9 visible top-level directories for internal governance machinery, creating cognitive overhead for consuming repo developers.

### Decision

Move 7 internal governance directories (personas, policy, schemas, emissions, manifests, prompts, docs) under a single `governance/` directory.

### Rationale

- Consuming developers see 3 clean directories: `governance/`, `instructions/`, `templates/`
- Internal governance machinery is a single tree to navigate
- Path references are longer but more discoverable

### Consequences

- All governance paths are prefixed with `governance/`
- Historical plan files and manifests were left unchanged as archival records

---

## ADR-005: Personas as Reasoning Roles, Not Agents

**Date:** 2026-02-21
**Status:** Active (transitioning — see ADR-011)

### Context

The governance framework needed domain expertise for code evaluation. Two models were considered: (1) personas as standalone agents, each with their own execution context, or (2) personas as reasoning roles that a single agent adopts sequentially.

### Decision

Personas are reasoning roles — 15-25 line markdown files defining Role, Evaluate For, Output Format, Principles, and Anti-patterns. A single AI agent loads a panel, reads each persona, and role-plays each perspective sequentially.

### Rationale

At Phase 3 (2026-02-21), no multi-agent runtime existed. Claude Code and GitHub Copilot are single-session tools. Building for multi-agent execution would have been premature abstraction.

### Consequences

- 60 persona files across 13 categories (subsequently consolidated into 21 review prompts in Issue #220; deprecated files removed in Issue #257; only 7 agentic personas remain)
- One model, sequential thinking, multiple hats
- The file separation suggests a distributed system that doesn't exist at runtime
- **This is the decision that ADR-010 and ADR-011 revisit**

### Future Direction

The long-term goal is Level 5 Dark Forge where personas become independent agents that work on code concurrently. The architecture must support this transition without massive refactoring. See ADR-010 for how the current consolidation preserves this path.

---

## ADR-006: Mandatory Panels Across All Policy Profiles

**Date:** 2026-02-21
**Status:** Active
**Commit:** `31fc9fd` — `feat(governance): add mandatory panels across all policy profiles (#78)`

### Context

Some panels (threat-modeling, cost-analysis, documentation-review) were optional and only triggered by file change patterns. This meant security-critical changes could bypass threat modeling if the file patterns didn't match.

### Decision

Six panels are mandatory on every PR regardless of files changed: code-review, security-review, threat-modeling, cost-analysis, documentation-review, data-governance-review.

### Rationale

- Security review should never be skippable
- Cost analysis catches resource implications that file patterns miss
- Documentation review prevents docs from drifting

### Consequences

- Every PR runs at minimum 6 panels
- Higher token cost per review cycle
- Stronger governance guarantees

---

## ADR-007: Structured Emissions with Schema Validation

**Date:** 2026-02-24
**Status:** Active
**Commit:** `54c4c04` — `feat: add structured emission example to all 19 panel definitions (#206)`

### Context

Panel output was markdown-only. The policy engine couldn't programmatically evaluate AI-generated prose. Agents inferred incorrect output structures when producing emissions.

### Decision

All panel output must include JSON between `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers, validated against `governance/schemas/panel-output.schema.json`. Each panel definition includes a minimal valid emission example.

### Rationale

- Deterministic policy evaluation requires structured data (per ADR-002: AI never interprets policy)
- Emission examples prevent agents from guessing field names or enum values
- `findings[].persona` uses string labels (`category/kebab-case`), not file paths — decoupled from filesystem layout

### Consequences

- Missing markers or invalid JSON = panel execution failed
- The `persona` label convention (`category/kebab-case`) is the contract, not the file path
- **This decoupling is what makes ADR-011 consolidation possible** — changing file layout doesn't break emissions

---

## ADR-008: Panel Pass/Fail Criteria and Scoring System

**Date:** 2026-02-21
**Status:** Active
**Commit:** `88dcfd1` — `feat(governance): panel pass/fail criteria and scoring system (#60)`

### Context

Panels produced verdicts but had no standardized way to express confidence, thresholds, or pass/fail criteria.

### Decision

Introduced `panels.schema.json` and `panels.defaults.json` with per-panel configuration: base confidence, severity deductions, min_confidence thresholds, max finding counts, required verdicts, and compliance score thresholds.

### Rationale

- Security panels need stricter thresholds (0.90 base confidence) than documentation panels (0.80)
- Consuming repos can override defaults via local panel config
- Scoring is deterministic — same findings always produce same confidence score

### Consequences

- All 21 panels have standardized scoring
- The scoring logic lives alongside the panel definition (cognitive artifact, interpreted by AI)
- **Open question from external review:** Should scoring move to the policy engine as actual code? Currently it's numerical logic in prose that AI interprets.

---

## ADR-009: Phase 5 as Governance Artifacts First

**Date:** 2026-02-22 through 2026-02-24
**Status:** Active
**Commits:** `9d497a4` (5b retrospective), `ba82d86` (5b tuning), `426d280` (5a self-proving), `33a6a91` (5e reduced touchpoint), `37ac3f7` (5c cross-session state), and others

### Context

Phase 5 (Dark Forge) requires runtime infrastructure that doesn't exist: multi-agent orchestrators, persistent daemon capabilities, parallel session coordination. The question was whether to block on runtime infrastructure or define governance artifacts that a future runtime would implement.

### Decision

Define all Phase 5 governance artifacts (schemas, policies, workflows, protocols) as config-only artifacts in the submodule. Runtime execution is explicitly deferred until platform capabilities arrive.

### Rationale

- Governance artifacts are the **specification** for what the runtime must do
- Defining them now ensures the runtime is built to governance requirements, not the reverse
- Every artifact is independently useful for documentation and planning
- Industry research (Google DeepMind, Anthropic) confirms multi-agent runtime adds complexity that should be deferred until demonstrably beneficial

### Consequences

- Phase 5 sub-phases (5a-5e) have complete governance artifacts but no runtime
- The gap between "artifacts defined" and "runtime executing" must be clearly communicated
- **This decision sets the frame for ADR-010** — the runtime doesn't exist yet, so optimizing for it is premature, but the architecture must not block it

---

## ADR-010: Self-Contained Review Prompts over MCP Skills

**Date:** 2026-02-25
**Status:** Active
**Issue:** #220
**Research:** `docs/research/README.md` (51 sources), `docs/research/technique-comparison.md`

### Context

Issue #220 called for consolidating 58 non-agentic persona files and 19 panel files. An external review report (`dark-forge-review-report`) proposed an alternative: convert high-reuse personas (~15-20) into MCP Skills registered as tools (`skill_security_auditor`, etc.) and distribute them via the awesome-dach-copilot MCP server. Panels would become orchestrator + sub-prompt trees with Task-based delegation. Dark Forge would slim down to enforcement-only (policy engine, schemas, CI).

Research was conducted across 51 sources to evaluate both approaches.

### Decision

Self-contained review prompts. Each panel + its persona definitions consolidated into a single markdown file in `governance/prompts/reviews/`. Shared perspectives (24 appearing in 2+ panels) defined in `governance/prompts/shared-perspectives.md` for DRY authoring but inlined at review time.

### Alternatives Considered

#### Alternative A: MCP Skills via awesome-dach-copilot

**Strengths:**
- Personas become standalone developer tools accessible via MCP from any IDE
- Single source of truth via MCP tool invocation instead of filesystem references
- Free infrastructure: catalog, hybrid distribution, content hashing, search/discovery
- Clean cognitive/enforcement repo split
- Sub-prompt decomposition maps to future multi-agent execution

**Weaknesses (research-grounded):**
- **Tool count degradation:** 3 existing skills + 15-20 persona-skills + base tools = 23-28 tools. Anthropic Opus 4 drops to 49% accuracy with large tool libraries, recovers to only 74% with Tool Search. OpenAI recommends <20 functions. Microsoft Research: "expose as few tools as possible." (Sources: Anthropic Advanced Tool Use, Microsoft Research Tool-Space Interference, OpenAI)
- **Sub-prompt decomposition hurts on frontier models:** arXiv (Feb 2025) found frontier models show diminishing/negative returns from prompt decomposition. Each panel going from 1 file → 7 files creates 5 error propagation boundaries. (Source: arXiv:2602.04853)
- **Multi-agent overhead:** Google DeepMind (Dec 2025): multi-agent degrades sequential performance by 39-70%, single agents 3.2x more token-efficient, 17.2x error amplification. Panel reviews are sequential reasoning — the category where multi-agent showed worst degradation. (Source: arXiv:2512.08296)
- **Two-repo coordination cost:** Breaking changes to `panel-output.schema.json` require coordinated releases across repos.
- **No infrastructure exists:** MCP server code was deliberately removed (ADR-003, commit `b636ebd`). Zero awesome-dach-copilot references in codebase.
- **Skills ≠ Tools in Anthropic's definition:** Skills are "the recipe" — markdown instructions loaded into context, not tool registrations. Self-contained review prompts already ARE skills in this sense. (Sources: Armin Ronacher, LlamaIndex, Anthropic)

#### Alternative B: Keep 60 separate persona files (status quo)

**Strengths:**
- Single source of truth per persona
- Audit traceability from `findings[].persona` → file path
- Git blame on individual persona files
- Composability story (mix personas into custom panels)

**Weaknesses:**
- 30-42 tool calls per PR review to load persona files (60-84% of tool call budget)
- Cross-file indirection contradicts Locality of Behaviour principle
- Composability is theoretical — no consuming repo uses custom panel compositions
- The file separation implies a distributed system that doesn't exist at runtime
- Contradicts Anthropic's "start simple" guidance

### Rationale for Decision

1. **Anthropic's Voting pattern is the direct match.** "You can use voting when reviewing a piece of code for vulnerabilities, where several different prompts review and flag the code if they find a problem." Self-contained review prompts implement this pattern exactly.

2. **Performance data is conclusive for the current runtime.** All research points to single-agent, consolidated prompts being more accurate, more token-efficient, and lower-risk than decomposed multi-agent approaches — on the frontier models where the governance pipeline operates.

3. **The emission contract is decoupled from the filesystem.** `findings[].persona` uses string labels (`compliance/security-auditor`), not file paths. Changing where persona definitions live doesn't break any emission, policy evaluation, or audit trail.

4. **Self-contained prompts become agent system prompts directly.** When Phase 5d/5e arrives and personas become independent agents, each perspective section within a review prompt IS the complete context that agent needs. The decomposition path is:
   - Each perspective section → extracted into an individual agent's system prompt
   - The review prompt's scoring/aggregation → becomes the orchestrator
   - `shared-perspectives.md` → becomes the shared agent configuration
   - No massive refactoring required

5. **MCP Skills remain a valid future path.** Nothing in this consolidation prevents later extracting perspectives into MCP Skills when: (a) the runtime infrastructure exists, (b) tool count degradation is solved at the model level, and (c) standalone persona use by developers is a demonstrated need.

### Constraints on Future Work

- **Persona labels are the contract.** All emissions use `category/kebab-case` persona identifiers. Any future decomposition (agents, skills, sub-prompts) MUST preserve these labels.
- **Shared perspectives must stay canonical.** `shared-perspectives.md` is the single source of truth for cross-panel perspectives. Future agents should read from this file (or its successor), not duplicate definitions.
- **Scoring logic stays with the review prompt** (for now). If scoring moves to the policy engine (per external review recommendation), that's a separate ADR.
- **Don't close the MCP door.** ADR-003 removed MCP server code from Dark Forge, but this doesn't prevent consuming repos or external systems from wrapping review prompts as MCP resources.

### Reassessment Triggers

Revisit this decision when any of the following occur:
1. **Multi-agent runtime arrives** — Claude Code or equivalent supports parallel agent sessions with shared state
2. **Tool count degradation is solved** — Model updates push the tool-count threshold above 30+ tools without accuracy loss
3. **Standalone persona demand emerges** — Developers request individual persona access outside the governance pipeline
4. **awesome-dach-copilot integration becomes concrete** — Team decides to actively pursue the integration proposal from the external review

---

## ADR-011: Persona Consolidation into Review Prompts

**Date:** 2026-02-25
**Status:** Active
**Issue:** #220
**Commit:** `c5c4b6f` — `feat: consolidate personas and panels into self-contained review prompts (#220)`

### Context

ADR-010 decided on self-contained review prompts. This ADR documents the implementation specifics.

### Decision

#### Created (20 new files)

- `governance/prompts/shared-perspectives.md` — Canonical definitions for 24 perspectives appearing in 2+ panels
- `governance/prompts/reviews/` — 21 self-contained review prompts, each containing:
  - Purpose and context
  - Perspective definitions (inlined from personas or referencing shared-perspectives.md)
  - Scoring formula and pass/fail criteria
  - Structured emission example with correct persona labels
  - Output format matching `panel-output.schema.json`

#### Deprecated (77 files)

- 58 persona files across 13 categories — deprecation notice added, pointing to `governance/prompts/reviews/` and `shared-perspectives.md`
- 21 panel files — deprecation notice added, pointing to corresponding review prompt
- Excluded: All agentic personas in `governance/personas/agentic/` (these define decision authority, not evaluation checklists). At the time of #220, 4 agentic personas existed; the current count is 7 (Project Manager added in #464, IaC Engineer added separately, Document Writer added later).

#### Updated (15+ files)

- 7 workflow files — panel references updated to `governance/prompts/reviews/` paths
- `governance/prompts/startup.md` — copilot review reference updated
- `governance/personas/index.md` — added consolidated prompts section
- `governance/policy/collision-domains.yaml` — added `governance/prompts/reviews/**`
- Documentation: CLAUDE.md, README.md, GOALS.md, DEVELOPER_GUIDE.md, governance model

#### Persona Label Convention

All persona labels normalized to `{directory}/{kebab-case-name}` matching `governance/personas/` directory structure:

| Category | Example Label |
|----------|--------------|
| Shared (from directory) | `compliance/security-auditor`, `operations/sre`, `engineering/test-engineer` |
| Inline-only (virtual) | `ai/safety-specialist`, `external/github-copilot`, `domain/domain-expert` |
| Agentic | `agentic/tech-lead` |

#### Threat Model Template

`reviews/threat-modeling.md` embeds a standardized 7-section output template based on the proven format from `governance/emissions/threat-model.md`:
1. System Scope and Trust Boundaries
2. MITRE Specialist — ATT&CK Mapping
3. Security Auditor — Vulnerability Assessment
4. Infrastructure Engineer — Deployment Impact
5. Adversarial Reviewer — Stress Testing
6. Architect — Structural Assessment
7. Consolidated Summary

### Coexistence Strategy

Deprecated files remain in place with deprecation notices. This allows:
- Gradual migration — consuming repos can reference either path during transition
- Rollback — if issues are found with consolidated prompts, old files still work
- Removal in a future release after validation period

### Path to Phase 5 (Personas as Agents)

The consolidation is designed so that the transition to independent persona-agents requires extraction, not rewriting:

```
Phase 4 (Current):
  review-prompt.md → single agent reads all perspectives sequentially

Phase 5d (Future):
  review-prompt.md → orchestrator agent
  shared-perspectives.md → agent configuration source
  Each perspective section → individual agent's system prompt
  findings[].persona labels → unchanged (already identify which agent)
  Scoring/aggregation → orchestrator responsibility
```

The key invariant: `findings[].persona` labels are the inter-agent contract. They're strings, not file paths. Whether a persona is a section in a review prompt, a standalone file, an MCP skill, or an independent agent — the emission format doesn't change.

---

## Decision Timeline

| Date | ADR | Summary | Commit |
|------|-----|---------|--------|
| 2026-02-21 | 001 | Governance-only repository | Initial |
| 2026-02-21 | 002 | Three artifact types (cognitive/enforcement/audit) | Initial |
| 2026-02-21 | 003 | Remove MCP server directories | `b636ebd` |
| 2026-02-21 | 004 | Collapse filesystem under governance/ | `75f9cca` |
| 2026-02-21 | 005 | Personas as reasoning roles, not agents | Initial |
| 2026-02-21 | 006 | Mandatory panels across all policy profiles | `31fc9fd` |
| 2026-02-21 | 008 | Panel pass/fail criteria and scoring system | `88dcfd1` |
| 2026-02-22–24 | 009 | Phase 5 as governance artifacts first | Multiple |
| 2026-02-24 | 007 | Structured emissions with schema validation | `54c4c04` |
| 2026-02-25 | 010 | Self-contained prompts over MCP Skills | `c5c4b6f` |
| 2026-02-25 | 011 | Persona consolidation into review prompts | `c5c4b6f` |

---

## References

- `docs/research/README.md` — 51-source research file informing ADR-010
- `docs/research/technique-comparison.md` — Research deliverable comparing consolidation techniques
- `governance/schemas/panel-output.schema.json` — The inter-agent emission contract
- `governance/policy/default.yaml` — Required panels and confidence weighting
- External review report (2026-02-25) — Proposed MCP Skills architecture via awesome-dach-copilot
