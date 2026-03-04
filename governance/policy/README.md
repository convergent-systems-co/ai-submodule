# Governance Policy Profiles

Policy profiles define deterministic rules for merge decisions. The policy engine evaluates structured panel emissions against these rules to produce one of four outcomes:

| Decision | Description |
|----------|-------------|
| `auto_merge` | All thresholds satisfied. Merge proceeds without human intervention. |
| `auto_remediate` | Issues detected but automatically fixable. Remediation attempted before re-evaluation. |
| `human_review_required` | Confidence, risk, or policy flags require human judgment. |
| `block` | Hard block. Merge cannot proceed without enterprise override. |

## Available Profiles

| Profile | File | Use When |
|---------|------|----------|
| Default | `default.yaml` | Standard internal repositories with moderate risk tolerance. |
| Financial PII High | `fin_pii_high.yaml` | Repositories handling financial data, PII, or regulated information (SOC2, PCI-DSS, HIPAA, GDPR). |
| Infrastructure Critical | `infrastructure_critical.yaml` | Infrastructure-as-code, CI/CD, deployment configs, platform services. |
| Fast-Track | `fast-track.yaml` | Lightweight profile for trivial changes (docs, typos, chores). Requires only code-review and security-review. |
| Reduced Touchpoint | `reduced_touchpoint.yaml` | Near-full autonomy, human approval only for policy overrides and dismissed security-critical findings (Phase 5e). |

## Profile Structure

Every policy profile defines:

1. **Weighting Model** - How panel confidence scores are aggregated.
2. **Risk Aggregation** - How individual risk assessments combine into a final risk level.
3. **Escalation Rules** - Conditions that trigger human review or block.
4. **Auto-merge Rules** - Conditions permitting automated merge.
5. **Auto-remediate Rules** - Conditions permitting automated fix attempts.
6. **Block Rules** - Hard stops that prevent merge.
7. **Override Rules** - Enterprise override procedure with audit requirements.
8. **Required Panels** - Panels that must execute for a valid decision.
9. **Optional Panels** - Panels triggered by change characteristics.

## Creating a New Profile

1. Copy `default.yaml` as a starting point.
2. Adjust thresholds, weights, and rules for your risk context.
3. Set `profile_name` and `profile_version`.
4. Reference the profile in your project's `project.yaml`:

```yaml
governance:
  policy_profile: fin_pii_high
```

## Design Principles

- **Deterministic**: Policy evaluation must produce the same result given the same inputs. No prose interpretation.
- **Auditable**: Every rule evaluation is logged in the run manifest.
- **Composable**: Profiles can be extended by overriding specific sections.
- **Backward Compatible**: New rules must not break existing profiles. Use additive changes only.

## Version History

| Profile | Current Version | Changes |
|---------|----------------|---------|
| default | 1.3.1 | Added parallel session support, reduced_touchpoint reference |
| fin_pii_high | 1.0.1 | Initial SOC2/PCI-DSS/HIPAA/GDPR compliance profile |
| infrastructure_critical | 1.0.1 | Initial mandatory architecture and SRE review profile |
| fast-track | 1.0.0 | Lightweight profile for trivial changes |
| reduced_touchpoint | 1.0.1 | Initial near-full autonomy profile |

## Schema Versioning Policy

Enforcement artifacts use **semantic versioning** (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking schema changes requiring migration. Consuming repos must update their configurations.
- **MINOR**: New optional fields, backward-compatible. No action required by consuming repos.
- **PATCH**: Documentation fixes, clarifications. No functional impact.

Cognitive artifacts (personas, prompts, workflows) version by **git SHA**. They evolve with the submodule and do not carry explicit version numbers.

Manifests are **immutable audit artifacts** -- never edited after creation. Each manifest carries a unique `manifest_id` and references the versions of all artifacts used in the governance decision.

## Breaking Change Process

When introducing a breaking change to a policy profile or schema:

1. Increment the **MAJOR** version in the `profile_version` field.
2. Document the change in the Version History table above.
3. Update consuming repo migration notes in `docs/governance/` or release notes.
4. Ensure backward compatibility is maintained for at least one major version (deprecate, then remove).
