# Personas Index

Quick reference for all available personas and when to use them.

## Quality

| Persona | File | Use When |
|---------|------|----------|
| Style Reviewer | `quality/style-reviewer.md` | Broad quality review — readability, naming, structure, conventions |
| Code Reviewer | `quality/code-reviewer.md` | Production-level review — correctness, security, concurrency, failure modes |
| Adversarial Reviewer | `quality/adversarial-reviewer.md` | Stress-testing a design — hidden assumptions, invariants, corruption paths |

## Architecture

| Persona | File | Use When |
|---------|------|----------|
| Architect | `architecture/architect.md` | System design evaluation — components, boundaries, data flow |
| API Designer | `architecture/api-designer.md` | REST/API contract review — versioning, compatibility, consumer experience |
| Systems Architect | `architecture/systems-architect.md` | Distributed systems — scalability, failure domains, state management |

## Engineering

| Persona | File | Use When |
|---------|------|----------|
| Test Engineer | `engineering/test-engineer.md` | Test strategy — coverage gaps, flaky tests, mock quality |
| Performance Engineer | `engineering/performance-engineer.md` | Performance analysis — hot paths, allocations, bottlenecks |
| Debugger | `engineering/debugger.md` | Root cause analysis — systematic isolation, hypothesis testing |
| Minimalist Engineer | `engineering/minimalist-engineer.md` | Complexity reduction — unnecessary abstraction, framework overuse |
| UX Engineer | `engineering/ux-engineer.md` | Developer experience — ergonomics, configuration, error messages |
| Refactor Specialist | `engineering/refactor-specialist.md` | Restructuring — incremental migration, responsibility cleanup |

## Operations

| Persona | File | Use When |
|---------|------|----------|
| SRE | `operations/sre.md` | Production stability — SLOs, error budgets, toil reduction |
| DevOps Engineer | `operations/devops-engineer.md` | Build/deploy pipelines — reproducibility, artifact management |
| Infrastructure Engineer | `operations/infrastructure-engineer.md` | Infrastructure security — IAM, network segmentation, TLS |
| Observability Engineer | `operations/observability-engineer.md` | Monitoring — logging, metrics, tracing, alerting |
| Failure Engineer | `operations/failure-engineer.md` | Failure modes — retry storms, partial failures, recovery paths |
| Cost Optimizer | `operations/cost-optimizer.md` | Cloud spend — right-sizing, reserved capacity, storage tiers |

## Domain

| Persona | File | Use When |
|---------|------|----------|
| Frontend Engineer | `domain/frontend-engineer.md` | Client-side — components, state, bundle size, rendering |
| Backend Engineer | `domain/backend-engineer.md` | Server-side — API patterns, caching, service boundaries |
| Data Architect | `domain/data-architect.md` | Data layer — schema evolution, indexing, migrations |
| ML Engineer | `domain/ml-engineer.md` | Machine learning — training pipelines, model versioning, drift |
| Mobile Engineer | `domain/mobile-engineer.md` | Mobile — platform conventions, offline-first, battery efficiency |
| LLM Engineer | `domain/llm-engineer.md` | LLM systems — prompt engineering, RAG, token optimization, guardrails |

## Compliance

| Persona | File | Use When |
|---------|------|----------|
| Security Auditor | `compliance/security-auditor.md` | Security assessment — injection, auth, secrets, insecure defaults |
| Compliance Officer | `compliance/compliance-officer.md` | Regulatory — GDPR, SOC2, HIPAA, PCI-DSS, audit readiness |
| Accessibility Engineer | `compliance/accessibility-engineer.md` | Accessibility — WCAG, screen readers, keyboard navigation |
| MITRE Specialist | `compliance/mitre-specialist.md` | Threat modeling — ATT&CK technique mapping, kill chains, detection gap analysis |

## Leadership

| Persona | File | Use When |
|---------|------|----------|
| Tech Lead | `leadership/tech-lead.md` | Technical leadership — decisions, knowledge distribution, coordination |
| Product Manager | `leadership/product-manager.md` | Requirements — acceptance criteria, scope, success metrics |
| Mentor | `leadership/mentor.md` | Teaching — concept explanation, guided examples, learning progression |
| Interviewer | `leadership/interviewer.md` | Hiring — skill assessment, evidence-based evaluation |
| Agile Coach | `leadership/agile-coach.md` | Agile process — story quality, DoD, sprint health, continuous improvement |

## Specialist

| Persona | File | Use When |
|---------|------|----------|
| Code Archaeologist | `specialist/code-archaeologist.md` | Legacy systems — historical context, tribal knowledge, hidden dependencies |
| Incident Commander | `specialist/incident-commander.md` | Active incidents — impact assessment, coordination, communication |
| Migration Specialist | `specialist/migration-specialist.md` | Data/system migrations — integrity, rollback, parallel running |
| API Consumer | `specialist/api-consumer.md` | API evaluation — from the consumer's perspective, DX friction |

## FinOps

| Persona | File | Use When |
|---------|------|----------|
| FinOps Engineer | `finops/finops-engineer.md` | Cloud cost governance — tagging compliance, budget enforcement, rightsizing, waste detection |
| FinOps Analyst | `finops/finops-analyst.md` | Financial reporting — showback/chargeback, unit economics, forecasting, anomaly detection |
| Cloud Cost Analyst | `finops/cloud-cost-analyst.md` | Cloud infrastructure costing — Azure/AWS cost estimation from Bicep, Terraform, CloudFormation |
| LLM Cost Analyst | `finops/llm-cost-analyst.md` | AI/LLM costing — token usage, agentic loop costs, inference pricing, development cost estimation |

## Governance

| Persona | File | Use When |
|---------|------|----------|
| Governance Auditor | `governance/governance-auditor.md` | Auditing the governance pipeline — manifest completeness, policy consistency, override legitimacy |
| Policy Evaluator | `governance/policy-evaluator.md` | Deterministic policy evaluation — applying rules to structured emissions, producing merge decisions |

## Agentic

| Persona | File | Use When |
|---------|------|----------|
| DevOps Engineer | `agentic/devops-engineer.md` | Session entry — pre-flight checks, issue triage, routing, session lifecycle management |
| Code Manager | `agentic/code-manager.md` | Pipeline orchestration — intent validation, panel selection, review coordination, merge decisions |
| Coder | `agentic/coder.md` | Code execution — branch creation, plan writing, implementation, test authoring |
| Tester | `agentic/tester.md` | Independent evaluation — test coverage gate, documentation verification, structured feedback |

### Agent Protocol

Inter-agent communication follows `governance/prompts/agent-protocol.md` — a structured message protocol with typed messages (ASSIGN, STATUS, RESULT, FEEDBACK, ESCALATE, APPROVE, BLOCK). The DevOps Engineer routes to Code Manager, which orchestrates Coder and Tester.

## Panels

Multi-perspective reviews where several personas collaborate. See `panels/` for full details.

| Review | File | Participants |
|--------|------|-------------|
| Code Review | `panels/code-review.md` | Code Reviewer, Security Auditor, Performance Engineer, Test Engineer, Refactor Specialist |
| Architecture Review | `panels/architecture-review.md` | Systems Architect, Security Auditor, Failure Engineer, Infrastructure Engineer, API Designer |
| Security Review | `panels/security-review.md` | Security Auditor, Infrastructure Engineer, Compliance Officer, Adversarial Reviewer, Backend Engineer |
| Performance Review | `panels/performance-review.md` | Performance Engineer, Backend Engineer, Frontend Engineer, Infrastructure Engineer, SRE |
| Testing Review | `panels/testing-review.md` | Test Engineer, Failure Engineer, Performance Engineer, Security Auditor, Code Reviewer |
| Production Readiness | `panels/production-readiness-review.md` | SRE, Infrastructure Engineer, Observability Engineer, Failure Engineer, DevOps Engineer |
| API Design Review | `panels/api-design-review.md` | API Designer, API Consumer, Security Auditor, Backend Engineer, Frontend Engineer |
| Data Design Review | `panels/data-design-review.md` | Data Architect, Backend Engineer, Performance Engineer, Security Auditor, Compliance Officer |
| Documentation Review | `panels/documentation-review.md` | Documentation Reviewer, Documentation Writer, API Consumer, Mentor, UX Engineer |
| Technical Debt Review | `panels/technical-debt-review.md` | Refactor Specialist, Systems Architect, Test Engineer, Tech Lead, Minimalist Engineer |
| Migration Review | `panels/migration-review.md` | Migration Specialist, Data Architect, SRE, Failure Engineer, Tech Lead |
| Incident Post-Mortem | `panels/incident-post-mortem.md` | Incident Commander, SRE, Systems Architect, Failure Engineer, Observability Engineer |
| Threat Modeling | `panels/threat-modeling.md` | MITRE Specialist, Security Auditor, Infrastructure Engineer, Adversarial Reviewer, Architect |
| Cost Analysis | `panels/cost-analysis.md` | FinOps Analyst, FinOps Engineer, Cost Optimizer, Cloud Cost Analyst, LLM Cost Analyst, Infrastructure Engineer |
| Copilot Review | `panels/copilot-review.md` | GitHub Copilot as a formal review panel — feedback parsing, severity classification, confidence scoring |

---

## Consolidated Review Prompts

> Personas and panels have been consolidated into self-contained review prompts.
> See `governance/prompts/reviews/` for the 19 consolidated review prompts.
> See `governance/prompts/shared-perspectives.md` for canonical definitions of the 19 perspectives appearing in 2+ panels.
>
> The persona files in this directory are **deprecated** — they remain for reference and backward compatibility during the transition period. The consolidated review prompts in `governance/prompts/reviews/` are the authoritative source.
