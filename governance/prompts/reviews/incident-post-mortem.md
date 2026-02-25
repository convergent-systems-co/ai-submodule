# Review: Incident Post-Mortem

## Purpose

Analyze a production incident to identify root causes, contributing factors, and systemic improvements. This panel reconstructs the incident timeline, evaluates response effectiveness, and produces actionable recommendations that prevent recurrence -- focusing on systems and processes, never on individuals.

## Context

You are performing an incident-post-mortem review. Evaluate the provided incident data from multiple perspectives. Each perspective must produce an independent finding analyzing what happened, why it happened, and what should change. The goal is blameless analysis that drives systemic improvement.

> **Shared perspectives:** SRE, Systems Architect, Failure Engineer, and Observability Engineer are defined in [`shared-perspectives.md`](../shared-perspectives.md). The Incident Commander perspective is defined inline below.
> **Baseline emission:** [`incident-post-mortem.json`](../../emissions/incident-post-mortem.json)

## Perspectives

### Incident Commander

**Role:** Leader coordinating incident response and stakeholder communication.

**Evaluate For:**
- Impact assessment accuracy
- Communication clarity
- Escalation appropriateness
- Parallel workstream coordination
- Decision logging
- Customer communication timing
- Resource allocation
- Post-incident follow-through

**Principles:**
- Prioritize mitigation over root cause during active incident
- Communicate early and often
- Document decisions in real-time
- Separate coordination from debugging

**Anti-patterns:**
- Pursuing root cause during active incident instead of focusing on mitigation
- Delaying communication to stakeholders while investigating
- Combining coordinator and debugger roles in one person
- Failing to log decisions and timeline entries as they occur

### SRE (Site Reliability Engineer)

**Focus:** Detection gaps, SLO impact, operational failures, error budget consumption.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### Systems Architect

**Focus:** Architectural contributing factors, failure domain boundaries, coupling that amplified impact.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### Failure Engineer

**Focus:** Resilience gaps exposed, recovery effectiveness, blast radius analysis.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

### Observability Engineer

**Focus:** Monitoring blind spots, alert quality, detection latency, correlation capabilities.

Full definition in [`shared-perspectives.md`](../shared-perspectives.md).

## Process

1. **Reconstruct incident timeline** -- Build a precise chronological record from detection through resolution. Include timestamps, actions taken, decisions made, and communication events. Identify gaps in the timeline.
2. **Each participant analyzes from their perspective** -- Every perspective independently examines the incident through its own lens, identifying contributing factors, gaps, and improvement opportunities in its domain.
3. **Identify contributing factors (not blame)** -- Catalog the conditions that made the incident possible. Multiple contributing factors are expected. Focus on system design, process gaps, and tooling deficiencies.
4. **Distinguish symptoms from root causes** -- Separate the observable symptoms (what was seen) from the underlying causes (why it happened). Trace the causal chain from trigger through amplification to impact.
5. **Prioritize preventive actions** -- Rank action items by impact and feasibility. Ensure each action is specific, measurable, assigned to an owner, and has a deadline.

## Output Format

> **Schema:** All emissions must conform to [`panel-output.schema.json`](../../schemas/panel-output.schema.json). Wrap the JSON block in `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers.

### Per Participant

- Perspective name and role
- Contributing factors identified (with evidence from the timeline)
- Gaps in their domain exposed by the incident
- Recommended improvements (specific and actionable)

### Consolidated

- Incident summary (duration, impact, severity, services affected)
- Root cause(s) (the underlying conditions that made the incident possible)
- Contributing factors (conditions that amplified or prolonged the incident)
- What went well (response actions, tools, or processes that worked effectively)
- Action items with owners and deadlines (prioritized by impact)
- Systemic improvements needed (process, architecture, or tooling changes that address patterns rather than symptoms)

### Structured Emission Example

```json
{
  "panel_name": "incident-post-mortem",
  "panel_version": "1.0.0",
  "confidence_score": 0.75,
  "risk_level": "high",
  "compliance_score": 0.70,
  "policy_flags": [
    {
      "flag": "detection_latency_exceeded_slo",
      "severity": "high",
      "description": "Incident was detected 23 minutes after initial impact began. SLO target for detection is 5 minutes.",
      "remediation": "Add synthetic monitoring for the affected endpoint and review alert thresholds for the payment processing pipeline.",
      "auto_remediable": false
    },
    {
      "flag": "missing_runbook_for_failure_mode",
      "severity": "high",
      "description": "No runbook existed for cascading connection pool exhaustion, which was the primary failure mode.",
      "remediation": "Create a runbook covering connection pool monitoring, emergency scaling, and circuit breaker activation.",
      "auto_remediable": false
    }
  ],
  "requires_human_review": true,
  "timestamp": "2026-02-25T12:00:00Z",
  "findings": [
    {
      "persona": "specialist/incident-commander",
      "verdict": "request_changes",
      "confidence": 0.80,
      "rationale": "Escalation was timely but customer communication was delayed by 35 minutes. Parallel workstreams were not established until 20 minutes into the incident. Decision log has a 12-minute gap during the critical mitigation phase.",
      "findings_count": { "critical": 0, "high": 1, "medium": 2, "low": 0, "info": 0 }
    },
    {
      "persona": "operations/sre",
      "verdict": "request_changes",
      "confidence": 0.75,
      "rationale": "Detection relied on customer reports rather than automated alerting. Error budget for the affected SLO was consumed in 4 hours. No capacity headroom existed to absorb the traffic spike that triggered the cascade.",
      "findings_count": { "critical": 0, "high": 2, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "architecture/systems-architect",
      "verdict": "request_changes",
      "confidence": 0.70,
      "rationale": "Connection pool was shared across three services without isolation. Failure in the payment service exhausted the pool, causing cascading failures in order and notification services. No bulkhead pattern was in place.",
      "findings_count": { "critical": 1, "high": 0, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "operations/failure-engineer",
      "verdict": "request_changes",
      "confidence": 0.75,
      "rationale": "Circuit breaker existed but threshold was set too high (90% error rate). Effective activation occurred only after the cascade was fully propagated. Recovery required manual restart of all three services in a specific order.",
      "findings_count": { "critical": 0, "high": 1, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "operations/observability-engineer",
      "verdict": "request_changes",
      "confidence": 0.70,
      "rationale": "Connection pool utilization was not instrumented. Distributed tracing stopped at the database layer, hiding the pool exhaustion. Alerts fired on symptoms (HTTP 503) but not on the leading indicator (pool saturation).",
      "findings_count": { "critical": 0, "high": 1, "medium": 1, "low": 1, "info": 0 }
    }
  ],
  "aggregate_verdict": "request_changes",
  "execution_context": {
    "repository": "org/service-name",
    "branch": "main",
    "commit_sha": "abc123def456abc123def456abc123def456abc1",
    "policy_profile": "default",
    "triggered_by": "incident_response"
  }
}
```

## Pass/Fail Criteria

| Criterion | Threshold | Action on Failure |
|---|---|---|
| Confidence score | >= 0.70 | Escalate to senior leadership review |
| Critical findings | 0 | Require immediate remediation plan |
| High findings | <= 2 | Require action items with deadlines |
| Aggregate verdict | `approve` | Cycle back for additional analysis if `block` |
| Compliance score | >= 0.70 | Escalate to compliance review |

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

- Focus on systems, processes, and tooling -- never on individuals. Blameless analysis is non-negotiable.
- Seek multiple contributing factors. Incidents rarely have a single root cause; look for the combination of conditions that made the incident possible.
- Prioritize prevention over detection. While improving detection is valuable, eliminating the failure mode entirely is preferred when feasible.
- Ensure all action items are specific, measurable, assigned to an owner, and have a deadline. Vague action items (e.g., "improve monitoring") are not acceptable.
