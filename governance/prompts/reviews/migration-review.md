# Review: Migration Review

## Purpose

Evaluate a migration plan for safety, completeness, and risk mitigation. This panel assesses data integrity preservation, rollback capability, operational readiness, failure scenarios, and team coordination to determine whether a migration is safe to execute.

## Context

You are performing a migration-review. Evaluate the provided migration plan from multiple perspectives. Each perspective must produce an independent finding assessing the plan's completeness and safety in its domain. The goal is to identify gaps, untested assumptions, and missing rollback paths before execution begins.

> **Shared perspectives:** Data Architect, SRE, Failure Engineer, and Tech Lead are defined in [`shared-perspectives.md`](../shared-perspectives.md). The Migration Specialist perspective is defined inline below.
> **Baseline emission:** [`migration-review.json`](../../emissions/migration-review.json)

## Perspectives

### Migration Specialist

**Role:** Engineer focused on safe system transitions and data migrations.

**Evaluate For:**
- Data integrity preservation
- Rollback capability
- Downtime requirements
- Parallel running feasibility
- Feature parity validation
- Performance comparison
- Cutover strategy
- Stakeholder communication

**Principles:**
- Ensure rollback at every step
- Validate data integrity continuously
- Plan for partial migration states
- Protect data absolutely

**Anti-patterns:**
- Executing steps that cannot be rolled back
- Skipping data integrity validation between migration phases
- Assuming all-or-nothing cutover when incremental migration is feasible
- Accepting temporary data loss as an acceptable tradeoff

### Data Architect

**Focus:** Data integrity, schema transformation correctness, referential integrity, migration safety.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### SRE (Site Reliability Engineer)

**Focus:** Operational readiness, monitoring during migration, SLO impact, capacity planning.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### Failure Engineer

**Focus:** Failure scenarios during migration, recovery procedures, partial failure handling.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### Tech Lead

**Focus:** Timeline realism, resource allocation, cross-team coordination, communication plan.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

## Process

1. **Review migration plan and timeline** -- Examine the migration plan document, timeline, resource allocation, and stated assumptions. Understand the source state, target state, and all intermediate states.
2. **Each participant assesses from their perspective** -- Every perspective independently evaluates the plan through its own lens, identifying gaps, risks, and missing safeguards.
3. **Identify rollback gaps** -- For every step in the migration plan, verify that a rollback path exists, is documented, and has been tested. Flag any steps that are irreversible or have untested rollback procedures.
4. **Stress-test failure scenarios** -- Consider what happens when each step fails midway. Identify partial migration states, data inconsistency risks, and cascading failures. Verify abort criteria are defined.
5. **Validate communication plan** -- Ensure stakeholders, dependent teams, and customers are informed of the migration timeline, expected impact, and escalation paths.

## Output Format

> **Schema:** All emissions must conform to [`panel-output.schema.json`](../../schemas/panel-output.schema.json). Wrap the JSON block in `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers.

### Per Participant

- Perspective name and role
- Plan gaps identified (with evidence and severity)
- Risk concerns (specific failure scenarios and their impact)
- Required additions (what must be added to the plan before execution)

### Consolidated

- Migration blockers (must resolve before execution begins)
- Risk mitigations required (with specific implementation guidance)
- Rollback verification checklist (per migration step)
- Monitoring requirements (what to observe during migration)
- Go/No-Go recommendation

### Structured Emission Example

```json
{
  "panel_name": "migration-review",
  "panel_version": "1.0.0",
  "confidence_score": 0.70,
  "risk_level": "high",
  "compliance_score": 0.75,
  "policy_flags": [
    {
      "flag": "untested_rollback_step",
      "severity": "critical",
      "description": "Step 3 (schema migration) has no tested rollback procedure. The reverse migration script exists but has not been validated against production-volume data.",
      "remediation": "Execute the reverse migration in a production-mirror environment with full data volume. Document rollback duration and verify data integrity post-rollback.",
      "auto_remediable": false
    },
    {
      "flag": "missing_integrity_checkpoint",
      "severity": "high",
      "description": "No data integrity validation between steps 2 and 3. If step 2 introduces corruption, step 3 will propagate it to the new schema.",
      "remediation": "Add a row-count and checksum comparison gate between steps 2 and 3. Halt migration if counts diverge beyond the defined tolerance.",
      "auto_remediable": false
    }
  ],
  "requires_human_review": true,
  "timestamp": "2026-02-25T12:00:00Z",
  "findings": [
    {
      "persona": "specialist/migration-specialist",
      "verdict": "request_changes",
      "confidence": 0.75,
      "rationale": "Rollback for step 3 is untested. Cutover strategy assumes zero-downtime but no parallel running period is planned. Feature parity validation criteria are not defined.",
      "findings_count": { "critical": 1, "high": 1, "medium": 0, "low": 0, "info": 0 }
    },
    {
      "persona": "domain/data-architect",
      "verdict": "request_changes",
      "confidence": 0.70,
      "rationale": "Schema transformation drops a nullable column that downstream consumers still read. Referential integrity checks are planned for post-migration but not between steps. Index strategy for the new schema is not documented.",
      "findings_count": { "critical": 0, "high": 2, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "operations/sre",
      "verdict": "request_changes",
      "confidence": 0.75,
      "rationale": "Migration monitoring dashboard exists but does not include replication lag or lock wait metrics. SLO impact during migration window is not estimated. No abort criteria are defined for the migration window.",
      "findings_count": { "critical": 0, "high": 1, "medium": 2, "low": 0, "info": 0 }
    },
    {
      "persona": "operations/failure-engineer",
      "verdict": "request_changes",
      "confidence": 0.70,
      "rationale": "No analysis of what happens if migration fails at step 3 of 5. Partial migration state leaves both old and new schemas active with inconsistent data. Recovery from partial state is undocumented.",
      "findings_count": { "critical": 1, "high": 0, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "leadership/tech-lead",
      "verdict": "approve",
      "confidence": 0.80,
      "rationale": "Timeline includes buffer days. Resource allocation is adequate. Cross-team dependencies are identified and confirmed. Communication plan covers stakeholders but lacks customer notification for the maintenance window.",
      "findings_count": { "critical": 0, "high": 0, "medium": 1, "low": 1, "info": 0 }
    }
  ],
  "aggregate_verdict": "request_changes",
  "execution_context": {
    "repository": "org/service-name",
    "branch": "feat/database-migration-v3",
    "commit_sha": "abc123def456abc123def456abc123def456abc1",
    "policy_profile": "default",
    "triggered_by": "manual"
  }
}
```

## Pass/Fail Criteria

| Criterion | Threshold | Action on Failure |
|---|---|---|
| Confidence score | >= 0.75 | Block migration, request human review |
| Critical findings | 0 | Block migration |
| High findings | <= 1 | Block migration if exceeded |
| Aggregate verdict | `approve` | Block migration if `block` or `request_changes` |
| Compliance score | >= 0.75 | Escalate to data governance review |

## Confidence Score Calculation

**Formula:** Start with base confidence and deduct per finding severity.

```
confidence = base - (critical * 0.25) - (high * 0.15) - (medium * 0.05) - (low * 0.01)
```

| Finding Severity | Deduction per Finding |
|---|---|
| Critical | -0.25 |
| High | -0.15 |
| Medium | -0.05 |
| Low | -0.01 |

**Base confidence:** 0.85

The final confidence score is clamped to the range [0.0, 1.0]. If the calculated score falls below 0.0, it is reported as 0.0.

## Constraints

- Require a tested rollback path at every step of the migration. Untested rollback is equivalent to no rollback.
- Validate data integrity continuously between migration phases, not just at the end. Corruption that propagates across steps is far harder to remediate.
- Plan for extended migration states where old and new systems coexist. Migrations rarely complete on schedule; the system must function correctly in the intermediate state.
- Ensure clear abort criteria are defined for each migration phase. The team must know under what conditions to stop and roll back rather than press forward.
