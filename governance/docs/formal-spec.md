# Formal Spec Schema

**Schema:** `governance/schemas/formal-spec.schema.json`
**Example:** `governance/schemas/examples/formal-spec.example.json`
**Phase:** 5e — Spec-Driven Interface
**Artifact type:** Enforcement (JSON Schema)

## Purpose

The formal spec schema defines a structured specification format richer than GitHub issue templates. It enables:

1. **Structured acceptance criteria** — Each criterion has a testable assertion and a verification method, not just free text
2. **Dependency declarations** — Explicit blocking/non-blocking dependency graph between specs and issues
3. **Risk pre-classification** — Severity, policy profile, compliance flags, and data classification declared upfront
4. **Machine-verifiable completion conditions** — Conditions an agent can check programmatically to determine if a spec is fully implemented

## How It Integrates

```
GitHub Issue (free text)
    |
    v
Formal Spec (structured, machine-readable)
    |
    v
Plan (.plans/ — implementation strategy)
    |
    v
Implementation + Tests
    |
    v
Completion Conditions verified (automated)
    |
    v
Acceptance Criteria verified (automated + panel)
    |
    v
Panel Review → Policy Engine → Merge Decision
```

The formal spec sits between issue intake and plan creation. It translates human intent into machine-verifiable contracts. The acceptance verification workflow (future 5e artifact) will consume formal specs to validate implementations before triggering review panels.

## Schema Structure

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `spec_version` | string | Always `"1.0.0"` |
| `spec_id` | uuid | Unique identifier |
| `title` | string | Short title (max 200 chars) |
| `origin` | enum | How the spec was created: `human`, `runtime-signal`, `goals-item`, `retrospective` |
| `acceptance_criteria` | array | At least one structured criterion |
| `risk_classification` | object | Severity + policy profile |
| `completion_conditions` | array | At least one machine-verifiable condition |
| `created_at` | datetime | ISO 8601 creation timestamp |

### Acceptance Criteria

Each criterion specifies:

- **`id`** — Identifier like `AC-1`, `AC-2`
- **`description`** — What must be true
- **`verification_method`** — How to verify: `automated_test`, `schema_validation`, `file_exists`, `grep_match`, `manual_review`, or `panel_emission`
- **`verification_target`** — File path, test name, grep pattern, or panel name
- **`priority`** — MoSCoW: `must` (blocks completion), `should` (expected), `could` (nice to have)

### Completion Conditions

Machine-verifiable checks:

| Type | What It Checks |
|------|---------------|
| `file_exists` | A specific file must exist |
| `file_not_exists` | A file must not exist |
| `schema_valid` | Output validates against a JSON Schema |
| `grep_match` | A pattern must match in specified files |
| `grep_no_match` | A pattern must not match (e.g., no hardcoded secrets) |
| `ci_check_passes` | A CI check must pass |
| `panel_approves` | A governance panel must approve |
| `test_passes` | Tests in a directory/file must pass |
| `documentation_updated` | A documentation file must be updated |

### Dependencies

Each dependency declares:

- **`type`** — `blocking` (must resolve first), `non-blocking` (work can proceed), `informational` (awareness only)
- **`ref`** — Issue number, spec ID, file path, or URL
- **`resolved`** — Whether the dependency has been met

### Risk Classification

Pre-classifies the change to route it to the correct policy profile and panels:

- **`severity`** — `critical`, `high`, `medium`, `low`, `negligible`
- **`policy_profile`** — Which governance profile applies
- **`affected_layers`** — Which governance layers are affected
- **`compliance_flags`** — Relevant regulatory frameworks
- **`data_classification`** — Highest data sensitivity level

## Usage

### For Agents (Code Manager)

1. When validating intent (Step 4 of startup.md), translate the issue into a formal spec
2. Use completion conditions to determine when implementation is done
3. Use acceptance criteria to scope the plan
4. Use risk classification to select the appropriate policy profile

### For Humans

1. Create a formal spec when requirements are complex or regulated
2. Attach the spec to the GitHub issue body or link it
3. The structured format reduces ambiguity and provides a clear completion checklist

### Storage

Formal specs can be stored:
- Inline in issue bodies (as JSON code blocks)
- As files in `.specs/` (consuming repo directory, not yet created by init.sh)
- As attachments to plans in `.plans/`

## Future Integration

- **Acceptance verification workflow** (5e) — Reads formal specs and runs completion conditions before triggering panels
- **Reduced human touchpoint model** (5e) — Uses risk classification and completion conditions to determine if human approval is needed
