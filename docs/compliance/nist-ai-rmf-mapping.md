# NIST AI Risk Management Framework -- Dark Forge Mapping

> NIST AI RMF 1.0 (AI 100-1), January 2023. Voluntary framework for managing AI risks throughout the AI system lifecycle.

## Overview

The NIST AI Risk Management Framework defines four core functions -- Govern, Map, Measure, and Manage -- each with categories and subcategories. This document maps those functions to the Dark Forge's layers, artifacts, and controls.

## Function Mapping Summary

| NIST AI RMF Function | Governance Layer | Primary Artifacts |
|----------------------|-----------------|-------------------|
| **Govern** | Execution | Policy engine, policy profiles, CODEOWNERS |
| **Map** | Cognitive | Panel system, risk classification, Design Intent |
| **Measure** | Cognitive + Execution | Structured emissions, confidence scores, compliance scores, canary calibration |
| **Manage** | Execution + Runtime | Escalation chains, human intervention, remediation tracking |

## Govern Function

*Cultivate and implement a culture of risk management.*

| NIST Subcategory | ID | Governance Control | Artifact |
|------------------|----|--------------------|----------|
| Policies, processes, procedures | GV-1 | Five deterministic policy profiles enforce risk tolerance | `governance/policy/default.yaml`, `fin_pii_high.yaml`, `infrastructure_critical.yaml`, `fast-track.yaml`, `reduced_touchpoint.yaml` |
| Accountability structures | GV-2 | CODEOWNERS defines approval authority; agent protocol defines role boundaries | `CODEOWNERS`, `governance/prompts/agent-protocol.md` |
| Workforce diversity of perspectives | GV-3 | 24 review perspectives across 6 panel types ensure multi-viewpoint evaluation | `governance/prompts/reviews/`, `governance/prompts/shared-perspectives.md` |
| Organizational commitments | GV-4 | Governance pipeline is mandatory in all modes (local and remote) | `CLAUDE.md` conventions, `project.yaml` |
| Processes for ongoing monitoring | GV-5 | Agentic startup loop re-evaluates state on every session; canary calibration detects drift | `governance/prompts/startup.md`, canary calibration |
| Risk tolerance defined | GV-6 | Policy profiles define risk thresholds (auto-merge conditions, approver counts, required panels) | `governance/policy/*.yaml` |

## Map Function

*Contextualize risks related to an AI system.*

| NIST Subcategory | ID | Governance Control | Artifact |
|------------------|----|--------------------|----------|
| Intended purpose and context | MP-1 | Design Intent (DI) intake documents purpose, scope, and constraints before implementation | `.artifacts/plans/` |
| Interdependencies mapped | MP-2 | Panel system evaluates cross-cutting concerns (security, cost, data governance, documentation, threat modeling) | Six mandatory panel types |
| Risk identification | MP-3 | `risk_level` field classifies every change; `ai_act_risk_tier` adds regulatory classification | `panel-output.schema.json` |
| Impacts to individuals and groups | MP-4 | `data-governance-review` panel assesses PII exposure; `data_classification` tracks sensitivity | `data_classification` field, `data-governance-review` panel |
| Likelihood and severity assessment | MP-5 | `policy_flags` with severity levels (`critical`, `high`, `medium`, `low`, `info`); `findings_count` per persona | `policy_flags`, `findings_count` in emissions |

## Measure Function

*Employ quantitative, qualitative, or mixed-method tools to analyze, assess, benchmark, and monitor AI risk and related impacts.*

| NIST Subcategory | ID | Governance Control | Artifact |
|------------------|----|--------------------|----------|
| Metrics established | MS-1 | `confidence_score` (0.0-1.0), `compliance_score` (0.0-1.0), per-persona `confidence` | Structured emission fields |
| System performance assessed | MS-2 | `canary_results` inject known issues to calibrate panel detection accuracy | `canary_results` in emissions |
| Detection of anomalies | MS-3 | `severity_match` in canary results flags calibration drift; `execution_trace` records analysis depth | `canary_results.severity_match`, `execution_trace` |
| Measurement approaches | MS-4 | Multi-persona voting (Anthropic Parallelization pattern) produces aggregate verdicts from independent assessments | `findings` array, `aggregate_verdict` |

## Manage Function

*Allocate resources for risk response and recovery.*

| NIST Subcategory | ID | Governance Control | Artifact |
|------------------|----|--------------------|----------|
| Risk responses prioritized | MG-1 | Policy engine produces deterministic decisions: `approved`, `approved_with_conditions`, `changes_requested`, `blocked`, `human_review_required` | Policy engine output |
| Risk treatments implemented | MG-2 | `auto_remediable` flag on policy flags enables autonomous remediation (Phase 4b); non-remediable issues escalate | `policy_flags.auto_remediable` |
| Escalation and intervention | MG-3 | `requires_human_review` field; `human_review_required` policy decision; `fin_pii_high.yaml` disables auto-merge | `requires_human_review`, escalation chains |
| Residual risk documented | MG-4 | Run manifests are immutable audit records; `execution_context` captures full provenance (model version, hash, provider) | Audit manifests, `execution_context` |

## Trustworthy AI Characteristics Mapping

The NIST AI RMF identifies seven characteristics of trustworthy AI. Each maps to governance controls:

| Characteristic | Governance Control |
|---------------|-------------------|
| **Valid and Reliable** | Canary calibration; `confidence_score`; multi-persona consensus |
| **Safe** | `security-review` panel; `threat-modeling` panel; `risk_level` classification |
| **Secure and Resilient** | Mandatory security review on every PR; `execution_trace` audit trail |
| **Accountable and Transparent** | Structured emissions with evidence grounding; `execution_context` provenance; immutable manifests |
| **Explainable and Interpretable** | Per-persona `rationale` field; `evidence` with file/line/snippet grounding |
| **Privacy-Enhanced** | `data-governance-review` panel; `data_classification` field; `fin_pii_high.yaml` profile |
| **Fair -- with Harmful Bias Managed** | 24 diverse perspectives across panels; multi-persona voting reduces individual bias |

## Related Documents

- [EU AI Act Mapping](eu-ai-act-mapping.md)
- [ISO/IEC 42001 Mapping](iso-42001-mapping.md)
- `governance/schemas/panel-output.schema.json` -- structured emission schema
- `governance/policy/` -- policy profiles implementing risk tolerance
