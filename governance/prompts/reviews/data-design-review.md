# Review: Data Design

## Purpose

Evaluate data architecture, schema design, and data management practices for proposed changes. This panel assesses structural soundness, query performance, migration safety, security posture, and regulatory compliance of data-layer changes.

## Context

You are performing a data-design review. Evaluate the provided code change from multiple perspectives. Each perspective must produce an independent finding.

> **Shared perspectives:** Data Architect, Backend Engineer, Performance Engineer, Security Auditor, and Compliance Officer are defined in [`shared-perspectives.md`](../shared-perspectives.md).
> **Baseline emission:** [`data-design-review.json`](../../emissions/data-design-review.json)

## Perspectives

### Data Architect

> Defined in [`shared-perspectives.md`](../shared-perspectives.md).

---

### Backend Engineer

> Defined in [`shared-perspectives.md`](../shared-perspectives.md).

---

### Performance Engineer

> Defined in [`shared-perspectives.md`](../shared-perspectives.md).

---

### Security Auditor

> Defined in [`shared-perspectives.md`](../shared-perspectives.md).

---

### Compliance Officer

> Defined in [`shared-perspectives.md`](../shared-perspectives.md).

---

## Process

1. Review the data model, schema definitions, and access patterns introduced or modified by the change
2. Each participant evaluates the change independently from their perspective
3. Identify schema evolution risks (backward compatibility, migration complexity, rollback safety)
4. Assess query performance implications (index coverage, N+1 patterns, join complexity)
5. Evaluate compliance requirements (retention, privacy, audit trail, data classification)
6. Produce consolidated assessment with prioritized findings

## Output Format

> **Schema:** All emissions must conform to [`panel-output.schema.json`](../../schemas/panel-output.schema.json). Wrap the JSON block in `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers.

### Per Participant

- Perspective name
- Data concerns identified
- Risk level (critical / high / medium / low / info)
- Recommended changes

### Consolidated

- Schema issues requiring change (breaking changes, integrity violations)
- Performance risks (missing indexes, unbounded queries, N+1 patterns)
- Security and compliance gaps (unencrypted PII, missing audit columns, retention violations)
- Migration complexity assessment (reversibility, downtime requirements, data backfill)
- Data architecture recommendations (normalization, partitioning, caching strategy)

### Structured Emission Example

```json
<!-- STRUCTURED_EMISSION_START -->
{
  "panel_name": "data-design-review",
  "panel_version": "1.0.0",
  "confidence_score": 0.80,
  "risk_level": "medium",
  "compliance_score": 0.85,
  "policy_flags": [
    {
      "flag": "missing_index",
      "severity": "high",
      "description": "New query pattern on `orders.customer_id` lacks a covering index. Will degrade at scale.",
      "remediation": "Add composite index on (customer_id, created_at DESC) to support the new access pattern.",
      "auto_remediable": true
    },
    {
      "flag": "schema_backward_incompatible",
      "severity": "medium",
      "description": "Column rename from `status` to `order_status` breaks existing consumers.",
      "remediation": "Use additive migration: add `order_status`, backfill, migrate consumers, then drop `status`.",
      "auto_remediable": false
    }
  ],
  "requires_human_review": false,
  "timestamp": "2026-02-25T12:00:00Z",
  "findings": [
    {
      "persona": "domain/data-architect",
      "verdict": "request_changes",
      "confidence": 0.82,
      "rationale": "Schema rename is not backward compatible. Additive migration strategy required. Referential integrity constraints are correctly defined.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 1,
        "low": 1,
        "info": 0
      }
    },
    {
      "persona": "domain/backend-engineer",
      "verdict": "approve",
      "confidence": 0.80,
      "rationale": "Access patterns are well-defined. ORM usage is correct. Transaction boundaries are appropriate for the write path.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 1,
        "info": 1
      }
    },
    {
      "persona": "engineering/performance-engineer",
      "verdict": "request_changes",
      "confidence": 0.78,
      "rationale": "Missing index on the new query path will cause full table scans at scale. Cold-path queries are acceptable.",
      "findings_count": {
        "critical": 0,
        "high": 1,
        "medium": 0,
        "low": 0,
        "info": 0
      }
    },
    {
      "persona": "compliance/security-auditor",
      "verdict": "approve",
      "confidence": 0.85,
      "rationale": "Data encryption at rest and in transit is maintained. Access control on the new table follows least-privilege. No sensitive data exposed in logs.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 1
      }
    },
    {
      "persona": "compliance/compliance-officer",
      "verdict": "approve",
      "confidence": 0.83,
      "rationale": "Retention policy applied to new table. Audit columns (created_at, updated_by) present. PII fields identified and classified.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 1,
        "info": 0
      }
    }
  ],
  "aggregate_verdict": "request_changes",
  "execution_context": {
    "repository": "example/repo",
    "branch": "feat/order-schema",
    "commit_sha": "abc123def456abc123def456abc123def456abc1",
    "pr_number": 55,
    "policy_profile": "default",
    "triggered_by": "ci"
  }
}
<!-- STRUCTURED_EMISSION_END -->
```

## Pass/Fail Criteria

| Criterion | Threshold |
|-----------|-----------|
| Confidence score | >= 0.70 |
| Critical findings | 0 |
| High findings | <= 1 |
| Aggregate verdict | `approve` |
| Compliance score | >= 0.75 |

## Confidence Score Calculation

**Base confidence:** 0.85

Apply deductions based on the highest-severity finding from each participant:

| Severity | Deduction |
|----------|-----------|
| Critical | -0.25 |
| High | -0.15 |
| Medium | -0.05 |
| Low | -0.01 |

**Formula:**
```
final_confidence = base - sum(deductions for each participant's highest-severity finding)
```

If any single deduction would push the score below 0.0, clamp to 0.0. Confidence scores above 1.0 are not possible given the base and deduction model.

## Constraints

- Plan for schema evolution -- all schema changes must be additive or use multi-phase migration
- Consider data growth trajectories when evaluating index and query strategies
- Ensure audit trail coverage for all tables containing business-critical or regulated data
- Design for both OLTP (transactional) and analytics (reporting) access patterns where applicable
- Migration scripts must include tested rollback procedures
- PII and sensitive fields must be classified and documented in the schema
