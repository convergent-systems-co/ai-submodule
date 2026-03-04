# Escalation Audit Trail

> Added in run-manifest schema v1.0.0 (Issue #436)

The escalation audit trail captures every instance where an automated governance agent escalated a decision to a human reviewer, and records the human's response. This provides a complete, immutable chain of custody for compliance audits.

## Overview

The `escalation_chain` property is an optional array on the run manifest. Each element represents a single escalation event -- the moment an agent determined it could not proceed autonomously and requested human judgment. When the human responds, their decision is recorded inline on the same event.

Because `escalation_chain` is optional and defaults to absent, all existing manifests remain valid (backward compatible).

## When Escalation Events Are Generated

The policy engine records an escalation event whenever:

| Trigger | `escalation_type` | Description |
|---|---|---|
| Policy evaluation returns `human_review_required` | `human_review_required` | A policy rule explicitly requires human sign-off (e.g., high-risk change in `fin_pii_high` profile). |
| Policy evaluation returns `block` and a human is consulted | `block_decision` | The engine blocked a merge and a human was asked to confirm or override the block. |
| A human requests a policy override | `policy_override` | A reviewer overrides the engine's decision (e.g., accepting risk on a blocked PR). |
| Circuit breaker threshold exceeded | `circuit_breaker` | Aggregate confidence dropped below the circuit-breaker threshold, halting autonomous processing. |

## Schema

Each escalation event object has the following fields:

### Required Fields

| Field | Type | Description |
|---|---|---|
| `timestamp` | `string` (date-time) | ISO 8601 timestamp when the escalation was initiated. |
| `source_agent` | `string` | The agent or component that initiated the escalation (e.g., `policy-engine`, `tech-lead`, `security-review`). |
| `target_role` | `string` | The human role escalated to (e.g., `security-lead`, `architect`, `compliance-officer`). |
| `reason` | `string` | Human-readable explanation of why the escalation was triggered. |
| `escalation_type` | `enum` | One of: `policy_override`, `human_review_required`, `circuit_breaker`, `block_decision`. |

### Optional Fields

| Field | Type | Description |
|---|---|---|
| `human_decision` | `object` | The human reviewer's response, recorded once a decision is made. |

### `human_decision` Object

When present, the `human_decision` object has these fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `action` | `enum` | Yes | One of: `approve`, `reject`, `defer`, `override`. |
| `justification` | `string` | When action is `override` | Explains why the reviewer overrode the governance decision. |
| `decision_timestamp` | `string` (date-time) | Yes | ISO 8601 timestamp when the decision was recorded. |
| `reviewer` | `string` | Yes | GitHub username of the human reviewer. |

## Example

```json
{
  "escalation_chain": [
    {
      "timestamp": "2026-02-27T12:01:00Z",
      "source_agent": "security-review",
      "target_role": "security-lead",
      "reason": "Critical CVE detected in transitive dependency (CVE-2026-1234).",
      "escalation_type": "circuit_breaker"
    },
    {
      "timestamp": "2026-02-27T12:05:00Z",
      "source_agent": "policy-engine",
      "target_role": "architect",
      "reason": "Block decision on PR #789 — human confirmation requested.",
      "escalation_type": "block_decision",
      "human_decision": {
        "action": "override",
        "justification": "Risk accepted per ADR-042; patch scheduled for next sprint.",
        "decision_timestamp": "2026-02-27T12:15:00Z",
        "reviewer": "octocat"
      }
    }
  ]
}
```

## Querying the Escalation Chain for Compliance Audits

### All escalations for a given PR

Extract from the run manifest JSON:

```bash
jq '.escalation_chain' run-manifest-20260227-120000-abcdef1.json
```

### All human overrides across manifests

```bash
jq -r '.escalation_chain[]? | select(.human_decision.action == "override") | "\(.timestamp) \(.human_decision.reviewer): \(.human_decision.justification)"' manifests/*.json
```

### Escalations without a human response (pending)

```bash
jq '.escalation_chain[]? | select(.human_decision == null)' manifests/*.json
```

### Count escalations by type

```bash
jq '[.escalation_chain[]?.escalation_type] | group_by(.) | map({type: .[0], count: length})' manifests/*.json
```

## Regulatory Compliance

### GDPR Article 22 — Automated Decision-Making

GDPR Article 22 grants data subjects the right not to be subject to a decision based solely on automated processing that produces legal or similarly significant effects. The escalation audit trail directly supports compliance by:

- **Recording when human oversight occurred.** Each `human_decision` entry proves a human was involved in the decision chain, satisfying the "not solely automated" requirement.
- **Capturing justification for overrides.** When a human overrides an automated block, the `justification` field documents the reasoning, which is required for demonstrating meaningful human involvement under Article 22(3).
- **Providing a queryable chain of custody.** Supervisory authorities can audit the full escalation history to verify that automated decisions were subject to appropriate human review.

### SOC 2 — Trust Services Criteria

The escalation chain supports SOC 2 Type II audits across multiple trust services criteria:

| Criteria | How the escalation chain helps |
|---|---|
| **CC6.1** (Logical access controls) | Records which human reviewer (by GitHub username) made each decision, linking governance actions to authenticated identities. |
| **CC7.2** (System operations monitoring) | Circuit-breaker escalations demonstrate that the system detects anomalies and halts automated processing when thresholds are exceeded. |
| **CC8.1** (Change management) | Every policy override is recorded with justification, providing auditors with evidence that changes followed an authorized approval process. |
| **CC9.1** (Risk mitigation) | The full escalation chain shows how risks were identified, escalated, and resolved — whether by automated block, human approval, or override with documented rationale. |

### Retention

Run manifests are append-only audit artifacts. The `escalation_chain` inherits this immutability — once a manifest is written, its escalation events must not be modified or deleted. Retention periods should align with your organization's compliance requirements (typically 7 years for SOC 2, or as required by applicable data protection regulations for GDPR).
