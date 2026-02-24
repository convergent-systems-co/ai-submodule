# .ai — Dark Factory Governance Platform

AI governance framework for autonomous software delivery. Provides personas, panels, policy enforcement, structured emissions, and audit manifests — distributed as a git submodule to any repository.

> **New here?** See the [Developer Quick Guide](DEVELOPER_GUIDE.md) for a TLDR onboarding.

## Goals

The Dark Factory Governance Platform exists to:

1. **Automate software delivery governance** — Replace manual code review gates with structured, auditable AI-driven review panels that produce deterministic merge decisions.
2. **Enforce policy without human bottlenecks** — Deterministic policy profiles (default, financial/PII, infrastructure-critical) evaluate every change programmatically. AI models never interpret policy rules.
3. **Maintain compliance at scale** — Embed SOC2, PCI-DSS, HIPAA, and GDPR compliance into the review pipeline so regulated changes are caught at intake, not after merge.
4. **Enable autonomous agentic operation** — A Code Manager persona orchestrates the full lifecycle (issue triage, planning, implementation, review, merge) with human oversight only where policy requires it.
5. **Distribute governance as infrastructure** — Ship as a git submodule so any repository gets personas, panels, policies, and CI workflows by adding a single dependency.
6. **Reach full Dark Factory** — Progress through defined maturity phases toward fully autonomous software delivery with runtime feedback loops and self-evolving governance.

See [GOALS.md](GOALS.md) for detailed phase tracking, completed work, and open enhancements.

## Governance Maturity Model

| Phase | Name | Description | Status |
|-------|------|-------------|--------|
| 3 | Agentic Orchestration | Personas, panels, workflows with human gates | Implemented |
| 4a | Policy-Bound Autonomy | Deterministic merge decisions, structured emissions | **Implemented** — CI enforcement live |
| 4b | Autonomous Remediation | Auto-fix, drift detection, remediation loops | **Implemented** — drift detection, auto-remediation, and incident-to-DI governance artifacts complete |
| 5 | Dark Factory | Full automation — decomposed into sub-phases 5a-5e with achievability assessment | 5a, 5b, 5d, 5e governance artifacts complete; 5c, 5d runtime blocked by platform |

See [GOALS.md](GOALS.md) for detailed progress tracking, completed work, and open enhancements.

## Repository Structure

> **Note:** In consuming repositories, this content lives at `.ai/` as a git submodule. In this repository itself, the files are at the root.

```
.ai/  (or repo root when working on this repo directly)
  instructions.md              Base AI instructions (< 200 tokens, Tier 0)
  instructions/                Decomposed instruction modules (code-quality, security, testing, etc.)
  config.yaml                  Symlink and sync configuration
  init.sh                      Bootstrap script for consuming repos (macOS/Linux)
  init.ps1                     Bootstrap script for consuming repos (Windows)

  templates/                   Language-specific scaffolding
    go/                        Go conventions and project config
    python/                    Python conventions and project config
    node/                      Node.js/TypeScript conventions
    react/                     React conventions
    csharp/                    C#/.NET conventions

  governance/                  All governance machinery (personas, policy, schemas, etc.)
    personas/                  AI persona definitions (Markdown)
      architecture/            System design personas
      quality/                 Code review personas
      compliance/              Security, regulatory, accessibility personas
      documentation/           Content creation and review personas
      domain/                  Frontend, backend, data, ML, mobile personas
      engineering/             Testing, performance, debugging personas
      operations/              SRE, DevOps, infrastructure personas
      leadership/              Technical leadership, product, mentoring personas
      specialist/              Legacy, incidents, migrations personas
      governance/              Governance Auditor, Policy Evaluator
      agentic/                 Code Manager, Coder
      panels/                  Multi-persona review panels (see index.md for full list)
      index.md                 Persona and panel reference grid

    prompts/                   Reusable prompt templates
      startup.md               Agentic improvement loop entry point
      init.md                  Agentic bootstrap prompt (interactive install for consuming repos)
      retrospective.md         Post-merge process evaluation prompt
      governance-compliance-checklist.md  Required governance steps per PR (#176)
      cross-repo-escalation-workflow.md   Cross-repo escalation detect-dedup-escalate flow (#184)
      checkpoint-resumption-workflow.md    Session resumption from checkpoint files (Phase 5c)
      templates/               Reusable document templates
        plan-template.md       Standardized plan template for AI and humans
        runtime-di-template.md DI template for runtime-generated intents
      workflows/               Multi-phase orchestration (8 workflows)

    schemas/                   Enforcement artifacts (JSON Schema)
      panel-output.schema.json Structured emission standard for panel reviews
      panels.schema.json       Panel configuration validation
      panels.defaults.json     Default panel pass/fail thresholds
      run-manifest.schema.json Audit manifest for every merge decision
      baseline.schema.json     Baseline measurement definitions
      breaking-change.schema.json          Breaking change detection for backward compatibility
      remediation-action.schema.json       Auto-remediation action definitions (Phase 4b)
      remediation-verification.schema.json Remediation verification criteria (Phase 4b)
      runtime-di.schema.json               Runtime-generated Design Intent (Phase 4b)
      runtime-signal.schema.json           Runtime anomaly signal classification (Phase 5)
      autonomy-metrics.schema.json         Autonomy index and health thresholds (Phase 5)
      retrospective-aggregation.schema.json  Aggregated retrospective data (Phase 5b)
      project.schema.json                  Project configuration validation
      formal-spec.schema.json              Formal specification for Phase 5e Spec-Driven Interface
      conflict-detection.schema.json       Multi-agent conflict detection for Phase 5d
      governance-compliance.schema.json    Governance step compliance evidence (#176)
      persona-effectiveness.schema.json    Per-persona signal-to-noise ratio (Phase 5b)
      test-governance.schema.json          Test coverage expectations per policy profile (Phase 5a)
      cross-repo-escalation.schema.json    Cross-repo issue escalation records (#184)
      checkpoint.schema.json               Session checkpoint state for resumption (Phase 5c)

    policy/                    Deterministic policy profiles and supporting rules (YAML)
      default.yaml             Standard risk tolerance
      fin_pii_high.yaml        Financial/PII — SOC2, PCI-DSS, HIPAA, GDPR
      infrastructure_critical.yaml  Infrastructure-as-code, deployment configs
      reduced_touchpoint.yaml  Near-full autonomy — Phase 5e
      threshold-tuning.yaml    Auto-tuning rules for confidence threshold adjustment
      drift-policy.yaml        Drift detection thresholds and triggers
      drift-remediation.yaml   Drift remediation action rules
      autonomy-thresholds.yaml Autonomy metric health thresholds
      circuit-breaker.yaml     Safety circuit breaker rules
      deduplication.yaml       Signal deduplication rules
      rate-limits.yaml         Signal processing rate limits
      severity-reclassification.yaml  Runtime severity reclassification rules
      component-registry.yaml  Component ownership registry
      signal-panel-mapping.yaml  Signal-to-panel routing rules
      merge-sequencing.yaml    Multi-agent PR ordering rules — Phase 5d
      parallel-session-protocol.yaml  Parallel agent session coordination — Phase 5d
      signal-adapters/         Polling adapter configurations for runtime signals

    emissions/                 Panel emission outputs (structured JSON)
    manifests/                 Run manifests (audit trail, append-only)

    docs/                      Architecture and design documents
      dark-factory-governance-model.md    Governance layers and decision authority
      artifact-classification.md          Cognitive, Enforcement, Audit artifact types
      context-management.md               JIT loading and context reset protection
      runtime-feedback-architecture.md    Drift detection and incident-to-DI generation
      autonomy-metrics.md                 Autonomy index and weekly reporting
      ci-gating-blueprint.md              CI checks, branch protection, auto-merge
      naming-review.md                    Persona/panel naming consistency review
      repository-configuration.md         Repository settings and CODEOWNERS setup
      copilot-auto-fix.md                 Copilot auto-fix configuration guide
      retrospective-aggregation.md        Aggregated retrospective data schema docs
      threshold-tuning.md                 Auto-tuning mechanism and safety bounds
      cross-repo-escalation.md             Cross-repo escalation setup and architecture (#184)

  .governance/                 Policy engine runtime
    policy-engine.py           Deterministic evaluation engine (Phase 4b)

  .plans/                      Implementation plans (archived to releases after merge)
  .checkpoints/                Context capacity checkpoints (session state)
  .github/
    workflows/
      dark-factory-governance.yml   Governance review CI (detect + policy engine + review)
      plan-archival.yml             Archives plans to releases on PR merge
      propagate-submodule.yml       Auto-propagation for consuming repos
      jm-compliance.yml             Enterprise-locked compliance checks
    ISSUE_TEMPLATE/
      feature-request.yml           Structured feature request form
      bug-report.yml                Structured bug report form
      config.yml                    Template chooser configuration
```

## How It Works

### For Code Changes (Phase 4a)

```
Issue / Design Intent
        |
        v
Code Manager validates intent (Layer 1: Intent Governance)
        |
        v
Panel graph activated (Layer 2: Cognitive Governance)
  - Personas assigned based on change type and risk
  - Panels execute in parallel where possible
        |
        v
Panels emit structured JSON (Layer 3: Execution Governance)
  - Confidence scores, risk levels, policy flags
  - Validated against governance/schemas/panel-output.schema.json
        |
        v
Policy engine evaluates (deterministic, no prose)
  - Reads active policy profile (default, fin_pii_high, infrastructure_critical, reduced_touchpoint)
  - Produces decision: auto_merge | auto_remediate | human_review_required | block
        |
        v
Run manifest logged (governance/schemas/run-manifest.schema.json)
  - Complete audit trail for replay and compliance
```

### For Runtime Feedback (Phase 5 — Designed)

```
Runtime anomaly detected
        |
        v
Signal classified and deduplicated
        |
        v
Design Intent generated automatically
        |
        v
Feeds back into Layer 1 (closes the autonomous loop)
```

## Compliance and Security

Security, regulatory compliance, and code quality are embedded at every governance layer:

| Layer | Compliance Mechanism |
|-------|---------------------|
| Intent | Risk classification at intake; PII/financial flags trigger `fin_pii_high` profile |
| Cognitive | Security Auditor and Compliance Officer personas activated for regulated changes |
| Execution | Policy engine enforces compliance scores, blocks PII exposure, requires security panel |
| Runtime | Drift detection monitors compliance regression; incidents generate remediation DIs |
| Evolution | Backward compatibility checks; breaking changes require migration plans |

Policy profiles provide pre-configured compliance postures:
- **`fin_pii_high`** — SOC2, PCI-DSS, HIPAA, GDPR. Auto-merge disabled. 3-approver override.
- **`infrastructure_critical`** — Production stability. Mandatory architecture and SRE review.
- **`default`** — Standard internal applications. Balanced automation and oversight.
- **`reduced_touchpoint`** — Near-full autonomy. Human approval only for policy overrides, dismissed security-critical findings, or critical risk. Phase 5e.

## Context Management

The framework uses JIT (Just-In-Time) loading to minimize AI context window usage:

| Tier | Content | Budget | Survives Reset |
|------|---------|--------|----------------|
| 0 | Base instructions + project identity | ~400 tokens | Yes (pinned) |
| 1 | Language conventions + active personas | ~2,000 tokens | Session duration |
| 2 | Current workflow phase + panel context | ~3,000 tokens | Released per phase |
| 3 | Policies, schemas, docs | 0 tokens | Queried on-demand |

See `governance/docs/context-management.md` for the full strategy including checkpoint-based reset protection and instruction decomposition.

## Repo Rename Recommendation

This repository is currently named `ai-submodule`. Given its evolution into a governance platform, a more descriptive name is recommended:

| Candidate | Rationale |
|-----------|-----------|
| **`dark-factory`** | Aligns with the governance model name and Phase 5 goal |
| **`ai-governance`** | Descriptive of current function |
| **`forge`** | Short, evocative of autonomous manufacturing |

The rename should be coordinated across all consuming repositories that reference the submodule URL.

## References & Industry Context

The Phase 5 roadmap and maturity model are informed by the following industry frameworks. See [GOALS.md](GOALS.md) for detailed sub-phase decomposition and achievability assessment.

| Source | Relevance |
|--------|-----------|
| [Dan Shapiro — 5 Levels of Agentic Coding](https://www.linkedin.com/pulse/5-levels-agentic-coding-dan-shapiro/) | Defines the L1-L5 progression that maps to Dark Factory's phase model |
| [Mars Shot — MSV-CMM](https://www.mars-shot.dev/) | Capability maturity model for machine-speed verification; informs self-proving systems (5a) |
| [Bessemer — Roadmap to AI Coding Agents](https://www.bvp.com/atlas/roadmap-to-ai-coding-agents) | Autonomy scale identifying the gap between assisted coding and full agency |
| [Addy Osmani — The 70% Problem](https://addyo.substack.com/p/the-70-problem-hard-truths-about) | Analysis of where AI coding agents stall; informs achievability assessments |

## Why a Git Submodule?

| Approach | Drawback |
|----------|----------|
| Copy-paste | Drifts immediately. No propagation across repos. |
| Package manager | Runtime dependency for static text. Overkill. |
| Monorepo | Forces all projects into one repo. |
| Template repo | One-time only. Updates don't flow. |
| Git subtree | Merges history into host repo. Hard to update cleanly. |

Submodules provide version-pinned, single-source-of-truth distribution with no toolchain requirement.

## Usage

### Adding to a Project

```bash
git submodule add git@github.com:SET-Apps/ai-submodule.git .ai
git commit -m "Add .ai submodule"
```

### Bootstrap (after adding submodule)

**macOS / Linux:**
```bash
bash .ai/init.sh
```

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File .ai\init.ps1
```

The bootstrap script creates symlinks so Claude Code, GitHub Copilot, and Cursor all receive shared instructions. On Windows, if symlinks are unavailable (requires Developer Mode or admin), it falls back to file copies.

**Windows prerequisites:**
- **Python 3.12+** — required for the governance policy engine. Install from [python.org](https://www.python.org/downloads/) and ensure it's in your PATH.
- After installing Python: `pip install jsonschema pyyaml`

### Cloning with Submodule

```bash
git clone --recurse-submodules <PROJECT_URL>
```

### Updating

```bash
git submodule update --remote .ai
git add .ai
git commit -m "Update .ai submodule"
```

### Pinning a Version

```bash
cd .ai
git checkout v2.0.0
cd ..
git add .ai
git commit -m "Pin .ai submodule to v2.0.0"
```

### Project-Specific Configuration

1. Copy a language template: `cp .ai/templates/python/project.yaml project.yaml`
2. Customize personas, panels, and conventions
3. Set the governance policy profile:
   ```yaml
   governance:
     policy_profile: default
   ```

### Removing

```bash
git submodule deinit -f .ai
git rm -f .ai
rm -rf .git/modules/.ai
git commit -m "Remove .ai submodule"
```
