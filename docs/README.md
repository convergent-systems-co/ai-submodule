# Documentation

Navigation hub for all Dark Forge documentation.

## Quick Start

New to the platform? Start here:

1. [Developer Quickstart](guides/developer-quickstart.md) — 5-minute cliff notes (install, daily use, configuration)
2. [Developer Guide](onboarding/developer-guide.md) — Detailed onboarding walkthrough
3. [Governance Model](architecture/governance-model.md) — Understand the five governance layers
4. [Repository Setup](configuration/repository-setup.md) — Configure your project

## Architecture

Deep-dive into platform design and internals.

| Document | Topic |
|----------|-------|
| [Governance Model](architecture/governance-model.md) | Five governance layers, decision authority, and policy profiles |
| [Runtime Feedback](architecture/runtime-feedback.md) | Drift detection and incident-to-DI generation (Phase 4b/5) |
| [Context Management](architecture/context-management.md) | JIT loading tiers, context budgets, and checkpoint-based reset protection |
| [Cross-Repo Escalation](architecture/cross-repo-escalation.md) | Cross-repository issue escalation architecture |
| [Mass Parallelization](architecture/mass-parallelization.md) | Multi-agent orchestration with collision domains (Phase 5e) |
| [Session State Persistence](architecture/session-state-persistence.md) | Cross-session governance state storage strategy (Phase 5c) |
| [Event-Driven Triggers](architecture/event-driven-triggers.md) | Event-driven governance session dispatch (Phase 5c) |
| [Formal Specification](architecture/formal-spec.md) | Formal specification of governance invariants |
| [Agent Architecture](architecture/agent-architecture.md) | 7-agent prompt-chained architecture, protocol, transport phases, failure modes |

### Agentic Architecture

The agentic loop uses a 7-agent prompt-chained pipeline. Start it with `/startup` in your AI tool.

| Persona | Pattern | Role |
|---------|---------|------|
| [Project Manager](../governance/personas/agentic/project-manager.md) | Orchestrator-Workers | Portfolio orchestrator, multiplexed Tech Leads (opt-in) |
| [DevOps Engineer](../governance/personas/agentic/devops-engineer.md) | Routing | Session entry, pre-flight, triage, issue routing |
| [Tech Lead](../governance/personas/agentic/tech-lead.md) | Orchestrator-Workers | Intent validation, panel selection, review coordination, merge |
| [Coder](../governance/personas/agentic/coder.md) | Worker | Implementation, tests, documentation |
| [IaC Engineer](../governance/personas/agentic/iac-engineer.md) | Worker | Infrastructure changes (conditional) |
| [Tester](../governance/personas/agentic/test-evaluator.md) | Evaluator-Optimizer | Independent evaluation, test coverage gate, structured feedback |
| [Document Writer](../governance/personas/agentic/document-writer.md) | Worker | Documentation generation and maintenance |

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

Inter-agent communication: [Agent Protocol](../governance/prompts/agent-protocol.md) | Startup: [startup.md](../governance/prompts/startup.md) | Developer Guide: [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md)

## Configuration

Setup guides for repository and tool integration.

| Document | Topic |
|----------|-------|
| [Repository Setup](configuration/repository-setup.md) | Settings, CODEOWNERS, branch protection, and per-project overrides |
| [CI Gating](configuration/ci-gating.md) | CI checks, branch protection, and auto-merge configuration |
| [Copilot Integration](configuration/copilot-integration.md) | Configuring GitHub Copilot auto-fix in the governance workflow |

## Governance

Artifact classification and review processes.

| Document | Topic |
|----------|-------|
| [Artifact Classification](governance/artifact-classification.md) | Cognitive, Enforcement, and Audit artifact types and their handling |
| [Acceptance Verification](governance/acceptance-verification.md) | Acceptance criteria verification process |
| [Naming Review](governance/naming-review.md) | Persona and panel naming consistency proposals |

## Operations

Metrics, tuning, and operational guides.

| Document | Topic |
|----------|-------|
| [Autonomy Metrics](operations/autonomy-metrics.md) | Autonomy index, health thresholds, and weekly reporting |
| [Migration Summary](operations/migration-summary.md) | Migration steps and deliverable checklist |
| [Threshold Tuning](operations/threshold-tuning.md) | Auto-tuning mechanism and safety bounds |
| [Retrospective Aggregation](operations/retrospective-aggregation.md) | Aggregated retrospective data schema documentation |
| [Token Costs](operations/token-costs.md) | Per-PR token budget, model pricing, cost estimation, and `--dry-run` mode |

## Research

Research and architectural decision records.

| Document | Topic |
|----------|-------|
| [Research](research/README.md) | 51-source research informing persona consolidation (ADR-010) |
| [Technique Comparison](research/technique-comparison.md) | Consolidation technique evaluation |

## Decisions

| Document | Topic |
|----------|-------|
| [Architectural Decisions](decisions/README.md) | ADR log — all recorded architectural decisions |

## Session Summaries

Post-session reports from agentic improvement loops.

| Document | Date | Scope |
|----------|------|-------|
| [Phase 4b Improvement Loop](session-summaries/2026-03-03-phase-4b-improvement-loop.md) | 2026-03-03 | 10 PRs: Go binary distribution, agent architecture hardening, ADO E2E, developer experience |

## Onboarding

| Document | Topic |
|----------|-------|
| [Developer Guide](onboarding/developer-guide.md) | Quick-start guide for developers adopting the platform |
| [Architecture Overview](onboarding/architecture.html) | Visual architecture overview (HTML) |
| [Risks & Mitigation](onboarding/risks-mitigation.html) | Risk assessment and mitigation strategies (HTML) |
| [Team Starter](onboarding/team-starter.html) | Team onboarding starter kit (HTML) |

## Tutorials

| Document | Topic |
|----------|-------|
| [End-to-End Walkthrough](tutorials/end-to-end-walkthrough.md) | Complete walkthrough of the governance pipeline |
