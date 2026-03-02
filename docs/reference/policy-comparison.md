# Policy Comparison

Side-by-side comparison of the five deterministic policy profiles.
All profiles are evaluated programmatically by the policy engine --
AI models never interpret policy rules.

> **Auto-generated** by `governance/bin/generate-catalog.py`.
> Do not edit manually -- regenerate with `python governance/bin/generate-catalog.py`.

| Feature | **default** | **fin_pii_high** | **infrastructure_critical** | **reduced_touchpoint** |
|---------|------|------|------|------|
| Profile Version | 1.4.0 | 1.0.1 | 1.0.1 | 1.0.1 |
| Required Panels (count) | 6 | 8 | 6 | 6 |
| Auto-merge Enabled | Yes | No | Yes | Yes |
| Auto-merge Confidence Threshold | 0.85 | N/A | 0.90 | 0.75 |
| Escalation Threshold | 0.70 | 0.85 | 0.80 | policy override only |
| Block Threshold | 0.40 | 0.50 | 0.50 | 0.40 |
| Risk Aggregation | highest_severity | highest_severity | highest_severity | highest_severity |
| Override Min Approvals | 2 | 3 | 2 | 1 |
| Override Required Roles | senior_engineer, tech_lead | senior_engineer, security_lead, compliance_officer | sre_lead, infrastructure_lead | tech_lead |

## Profile Descriptions

### default

Baseline policy profile for standard repositories. Balances automation with human oversight. Suitable for internal applications with moderate risk tolerance.

### fin_pii_high

High-security policy profile for financial services and PII-handling repositories. Enforces strict compliance gating, mandatory security review, and reduced automation thresholds. Designed for SOC2, PCI-DSS, HIPAA, and GDPR compliance contexts.

### infrastructure_critical

Policy profile for infrastructure and platform repositories. Emphasizes production stability, blast radius assessment, and rollback capability. Mandatory architecture and production readiness reviews for structural changes.

### reduced_touchpoint

Near-full-autonomy policy profile that requires human approval only for policy-override scenarios, dismissed security-critical findings, or confidence drops below minimum threshold. Designed for repositories with mature governance pipelines where routine changes should flow through automated gates without human bottlenecks. All governance panels still execute — only the escalation and merge decision points are relaxed.

## Required Panels by Profile

### default

- code-review
- security-review
- threat-modeling
- cost-analysis
- documentation-review
- data-governance-review

### fin_pii_high

- code-review
- security-review
- data-design-review
- testing-review
- threat-modeling
- cost-analysis
- documentation-review
- data-governance-review

### infrastructure_critical

- code-review
- security-review
- architecture-review
- threat-modeling
- cost-analysis
- documentation-review

### reduced_touchpoint

- code-review
- security-review
- threat-modeling
- cost-analysis
- documentation-review
- data-governance-review
