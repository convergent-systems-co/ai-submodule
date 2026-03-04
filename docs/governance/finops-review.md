# FinOps Review Panel

## Purpose

The FinOps review panel (`finops-review`) evaluates the financial operations impact of proposed changes. It provides cost optimization recommendations including resource right-sizing, savings plan analysis, cost allocation compliance, and safe shutdown/decommission guidance with mandatory human approval guardrails.

## Panel Location

- **Review prompt:** `governance/prompts/reviews/finops-review.md`
- **Baseline emission:** `governance/emissions/finops-review.json`

## Perspectives

The panel uses five specialized perspectives:

| Perspective | Focus Area |
|-------------|------------|
| **FinOps Strategist** | Strategic cost optimization, cloud financial management, FinOps maturity |
| **Resource Optimizer** | Right-sizing, reserved instances, spot usage, idle resource detection |
| **Shutdown/Decommission Analyst** | Safe shutdown recommendations, destruction guardrails, rollback plans |
| **Savings Plan Advisor** | Reserved capacity analysis, commitment optimization, break-even analysis |
| **Cost Allocation Auditor** | Tagging compliance, cost allocation accuracy, showback/chargeback |

## Emission Fields

In addition to the standard fields defined in `panel-output.schema.json`, the FinOps review panel emits two additional fields:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `destruction_recommended` | boolean | `false` | Whether the panel recommends resource destruction or shutdown |
| `requires_human_approval` | boolean | `false` | Whether the change requires explicit human approval |

These fields are defined as optional in the schema and are available to all panels, though they are primarily used by the FinOps review panel.

## Safety Constraints

The following constraints are non-negotiable:

1. **NEVER automate resource destruction or shutdown.** The panel recommends; humans decide.
2. **`destruction_recommended: true` MUST always set `requires_human_approval: true`.** Destruction without human approval is never permitted.
3. **The policy engine blocks auto-merge when destruction is recommended.** The `default.yaml` profile includes a block condition: `destruction_recommended == true`.
4. **Every destruction recommendation MUST include a rollback plan.** The Shutdown/Decommission Analyst perspective is responsible for documenting rollback steps.

## Policy Integration

The `finops-review` panel is a required panel in four of the five policy profiles:

| Profile | Required |
|---------|----------|
| `default.yaml` | Yes |
| `fin_pii_high.yaml` | Yes |
| `infrastructure_critical.yaml` | Yes |
| `fast-track.yaml` | No |
| `reduced_touchpoint.yaml` | Yes |

### Block Conditions

The `default.yaml` profile includes a block condition that prevents auto-merge when destruction is recommended:

```yaml
block:
  conditions:
    - description: "Destruction recommended by FinOps review requires human approval."
      condition: destruction_recommended == true
```

### Weighting

In the `default.yaml` profile, `finops-review` has a weight of `0.04` in the confidence weighting model, consistent with the `cost-analysis` panel weight.

## Relationship to Cost Analysis

The `finops-review` panel complements the existing `cost-analysis` panel:

- **cost-analysis** focuses on estimating implementation, infrastructure, and runtime costs for a specific change.
- **finops-review** focuses on ongoing financial operations: optimization opportunities, resource lifecycle management, and organizational FinOps practices.

Both panels are required in the default profile. They serve different but complementary purposes in the governance pipeline.
