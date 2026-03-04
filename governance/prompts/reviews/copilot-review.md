# Review: Copilot Integration

## Purpose

Integrates GitHub Copilot as a formal review panel within the Dark Forge governance pipeline. Copilot feedback is parsed, classified, and emitted as structured output compatible with the policy engine. This enables Copilot's automated code analysis to participate in governance decisions alongside persona-based panels.

## Context

This review panel is unique -- it has a single participant (GitHub Copilot), and it is an external system integration rather than a persona-based review. Copilot comments are fetched from the GitHub API, parsed, classified by severity, and emitted as a structured panel output that the policy engine evaluates alongside all other panels.

> **Baseline emission:** [`copilot-review.json`](../../emissions/copilot-review.json)

## Role

GitHub Copilot acts as an **automated first-pass reviewer**. It does not have veto authority. Its findings are classified and weighted by the policy engine like any other panel, but Copilot cannot independently block a merge. Critical findings from Copilot escalate to human review rather than issuing a direct block.

## Integration Model

```
PR Created/Updated
       |
       v
GitHub Copilot Review (automatic, triggered by branch protection)
       |
       v
Parse Copilot Comments (via GitHub API)
       |
       v
Classify Findings (pattern-match severity)
       |
       v
Emit Structured Output (panel-output.schema.json)
       |
       v
Policy Engine (evaluates alongside other panel emissions)
```

## Feedback Parsing

### Comment Endpoints

Copilot posts review comments via the GitHub API. The following endpoints are queried to collect all Copilot feedback:

| Endpoint | API Path | Description |
|----------|----------|-------------|
| PR review comments | `GET /repos/{owner}/{repo}/pulls/{pull_number}/comments` | Line-level review comments |
| PR reviews | `GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews` | Top-level review summaries |
| Issue comments | `GET /repos/{owner}/{repo}/issues/{pull_number}/comments` | General PR conversation comments |

### Bot Identity

Copilot comments are identified by the `user.login` field on the comment object. The following identities are recognized:

| `user.login` | Description |
|---------------|-------------|
| `copilot` | Primary Copilot bot identity |
| `github-copilot[bot]` | GitHub App bot identity |
| `copilot-pull-request-reviewer[bot]` | Copilot PR reviewer bot |
| `github-advanced-security[bot]` | CodeQL / advanced security findings surfaced via Copilot |

### Filter Expression

Use the following `jq` filter to extract Copilot comments from the combined comment stream:

```jq
[.[] | select(.user.login == "copilot" or .user.login == "github-copilot[bot]" or .user.login == "copilot-pull-request-reviewer[bot]" or .user.login == "github-advanced-security[bot]")]
```

### Diagnostic Pre-Fetch Requirement

Before classifying Copilot comments, the integration must verify that Copilot has completed its review. If the PR was recently pushed to, Copilot may still be processing. The integration should:

1. Check the `reviews` endpoint for a Copilot review with `state: "APPROVED"` or `state: "CHANGES_REQUESTED"`
2. If no Copilot review exists and the PR was pushed to within the last 5 minutes, wait and retry (max 3 retries, 60-second intervals)
3. If no Copilot review exists after retries, emit a structured output with `confidence_score: 0.0` and the `copilot_review_missing` policy flag

### Classification Rules

Each Copilot comment body is pattern-matched against the following rules to assign a severity level:

| Severity | Patterns | Description |
|----------|----------|-------------|
| `critical` | `security vulnerability`, `injection`, `remote code execution`, `authentication bypass`, `secret exposed` | Direct security threats requiring immediate remediation |
| `high` | `bug`, `incorrect`, `will fail`, `data loss`, `race condition`, `null pointer`, `undefined behavior` | Functional defects likely to cause production incidents |
| `medium` | `potential issue`, `consider`, `may cause`, `edge case`, `error handling`, `missing validation` | Quality concerns that could lead to issues under certain conditions |
| `low` | `suggestion`, `improvement`, `readability`, `naming`, `simplify`, `refactor` | Code quality suggestions and style improvements |
| `info` | `note`, `fyi`, `documentation`, `comment`, `style` | Informational observations with no action required |

Classification is case-insensitive. If a comment matches multiple severity levels, the highest severity applies. Comments that match no pattern default to `info`.

## Output Format

> **Schema:** All emissions must conform to [`panel-output.schema.json`](../../schemas/panel-output.schema.json). Wrap the JSON block in `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers.

### Structured Emission Example

```json
<!-- STRUCTURED_EMISSION_START -->
{
  "panel_name": "copilot-review",
  "panel_version": "1.0.0",
  "confidence_score": 0.72,
  "risk_level": "medium",
  "compliance_score": 0.80,
  "policy_flags": [
    {
      "flag": "missing_null_check",
      "severity": "high",
      "description": "Copilot identified a potential null pointer dereference on line 45 of `src/handler.ts`.",
      "remediation": "Add null check before accessing `request.body.userId`.",
      "auto_remediable": true
    },
    {
      "flag": "unused_import",
      "severity": "low",
      "description": "Copilot flagged unused import of `lodash` in `src/utils.ts`.",
      "remediation": "Remove unused import.",
      "auto_remediable": true
    }
  ],
  "requires_human_review": false,
  "timestamp": "2026-02-25T12:00:00Z",
  "findings": [
    {
      "persona": "external/github-copilot",
      "verdict": "request_changes",
      "confidence": 0.72,
      "rationale": "Copilot identified 1 high-severity issue (null pointer dereference), 2 medium-severity issues (missing error handling, edge case), and 3 low-severity suggestions. No critical findings.",
      "findings_count": {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "info": 1
      }
    }
  ],
  "aggregate_verdict": "request_changes",
  "execution_context": {
    "repository": "example/repo",
    "branch": "feat/new-handler",
    "commit_sha": "abc123def456abc123def456abc123def456abc1",
    "pr_number": 73,
    "policy_profile": "default",
    "triggered_by": "ci"
  }
}
<!-- STRUCTURED_EMISSION_END -->
```

## Failure Conditions

The following conditions cause the Copilot panel to emit a degraded or failed result:

| Condition | Behavior | Emission |
|-----------|----------|----------|
| Copilot review not found after retries | Emit with zero confidence | `confidence_score: 0.0`, flag: `copilot_review_missing` |
| GitHub API rate limit exceeded | Emit with zero confidence | `confidence_score: 0.0`, flag: `api_rate_limited` |
| Comment parsing failure | Emit with zero confidence | `confidence_score: 0.0`, flag: `parse_error` |
| Copilot review is pending (not yet complete) | Retry up to 3 times, then emit degraded | `confidence_score: 0.0`, flag: `copilot_review_pending` |
| No Copilot comments (clean review) | Emit as passing with full confidence | `confidence_score: 0.80`, verdict: `approve` |

## Severity Mapping

Copilot comment severities map to policy engine severities as follows:

| Copilot Classification | Policy Engine Severity | Policy Weight |
|------------------------|------------------------|---------------|
| `critical` | `critical` | Escalate to human review |
| `high` | `high` | Weighted against approval threshold |
| `medium` | `medium` | Contributes to confidence deduction |
| `low` | `low` | Minimal impact on confidence |
| `info` | `info` | No impact on confidence or verdict |

## Pass/Fail Criteria

| Criterion | Threshold |
|-----------|-----------|
| Confidence score | >= 0.60 |
| Critical findings | 0 (escalate to human review) |
| High findings | <= 3 |
| Aggregate verdict | `approve` |
| Compliance score | >= 0.60 |

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

Each finding's severity contributes its penalty once. If multiple perspectives flag the same issue, count it once at the highest severity. The score is floored at 0.0 and capped at 1.0.
## GitHub Branch Protection Compatibility

This panel is designed to work alongside GitHub's native Copilot review integration in branch protection rules:

- **Branch protection can require Copilot review** as a separate check from the governance pipeline. These are independent gates -- both must pass.
- **The governance pipeline parses Copilot's output** regardless of whether branch protection requires it. If Copilot is not enabled for the repository, this panel emits `confidence_score: 0.0` with the `copilot_review_missing` flag and does not block.
- **Copilot approval in branch protection does not satisfy governance approval.** The policy engine evaluates Copilot findings alongside all other panels to produce an aggregate verdict.

## Execution Trace

To provide evidence of actual code evaluation, include an `execution_trace` object in your structured emission:

- **`files_read`** (required) — List every file you read during this review. Include the full relative path for each file (e.g., `src/auth/login.ts`, `infrastructure/main.bicep`). Do not omit files — this is the audit record of what was actually evaluated.
- **`diff_lines_analyzed`** — Count the total number of diff lines (added + removed + modified) you analyzed.
- **`analysis_duration_ms`** — Approximate wall-clock time spent on the analysis in milliseconds.
- **`grounding_references`** — For each finding, link it to a specific code location. Each entry must include `file` (file path) and `finding_id` (matching the finding's persona or a unique identifier). Include `line` (line number) when the finding maps to a specific line.

The `execution_trace` field is optional in the schema but **strongly recommended** for auditability. When present, it provides verifiable evidence that the panel agent actually read and analyzed the code rather than producing a generic assessment.

## Grounding Requirement

**Grounding Requirement**: Every finding with severity 'medium' or above MUST include an `evidence` block containing the file path, line range, and a code snippet (max 200 chars) from the actual code. Findings without evidence may be treated as hallucinated and discarded. If the review produces zero findings, you must still demonstrate analysis by populating `execution_trace.grounding_references` with at least one file+line reference showing what was examined.

## Limitations

- **No veto authority.** Copilot cannot independently block a merge. Critical findings escalate to human review.
- **Pattern-based classification.** Severity classification relies on keyword matching against comment bodies. Nuanced findings may be misclassified. When in doubt, the integration errs toward higher severity.
- **External dependency.** Panel reliability depends on GitHub API availability and Copilot service status. Transient failures produce degraded (zero-confidence) emissions, not pipeline failures.
- **No conversational context.** Copilot comments are classified individually. Multi-comment threads where Copilot refines its analysis are not correlated -- each comment is classified independently.
- **Model version opacity.** The underlying Copilot model version is not exposed via the API. The `model_version` field in `execution_context` is omitted for this panel.
