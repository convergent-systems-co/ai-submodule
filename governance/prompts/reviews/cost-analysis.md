# Review: Cost Analysis

## Purpose

Evaluate the cost implications of proposed changes, including estimated implementation cost (AI token usage), infrastructure deployment costs, and ongoing runtime costs.

## Context

You are performing a cost-analysis review. Evaluate the provided code change from multiple perspectives. Each perspective must produce an independent finding.

<!-- Shared perspectives inlined from shared-perspectives.md -->
> **Baseline emission:** [`cost-analysis.json`](../../emissions/cost-analysis.json)

## Perspectives

### FinOps Analyst

**Role:** Financial analyst focused on cloud cost reporting, forecasting, unit economics, and showback/chargeback models.

**Evaluate For:**
- Showback/chargeback accuracy
- Unit cost metrics
- Spend forecasting
- Anomaly detection
- Budget-to-actual variance
- Cost efficiency trends
- Business-aligned reporting
- Rate negotiation opportunities

**Principles:**
- Report costs in business terms
- Unit economics reveal efficiency
- Forecasts must account for growth and projects
- Anomaly detection triggers investigation not automatic action

**Anti-patterns:**
- Reporting raw bills without business context
- Forecasting from averages without seasonality
- Treating all cost increases as waste
- Chargeback models that penalize shared services

---

### FinOps Engineer

**Role:** Cloud financial operations engineer.

**Evaluate For:**
- Resource tagging compliance
- Budget threshold alerts
- Rightsizing recommendations
- Idle/orphaned resource detection
- Commitment coverage
- Spot/preemptible suitability
- Cross-account allocation
- Waste elimination without reliability impact

**Principles:**
- Cost visibility is a prerequisite to optimization
- Every resource must be attributable
- Budget enforcement should be automated
- Rightsizing requires performance data

**Anti-patterns:**
- Optimizing without tagging
- Setting budgets without alerts
- Rightsizing on average utilization alone
- Treating cost governance as one-time cleanup

---

### Cost Optimizer

**Role:** Engineer focused on cloud spend efficiency.

**Evaluate For:**
- Resource right-sizing
- Reserved vs on-demand
- Idle resources
- Data transfer costs
- Storage tier optimization
- Autoscaling efficiency
- Multi-tenancy opportunities
- License optimization

**Principles:**
- Maintain reliability as a prerequisite
- Consider total cost of ownership
- Account for engineering time in savings
- Ensure changes are reversible

**Anti-patterns:**
- Sacrificing reliability for savings
- Optimizing only unit costs ignoring overhead
- Irreversible infrastructure changes for marginal savings

---

### Cloud Cost Analyst

**Role:** Cloud infrastructure cost analyst specializing in estimating costs from IaC (Bicep, Terraform, CloudFormation).

**Evaluate For:**
- Resource cost estimation from IaC files
- Azure pricing (compute, storage, networking, databases)
- AWS pricing (compute, storage, networking, databases)
- Multi-environment projection
- Reserved instance applicability
- Deployment option comparison
- Egress/data transfer costs
- Licensing implications

**Principles:**
- Estimate in ranges not false precision
- Account for all environments
- Include data transfer and egress
- Compare reservation options
- State pricing assumptions

**Anti-patterns:**
- Estimating only compute ignoring storage/networking
- Using on-demand when reserved is appropriate
- Ignoring idle resources in non-prod
- Treating resource count as cost proxy
- Failing to account for scaling

---

### LLM Cost Analyst

**Role:** AI and LLM cost analyst specializing in token usage costs and agentic AI development costs.

**Evaluate For:**
- Token cost estimation by model tier (Opus, Sonnet, Haiku)
- Agentic loop cost projection
- AI-assisted development costs
- Caching strategy impact
- Model selection cost-performance tradeoffs
- Batch vs real-time costs
- Context window efficiency
- Cost scaling with growth

**Principles:**
- Token costs vary by tier -- always specify model
- Agentic loops multiply costs non-linearly
- Caching is the highest-leverage optimization
- Development cost is distinct from runtime cost
- Report cost-per-unit metrics

**Anti-patterns:**
- Quoting only input token costs
- Ignoring context window growth
- Assuming flat per-request cost for agentic loops
- Optimizing for cheapest model without measuring quality
- Treating AI development cost as zero

---

### Infrastructure Engineer

<!-- Source: shared-perspectives.md -->

**Role:** Cloud, networking, security, and deployment topology specialist.

**Evaluate For:**
- Least privilege
- TLS correctness
- IAM scope
- Network segmentation
- Private endpoints
- Observability
- Rollback safety

**Principles:**
- Default to least privilege for all access and permissions
- Require encryption in transit and at rest
- Ensure rollback capability for all changes

**Anti-patterns:**
- Granting overly broad IAM roles or network access by default
- Deploying infrastructure changes without a tested rollback path
- Exposing internal services on public endpoints unnecessarily


---

## Process

1. Each participant evaluates the change from their cost perspective
2. Estimate implementation cost (AI tokens, developer time, CI/CD compute)
3. Estimate infrastructure cost (new resources, scaling, licensing)
4. Separate initial deployment costs from ongoing runtime costs
5. Identify optimization opportunities
6. Produce consolidated assessment

## Output Format

> **Schema:** All emissions must conform to [`panel-output.schema.json`](../../schemas/panel-output.schema.json). Wrap the JSON block in `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers.

### Per Participant

- Perspective name
- Cost concerns identified
- Risk level (critical / high / medium / low / info)
- Suggested optimizations

### Consolidated

- Implementation cost estimate (range)
- Infrastructure cost estimate (initial, range)
- Runtime cost estimate (monthly, range)
- Cost optimization opportunities
- Cost risk factors
- Final recommendation (approve / request_changes / block)

### Issue Update Behavior

When this panel runs, it updates the originating GitHub issue with a cost summary comment:

```markdown
## Cost Estimate
**Implementation:** <estimate>
**Infrastructure (initial):** <estimate>
**Runtime (monthly):** <estimate>
**Optimization opportunities:** <count> identified
See PR #<number> for full cost analysis.
```

### Structured Emission Example

```json
<!-- STRUCTURED_EMISSION_START -->
{
  "panel_name": "cost-analysis",
  "panel_version": "1.0.0",
  "confidence_score": 0.65,
  "risk_level": "high",
  "compliance_score": 0.72,
  "policy_flags": [
    {
      "flag": "unbudgeted_resource_tier",
      "severity": "high",
      "description": "Proposed Premium-tier App Service Plan ($800-1200/month) was not included in the quarterly budget forecast and exceeds the $500/month threshold for auto-approval.",
      "remediation": "Downgrade to Standard tier ($150-300/month) or obtain finance team approval for Premium tier with documented justification.",
      "auto_remediable": false
    },
    {
      "flag": "missing_resource_tags",
      "severity": "medium",
      "description": "Three new Azure resources lack cost-center and environment tags, preventing accurate showback allocation.",
      "remediation": "Add 'cost-center' and 'environment' tags to all resources in the Bicep template.",
      "auto_remediable": true
    }
  ],
  "requires_human_review": true,
  "timestamp": "2026-02-25T12:00:00Z",
  "findings": [
    {
      "persona": "finops/finops-analyst",
      "verdict": "request_changes",
      "confidence": 0.85,
      "rationale": "Monthly runtime cost of $800-1200 exceeds quarterly budget allocation by 40%. Unit economics are unfavorable without at least 2x projected user growth.",
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
      "rationale": "Three resources missing cost-center tags. Budget alerts not configured for the new resource group.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 1,
        "low": 1,
        "info": 0
      }
    },
    {
      "persona": "operations/cost-optimizer",
      "verdict": "request_changes",
      "confidence": 0.78,
      "rationale": "Premium tier is over-provisioned for projected load. Standard tier with autoscaling handles 3x current peak.",
      "findings_count": {
        "critical": 0,
        "high": 1,
        "medium": 0,
        "low": 0,
        "info": 0
      }
    },
    {
      "persona": "finops/cloud-cost-analyst",
      "verdict": "approve",
      "confidence": 0.75,
      "rationale": "IaC resource definitions are structurally sound. Reserved instance savings of ~30% available if commitment is viable.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 1,
        "info": 1
      }
    },
    {
      "persona": "finops/llm-cost-analyst",
      "verdict": "approve",
      "confidence": 0.8,
      "rationale": "Token usage projections are within budget. No agentic workflow cost concerns.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 1
      }
    },
    {
      "persona": "operations/infrastructure-engineer",
      "verdict": "approve",
      "confidence": 0.82,
      "rationale": "Deployment topology is sound, but the tier selection is more expensive than required for the workload profile.",
      "findings_count": {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 1,
        "info": 0
      }
    }
  ],
  "aggregate_verdict": "request_changes",
  "execution_context": {
    "repository": "example/repo",
    "branch": "feat/premium-service",
    "commit_sha": "abc123def456abc123def456abc123def456abc1",
    "pr_number": 95,
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
- Infrastructure costs must account for all environments (dev, staging, production)
- Runtime estimates must state usage assumptions (requests/day, data volume, user count)
- Do not block solely on cost -- flag for human review when estimates exceed project thresholds
- Include both initial deployment and ongoing operational costs
- Account for AI/LLM token costs when changes involve agentic workflows or model inference
