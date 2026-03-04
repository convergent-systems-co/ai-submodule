# Comparative Analysis: awesome-dach-copilot vs. dark-forge

**Date:** 2026-02-27
**Issue:** [#424](https://github.com/convergent-systems-co/dark-forge/issues/424)
**Status:** Proposed

---

## 1. Repository Overview

### awesome-dach-copilot

A **prompt engineering knowledge base and distribution platform**. Curates 68 AI prompts across 3 namespaces (`global/`, `dachz/`, `compoz/`), distributes them via a TypeScript MCP server (`@jm-packages/dach-prompts`), and runs a fully autonomous issue-to-PR pipeline powered by GitHub Copilot CLI. Includes AKS deployment infrastructure, a 7-category documentation framework, and an interactive catalog on GitHub Pages.

- **Repo:** `SET-Apps/awesome-dach-copilot`
- **Language:** Python (primary), TypeScript (MCP server)
- **License:** MIT
- **Activity:** 830+ issues, ~3:1 bot-to-human commit ratio, weekly releases
- **Maturity:** Production (v1.7.0)

### dark-forge

An **AI governance framework for autonomous software delivery**. Provides 19 consolidated review panels, a deterministic Python policy engine, 26 JSON schemas, 5 policy profiles and 4 supporting policy configurations (plus 14 future Phase 5 configurations), and a 7-persona agentic architecture. Distributed as a git submodule (`.ai/`) to consuming repositories.

- **Repo:** `convergent-systems-co/dark-forge`
- **Language:** Python (policy engine), Bash/PowerShell (bootstrap)
- **License:** Internal
- **Activity:** Steady governance-focused development
- **Maturity:** Phase 4b (Autonomous Remediation)

---

## 2. Architecture Comparison

```mermaid
graph TB
    subgraph ADC["awesome-dach-copilot"]
        direction TB
        ADC_PROMPTS["68 Prompts<br/>global / dachz / compoz"]
        ADC_MCP["MCP Server<br/>TypeScript STDIO"]
        ADC_CATALOG["Interactive Catalog<br/>GitHub Pages"]
        ADC_AGENTIC["Agentic Loop<br/>Copilot CLI + Multi-Model"]
        ADC_DEPLOY["AKS Deployment<br/>Bicep + Helm"]
        ADC_DOCS["7-Category Docs<br/>18 ADRs"]

        ADC_PROMPTS --> ADC_MCP
        ADC_PROMPTS --> ADC_CATALOG
        ADC_PROMPTS --> ADC_AGENTIC
        ADC_AGENTIC --> ADC_DEPLOY
    end

    subgraph AIS["dark-forge"]
        direction TB
        AIS_PANELS["19 Review Panels<br/>Voting Pattern"]
        AIS_ENGINE["Policy Engine<br/>Python Deterministic"]
        AIS_SCHEMAS["26 JSON Schemas<br/>Enforcement"]
        AIS_POLICY["5 Policy Profiles<br/>Risk-Tiered"]
        AIS_PERSONAS["5 Agentic Personas<br/>Prompt-Chained"]
        AIS_NAMING["Azure Naming CLI<br/>100+ Resource Types"]

        AIS_PANELS --> AIS_ENGINE
        AIS_SCHEMAS --> AIS_ENGINE
        AIS_POLICY --> AIS_ENGINE
        AIS_PERSONAS --> AIS_PANELS
    end

    ADC_MCP -->|"Serves to"| IDES["Any MCP IDE<br/>VS Code, Claude Code,<br/>Cursor, JetBrains"]
    AIS_ENGINE -->|"Submodule .ai/"| REPOS["Consuming<br/>Repositories"]
```

---

## 3. Capability Matrix

```mermaid
graph LR
    subgraph "awesome-dach-copilot Strengths"
        A1["MCP Distribution"]
        A2["Multi-Model Execution"]
        A3["Interactive Catalog"]
        A4["Dev Containers"]
        A5["Plan-Driven 5-Prompt Chain"]
        A6["Agentic Label System"]
    end

    subgraph "dark-forge Strengths"
        B1["Deterministic Policy Engine"]
        B2["Structured Emissions + Schemas"]
        B3["Risk-Tiered Policy Profiles"]
        B4["7-Persona Architecture"]
        B5["Context Management"]
        B6["Azure Resource Naming"]
    end

    subgraph "Shared"
        C1["Conventional Commits"]
        C2["Plan-First Development"]
        C3["Autonomous Issue Processing"]
        C4["jm-compliance.yml"]
    end

    style A1 fill:#4CAF50,color:#fff
    style A2 fill:#4CAF50,color:#fff
    style A3 fill:#4CAF50,color:#fff
    style B1 fill:#2196F3,color:#fff
    style B2 fill:#2196F3,color:#fff
    style B3 fill:#2196F3,color:#fff
    style B4 fill:#2196F3,color:#fff
    style B5 fill:#2196F3,color:#fff
```

---

## 4. Benefits

### awesome-dach-copilot

| Benefit | Detail |
|---------|--------|
| **MCP Distribution** | Serves prompts to any MCP-compatible IDE via `npx` or Docker. Multi-IDE reach without requiring submodule setup. |
| **Multi-Model Execution** | Agentic loop supports Claude Opus 4.6, Sonnet 4, GPT-5-mini, GPT-4.1. Model selection per task type. |
| **Interactive Catalog** | Searchable GitHub Pages dashboard with maturity visualization. Lowers prompt discoverability barrier. |
| **High Automation Velocity** | 830+ issues processed, 3:1 bot-to-human commit ratio. Weekly releases. |
| **Plan-Driven 5-Prompt Chain** | create → review → refine → execute → complete with multi-model validation. |
| **Dev Containers** | Pre-configured with corporate CA certs and post-create scripts. Zero-friction onboarding. |
| **Agentic Label System** | Clean state machine: `agentic-ready` → `agentic-in-progress` → `agentic-feedback-needed`. |

### dark-forge

| Benefit | Detail |
|---------|--------|
| **Deterministic Policy Engine** | Confidence-weighted panel aggregation. Machine-evaluates structured emissions. Produces auditable merge decisions. |
| **Structured Emissions** | JSON output validated against schemas between `STRUCTURED_EMISSION_START/END` markers. Machine-readable, auditable. |
| **Risk-Tiered Profiles** | `default`, `fin_pii_high` (SOC2/PCI-DSS/HIPAA/GDPR), `infrastructure_critical`, `reduced_touchpoint`. |
| **7-Persona Architecture** | Project Manager, DevOps Engineer, Team Lead, Coder, IaC Engineer, Tester, Document Writer with typed inter-agent protocol. |
| **Context Management** | 4-tier JIT loading, 80% capacity hard stop, checkpoint/resumption. Prevents context overflow. |
| **Version-Pinned Governance** | Git submodule guarantees consuming repos get the exact governance version they pin to. |
| **Azure Naming** | 100+ resource types, deterministic shortening, JM convention compliance. |
| **26 JSON Schemas** | Enforcement artifacts for panel output, manifests, baselines, autonomy metrics, conflict detection, formal specs. |

---

## 5. Problems

### awesome-dach-copilot

```mermaid
graph TD
    P1["No Deterministic<br/>Policy Engine"] -->|"Impact"| I1["Merge decisions rely on<br/>labels and human judgment"]
    P2["Copilot CLI<br/>Dependency"] -->|"Impact"| I2["Single point of failure<br/>for autonomous pipeline"]
    P3["No Structured<br/>Emissions"] -->|"Impact"| I3["Cannot programmatically<br/>audit review quality"]
    P4["Prompt Sprawl<br/>Risk"] -->|"Impact"| I4["68 prompts without<br/>governance rigor can drift"]
    P5["Single-Repo<br/>Scope"] -->|"Impact"| I5["No governance propagation<br/>to consuming projects"]
    P6["No Compliance<br/>Profiles"] -->|"Impact"| I6["Cannot enforce SOC2/<br/>PCI-DSS/HIPAA/GDPR"]
    P7["No Context<br/>Management"] -->|"Impact"| I7["Long sessions risk<br/>silent context overflow"]

    style P1 fill:#f44336,color:#fff
    style P3 fill:#f44336,color:#fff
    style P6 fill:#f44336,color:#fff
```

### dark-forge

```mermaid
graph TD
    Q1["No Prompt<br/>Distribution"] -->|"Impact"| J1["Prompts only accessible<br/>via submodule filesystem"]
    Q2["Higher Adoption<br/>Overhead"] -->|"Impact"| J2["Submodule setup, init.sh,<br/>Python venv required"]
    Q3["Governance<br/>Ceremony"] -->|"Impact"| J3["Plan → panels → emissions<br/>→ policy for every change"]
    Q4["No Multi-Model<br/>Execution"] -->|"Impact"| J4["Designed primarily<br/>for Claude Code"]
    Q5["No Interactive<br/>Catalog"] -->|"Impact"| J5["Discoverability limited<br/>to reading markdown files"]
    Q6["No MCP Server"] -->|"Impact"| J6["Cannot serve governance<br/>prompts to arbitrary IDEs"]

    style Q1 fill:#FF9800,color:#fff
    style Q6 fill:#FF9800,color:#fff
```

---

## 6. Adoption Recommendation

### From awesome-dach-copilot — adopt into dark-forge:

1. **MCP Server distribution** — Serve review prompts and governance tools to any IDE
2. **Interactive catalog + GitHub Pages dashboard** — Visual discoverability for panels and policies
3. **Multi-model agentic execution** — Resilience via multiple LLM backends
4. **Plan-driven 5-prompt chain** — Richer plan lifecycle than current template
5. **Agentic label system** — Visible state machine for issue processing
6. **Dev containers** — Zero-friction onboarding for new contributors

### From dark-forge — retain and strengthen:

1. **Deterministic policy engine** — Non-negotiable for trustworthy autonomy
2. **Structured emissions with schema validation** — Auditable, enforceable governance
3. **Risk-tiered policy profiles** — SOC2/PCI-DSS/HIPAA/GDPR compliance
4. **7-persona agentic architecture** — Architecturally superior to Copilot CLI loops
5. **Context management** — Essential for reliable long-running sessions
6. **Submodule distribution** — Version-pinned governance enforcement
7. **Azure resource naming** — Enterprise-specific value

---

## 7. Integration Driver

**The dark-forge should be the driver.**

```mermaid
graph TB
    subgraph "Why dark-forge drives"
        R1["Governance = Control Plane<br/>Prompts = Data Plane"]
        R2["Submodule = Correct for<br/>version-pinned enforcement"]
        R3["Policy engine + 26 schemas<br/>= harder problem already solved"]
        R4["Compliance requires<br/>deterministic evaluation"]
    end

    R1 --> CONCLUSION["dark-forge drives governance<br/>MCP server is additive distribution"]
    R2 --> CONCLUSION
    R3 --> CONCLUSION
    R4 --> CONCLUSION

    style CONCLUSION fill:#2196F3,color:#fff
```

**Rationale:**
- Governance is the control plane; prompts are the data plane. You can add distribution to governance; you cannot retroactively add deterministic enforcement to a prompt library.
- Submodule distribution is structurally correct for governance — consuming repos pin to a version.
- The dark-forge has the harder problem solved (policy engine, schemas, personas). An MCP server is additive.
- SOC2/PCI-DSS/HIPAA/GDPR compliance demands auditable, deterministic policy evaluation.

---

## 8. Integration Plan

### Phase Overview

```mermaid
gantt
    title MCP Server Integration Roadmap
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d

    section Phase 1 - Prompt Absorption
    Import global prompts              :p1a, 2026-03-03, 5d
    Map maturity metadata              :p1b, after p1a, 3d
    Add catalog generation             :p1c, after p1b, 3d

    section Phase 2 - MCP Server
    Scaffold TypeScript server         :p2a, 2026-03-14, 5d
    Implement MCP Resources            :p2b, after p2a, 5d
    Implement MCP Tools                :p2c, after p2b, 5d
    Implement MCP Prompts              :p2d, after p2c, 3d
    Installer scripts                  :p2e, after p2d, 3d
    Docker + npm publishing            :p2f, after p2e, 3d

    section Phase 3 - Multi-Model
    Abstract execution backend         :p3a, 2026-04-13, 5d
    Add Copilot CLI backend            :p3b, after p3a, 5d
    Model selection per task type      :p3c, after p3b, 3d

    section Phase 4 - Dashboard
    GitHub Pages deployment            :p4a, 2026-05-01, 5d
    Interactive governance dashboard   :p4b, after p4a, 5d
    Searchable prompt catalog          :p4c, after p4b, 5d

    section Phase 5 - Consumer Migration
    awesome-dach-copilot adds .ai/    :p5a, 2026-05-18, 5d
    Merge MCP servers                  :p5b, after p5a, 5d
    Domain prompts as extensions       :p5c, after p5b, 3d
```

### Phase 1: Prompt Absorption

**Goal:** Import awesome-dach-copilot's reusable prompts into dark-forge.

```mermaid
flowchart LR
    ADC_GLOBAL["awesome-dach-copilot<br/>global/ (45 prompts)"]
    ADC_META["Frontmatter Metadata<br/>maturity, tags, category"]

    AIS_LIBRARY["dark-forge<br/>governance/prompts/library/"]
    AIS_CATALOG["catalog.json<br/>+ schema validation"]

    ADC_GLOBAL -->|"Import"| AIS_LIBRARY
    ADC_META -->|"Map to"| AIS_CATALOG

    style AIS_LIBRARY fill:#4CAF50,color:#fff
    style AIS_CATALOG fill:#4CAF50,color:#fff
```

**Tasks:**
1. Create `governance/prompts/library/` for imported prompts
2. Import `global/` prompts from awesome-dach-copilot (skip `dachz/` and `compoz/` — those are domain-specific)
3. Map prompt maturity statuses (Production/Beta/Concept) to dark-forge schema metadata
4. Add `catalog.json` generation script to `governance/bin/`
5. Validate catalog against a new `governance/schemas/catalog.schema.json`

**What stays in awesome-dach-copilot:** `dachz/` and `compoz/` prompts (team-specific), AKS deployment configs, presentation materials.

### Phase 2: MCP Server (Issue #424)

**Goal:** TypeScript STDIO MCP server distributing governance prompts and tools.

```mermaid
flowchart TB
    subgraph "MCP Server (mcp-server/)"
        direction TB
        INDEX["index.ts<br/>Server entry point"]
        RESOURCES["resources.ts<br/>Resource registration"]
        TOOLS["tools.ts<br/>Tool registration"]
        PROMPTS_MCP["prompts.ts<br/>Prompt registration"]
        INSTALL["install.ts<br/>Multi-IDE installer"]
    end

    subgraph "MCP Resources (read-only)"
        R1["19 Review Panels"]
        R2["10 Workflow Templates"]
        R3["7 Persona Definitions"]
        R4["Shared Perspectives"]
        R5["Policy Profile Summaries"]
        R6["Imported Prompt Library"]
    end

    subgraph "MCP Tools (executable)"
        T1["validate_emission<br/>Schema validation"]
        T2["check_policy<br/>Policy engine dry-run"]
        T3["generate_name<br/>Azure naming CLI"]
        T4["list_panels<br/>Panel metadata"]
        T5["list_policy_profiles<br/>Profile descriptions"]
    end

    subgraph "MCP Prompts (invocable)"
        MP1["governance_review<br/>Run a review panel"]
        MP2["plan_create<br/>Generate plan from template"]
        MP3["threat_model<br/>Run threat model"]
    end

    RESOURCES --> R1 & R2 & R3 & R4 & R5 & R6
    TOOLS --> T1 & T2 & T3 & T4 & T5
    PROMPTS_MCP --> MP1 & MP2 & MP3

    subgraph "Distribution"
        NPM["npx @jm-packages/<br/>dark-forge-mcp"]
        DOCKER["Docker GHCR<br/>ghcr.io/set-apps/<br/>dark-forge-mcp"]
        INSTALLER["install.sh / install.ps1<br/>Auto-configure IDEs"]
    end

    INDEX --> NPM & DOCKER
    INSTALL --> INSTALLER
```

**Tasks:**
1. Scaffold `mcp-server/` with TypeScript, `@modelcontextprotocol/sdk`, `zod`, `gray-matter`
2. Implement resource serving for all review prompts, workflows, personas, and library prompts
3. Implement tools wrapping the policy engine (`python governance/bin/policy-engine.py`) and naming CLI
4. Implement prompts for governance review, plan creation, and threat modeling
5. Build multi-IDE installer scripts (Claude Code `~/.claude.json`, VS Code `settings.json`, Cursor)
6. Publish to npm (`@jm-packages/dark-forge-mcp`) and GHCR
7. Add manifest-based integrity tracking (content hashes per resource)
8. Update `init.sh` with `--install-mcp` flag

**Key constraint:** The MCP server is a **distribution layer only**. It does not replace the policy engine or submodule enforcement. Consuming repos with the submodule still get full governance; the MCP server provides access to repos that don't have it.

### Phase 3: Multi-Model Execution

**Goal:** Abstract the agentic loop to support multiple LLM backends.

```mermaid
flowchart TB
    ORCHESTRATOR["Team Lead<br/>(Orchestrator)"]

    subgraph "Execution Backends"
        CLAUDE["Claude Code<br/>(Primary)"]
        COPILOT["Copilot CLI<br/>(Secondary)"]
        FUTURE["Future Backends<br/>(Extensible)"]
    end

    subgraph "Contract"
        EMISSIONS["Structured Emissions<br/>panel-output.schema.json"]
    end

    ORCHESTRATOR -->|"Dispatch"| CLAUDE
    ORCHESTRATOR -->|"Dispatch"| COPILOT
    ORCHESTRATOR -->|"Dispatch"| FUTURE

    CLAUDE -->|"Produces"| EMISSIONS
    COPILOT -->|"Produces"| EMISSIONS
    FUTURE -->|"Produces"| EMISSIONS

    EMISSIONS -->|"Evaluated by"| ENGINE["Policy Engine<br/>(Backend-Agnostic)"]

    style EMISSIONS fill:#FF9800,color:#fff
    style ENGINE fill:#2196F3,color:#fff
```

**Tasks:**
1. Define execution backend interface (input: issue context + plan; output: structured emission)
2. Refactor Coder persona dispatch to use backend abstraction
3. Add Copilot CLI backend (leveraging awesome-dach-copilot's agentic loop pattern)
4. Implement model selection per task type in `project.yaml` configuration
5. Structured emissions remain the universal contract — backend-agnostic

### Phase 4: Dashboard & Catalog

**Goal:** Interactive governance dashboard and searchable prompt catalog on GitHub Pages.

**Tasks:**
1. Add `mkdocs` GitHub Pages deployment workflow (already has `mkdocs.yml`)
2. Build interactive governance dashboard showing panel results, policy decisions, autonomy metrics
3. Add searchable prompt/panel catalog with maturity visualization
4. Agentic workflow visualization (session timelines, agent interactions)
5. Adopt awesome-dach-copilot's synthwave aesthetic for diagrams (optional)

### Phase 5: Consumer Migration

**Goal:** awesome-dach-copilot becomes a governed consumer of dark-forge.

```mermaid
flowchart TB
    subgraph "dark-forge (Driver)"
        GOV["Governance Engine"]
        MCP_CENTRAL["Central MCP Server"]
        PROMPTS_CENTRAL["Central Prompt Library"]
    end

    subgraph "awesome-dach-copilot (Consumer)"
        SUBMOD[".ai/ submodule"]
        DOMAIN["Domain Prompts<br/>dachz/ compoz/"]
        AKS["AKS Deployment<br/>(Retained)"]
        ADC_MCP_OLD["Original MCP Server<br/>(Deprecated)"]
    end

    GOV -->|"submodule"| SUBMOD
    MCP_CENTRAL -->|"serves"| DOMAIN
    SUBMOD -->|"enforces governance on"| DOMAIN
    ADC_MCP_OLD -.->|"merged into"| MCP_CENTRAL

    subgraph "End State"
        ES1["Domain prompts extend<br/>central library"]
        ES2["Agentic loop gains<br/>structured emissions"]
        ES3["Policy engine enforces<br/>prompt quality"]
    end

    DOMAIN --> ES1
    SUBMOD --> ES2
    GOV --> ES3

    style ADC_MCP_OLD fill:#f44336,color:#fff
    style MCP_CENTRAL fill:#4CAF50,color:#fff
```

**Tasks:**
1. awesome-dach-copilot adds `.ai/` submodule and runs `init.sh`
2. Its prompts gain structured emission tracking and policy evaluation
3. Domain-specific prompts (`dachz/`, `compoz/`) register as extensions in `project.yaml`
4. Original MCP server (`@jm-packages/dach-prompts`) deprecated in favor of central MCP server
5. Central MCP server serves domain extensions alongside governance prompts

---

## 9. End-State Architecture

```mermaid
graph TB
    subgraph "dark-forge (.ai/)"
        direction TB

        subgraph "Governance Core"
            ENGINE["Policy Engine"]
            SCHEMAS["26 Schemas"]
            POLICY["5 Policy Profiles"]
            PERSONAS["7 Personas"]
        end

        subgraph "Review System"
            PANELS["19 Review Panels"]
            EMISSIONS["Structured Emissions"]
            MANIFESTS["Audit Manifests"]
        end

        subgraph "Prompt Library (New)"
            LIBRARY["Absorbed global/ prompts"]
            CATALOG["catalog.json"]
        end

        subgraph "MCP Server (New)"
            MCP["TypeScript STDIO"]
            MCP_RES["Resources"]
            MCP_TOOLS["Tools"]
            MCP_PROMPTS["Prompts"]
        end

        subgraph "Execution Layer (Enhanced)"
            CLAUDE_BE["Claude Code Backend"]
            COPILOT_BE["Copilot CLI Backend"]
        end

        subgraph "Dashboard (New)"
            PAGES["GitHub Pages"]
            DASH["Governance Dashboard"]
            CAT["Prompt Catalog"]
        end

        PANELS --> EMISSIONS --> ENGINE
        SCHEMAS --> ENGINE
        POLICY --> ENGINE
        ENGINE --> MANIFESTS
        PERSONAS --> PANELS

        LIBRARY --> MCP_RES
        PANELS --> MCP_RES
        ENGINE --> MCP_TOOLS

        CLAUDE_BE --> EMISSIONS
        COPILOT_BE --> EMISSIONS
    end

    subgraph "Consumers"
        REPO_A["Repo A<br/>.ai/ submodule<br/>Full governance"]
        REPO_B["Repo B<br/>.ai/ submodule<br/>Full governance"]
        ADC["awesome-dach-copilot<br/>.ai/ submodule<br/>+ domain prompts"]
        IDE_X["IDE X<br/>MCP only<br/>Prompt access"]
        IDE_Y["IDE Y<br/>MCP only<br/>Prompt access"]
    end

    ENGINE -->|"submodule"| REPO_A & REPO_B & ADC
    MCP -->|"MCP protocol"| IDE_X & IDE_Y

    style MCP fill:#4CAF50,color:#fff
    style LIBRARY fill:#4CAF50,color:#fff
    style DASH fill:#4CAF50,color:#fff
    style COPILOT_BE fill:#4CAF50,color:#fff
```

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| MCP server becomes a governance bypass vector | Medium | High | MCP is read-only distribution. Policy enforcement remains in submodule + CI. MCP `check_policy` is dry-run only. |
| Prompt absorption creates maintenance burden | Low | Medium | Automated catalog generation validates on every commit. Maturity model gates promotion. |
| Multi-model execution produces inconsistent emissions | Medium | Medium | Structured emission schema is the contract. Schema validation rejects non-conforming output regardless of backend. |
| awesome-dach-copilot team resists migration | Low | Low | Migration is additive — they keep domain prompts and AKS infra. Governance adds value without removing capabilities. |
| MCP server dependency on policy engine subprocess | Low | Medium | Graceful degradation: if Python/policy engine unavailable, tools return error; resources still served. |

---

## 11. Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Driver** | dark-forge | Governance (control plane) drives; prompts (data plane) are additive |
| **Distribution** | MCP Server + Submodule (dual) | Submodule for enforcement, MCP for IDE-agnostic access |
| **Prompt Source** | Absorb awesome-dach-copilot's `global/` | Reusable prompts belong in the governance framework |
| **Domain Prompts** | Stay in awesome-dach-copilot | Team-specific prompts don't belong in governance |
| **Policy Engine** | Unchanged (Python, deterministic) | Non-negotiable for compliance |
| **Agentic Loop** | Extend to multi-model | Claude Code primary, Copilot CLI secondary |
| **awesome-dach-copilot fate** | Becomes governed consumer | Adds `.ai/` submodule, retains domain extensions |
