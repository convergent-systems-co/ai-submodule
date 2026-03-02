# ISO/IEC 42001 -- Dark Factory Governance Mapping

> ISO/IEC 42001:2023 Artificial Intelligence Management System (AIMS). International standard specifying requirements for establishing, implementing, maintaining, and continually improving an AI management system.

## Overview

ISO/IEC 42001 follows the Annex SL high-level structure (clauses 4-10) common to all ISO management system standards. This document maps each clause to the Dark Factory Governance Platform's artifacts, processes, and controls, demonstrating how the platform supports organizations seeking ISO/IEC 42001 certification.

## Clause Mapping Summary

| ISO/IEC 42001 Clause | Governance Artifact | Key Controls |
|----------------------|--------------------|--------------|
| 4. Context of the Organization | `project.yaml`, policy profiles | Project configuration, risk tolerance, regulatory context |
| 5. Leadership | `CODEOWNERS`, escalation chains | Approval authority, role boundaries, accountability |
| 6. Planning | `.governance/plans/` | Mandatory plan-first workflow, risk treatment plans |
| 7. Support | Documentation, personas, prompts | Context management, review prompts, shared perspectives |
| 8. Operation | Panel execution, structured emissions | Multi-persona review, deterministic policy evaluation |
| 9. Performance Evaluation | Run manifests, canary calibration | Audit records, detection accuracy measurement, metrics |
| 10. Improvement | Retrospectives, `GOALS.md` | Continuous improvement tracking, evolution roadmap |

## Clause 4 -- Context of the Organization

*Understanding the organization and its context, interested parties, scope, and AI management system.*

| Requirement | Governance Control | Artifact |
|-------------|-------------------|----------|
| 4.1 External/internal issues | `project.yaml` captures project-specific configuration; policy profiles encode regulatory context (GDPR, SOC2, PCI-DSS, HIPAA) | `project.yaml`, `governance/policy/fin_pii_high.yaml` |
| 4.2 Interested parties | CODEOWNERS defines stakeholders; panel perspectives represent diverse viewpoints | `CODEOWNERS`, 24 shared perspectives |
| 4.3 Scope of AIMS | Governance pipeline scope defined in CLAUDE.md; five governance layers cover full lifecycle | `CLAUDE.md`, governance architecture |
| 4.4 AI management system | The governance platform itself is the AIMS -- policy engine, panel system, structured emissions, audit trail | Full platform |

## Clause 5 -- Leadership

*Top management commitment, policy, roles, and responsibilities.*

| Requirement | Governance Control | Artifact |
|-------------|-------------------|----------|
| 5.1 Leadership and commitment | Governance pipeline is mandatory in all modes; no exceptions or bypasses | `CLAUDE.md` key conventions |
| 5.2 AI policy | Five deterministic policy profiles define risk tolerance, review requirements, and merge conditions | `governance/policy/*.yaml` |
| 5.3 Roles and responsibilities | Six agentic personas with defined boundaries; CODEOWNERS for approval authority; agent protocol for communication | `governance/personas/agentic/`, `CODEOWNERS`, `governance/prompts/agent-protocol.md` |

## Clause 6 -- Planning

*Actions to address risks and opportunities, AI objectives, and planning of changes.*

| Requirement | Governance Control | Artifact |
|-------------|-------------------|----------|
| 6.1 Risk assessment | `risk_level` classification on every change; `ai_act_risk_tier` for EU regulatory classification; `policy_flags` for specific risk identification | `panel-output.schema.json` fields |
| 6.1.2 AI risk assessment process | Multi-persona panels with independent assessments, aggregate verdicts, and evidence grounding | Panel system, `findings` array |
| 6.1.3 AI risk treatment | `auto_remediable` flags for autonomous remediation; escalation chains for human intervention; policy-driven merge decisions | Policy engine decisions, `policy_flags` |
| 6.2 AI objectives | `GOALS.md` tracks project objectives; plans document implementation intent | `GOALS.md`, `.governance/plans/` |
| 6.3 Planning of changes | Mandatory plan-first workflow -- every implementation requires a plan before code | `.governance/plans/`, plan template |

## Clause 7 -- Support

*Resources, competence, awareness, communication, documented information.*

| Requirement | Governance Control | Artifact |
|-------------|-------------------|----------|
| 7.1 Resources | Context management tiers (Tier 0-3) optimize resource allocation; parallel Coder dispatch scales execution | Context management architecture |
| 7.2 Competence | 24 specialized review perspectives with full evaluation criteria; six agentic personas with domain expertise | `governance/prompts/reviews/`, `governance/prompts/shared-perspectives.md` |
| 7.3 Awareness | CLAUDE.md and instructions.md distributed via symlinks to all consuming repos; copilot-instructions.md for IDE integration | `config.yaml` symlink configuration |
| 7.4 Communication | Agent protocol with typed messages (ASSIGN, STATUS, RESULT, FEEDBACK, ESCALATE, APPROVE, BLOCK, CANCEL) | `governance/prompts/agent-protocol.md` |
| 7.5 Documented information | Three artifact types (Cognitive, Enforcement, Audit) with defined mutability; schemas enforce structure | Artifact type system, JSON schemas |

## Clause 8 -- Operation

*Operational planning and control, AI risk assessment, AI risk treatment.*

| Requirement | Governance Control | Artifact |
|-------------|-------------------|----------|
| 8.1 Operational planning | Agentic startup sequence (5 phases) automates operational workflow; governance pipeline enforced on every change | `governance/prompts/startup.md` |
| 8.2 AI risk assessment | Six mandatory panel types on every PR: security-review, threat-modeling, cost-analysis, documentation-review, data-governance-review, code-review | Policy profile `required_panels` |
| 8.3 AI risk treatment | Policy engine produces deterministic decisions; `execution_context` records full provenance (model version, hash, provider, version date) | Policy engine, `execution_context` |
| 8.4 AI system impact assessment | `data_classification` tracks emission sensitivity; `compliance_score` measures policy adherence | `data_classification`, `compliance_score` |

## Clause 9 -- Performance Evaluation

*Monitoring, measurement, analysis, evaluation, internal audit, management review.*

| Requirement | Governance Control | Artifact |
|-------------|-------------------|----------|
| 9.1 Monitoring and measurement | `confidence_score`, `compliance_score`, `duration_ms` on every emission; per-persona `confidence` ratings | Structured emission metrics |
| 9.1.2 Effectiveness evaluation | `canary_results` inject known issues to measure panel detection accuracy; `severity_match` detects calibration drift | `canary_results` in emissions |
| 9.2 Internal audit | Run manifests are immutable audit records; `execution_trace` records files read, diff lines analyzed, analysis duration | Audit manifests, `execution_trace` |
| 9.3 Management review | Retrospective phase in agentic startup sequence; checkpoint system preserves state across sessions | Phase 5 retrospective, `.governance/checkpoints/` |

## Clause 10 -- Improvement

*Nonconformity, corrective action, continual improvement.*

| Requirement | Governance Control | Artifact |
|-------------|-------------------|----------|
| 10.1 Nonconformity and corrective action | `policy_flags` identify nonconformities with severity and remediation; `auto_remediable` enables autonomous correction | `policy_flags` with `remediation` field |
| 10.2 Continual improvement | `GOALS.md` tracks improvement objectives; Phase 5 Evolution layer enables self-improvement loops with backward compatibility checks | `GOALS.md`, Evolution governance layer |

## Annex A -- Reference Controls

ISO/IEC 42001 Annex A provides reference controls organized by objective. Key mappings:

| Annex A Control | ID | Governance Control |
|-----------------|----|--------------------|
| AI system lifecycle processes | A.5.2 | Five governance layers (Intent, Cognitive, Execution, Runtime, Evolution) |
| Data quality for AI systems | A.5.4 | `data-governance-review` panel; `data_classification` field |
| AI system documentation | A.6.2 | `documentation-review` panel; mandatory plans; structured emissions |
| Record management | A.6.3 | Immutable run manifests; append-only audit artifacts |
| AI system risk management | A.7.2 | Multi-profile policy engine; `risk_level` and `ai_act_risk_tier` classification |
| AI system impact assessment | A.7.4 | Six mandatory panels with evidence-grounded findings |
| Responsible use of AI | A.8.2 | `requires_human_review`; escalation chains; GDPR Article 22 controls |
| Third-party AI components | A.9.2 | `execution_context.provider`, `model_hash`, `model_version` for model provenance |
| AI system performance monitoring | A.9.4 | Canary calibration; `confidence_score`; `compliance_score` |

## Annex B -- Implementation Guidance

For organizations using Dark Factory to support ISO/IEC 42001 certification:

1. **Scope definition** -- Configure `project.yaml` with appropriate policy profile and governance settings.
2. **Risk assessment** -- Ensure all six mandatory panels execute on every change; review `ai_act_risk_tier` classifications.
3. **Evidence collection** -- Structured emissions with `execution_trace` provide audit evidence; run manifests serve as immutable records.
4. **Gap analysis** -- Compare panel emissions against Annex A controls to identify coverage gaps.
5. **Continuous monitoring** -- Enable canary calibration to detect panel accuracy drift over time.

## Related Documents

- [EU AI Act Mapping](eu-ai-act-mapping.md)
- [NIST AI RMF Mapping](nist-ai-rmf-mapping.md)
- `governance/schemas/panel-output.schema.json` -- structured emission schema
- `governance/policy/` -- policy profiles implementing risk tolerance
- `governance/prompts/reviews/` -- consolidated review prompts with 24 perspectives
