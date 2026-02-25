# Review: Performance Review

## Purpose

Comprehensive performance analysis from multiple perspectives. This panel evaluates algorithmic efficiency, infrastructure capacity, frontend responsiveness, and production reliability to identify bottlenecks, optimization opportunities, and capacity risks.

## Context

You are performing a performance-review. Evaluate the provided code change from multiple perspectives. Each perspective must produce an independent finding.

> **Shared perspectives:** Performance Engineer, Backend Engineer, Frontend Engineer, Infrastructure Engineer, SRE are defined in [`shared-perspectives.md`](../shared-perspectives.md).
> **Baseline emission:** [`performance-review.json`](../../emissions/performance-review.json)

## Perspectives

### Performance Engineer

See [`shared-perspectives.md`](../shared-perspectives.md) for the canonical definition.

### Backend Engineer

See [`shared-perspectives.md`](../shared-perspectives.md) for the canonical definition.

### Frontend Engineer

See [`shared-perspectives.md`](../shared-perspectives.md) for the canonical definition.

### Infrastructure Engineer

See [`shared-perspectives.md`](../shared-perspectives.md) for the canonical definition.

### SRE

See [`shared-perspectives.md`](../shared-perspectives.md) for the canonical definition.

## Process

1. Review performance requirements and SLOs relevant to the changed code
2. Analyze current metrics and known bottlenecks in the affected area
3. Each participant identifies performance issues from their perspective
4. Prioritize findings by user impact and production risk
5. Define measurement strategy for validating improvements

## Output Format

> **Schema:** All emissions must conform to [`panel-output.schema.json`](../../schemas/panel-output.schema.json). Wrap the JSON block in `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers.

### Per Participant

- Perspective name
- Bottlenecks identified
- Optimization opportunities
- Measurement recommendations

### Consolidated

- Critical performance issues (blocking merge or requiring immediate attention)
- Quick wins (low-effort optimizations with measurable impact)
- Longer-term optimizations (require design changes or dedicated effort)
- Capacity risks (scaling limits, resource exhaustion trajectories)
- Performance testing recommendations (benchmarks, load tests, profiling targets)

### Structured Emission Example

```json
<!-- STRUCTURED_EMISSION_START -->
{
  "panel_name": "performance-review",
  "panel_version": "1.0.0",
  "confidence_score": 0.72,
  "risk_level": "medium",
  "compliance_score": 0.75,
  "policy_flags": [
    {
      "flag": "n_plus_one_query",
      "severity": "high",
      "description": "OrderService.listWithItems() executes N+1 database queries when loading order items, scaling linearly with result set size.",
      "remediation": "Use a JOIN or batch query to load order items in a single database round-trip.",
      "auto_remediable": true
    },
    {
      "flag": "missing_cache_strategy",
      "severity": "medium",
      "description": "Product catalog lookup is called on every request with no caching layer. At projected traffic, this will saturate the database connection pool.",
      "remediation": "Introduce a read-through cache with TTL appropriate to catalog update frequency.",
      "auto_remediable": false
    }
  ],
  "requires_human_review": false,
  "timestamp": "2026-02-25T12:00:00Z",
  "findings": [
    {
      "persona": "engineering/performance-engineer",
      "verdict": "request_changes",
      "confidence": 0.80,
      "rationale": "N+1 query pattern in OrderService will degrade linearly with order count. Algorithmic complexity of search filtering is O(n^2) due to nested iteration.",
      "findings_count": { "critical": 0, "high": 1, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "domain/backend-engineer",
      "verdict": "request_changes",
      "confidence": 0.75,
      "rationale": "Database connection pool will be exhausted under concurrent load due to long-held transactions in the order listing path. No caching strategy for catalog data.",
      "findings_count": { "critical": 0, "high": 1, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "domain/frontend-engineer",
      "verdict": "approve",
      "confidence": 0.85,
      "rationale": "No frontend changes in this PR. API response payload size is reasonable for the use case.",
      "findings_count": { "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 1 }
    },
    {
      "persona": "operations/infrastructure-engineer",
      "verdict": "approve",
      "confidence": 0.80,
      "rationale": "Current resource allocation can handle projected load after query optimization. No scaling limit concerns at this stage.",
      "findings_count": { "critical": 0, "high": 0, "medium": 0, "low": 1, "info": 0 }
    },
    {
      "persona": "operations/sre",
      "verdict": "approve",
      "confidence": 0.70,
      "rationale": "SLO latency budget is at risk if N+1 query is not resolved before traffic increase. Recommend adding latency histogram metric for the order listing endpoint.",
      "findings_count": { "critical": 0, "high": 0, "medium": 1, "low": 0, "info": 0 }
    }
  ],
  "aggregate_verdict": "request_changes"
}
<!-- STRUCTURED_EMISSION_END -->
```

## Pass/Fail Criteria

| Criterion | Threshold |
|---|---|
| Confidence score | >= 0.65 |
| Critical findings | 0 |
| High findings | <= 2 |
| Aggregate verdict | approve |
| Compliance score | >= 0.65 |

## Confidence Score Calculation

**Formula:** `final = base - sum(severity_penalties)`

| Severity | Penalty per finding |
|---|---|
| Base | 0.85 |
| Critical | -0.25 |
| High | -0.15 |
| Medium | -0.05 |
| Low | -0.01 |

The confidence score is floored at 0.0 and capped at 1.0. Each finding's severity contributes its penalty once. If multiple perspectives flag the same bottleneck, count it once at the highest severity.

## Constraints

- Measure before optimizing -- do not recommend changes without evidence of a performance problem or credible projections
- Focus on user-perceived performance, not micro-benchmarks in isolation
- Consider the cost of optimization (code complexity, maintenance burden) against the expected improvement
- Require benchmarks or profiling data to validate any claim of significant performance impact
- Performance findings must include specific metrics or measurement approaches for validation
- Do not flag theoretical bottlenecks on cold paths without evidence of user impact
