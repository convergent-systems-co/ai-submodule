# Review: Production Readiness Review

## Purpose

Assess whether a system is ready for production deployment. This panel evaluates operational maturity across reliability, infrastructure, observability, resilience, and delivery pipeline dimensions to determine if the system meets the bar for serving production traffic.

## Context

You are performing a production-readiness-review. Evaluate the provided system from multiple operational perspectives. Each perspective must produce an independent finding assessing readiness in its domain. The goal is to identify launch blockers, accepted risks, and post-launch requirements.

> **Shared perspectives:** SRE, Infrastructure Engineer, Observability Engineer, Failure Engineer, and DevOps Engineer are defined in [`shared-perspectives.md`](../shared-perspectives.md).
> **Baseline emission:** [`production-readiness-review.json`](../../emissions/production-readiness-review.json)

## Perspectives

### SRE (Site Reliability Engineer)

**Focus:** SLO definitions, error budgets, runbook completeness, on-call readiness, capacity planning.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### Infrastructure Engineer

**Focus:** Deployment topology, security posture, networking, least privilege, rollback safety.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### Observability Engineer

**Focus:** Logging completeness, metric coverage, distributed tracing, alert signal-to-noise, dashboard usefulness.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### Failure Engineer

**Focus:** Recovery procedures, rollback capability, graceful degradation, partial failure handling.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### DevOps Engineer

**Focus:** CI/CD pipeline health, artifact immutability, environment parity, secret handling, drift detection.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

## Process

1. **Review deployment architecture** -- Examine infrastructure diagrams, deployment configurations, scaling policies, and environment topology. Understand what is being deployed and where.
2. **Each participant assesses operational readiness** -- Every perspective independently evaluates the system's readiness in its domain, referencing checklists, standards, and operational experience.
3. **Identify gaps in observability and recovery** -- Surface blind spots in monitoring, logging, tracing, and alerting. Verify that recovery procedures exist, are documented, and have been tested.
4. **Evaluate incident response capability** -- Assess whether the team can detect, diagnose, and resolve production issues. Check for runbooks, escalation paths, and on-call coverage.
5. **Determine launch blockers vs follow-ups** -- Classify findings as launch blockers (must resolve before deployment) or follow-ups (acceptable post-launch with a tracked timeline).

## Output Format

> **Schema:** All emissions must conform to [`panel-output.schema.json`](../../schemas/panel-output.schema.json). Wrap the JSON block in `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers.

### Per Participant

- Perspective name and role
- Readiness gaps identified (with severity and evidence)
- Risk level for each gap (critical / high / medium / low / info)
- Required before launch (specific actions that block deployment)

### Consolidated

- Launch blockers (must resolve before production deployment)
- Launch risks (accepted with documented mitigation strategy)
- Post-launch requirements (with owners and deadlines)
- Operational runbook status (complete / partial / missing per critical path)
- Go/No-Go recommendation

### Structured Emission Example

```json
{
  "panel_name": "production-readiness-review",
  "panel_version": "1.0.0",
  "confidence_score": 0.75,
  "risk_level": "medium",
  "compliance_score": 0.80,
  "policy_flags": [
    {
      "flag": "missing_runbook",
      "severity": "high",
      "description": "No runbook exists for database failover, which is a critical recovery path.",
      "remediation": "Create and validate a database failover runbook. Test it in staging before launch.",
      "auto_remediable": false
    },
    {
      "flag": "incomplete_alerting",
      "severity": "medium",
      "description": "Alerting covers API latency but not background job queue depth or processing lag.",
      "remediation": "Add alerts for job queue depth > threshold and processing lag > SLO target.",
      "auto_remediable": true
    }
  ],
  "requires_human_review": true,
  "timestamp": "2026-02-25T12:00:00Z",
  "findings": [
    {
      "persona": "operations/sre",
      "verdict": "request_changes",
      "confidence": 0.80,
      "rationale": "SLOs are defined but error budgets are not instrumented. On-call rotation exists but no runbook for the two most likely failure scenarios (database failover and upstream timeout).",
      "findings_count": { "critical": 0, "high": 1, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "operations/infrastructure-engineer",
      "verdict": "approve",
      "confidence": 0.85,
      "rationale": "Deployment uses rolling updates with health checks. IAM follows least privilege. Network segmentation isolates the service. TLS is enforced end-to-end.",
      "findings_count": { "critical": 0, "high": 0, "medium": 0, "low": 1, "info": 1 }
    },
    {
      "persona": "operations/observability-engineer",
      "verdict": "request_changes",
      "confidence": 0.75,
      "rationale": "Structured logging is in place but distributed tracing does not propagate through the async job processor. Alerts exist for API latency but not for background job lag.",
      "findings_count": { "critical": 0, "high": 1, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "operations/failure-engineer",
      "verdict": "approve",
      "confidence": 0.80,
      "rationale": "Rollback procedure is tested. Circuit breakers protect external dependencies. Graceful degradation returns cached data when upstream is unavailable.",
      "findings_count": { "critical": 0, "high": 0, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "operations/devops-engineer",
      "verdict": "approve",
      "confidence": 0.88,
      "rationale": "CI/CD pipeline produces immutable artifacts with SHA-pinned dependencies. Environment parity between staging and production is verified. Secrets are in Vault.",
      "findings_count": { "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 1 }
    }
  ],
  "aggregate_verdict": "request_changes",
  "execution_context": {
    "repository": "org/service-name",
    "branch": "release/v2.0.0",
    "commit_sha": "abc123def456abc123def456abc123def456abc1",
    "policy_profile": "default",
    "triggered_by": "manual"
  }
}
```

## Pass/Fail Criteria

| Criterion | Threshold | Action on Failure |
|---|---|---|
| Confidence score | >= 0.75 | Request human review |
| Critical findings | 0 | Block launch |
| High findings | <= 1 | Block launch if exceeded |
| Aggregate verdict | `approve` | Block launch if `block` or `request_changes` |
| Compliance score | >= 0.80 | Escalate to policy review |

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

- Ensure rollback capability exists and has been tested for every deployment mechanism in use
- Verify alerting covers all critical paths, including background processing and async workflows
- Require runbooks for all known failure modes before granting production readiness
- Document accepted risks explicitly, including the mitigation strategy and the conditions under which the risk must be revisited
