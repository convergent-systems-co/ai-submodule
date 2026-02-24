# Workflow: Acceptance Verification

Validates an implementation against a formal spec's acceptance criteria and completion conditions before triggering review panels. This workflow sits between implementation and panel review in the governance pipeline.

## Prerequisites

- A formal spec instance conforming to `governance/schemas/formal-spec.schema.json`
- Implementation complete (code committed, tests written)
- Access to the codebase and CI status

## Phases

1. **Spec Loading** → `[AV-1]`
2. **Completion Conditions** → `[AV-2]` — **GATE**
3. **Acceptance Criteria** → `[AV-3]` — **GATE**
4. **Dependency Check** → `[AV-4]`
5. **Verification Report** → `[AV-5]` — **GATE**

---

## Phase 1: Spec Loading

> **Adopt persona:** `governance/personas/agentic/code-manager.md`

### Input

- Path to the formal spec JSON file, or formal spec content inline
- The branch or PR containing the implementation

### Process

1. Load the formal spec and validate it against `governance/schemas/formal-spec.schema.json`
2. If validation fails, stop — the spec itself is malformed
3. Extract:
   - All `acceptance_criteria` items
   - All `completion_conditions` items
   - All `dependencies` items
   - The `risk_classification` for panel routing
4. Log the spec summary: title, ID, number of criteria, number of conditions, risk severity

### Output

`[AV-1]: Spec Summary` — Parsed spec with counts and risk classification.

---

## Phase 2: Completion Conditions

> **Adopt persona:** `governance/personas/agentic/coder.md`

Evaluate each `completion_condition` from the formal spec. These are machine-verifiable checks.

### Process

For each completion condition, evaluate based on its `type`:

| Type | Verification Method |
|------|-------------------|
| `file_exists` | Check if the file at `assertion` path exists in the codebase |
| `file_not_exists` | Check that the file at `assertion` path does NOT exist |
| `schema_valid` | Validate the relevant output against the JSON Schema at `assertion` path |
| `grep_match` | Search the codebase for the pattern in `assertion`; pass if at least one match |
| `grep_no_match` | Search the codebase for the pattern in `assertion`; pass if zero matches |
| `ci_check_passes` | Query CI check status for the check named in `assertion` |
| `panel_approves` | Verify the panel named in `assertion` has emitted an approval verdict |
| `test_passes` | Run or verify test results for the test path in `assertion` |
| `documentation_updated` | Verify the file in `assertion` has been modified in the current branch |

### Decision

- **All conditions pass:** Proceed to Phase 3
- **Any condition fails:** Log the failures, report them, and stop. Do not evaluate acceptance criteria when any completion condition is unsatisfied.

### Output

`[AV-2]: Completion Condition Results` — Table of condition ID, type, assertion, and pass/fail status.

---

## Phase 3: Acceptance Criteria

> **Adopt persona:** `governance/personas/quality/code-reviewer.md`

Evaluate each `acceptance_criterion` from the formal spec.

### Process

For each criterion, evaluate based on its `verification_method`:

| Method | Verification Approach |
|--------|---------------------|
| `automated_test` | Confirm the test at `verification_target` exists and passes |
| `schema_validation` | Validate output against the schema at `verification_target` |
| `file_exists` | Confirm the file at `verification_target` exists |
| `grep_match` | Search for the pattern in `verification_target` |
| `manual_review` | Flag for human review — cannot be verified automatically |
| `panel_emission` | Verify the panel at `verification_target` has emitted a passing verdict |

### Decision

- **All `must` criteria pass and all `should` criteria pass:** Full verification — proceed to Phase 4
- **All `must` criteria pass but some `should` criteria fail:** Partial verification — proceed with warnings
- **Any `must` criterion fails:** Verification blocked — report failures, do not proceed to panels

### Output

`[AV-3]: Acceptance Criteria Results` — Table of criterion ID, description, method, priority, and pass/fail/skipped status.

---

## Phase 4: Dependency Check

> **Adopt persona:** `governance/personas/agentic/code-manager.md`

### Process

1. For each `dependency` in the spec:
   - If `type` is `blocking` and `resolved` is `false`: fail
   - If `type` is `non-blocking` and `resolved` is `false`: warn
   - If `type` is `informational`: log only
2. Check that no new unresolved blocking dependencies have been introduced since the spec was created

### Decision

- **No unresolved blocking dependencies:** Proceed to Phase 5
- **Unresolved blocking dependencies exist:** Stop — cannot proceed until resolved

### Output

`[AV-4]: Dependency Status` — Table of dependency type, description, ref, and resolved status.

---

## Phase 5: Verification Report

> **Adopt persona:** `governance/personas/agentic/code-manager.md`

### Process

1. Aggregate results from Phases 2-4 into a structured verification report
2. Determine the overall verification verdict:
   - **`pass`** — All completion conditions pass, all `must` acceptance criteria pass, no blocking dependencies
   - **`pass_with_warnings`** — All `must` items pass, but some `should` items or non-blocking dependencies failed
   - **`fail`** — Any `must` completion condition, acceptance criterion, or blocking dependency failed
3. Include the risk classification from the spec to inform panel routing
4. Produce the report as a structured emission conforming to `governance/schemas/panel-output.schema.json`

### Output

`[AV-5]: Verification Report` — Structured panel emission conforming to `panel-output.schema.json`:

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
      "rationale": "All 5 completion conditions pass. All 3 must-have acceptance criteria verified. No blocking dependencies."
    }
  ],
  "aggregate_verdict": "approve"
}
```

Map workflow outcomes to schema verdicts:
- `pass` → `aggregate_verdict: "approve"`, all findings verdicts `"approve"`
- `pass_with_warnings` → `aggregate_verdict: "approve"`, include `policy_flags` for each warning, findings may use `"approve"` with reduced confidence
- `fail` → `aggregate_verdict: "request_changes"`, include failing conditions as `policy_flags`, findings use `"request_changes"`

Map `risk_classification.severity` from the spec directly to the emission's `risk_level`.

### Gate Decision

- **`pass`:** Proceed to governance panel review:
  - If the spec provides a non-empty `panels_required` list, invoke exactly those panels.
  - If `panels_required` is absent, use the default required panels from the active policy profile.
  - If `panels_required` is present but an empty list, do not add any spec-specific panels; only the policy profile's default required panels (if any) are invoked.
- **`pass_with_warnings`:** Proceed to panel review using the same panel-selection rules as `pass`, with warnings included in the emission.
- **`fail`:** Do not invoke panels. Return to implementation to address failures.

---

## Integration with Governance Pipeline

```
Implementation complete
    |
    v
Acceptance Verification Workflow (this workflow)
    |
    +---> [AV-2] Completion conditions checked
    +---> [AV-3] Acceptance criteria verified
    +---> [AV-4] Dependencies confirmed
    +---> [AV-5] Verification report emitted
    |
    v (if pass or pass_with_warnings)
Panel Review (code-review, security-review, etc.)
    |
    v
Policy Engine → Merge Decision
```

The acceptance verification report is emitted as a panel-compatible structured emission. The policy engine treats it like any other panel output — it factors into the aggregate confidence score and merge decision.

## When to Use This Workflow

- When a formal spec (`formal-spec.schema.json` instance) exists for the change
- After implementation is complete but before panel review
- Especially valuable for complex changes with many acceptance criteria or regulated changes requiring compliance verification

## When NOT to Use This Workflow

- Trivial changes without a formal spec (use standard panel review directly)
- Emergency hotfixes where verification can happen post-merge
- Changes that only affect cognitive artifacts (documentation, personas, prompts)
