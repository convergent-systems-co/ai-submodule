# Acceptance Verification Workflow

**Workflow:** `governance/prompts/workflows/acceptance-verification.md`
**Phase:** 5e — Spec-Driven Interface
**Artifact type:** Cognitive (workflow prompt)
**Depends on:** `governance/schemas/formal-spec.schema.json`

## Purpose

The acceptance verification workflow validates an implementation against a formal spec's acceptance criteria and completion conditions before triggering review panels. It bridges the gap between implementation and panel review by providing structured, machine-verifiable validation.

## Where It Fits in the Pipeline

```
Issue → Formal Spec → Plan → Implementation → Acceptance Verification → Panel Review → Policy Engine → Merge
```

The workflow runs after implementation is complete and produces a structured emission compatible with the panel output schema. The policy engine treats it like any other panel result.

## What It Verifies

### Completion Conditions

Machine-verifiable checks from the formal spec:

| Condition Type | What's Checked |
|---------------|---------------|
| `file_exists` / `file_not_exists` | File presence or absence |
| `schema_valid` | Output validates against a JSON Schema |
| `grep_match` / `grep_no_match` | Pattern presence or absence in code |
| `ci_check_passes` | CI check status |
| `panel_approves` | Panel verdict |
| `test_passes` | Test results |
| `documentation_updated` | File modification in current branch |

### Acceptance Criteria

Structured criteria with 6 verification methods:

| Method | Approach |
|--------|---------|
| `automated_test` | Test exists and passes |
| `schema_validation` | Output validates against schema |
| `file_exists` | File present |
| `grep_match` | Pattern found |
| `manual_review` | Flagged for human — cannot automate |
| `panel_emission` | Panel has approved |

### Dependencies

Explicit dependency graph from the formal spec:
- **Blocking** dependencies must be resolved
- **Non-blocking** dependencies generate warnings
- **Informational** dependencies are logged

## Verdicts

| Verdict | Meaning | Next Step |
|---------|---------|-----------|
| `pass` | All `must` items verified | Proceed to panel review |
| `pass_with_warnings` | All `must` items pass; some `should` items failed | Proceed with warnings |
| `fail` | One or more `must` items failed | Return to implementation |

## Output

The workflow produces a structured panel emission conforming to `panel-output.schema.json`:

```json
{
  "panel_name": "acceptance-verification",
  "panel_version": "1.0.0",
  "confidence_score": 0.95,
  "risk_level": "low",
  "compliance_score": 1.0,
  "policy_flags": [],
  "requires_human_review": false,
  "timestamp": "2026-02-24T13:00:00Z",
  "findings": [
    {
      "persona": "agentic/code-manager",
      "verdict": "approve",
      "confidence": 0.95,
      "rationale": "All completion conditions pass. All must-have acceptance criteria verified."
    }
  ],
  "aggregate_verdict": "approve"
}
```

Workflow outcomes map to schema verdicts: `pass` → `"approve"`, `pass_with_warnings` → `"approve"` with `policy_flags`, `fail` → `"request_changes"`.

This emission is consumed by the policy engine alongside other panel outputs.

## Usage

The Code Manager invokes this workflow after Step 6 (implementation) and before Step 7 (PR monitoring) in `startup.md`, when a formal spec exists for the change. For changes without formal specs, the standard panel review flow applies directly.
