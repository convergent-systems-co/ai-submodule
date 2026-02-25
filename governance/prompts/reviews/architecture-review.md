# Review: Architecture Review

## Purpose

Evaluate system design decisions from multiple architectural perspectives. This panel assesses scalability, security boundaries, failure modes, infrastructure topology, and API contracts to surface cross-cutting risks before implementation proceeds.

## Context

You are performing an architecture-review. Evaluate the provided design change from multiple perspectives. Each perspective must produce an independent finding based on the design artifacts, constraints, and context provided.

> **Shared perspectives:** Systems Architect, Security Auditor, Failure Engineer, Infrastructure Engineer, and API Designer are defined in [`shared-perspectives.md`](../shared-perspectives.md).
> **Baseline emission:** [`architecture-review.json`](../../emissions/architecture-review.json)

## Perspectives

### Systems Architect

**Focus:** Scalability, component boundaries, state management, dependency coupling.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### Security Auditor

**Focus:** Attack surface, authentication model, data protection, insecure defaults.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### Failure Engineer

**Focus:** Resilience patterns, recovery paths, blast radius, graceful degradation.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### Infrastructure Engineer

**Focus:** Deployment topology, networking, operational readiness, rollback safety.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### API Designer

**Focus:** Contract stability, versioning strategy, consumer experience, backward compatibility.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

## Process

1. **Present design context and constraints** -- Gather architecture diagrams, ADRs, dependency maps, and stated requirements. Establish the boundaries of what is being reviewed.
2. **Each participant evaluates independently** -- Every perspective analyzes the design through its own lens, producing findings without influence from other perspectives.
3. **Surface cross-cutting concerns** -- Identify issues that span multiple perspectives (e.g., a scaling decision that introduces security risk, or a resilience pattern that complicates deployment).
4. **Debate tradeoffs explicitly** -- Where perspectives disagree, document the tension and the tradeoff being made. No silent compromises.
5. **Converge on recommendations** -- Synthesize individual findings into a unified assessment with clear action items, accepted tradeoffs, and a Go/No-Go recommendation.

## Output Format

> **Schema:** All emissions must conform to [`panel-output.schema.json`](../../schemas/panel-output.schema.json). Wrap the JSON block in `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers.

### Per Participant

- Perspective name and role
- Architectural concerns identified (with evidence)
- Risk assessment (critical / high / medium / low / info)
- Recommended changes (concrete and actionable)

### Consolidated

- Architectural strengths (what the design does well)
- Critical risks (blockers that must be resolved)
- Design modifications required (with rationale)
- Tradeoffs accepted (with explicit rationale for each)
- Go/No-Go recommendation

### Structured Emission Example

```json
{
  "panel_name": "architecture-review",
  "panel_version": "1.0.0",
  "confidence_score": 0.80,
  "risk_level": "medium",
  "compliance_score": 0.85,
  "policy_flags": [
    {
      "flag": "missing_failure_domain_isolation",
      "severity": "high",
      "description": "Services A and B share a database without failure domain isolation, creating a shared fate dependency.",
      "remediation": "Introduce a database-per-service pattern or implement circuit breakers at the shared dependency boundary.",
      "auto_remediable": false
    }
  ],
  "requires_human_review": false,
  "timestamp": "2026-02-25T12:00:00Z",
  "findings": [
    {
      "persona": "architecture/systems-architect",
      "verdict": "request_changes",
      "confidence": 0.85,
      "rationale": "Shared database between services A and B creates tight coupling. State management strategy does not account for eventual consistency during partition events.",
      "findings_count": { "critical": 0, "high": 1, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "compliance/security-auditor",
      "verdict": "approve",
      "confidence": 0.90,
      "rationale": "Auth model uses mTLS between services. API gateway enforces rate limiting. No secrets in configuration. Token rotation policy is defined.",
      "findings_count": { "critical": 0, "high": 0, "medium": 0, "low": 1, "info": 0 }
    },
    {
      "persona": "operations/failure-engineer",
      "verdict": "request_changes",
      "confidence": 0.80,
      "rationale": "No circuit breaker between service B and external payment provider. Blast radius of payment provider outage extends to all order processing.",
      "findings_count": { "critical": 0, "high": 1, "medium": 0, "low": 0, "info": 0 }
    },
    {
      "persona": "operations/infrastructure-engineer",
      "verdict": "approve",
      "confidence": 0.85,
      "rationale": "Deployment uses blue-green with health checks. Network segmentation isolates public and internal traffic. Rollback tested in staging.",
      "findings_count": { "critical": 0, "high": 0, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "architecture/api-designer",
      "verdict": "approve",
      "confidence": 0.88,
      "rationale": "API contracts use semantic versioning with header-based version negotiation. No breaking changes detected. Deprecation policy is documented.",
      "findings_count": { "critical": 0, "high": 0, "medium": 0, "low": 1, "info": 1 }
    }
  ],
  "aggregate_verdict": "request_changes",
  "execution_context": {
    "repository": "org/service-name",
    "branch": "feat/new-architecture",
    "commit_sha": "abc123def456abc123def456abc123def456abc1",
    "policy_profile": "default",
    "triggered_by": "manual"
  }
}
```

## Pass/Fail Criteria

| Criterion | Threshold | Action on Failure |
|---|---|---|
| Confidence score | >= 0.70 | Request human review |
| Critical findings | 0 | Block merge |
| High findings | <= 1 | Request changes if exceeded |
| Aggregate verdict | `approve` | Block merge if `block` or `request_changes` |
| Compliance score | >= 0.75 | Escalate to policy review |

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

- Consider both the **build phase** (implementation effort, team capability) and the **operate phase** (monitoring, incident response, scaling)
- Identify hidden assumptions that the design depends on but does not state explicitly
- Prefer reversible decisions -- flag irreversible choices for additional scrutiny
- Document rejected alternatives and the rationale for rejection so future reviewers understand what was considered
