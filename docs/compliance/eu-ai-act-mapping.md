# EU AI Act -- Dark Forge Mapping

> Regulation (EU) 2024/1689 of the European Parliament and of the Council. General-purpose AI provisions apply from **2 August 2025**; full enforcement begins **2 August 2026**.

## Overview

The EU AI Act establishes a four-tier risk classification system for AI systems. This document maps the Dark Forge's controls to each tier, demonstrating how governance artifacts satisfy the Act's requirements for AI systems used in software delivery automation.

## Four-Tier Risk Classification

| Tier | AI Act Definition | Governance `risk_level` Mapping | `ai_act_risk_tier` Value |
|------|-------------------|---------------------------------|--------------------------|
| **Unacceptable** | Prohibited practices (social scoring, real-time biometric surveillance, manipulation of vulnerable groups) | N/A -- governance platform does not operate in prohibited domains | `unacceptable` |
| **High** | Systems in Annex III domains (critical infrastructure, employment, credit scoring, law enforcement) | `critical`, `high` when change affects regulated domains | `high` |
| **Limited** | Systems with transparency obligations (chatbots, emotion recognition, deepfakes) | `medium` when AI-generated content requires disclosure | `limited` |
| **Minimal** | All other AI systems (spam filters, AI-enabled games, inventory management) | `low`, `negligible` for standard software delivery automation | `minimal` |

## Per-Tier Requirements and Governance Controls

### Unacceptable Risk (Article 5)

The Dark Forge governance platform is a software delivery automation system, not a prohibited AI practice. Panel emissions include `ai_act_risk_tier` to explicitly classify each assessed change. If a panel classifies a change as `unacceptable`, the policy engine blocks the merge and escalates to human review.

**Governance control:** Policy engine `block` verdict on `ai_act_risk_tier: "unacceptable"`.

### High Risk (Articles 6-51)

High-risk requirements and corresponding governance controls:

| AI Act Requirement | Article | Governance Control |
|--------------------|---------|-------------------|
| Risk management system | Art. 9 | Policy engine with four deterministic profiles (`default.yaml`, `fin_pii_high.yaml`, `infrastructure_critical.yaml`, `reduced_touchpoint.yaml`) |
| Data governance | Art. 10 | `data-governance-review` panel on every PR; `data_classification` field in structured emissions |
| Technical documentation | Art. 11 | `documentation-review` panel; plans in `.artifacts/plans/`; run manifests as immutable audit records |
| Record-keeping / logging | Art. 12 | Structured emissions with `execution_context` (repository, branch, commit SHA, model version, model hash, provider); append-only audit manifests |
| Transparency | Art. 13 | Panel findings with evidence grounding (`evidence.file`, `evidence.line_start`, `evidence.snippet`); `execution_trace` with files read and analysis duration |
| Human oversight | Art. 14 | `requires_human_review` field; escalation chains in policy profiles; `human_review_required` policy engine decision |
| Accuracy, robustness, cybersecurity | Art. 15 | `canary_results` for calibration; `security-review` and `threat-modeling` panels mandatory on every PR |
| Quality management system | Art. 17 | Governance pipeline is mandatory -- plan-first, panel execution, structured emissions, policy evaluation |
| Conformity assessment | Art. 43 | `compliance_score` field (0.0-1.0); policy profile evaluation produces deterministic merge decisions |

### Limited Risk (Articles 50, 52)

| AI Act Requirement | Governance Control |
|--------------------|--------------------|
| Transparency disclosure for AI-generated content | `ai_act_risk_tier: "limited"` triggers documentation requirements in panel output |
| User notification of AI interaction | Agent protocol messages (`ASSIGN`, `STATUS`, `RESULT`) provide full traceability of AI-driven decisions |

### Minimal Risk (Article 95)

No mandatory requirements. The governance platform still applies full pipeline controls as a best practice, ensuring auditability even for minimal-risk changes.

## Model Provenance (Article 12 Compliance)

The `execution_context` in panel emissions supports model provenance tracking required by Article 12:

| Field | Purpose | AI Act Requirement |
|-------|---------|-------------------|
| `model_version` | Model identifier string | Art. 12(2) -- identification of AI system version |
| `model_hash` | SHA-256 hash of model weights or version identifier | Art. 12(2) -- unique identification of model used |
| `provider` | AI model provider name | Art. 12(3) -- identification of provider |
| `version_date` | Model version or training cutoff date | Art. 12(2) -- temporal identification of model |

## GDPR Article 22 -- Automated Decision-Making

Article 22 of the GDPR (referenced by the AI Act) grants data subjects the right not to be subject to decisions based solely on automated processing. The governance platform addresses this through:

1. **`requires_human_review: true`** -- panels can flag any change for mandatory human review, ensuring no fully automated decision when human rights are affected.
2. **`aggregate_verdict`** -- the computed verdict is a recommendation, not an autonomous action. Policy profiles (especially `fin_pii_high.yaml`) disable auto-merge entirely for regulated domains.
3. **Escalation chains** -- `human_review_required` policy engine decisions route to human approvers, satisfying the "meaningful human intervention" requirement.
4. **Audit trail** -- every automated decision is recorded in structured emissions with full evidence grounding, enabling the "right to explanation" under GDPR Article 22(3).

## Enforcement Timeline

| Date | Milestone |
|------|-----------|
| 1 August 2024 | AI Act entered into force |
| 2 February 2025 | Prohibited practices (Title II) apply |
| 2 August 2025 | General-purpose AI model obligations apply |
| **2 August 2026** | **Full enforcement** -- high-risk system requirements, conformity assessments, penalties |
| 2 August 2027 | Annex I high-risk systems (existing regulated products) must comply |

## Schema Reference

The `ai_act_risk_tier` field in `governance/schemas/panel-output.schema.json` supports values: `unacceptable`, `high`, `limited`, `minimal`. This field is optional and backward compatible -- existing emissions without it remain valid.

## Related Documents

- [NIST AI RMF Mapping](nist-ai-rmf-mapping.md)
- [ISO/IEC 42001 Mapping](iso-42001-mapping.md)
- `governance/schemas/panel-output.schema.json` -- structured emission schema with `ai_act_risk_tier` and model provenance fields
- `governance/policy/fin_pii_high.yaml` -- high-risk policy profile aligned with GDPR/SOC2/PCI-DSS requirements
