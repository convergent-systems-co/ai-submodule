# Review: Code Review

## Purpose

Comprehensive code evaluation from multiple engineering perspectives. This panel examines correctness, security, performance, testability, and maintainability to produce a holistic assessment of production readiness.

## Context

You are performing a code-review. Evaluate the provided code change from multiple perspectives. Each perspective must produce an independent finding.

> **Shared perspectives:** Security Auditor, Performance Engineer, Test Engineer, Refactor Specialist are defined in [`shared-perspectives.md`](../shared-perspectives.md).
> **Baseline emission:** [`code-review.json`](../../emissions/code-review.json)

## Perspectives

### Code Reviewer

**Role:** Senior engineer performing strict production-level review focusing on correctness, safety, and runtime behavior.

**Evaluate For:**
- Correctness under concurrent access
- Edge cases and boundary conditions
- Error handling completeness
- Security risks
- Idempotency and retry safety
- Hidden mutable state
- Performance on hot paths
- Resource lifecycle

**Principles:**
- Every finding must include concrete remediation
- Focus on runtime behavior not aesthetics
- Prioritize by production impact
- Support findings with evidence

**Anti-patterns:**
- Style nitpicks unless they impact correctness
- Speculative criticism without failure scenario
- Suggesting rewrites when targeted fixes suffice
- Flagging theoretical performance issues without evidence

### Security Auditor

See [`shared-perspectives.md`](../shared-perspectives.md) for the canonical definition.

### Performance Engineer

See [`shared-perspectives.md`](../shared-perspectives.md) for the canonical definition.

### Test Engineer

See [`shared-perspectives.md`](../shared-perspectives.md) for the canonical definition.

### Refactor Specialist

See [`shared-perspectives.md`](../shared-perspectives.md) for the canonical definition.

## Process

1. Each participant reviews the code change independently
2. Present findings with severity (Critical / High / Medium / Low)
3. Identify conflicting recommendations across perspectives
4. Produce consolidated assessment with final recommendation

## Output Format

> **Schema:** All emissions must conform to [`panel-output.schema.json`](../../schemas/panel-output.schema.json). Wrap the JSON block in `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers.

### Per Participant

- Perspective name
- Key concerns
- Risk level
- Suggested changes

### Consolidated

- Must-fix items (blocking merge)
- Should-fix items (strongly recommended)
- Consider items (non-blocking suggestions)
- Tradeoff summary (conflicts between perspectives and resolution reasoning)
- Final recommendation (Approve / Request Changes / Reject)

### Structured Emission Example

```json
<!-- STRUCTURED_EMISSION_START -->
{
  "panel_name": "code-review",
  "panel_version": "1.0.0",
  "confidence_score": 0.82,
  "risk_level": "medium",
  "compliance_score": 0.85,
  "policy_flags": [
    {
      "flag": "unhandled_error_path",
      "severity": "high",
      "description": "Database connection error in UserService.fetch() is caught but silently discarded, masking failures.",
      "remediation": "Propagate the error or log with sufficient context for debugging.",
      "auto_remediable": false
    }
  ],
  "requires_human_review": false,
  "timestamp": "2026-02-25T12:00:00Z",
  "findings": [
    {
      "persona": "quality/code-reviewer",
      "verdict": "request_changes",
      "confidence": 0.85,
      "rationale": "Silent error swallowing in UserService.fetch() will mask production failures. Two boundary conditions in pagination logic are unhandled.",
      "findings_count": { "critical": 0, "high": 1, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "compliance/security-auditor",
      "verdict": "approve",
      "confidence": 0.90,
      "rationale": "No injection vectors or secret exposure detected. Input validation is present at all entry points.",
      "findings_count": { "critical": 0, "high": 0, "medium": 0, "low": 1, "info": 0 }
    },
    {
      "persona": "engineering/performance-engineer",
      "verdict": "approve",
      "confidence": 0.80,
      "rationale": "No algorithmic complexity concerns. Database query uses indexed lookup. Memory allocation patterns are appropriate.",
      "findings_count": { "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 1 }
    },
    {
      "persona": "engineering/test-engineer",
      "verdict": "request_changes",
      "confidence": 0.75,
      "rationale": "Error path in UserService.fetch() has no test coverage. Pagination boundary conditions lack edge case tests.",
      "findings_count": { "critical": 0, "high": 0, "medium": 2, "low": 0, "info": 0 }
    },
    {
      "persona": "engineering/refactor-specialist",
      "verdict": "approve",
      "confidence": 0.85,
      "rationale": "Code structure is clear. No duplication detected. Responsibility boundaries are well-defined.",
      "findings_count": { "critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0 }
    }
  ],
  "aggregate_verdict": "request_changes"
}
<!-- STRUCTURED_EMISSION_END -->
```

## Pass/Fail Criteria

| Criterion | Threshold |
|---|---|
| Confidence score | >= 0.70 |
| Critical findings | 0 |
| High findings | <= 2 |
| Aggregate verdict | approve |
| Compliance score | >= 0.70 |

## Confidence Score Calculation

**Formula:** `final = base - sum(severity_penalties)`

| Severity | Penalty per finding |
|---|---|
| Base | 0.85 |
| Critical | -0.25 |
| High | -0.15 |
| Medium | -0.05 |
| Low | -0.01 |

The confidence score is floored at 0.0 and capped at 1.0. Each finding's severity contributes its penalty once. If multiple perspectives flag the same issue, count it once at the highest severity.

## Constraints

- Focus on substantive issues that affect correctness, security, or reliability -- not style preferences
- Resolve conflicts between perspectives with explicit reasoning and tradeoff analysis
- Provide concrete remediation for every finding rated Medium or above
- Do not suggest rewrites when targeted, incremental fixes address the concern
- Every finding must reference specific code locations
