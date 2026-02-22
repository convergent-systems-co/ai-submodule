# Panel: Cost Analysis

## Purpose
Evaluate the cost implications of proposed changes, including estimated implementation cost (AI token usage), infrastructure deployment costs, and ongoing runtime costs.

## Participants
- **FinOps Analyst** - Unit economics, forecasting, cost trend analysis
- **FinOps Engineer** - Tagging standards, budget enforcement, cost governance
- **Cost Optimizer** - Resource right-sizing, waste elimination, commitment planning
- **Infrastructure Engineer** - Deployment topology, resource requirements, scaling costs

## Process
1. Each participant evaluates the change from their cost perspective
2. Estimate implementation cost (AI tokens, developer time, CI/CD compute)
3. Estimate infrastructure cost (new resources, scaling changes, licensing)
4. Separate initial deployment cost from ongoing runtime cost
5. Identify cost optimization opportunities
6. Produce consolidated cost assessment with recommendations

## Output Format
### Per Participant
- Perspective name
- Cost concerns (bulleted)
- Risk level
- Suggested optimizations

### Consolidated
- **Implementation cost estimate** (one-time: AI tokens, CI compute, setup)
- **Infrastructure cost estimate** (initial deployment: new resources, licenses)
- **Runtime cost estimate** (monthly: compute, storage, bandwidth, licensing)
- **Cost optimization opportunities** (itemized savings)
- **Cost risk factors** (scaling surprises, usage-based pricing variability)
- Final recommendation (Approve/Flag for Review/Reject)

## Pass/Fail Criteria

This panel **passes** when all of the following are met:

| Criterion | Threshold | Blocked If |
|-----------|-----------|------------|
| Confidence score | >= 0.65 | Below 0.65 |
| Critical findings | 0 allowed | Any critical finding present |
| High findings | <= 2 | More than 2 high findings |
| Aggregate verdict | approve | Block or abstain majority |
| Compliance score | >= 0.65 | Below 0.65 |

When blocked, the panel emits a `block` verdict with a structured explanation of which criterion failed. The PR comment includes the specific scores and finding counts.

Local overrides via `panels.local.json` can increase these thresholds (more restrictive) but never decrease them. See `governance/schemas/panels.schema.json` for the override format.

## Confidence Score Calculation

```
confidence = 0.85  (base)
           - (critical_findings x 0.25)
           - (high_findings x 0.15)
           - (medium_findings x 0.05)
           - (low_findings x 0.01)
           = max(confidence, 0.0)  (floor)
```

| Finding Severity | Deduction | Example: 1 finding |
|-----------------|-----------|-------------------|
| Critical | -0.25 | 0.85 -> 0.60 |
| High | -0.15 | 0.85 -> 0.70 |
| Medium | -0.05 | 0.85 -> 0.80 |
| Low | -0.01 | 0.85 -> 0.84 |

## Issue Update Behavior

When this panel runs, it updates the originating GitHub issue with a cost summary comment:

```
## Cost Estimate

**Implementation:** <estimate>
**Infrastructure (initial):** <estimate>
**Runtime (monthly):** <estimate>
**Optimization opportunities:** <count> identified

See PR #<number> for full cost analysis.
```

## Constraints
- Cost estimates should use ranges, not false precision
- Infrastructure costs must account for all environments (dev, staging, prod)
- Runtime estimates must state assumptions about usage volume
- Do not block PRs solely on cost; flag for human review when estimates exceed thresholds
