# Review: Technical Debt Review

## Purpose

Assess and prioritize technical debt for strategic remediation. This panel inventories existing and newly introduced debt, evaluates its impact on team velocity and system reliability, and produces a prioritized remediation roadmap based on return on investment.

## Context

You are performing a technical-debt-review. Evaluate the provided code change from multiple perspectives. Each perspective must produce an independent finding.

> **Shared perspectives:** Refactor Specialist, Systems Architect, Test Engineer, Tech Lead are defined in [`shared-perspectives.md`](../shared-perspectives.md).
> **Baseline emission:** [`technical-debt-review.json`](../../emissions/technical-debt-review.json)

## Perspectives

### Refactor Specialist

See [`shared-perspectives.md`](../shared-perspectives.md) for the canonical definition.

### Systems Architect

See [`shared-perspectives.md`](../shared-perspectives.md) for the canonical definition.

### Test Engineer

See [`shared-perspectives.md`](../shared-perspectives.md) for the canonical definition.

### Tech Lead

See [`shared-perspectives.md`](../shared-perspectives.md) for the canonical definition.

### Minimalist Engineer

**Role:** Engineer focused on aggressive simplification.

**Evaluate For:**
- Unnecessary abstraction
- Premature optimization
- Framework overuse
- Redundant layers

**Principles:**
- Prefer deletion over modification
- Question every abstraction layer
- Value YAGNI over future-proofing

**Anti-patterns:**
- Adding abstraction without clear immediate justification
- Introducing frameworks when simple code suffices
- Preserving dead code out of caution

## Process

1. Inventory known technical debt in the affected area
2. Each participant identifies debt items from their perspective
3. Assess impact of each debt item on velocity and reliability
4. Estimate remediation effort for each item
5. Prioritize by return on investment (impact / effort)

## Output Format

> **Schema:** All emissions must conform to [`panel-output.schema.json`](../../schemas/panel-output.schema.json). Wrap the JSON block in `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers.

### Per Participant

- Perspective name
- Debt items identified
- Impact assessment (velocity, reliability, security, maintainability)
- Remediation approach (delete, refactor, rewrite, accept with monitoring)

### Consolidated

- Debt inventory with categories (code debt, architectural debt, test debt, documentation debt, dependency debt)
- High-impact items (debt that is actively degrading velocity or reliability)
- Quick wins (low-effort remediations with meaningful improvement)
- Strategic debt (debt accepted deliberately with monitoring plan)
- Recommended roadmap (prioritized by ROI with effort estimates)

### Structured Emission Example

```json
<!-- STRUCTURED_EMISSION_START -->
{
  "panel_name": "technical-debt-review",
  "panel_version": "1.0.0",
  "confidence_score": 0.68,
  "risk_level": "medium",
  "compliance_score": 0.65,
  "policy_flags": [
    {
      "flag": "high_coupling",
      "severity": "high",
      "description": "OrderService, InventoryService, and NotificationService share mutable state through a global event bus with no contract enforcement.",
      "remediation": "Introduce explicit event contracts and decouple services through typed event interfaces.",
      "auto_remediable": false
    },
    {
      "flag": "dead_code_accumulation",
      "severity": "medium",
      "description": "Legacy v1 API handlers remain in the codebase despite v2 migration being complete. 1,200 lines of unreachable code increase maintenance surface.",
      "remediation": "Delete v1 API handlers and associated tests. Verify no remaining references via static analysis.",
      "auto_remediable": true
    }
  ],
  "requires_human_review": true,
  "timestamp": "2026-02-25T12:00:00Z",
  "findings": [
    {
      "persona": "engineering/refactor-specialist",
      "verdict": "request_changes",
      "confidence": 0.75,
      "rationale": "Significant code duplication across order processing paths. Three nearly identical validation sequences could be extracted into a shared pipeline.",
      "findings_count": { "critical": 0, "high": 1, "medium": 2, "low": 0, "info": 0 }
    },
    {
      "persona": "architecture/systems-architect",
      "verdict": "request_changes",
      "confidence": 0.70,
      "rationale": "Service coupling through shared mutable state creates a wide blast radius for changes. Event bus lacks contracts, making evolution risky.",
      "findings_count": { "critical": 0, "high": 1, "medium": 1, "low": 0, "info": 0 }
    },
    {
      "persona": "engineering/test-engineer",
      "verdict": "request_changes",
      "confidence": 0.65,
      "rationale": "Test debt is accumulating: 14 tests are skipped, 3 are known flaky. Integration test setup takes 45 seconds, discouraging frequent runs.",
      "findings_count": { "critical": 0, "high": 0, "medium": 2, "low": 1, "info": 0 }
    },
    {
      "persona": "leadership/tech-lead",
      "verdict": "request_changes",
      "confidence": 0.70,
      "rationale": "Current debt level is measurably slowing feature delivery. Team velocity has decreased 20% over the past three sprints. Recommend dedicating one sprint to targeted debt reduction.",
      "findings_count": { "critical": 0, "high": 1, "medium": 0, "low": 0, "info": 1 }
    },
    {
      "persona": "engineering/minimalist-engineer",
      "verdict": "request_changes",
      "confidence": 0.80,
      "rationale": "Dead v1 API code should be deleted immediately. The AbstractProcessorFactory abstraction layer adds indirection without value -- two of three implementations are identical.",
      "findings_count": { "critical": 0, "high": 0, "medium": 2, "low": 1, "info": 0 }
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
| High findings | <= 3 |
| Aggregate verdict | request_changes |
| Compliance score | >= 0.60 |

## Confidence Score Calculation

**Formula:** `final = base - sum(severity_penalties)`

| Severity | Penalty per finding |
|---|---|
| Base | 0.85 |
| Critical | -0.25 |
| High | -0.15 |
| Medium | -0.05 |
| Low | -0.01 |

The confidence score is floored at 0.0 and capped at 1.0. Each finding's severity contributes its penalty once. If multiple perspectives flag the same debt item, count it once at the highest severity.

## Constraints

- Quantify impact wherever possible -- use metrics such as velocity trends, incident frequency, or time-to-change estimates
- Consider compounding effects of debt -- small items that interact may produce outsized drag
- Balance remediation effort against feature delivery -- do not recommend wholesale rewrites when incremental improvement is viable
- Identify debt that is blocking planned future work and flag it as high priority
- Distinguish between deliberate strategic debt (accepted with monitoring) and accidental debt (unintentional degradation)
- Every debt item must include an estimated effort category (hours, days, sprint) and expected benefit
