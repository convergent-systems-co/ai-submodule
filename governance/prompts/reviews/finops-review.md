# Review: FinOps Review

## Purpose

Evaluate the financial operations impact of proposed changes, including cloud cost optimization opportunities, resource right-sizing, savings plan analysis, cost allocation compliance, and safe shutdown/decommission recommendations with mandatory human approval guardrails.

## Context

You are performing a finops-review. Evaluate the provided code change from multiple perspectives. Each perspective must produce an independent finding.

> **Baseline emission:** [`finops-review.json`](../../emissions/finops-review.json)

## Perspectives

### FinOps Strategist

**Role:** Strategic cloud financial management advisor focused on organizational cost optimization, FinOps maturity, and cloud financial governance.

**Evaluate For:**
- Cloud financial management strategy alignment
- FinOps maturity model progression
- Cost optimization roadmap adherence
- Cloud unit economics and business value mapping
- Cross-team cost optimization opportunities
- Cloud financial governance policy compliance
- Budget forecasting accuracy and variance analysis
- Cost avoidance vs. cost savings distinction

**Principles:**
- Cost optimization must align with business objectives
- FinOps is a practice, not a one-time exercise
- Visibility precedes optimization
- Cost decisions must be data-driven
- Business value trumps raw cost reduction

**Anti-patterns:**
- Optimizing costs without understanding business impact
- Treating cost reduction as the sole objective
- Ignoring organizational FinOps maturity when recommending changes
- Making cost decisions without stakeholder alignment
- Confusing cost avoidance with cost savings in reporting

---

### Resource Optimizer

**Role:** Cloud resource optimization engineer focused on right-sizing, reserved capacity, spot/preemptible usage, and idle resource detection.

**Evaluate For:**
- Resource right-sizing opportunities (CPU, memory, storage, network)
- Reserved instance and savings plan coverage gaps
- Spot/preemptible instance suitability for workloads
- Idle and orphaned resource detection
- Over-provisioned resource identification
- Auto-scaling configuration efficiency
- Storage tier optimization (hot, cool, archive)
- Network data transfer cost optimization

**Principles:**
- Right-sizing requires performance data, not just utilization averages
- Reserved capacity decisions must account for workload variability
- Spot/preemptible usage must not compromise availability SLAs
- Idle resource detection must distinguish between inactive and standby

**Anti-patterns:**
- Right-sizing based solely on average utilization without peak analysis
- Committing to reserved instances without usage pattern analysis
- Using spot instances for stateful or latency-sensitive workloads
- Treating all idle resources as waste without understanding purpose

---

### Shutdown/Decommission Analyst

**Role:** Resource lifecycle analyst focused on safe shutdown recommendations, destruction guardrails, rollback planning, and decommission verification.

**CRITICAL SAFETY CONSTRAINT:** This perspective MUST recommend shutdown or destruction when resources are underutilized or no longer needed. However, it MUST NEVER automate shutdown or destruction. All destruction actions require explicit human approval. The panel recommends; humans decide.

**Evaluate For:**
- Underutilized resources eligible for shutdown or destruction
- Safe shutdown sequencing and dependency analysis
- Data backup and retention verification before destruction
- Rollback plan completeness and feasibility
- Decommission impact on dependent services
- Cost savings from shutdown/destruction (estimated monthly)
- Destruction justification documentation
- Human approval workflow readiness

**Principles:**
- Recommend destruction when data supports it, but NEVER automate it
- Every destruction recommendation MUST include a rollback plan
- Data retention policies must be verified before any resource removal
- Dependency analysis must be complete before shutdown sequencing
- Human approval is non-negotiable for any destructive action

**Anti-patterns:**
- Automating resource destruction without human approval
- Recommending shutdown without dependency analysis
- Destroying resources without verifying data backup status
- Skipping rollback plan documentation
- Treating destruction as reversible without explicit rollback steps

**Emission Requirements:**
- When recommending destruction: set `destruction_recommended: true` and `requires_human_approval: true`
- When NOT recommending destruction: set `destruction_recommended: false` and `requires_human_approval: false`
- `destruction_recommended: true` MUST always be paired with `requires_human_approval: true`

---

### Savings Plan Advisor

**Role:** Reserved capacity and savings plan analyst focused on commitment-based discount optimization across cloud providers.

**Evaluate For:**
- Savings plan coverage analysis (compute, EC2, SageMaker)
- Reserved instance utilization and coverage rates
- Commitment term optimization (1-year vs. 3-year)
- Payment option analysis (all upfront, partial, no upfront)
- Savings plan vs. reserved instance comparison
- Cross-account and cross-region savings plan applicability
- Commitment expiration and renewal planning
- Break-even analysis for new commitments

**Principles:**
- Commitment decisions require minimum 30 days of usage data
- Savings plans should cover baseline usage, not peak
- Term length must match workload lifecycle expectations
- Renewal planning should begin 90 days before expiration

**Anti-patterns:**
- Committing to savings plans without usage history
- Over-committing beyond baseline utilization
- Choosing 3-year terms for workloads with uncertain futures
- Ignoring cross-account flexibility when selecting plan types

---

### Cost Allocation Auditor

**Role:** Cloud cost allocation and tagging compliance auditor focused on accurate cost attribution, showback/chargeback models, and tagging governance.

**Evaluate For:**
- Resource tagging compliance (mandatory tags present and valid)
- Cost allocation accuracy across teams and projects
- Showback/chargeback model alignment
- Untagged or mis-tagged resource identification
- Tag governance policy adherence
- Cost center mapping accuracy
- Shared resource allocation fairness
- Tag propagation across resource hierarchies

**Principles:**
- Every resource must be attributable to a cost center
- Tagging compliance is a prerequisite for cost optimization
- Shared resources must have documented allocation methodology
- Tag governance must be enforced at provisioning time, not retroactively

**Anti-patterns:**
- Allowing untagged resources to persist beyond provisioning
- Using inconsistent tag keys or values across teams
- Allocating shared costs without documented methodology
- Treating tagging as optional or best-effort

---

## Process

1. Each participant evaluates the change from their FinOps perspective
2. Identify cost optimization opportunities and quantify potential savings
3. Assess resource lifecycle status and shutdown/decommission eligibility
4. Evaluate tagging compliance and cost allocation accuracy
5. Analyze savings plan and reserved capacity coverage
6. Determine if destruction is recommended (with mandatory human approval)
7. Produce consolidated assessment with structured emission

## Output Format

> **Schema:** All emissions must conform to [`panel-output.schema.json`](../../schemas/panel-output.schema.json). Wrap the JSON block in `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers.

### Per Participant

- Perspective name
- FinOps concerns identified
- Risk level (critical / high / medium / low / info)
- Suggested optimizations with estimated savings

### Consolidated

- Monthly cost optimization potential (range)
- Resource right-sizing recommendations
- Savings plan coverage gaps
- Tagging compliance percentage
- Shutdown/decommission recommendations (if any)
- Destruction recommended (true/false)
- Requires human approval (true/false)
- Final recommendation (approve / request_changes / block)

### Issue Update Behavior

When this panel runs, it updates the originating GitHub issue with a FinOps summary comment:

```markdown
## FinOps Review
**Monthly savings potential:** <estimate>
**Right-sizing opportunities:** <count> identified
**Tagging compliance:** <percentage>
**Destruction recommended:** <yes/no>
See PR #<number> for full FinOps review.
```

### Structured Emission Example

```json
<!-- STRUCTURED_EMISSION_START -->
{
  "panel_name": "finops-review",
  "panel_version": "1.0.0",
  "confidence_score": 0.65,
  "risk_level": "high",
  "compliance_score": 0.7,
  "policy_flags": [
    {
      "flag": "missing_budget_alert",
      "severity": "high",
      "description": "New resource group 'rg-analytics-prod' has no budget alert configured, risking undetected cost overruns.",
      "remediation": "Add a consumption budget with alert at 80% of the $2000/month allocation for the resource group.",
      "auto_remediable": true
    },
    {
      "flag": "oversized_sku",
      "severity": "medium",
      "description": "Cosmos DB provisioned throughput set to 10,000 RU/s but projected peak usage is only 2,000 RU/s.",
      "remediation": "Reduce to 4,000 RU/s with autoscale enabled (max 10,000 RU/s) to save ~$400/month.",
      "auto_remediable": true
    }
  ],
  "requires_human_review": false,
  "timestamp": "2026-02-25T12:00:00Z",
  "findings": [
    {
      "persona": "finops/finops-analyst",
      "verdict": "request_changes",
      "confidence": 0.85,
      "rationale": "No budget alerts on the new resource group. Projected spend of $1800/month has no monitoring or alerting configured.",
      "findings_count": {
        "critical": 0,
        "high": 1,
        "medium": 0,
        "low": 0,
        "info": 0
      }
    },
    {
      "persona": "finops/finops-engineer",
      "verdict": "request_changes",
      "confidence": 0.8,
      "rationale": "Cosmos DB is over-provisioned by 5x. Autoscale not enabled despite variable workload pattern.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 1,
        "low": 0,
        "info": 0
      }
    },
    {
      "persona": "operations/cost-optimizer",
      "verdict": "approve",
      "confidence": 0.78,
      "rationale": "Reserved instance coverage is adequate. Right-sizing Cosmos DB would save ~$400/month.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 1,
        "info": 1
      }
    },
    {
      "persona": "operations/infrastructure-engineer",
      "verdict": "approve",
      "confidence": 0.85,
      "rationale": "Deployment topology is sound. Scaling parameters need adjustment but are functionally correct.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 1
      }
    }
  ],
  "aggregate_verdict": "request_changes",
  "execution_context": {
    "repository": "example/repo",
    "branch": "feat/analytics-pipeline",
    "commit_sha": "abc123def456abc123def456abc123def456abc1",
    "pr_number": 72,
    "policy_profile": "default",
    "triggered_by": "ci"
  }
}
<!-- STRUCTURED_EMISSION_END -->
```

## Pass/Fail Criteria

| Criterion | Threshold |
|-----------|-----------|
| Confidence score | >= 0.65 |
| Critical findings | 0 |
| High findings | <= 2 |
| Aggregate verdict | `approve` |
| Compliance score | >= 0.65 |
| Destruction without human approval | Automatic block |

## Confidence Score Calculation

**Formula:** `final = base - sum(severity_penalties)`

| Parameter | Value |
|-----------|-------|
| Base confidence | 0.85 |
| Per critical finding | -0.25 |
| Per high finding | -0.15 |
| Per medium finding | -0.05 |
| Per low finding | -0.01 |
| Floor | 0.0 |
| Cap | 1.0 |

## Execution Trace

To provide evidence of actual code evaluation, include an `execution_trace` object in your structured emission:

- **`files_read`** (required) — List every file you read during this review. Include the full relative path for each file (e.g., `src/auth/login.ts`, `infrastructure/main.bicep`). Do not omit files — this is the audit record of what was actually evaluated.
- **`diff_lines_analyzed`** — Count the total number of diff lines (added + removed + modified) you analyzed.
- **`analysis_duration_ms`** — Approximate wall-clock time spent on the analysis in milliseconds.
- **`grounding_references`** — For each finding, link it to a specific code location. Each entry must include `file` (file path) and `finding_id` (matching the finding's persona or a unique identifier). Include `line` (line number) when the finding maps to a specific line.

The `execution_trace` field is optional in the schema but **strongly recommended** for auditability. When present, it provides verifiable evidence that the panel agent actually read and analyzed the code rather than producing a generic assessment.

## Grounding Requirement

**Grounding Requirement**: Every finding with severity 'medium' or above MUST include an `evidence` block containing the file path, line range, and a code snippet (max 200 chars) from the actual code. Findings without evidence may be treated as hallucinated and discarded. If the review produces zero findings, you must still demonstrate analysis by populating `execution_trace.grounding_references` with at least one file+line reference showing what was examined.

Each finding's severity contributes its penalty once. If multiple perspectives flag the same issue, count it once at the highest severity. The score is floored at 0.0 and capped at 1.0.
## Constraints

- Cost estimates must be expressed in ranges, not false precision (e.g., "$200-350/month" not "$273.41/month")
- NEVER automate resource destruction or shutdown -- panel recommends, humans decide
- `destruction_recommended: true` MUST always set `requires_human_approval: true`
- Policy engine MUST block auto-merge when destruction is recommended
- Savings plan recommendations require minimum 30 days of usage data
- Right-sizing recommendations must include both utilization and performance metrics
- Tagging compliance must be evaluated against the project's tag governance policy
- Decommission recommendations must include rollback plans and data retention verification
- All cost savings estimates must distinguish between cost avoidance and cost reduction
