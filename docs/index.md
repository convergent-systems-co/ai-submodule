# Dark Forge

AI governance framework for autonomous software delivery.

---

## What is Dark Forge?

Dark Forge is a governance platform distributed as a git submodule that provides structured oversight for AI-driven software delivery. It enforces policy, manages multi-agent orchestration, and produces auditable decision records -- all without containing application source code.

**Current maturity: Phase 4b (Autonomous Remediation)**

## Quick Start

New to the platform? Start here:

1. **[Developer Quickstart](guides/developer-quickstart.md)** -- 5-minute cliff notes (install, daily use, configuration)
2. **[Simple Explainer](onboarding/eli5.md)** -- Plain-language overview of what this is and why it exists
3. **[Developer Guide](onboarding/developer-guide.md)** -- Detailed onboarding for engineers
4. **[Repository Setup](configuration/repository-setup.md)** -- Configure your project
5. **[End-to-End Walkthrough](tutorials/end-to-end-walkthrough.md)** -- Complete pipeline walkthrough

See the [Project Structure](onboarding/project-structure.md) guide for a detailed breakdown of the repository layout.

## Five Governance Layers

Every code change flows through these layers in order:

| Layer | Name | Purpose |
|-------|------|---------|
| 1 | **Intent** | Design Intent intake, completeness validation, risk classification |
| 2 | **Cognitive** | Persona-based reasoning via multi-persona panels producing structured emissions |
| 3 | **Execution** | Deterministic policy engine evaluates panel emissions, produces merge decisions |
| 4 | **Runtime** | Drift detection, incident-to-DI generation |
| 5 | **Evolution** | Self-improvement loops with backward compatibility checks |

## Agentic Architecture

The agentic loop uses a multi-agent prompt-chained pipeline. Start it with `/startup` in your AI tool.

| Persona | Pattern | Role |
|---------|---------|------|
| DevOps Engineer | Routing | Session entry, pre-flight, triage, issue routing |
| Tech Lead | Orchestrator-Workers | Intent validation, panel selection, review coordination, merge |
| Coder | Worker | Implementation, tests, documentation |
| IaC Engineer | Worker | Infrastructure execution (Bicep/Terraform) |
| Test Evaluator | Evaluator-Optimizer | Independent evaluation, test coverage gate, structured feedback |

```mermaid
flowchart TD
    START([/startup]) --> PF[Phase 1: Pre-flight & Triage<br/>DevOps Engineer]
    PF --> SCAN[Scan & prioritize issues]
    SCAN -->|ASSIGN| INTENT[Phase 2: Intent & Planning<br/>Tech Lead]
    INTENT --> IMPL[Phase 3: Implementation<br/>Coder]
    IMPL --> EVAL[Phase 4: Evaluation<br/>Tester]
    EVAL -->|FEEDBACK| IMPL
    EVAL -->|APPROVE| REVIEW[Security + Context Reviews<br/>Tech Lead]
    REVIEW --> MERGE[Phase 5: Merge & Loop]
    MERGE -->|More issues?| SCAN
    MERGE -->|Session cap or no issues| EXIT([Exit])
```

## Policy Profiles

Five deterministic YAML profiles control governance behavior:

- **default** -- Standard risk tolerance, auto-merge enabled with conditions
- **fin_pii_high** -- SOC2/PCI-DSS/HIPAA/GDPR, auto-merge disabled, 3-approver override
- **infrastructure_critical** -- Mandatory architecture and SRE review
- **fast-track** -- Lightweight profile for trivial changes (docs, typos, chores)
- **reduced_touchpoint** -- Near-full autonomy, human approval only for policy overrides

## Documentation Sections

| Section | What You'll Find |
|---------|-----------------|
| [Architecture](architecture/governance-model.md) | Governance layers, agent design, context management, formal specs |
| [Configuration](configuration/repository-setup.md) | Repository setup, CI gating, Copilot integration |
| [Governance](governance/artifact-classification.md) | Artifact classification, acceptance verification, manifest lifecycle |
| [Operations](operations/autonomy-metrics.md) | Autonomy metrics, threshold tuning, token costs |
| [Research](research/README.md) | Research backing persona consolidation and technique comparison |
| [Decisions](decisions/README.md) | Architectural Decision Records (ADRs) |

## Bootstrap

```bash
# From your consuming repository:
git submodule add git@github.com:convergent-systems-co/dark-forge.git .ai
bash .ai/bin/init.sh --install-deps
```
