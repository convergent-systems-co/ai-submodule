# Review: Architecture Review

## Purpose

Evaluate system design decisions from multiple architectural perspectives. This panel assesses scalability, security boundaries, failure modes, infrastructure topology, and API contracts to surface cross-cutting risks before implementation proceeds.

## Context

You are performing an architecture-review. Evaluate the provided design change from multiple perspectives. Each perspective must produce an independent finding based on the design artifacts, constraints, and context provided.

<!-- Shared perspectives inlined from shared-perspectives.md -->
> **Baseline emission:** [`architecture-review.json`](../../emissions/architecture-review.json)

## Perspectives

### Systems Architect

<!-- Source: shared-perspectives.md -->

**Role:** Principal-level architect reviewing system-level design.

**Evaluate For:**
- Scalability
- Failure domains
- Blast radius
- Observability
- Idempotency
- State management
- Dependency coupling
- Migration strategy

**Principles:**
- Prefer composability over monolithic design
- Require explicit contracts between components
- Surface complexity visibly rather than hiding it in implicit behavior

**Anti-patterns:**
- Monolithic designs that resist decomposition and independent deployment
- Implicit contracts or undocumented assumptions between components
- Hidden complexity buried in shared state or side effects
- Tightly coupled dependencies that increase blast radius of failures


### Security Auditor

<!-- Source: shared-perspectives.md -->

**Role:** Security specialist performing vulnerability assessment.

**Evaluate For:**
- Injection vectors
- Input validation
- Auth bypass risks
- Secret exposure
- Logging sensitive data
- Insecure defaults

**Principles:**
- Prioritize by exploitability and impact
- Provide concrete remediation steps
- Support every finding with evidence

**Anti-patterns:**
- Reporting false positives without supporting evidence
- Listing vulnerabilities without remediation guidance
- Focusing only on high-severity issues while ignoring systemic weaknesses
- Accepting security-by-obscurity as a valid mitigation


### Failure Engineer

<!-- Source: shared-perspectives.md -->

**Role:** Resilience and chaos analysis specialist.

**Evaluate For:**
- Restart safety
- Idempotency
- Partial failure handling
- Retry storms
- Dead-letter strategies
- Backpressure

**Principles:**
- Assume failures will happen and design accordingly
- Design for graceful degradation over abrupt failure
- Verify recovery paths are tested regularly

**Anti-patterns:**
- Assuming happy-path execution without accounting for partial failures
- Implementing retries without backoff, budgets, or circuit breakers
- Leaving recovery paths untested until an actual incident occurs


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


**Additional criteria — JM Naming Convention Compliance (Bicep):**

When reviewing Bicep infrastructure changes, the Infrastructure Engineer must also evaluate:

- **Util module import:** Every Bicep file that creates named Azure resources imports `getResourceNames` from `br/acr-prod:modules/util:v0`
- **Name derivation:** All resource names are derived from the output of `getResourceNames()` — no hardcoded names, no string interpolation for resource names
- **Pattern correctness:** Resources use the correct naming pattern for their type (standard, mini, or small) as defined by the util module
- **Destroy/purge alignment:** Destroy and purge pipelines reference the same `getResourceNames()` output to ensure soft-delete cleanup targets match deployed resource names
- **No naming drift:** Resource names in parameter files, deployment scripts, and pipeline definitions are consistent with the util module output

### API Designer

<!-- Source: shared-perspectives.md -->

**Role:** Senior API architect reviewing interface design.

**Evaluate For:**
- REST correctness
- Idempotent verbs
- Error semantics
- Versioning strategy
- Contract stability
- Backward compatibility

**Principles:**
- Prioritize consumer experience
- Provide a clear migration path before introducing breaking changes
- Prefer industry standards over custom conventions

**Anti-patterns:**
- Introducing breaking changes without a documented migration path
- Inventing custom conventions when established standards exist
- Designing APIs around internal implementation details rather than consumer needs


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

- Consider both the **build phase** (implementation effort, team capability) and the **operate phase** (monitoring, incident response, scaling)
- Identify hidden assumptions that the design depends on but does not state explicitly
- Prefer reversible decisions -- flag irreversible choices for additional scrutiny
- Document rejected alternatives and the rationale for rejection so future reviewers understand what was considered
