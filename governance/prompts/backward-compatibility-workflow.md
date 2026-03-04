# Backward Compatibility Workflow

**Purpose:** Agentic workflow for the Tech Lead to check proposed changes for backward compatibility before merging. Prevents breaking changes from entering the governance pipeline without explicit approval and a documented migration path.

**Schema:** `governance/schemas/breaking-change.schema.json` (v1.0.0)
**Convention reference:** CLAUDE.md ("All changes must be additive. Breaking changes require migration plans and version bumps.")

---

## When to Execute

This workflow should be invoked by the Tech Lead during **Phase 3** (Implementation, before committing changes) and during **Phase 4e** (CI & Copilot Review Loop, reviewing recommendations). It applies to every PR that modifies governance artifacts.

**Trigger conditions (any one is sufficient):**
- A schema file (`governance/schemas/*.json`) is modified (not created)
- A policy file (`governance/policy/*.yaml`) is modified
- A prompt or workflow file (`governance/prompts/*.md`) is modified in a way that changes expected inputs/outputs
- A review prompt (`governance/prompts/reviews/*.md`) changes its structured emission format
- A configuration file (`config.yaml`, `panels.local.json`, `panels.defaults.json`) changes its structure
- An instruction file (`instructions.md`, `instructions/*.md`) changes in a way that alters agent behavior contracts

**Skip conditions:**
- The PR only adds new files (purely additive)
- The PR only modifies documentation files (`docs/**/*.md`, `README.md`, `DEVELOPER_GUIDE.md`)
- The PR only modifies `.artifacts/plans/` files
- The PR only modifies manifests or emissions (audit artifacts)

---

## Step 1: Artifact Type Detection

For each modified file in the PR, classify it:

| File Pattern | Artifact Type | Classification | Version Source |
|-------------|---------------|----------------|----------------|
| `governance/schemas/*.schema.json` | schema | enforcement | Semantic version field (e.g., `version` or `*_version`) if present; otherwise diff-based |
| `governance/policy/*.yaml` | policy | enforcement | `profile_version` or `version` field |
| `governance/prompts/*.md` | prompt | cognitive | Git SHA (no semantic version) |
| `governance/templates/prompts/*.md` | template | cognitive | Git SHA |
| `governance/prompts/reviews/*.md` | prompt | cognitive | Git SHA |
| `governance/schemas/panels.*.json` | configuration | enforcement | Internal semantic version field if present; otherwise diff-based |
| `config.yaml` | configuration | enforcement | Git SHA |
| `instructions*.md` | convention | cognitive | Git SHA |

> **Note:** Many existing JSON Schemas in this repo do not expose a dedicated `version` field. For those schemas, treat them as diff-analyzed artifacts: rely on structural diff review for compatibility, and only perform semantic version comparison when an explicit version field is present.

### Enforcement Artifacts (Versioned)

For enforcement artifacts **that expose a semantic version field**, extract the current version from the file and compare with the version on `main`. For enforcement artifacts **without** an explicit version field, skip version comparison and analyze the diff for breaking changes (same approach as cognitive artifacts).

### Cognitive Artifacts (Git SHA Versioned)

For cognitive artifacts, the "version" is the Git SHA. Breaking changes are detected by analyzing the diff, not by version comparison.

---

## Step 2: Contract Compatibility Check

For each modified artifact, determine whether the change preserves backward compatibility.

### Schema Changes (JSON Schema)

Check the diff against these breaking change rules:

| Change | Breaking? | Rule |
|--------|-----------|------|
| Remove a required field | **Yes** | Existing data will fail validation |
| Add a required field | **Yes** | Existing data missing the field will fail validation |
| Change a field's type | **Yes** | Existing data with the old type will fail validation |
| Remove an enum value | **Yes** | Existing data using that value will fail validation |
| Narrow a constraint (e.g., tighten min/max) | **Yes** | Existing data outside new bounds will fail |
| Add an optional field | No | Existing data is unaffected |
| Add an enum value | No | Existing data is unaffected |
| Widen a constraint | No | Existing data still valid |
| Change `description` text | No | No functional impact |
| Change `$id` or `title` | **Maybe** | Breaking if consumers reference by `$id` |

### Policy Changes (YAML)

| Change | Breaking? | Rule |
|--------|-----------|------|
| Remove a policy rule | **Yes** | Consumers relying on that rule lose enforcement |
| Change a threshold to be more restrictive | **Yes** | PRs that previously passed may now fail |
| Change `allowed_decisions` | **Yes** | Policy engine behavior changes |
| Add a new rule | No | Existing behavior unaffected |
| Change a threshold to be less restrictive | No | Existing passing PRs still pass |
| Change comments or descriptions | No | No functional impact |

### Prompt/Workflow Changes (Markdown)

| Change | Breaking? | Rule |
|--------|-----------|------|
| Remove or rename a step | **Yes** | Agents following the workflow will fail at that step |
| Change expected input format | **Yes** | Upstream producers must change |
| Change expected output format | **Yes** | Downstream consumers must change |
| Change structured emission format | **Yes** | Schema validation will fail |
| Add a new step | No | Existing steps unaffected |
| Clarify or reword existing steps | No | No behavioral change |
| Fix a bug in workflow logic | No | Correction, not breaking change |

### Template Changes

| Change | Breaking? | Rule |
|--------|-----------|------|
| Remove a template variable | **Yes** | Hydration will produce incomplete output |
| Rename a template variable | **Yes** | Hydration references will break |
| Change structured emission block format | **Yes** | Schema validation will fail |
| Add a new template variable | No | Hydration ignores unused variables |
| Reorder sections | No | No functional impact |

---

## Step 3: Breaking Change Decision

If **no breaking changes** are detected in Step 2:
- Log: "Backward compatibility check passed. No breaking changes detected."
- Exit workflow. Proceed with normal merge process.

If **breaking changes** are detected:
- Continue to Step 4.

---

## Step 4: Record the Breaking Change

For each breaking change detected, create a record conforming to `governance/schemas/breaking-change.schema.json`.

### Required Information

1. **Generate `change_id`** (UUID v4)
2. **Identify the affected artifact** (path, type, classification)
3. **Classify the change** (breaking or deprecation)
4. **Determine severity** based on consumer impact:
   - `critical` — All consumers break immediately (e.g., removing a required schema field used everywhere)
   - `high` — Most consumers break (e.g., changing a policy threshold used by the governance CI)
   - `medium` — Some consumers break (e.g., changing a prompt step that only some workflows reference)
   - `low` — Edge cases only (e.g., narrowing a constraint that only affects unusual inputs)
5. **Document version bump** — `version_before` from current `main`, `version_after` with appropriate major version bump
6. **Write migration path** — Concrete, ordered steps for each affected consumer
7. **List affected consumers** — Every consumer of this artifact

---

## Step 5: Require Approval

Breaking changes **cannot be auto-merged**. This overrides any governance review `auto_merge` decision.

### Approval Requirements by Severity

| Severity | Requirement |
|----------|-------------|
| `critical` | Human approval required. Flag the PR for human review. Do not proceed. |
| `high` | Human approval required. Flag the PR for human review. Do not proceed. |
| `medium` | Tech Lead may proceed if migration path is automated and all consumers are internal. Otherwise, human approval required. |
| `low` | Tech Lead may proceed if migration path is documented and no external consumers are affected. |

### If Approval Required

1. Comment on the PR with the breaking change record:
   ```
   ## Breaking Change Detected

   **Artifact:** {path}
   **Severity:** {severity}
   **Description:** {description}

   ### Migration Required
   {migration_steps}

   ### Affected Consumers
   {consumer_list}

   This PR requires human approval before merge.
   ```
2. Label the PR with `breaking-change`
3. Do not merge. Move to the next issue.

### If Self-Approval Permitted

1. Record the approval in the breaking change record with `approved_by: "tech-lead"`
2. Include the breaking change record in the commit
3. Ensure the version bump is applied to the artifact
4. Proceed to merge

---

## Step 6: Version Bump Verification

Before allowing merge of any PR containing a breaking change:

1. **For enforcement artifacts (schemas, policies):**
   - Verify the semantic version has been bumped appropriately:
     - Breaking change → major version bump (e.g., 1.0.0 → 2.0.0)
     - Deprecation → minor version bump with deprecation notice (e.g., 1.0.0 → 1.1.0)
   - If version was not bumped, block merge and request version update

2. **For cognitive artifacts (prompts, workflows, templates):**
   - No explicit version bump required (versioned by Git SHA)
   - Ensure the change is documented in the Decision Log of the active plan

3. **For configuration artifacts:**
   - Verify `config.yaml` version or structure version is updated if applicable

---

## Error Handling

| Error | Action |
|-------|--------|
| Cannot determine artifact type | Treat as potential breaking change. Require human review. |
| Cannot extract version from artifact | Log warning. Check diff for breaking patterns without version comparison. |
| Breaking change record fails schema validation | Fix the record. Do not proceed without a valid record. |
| Consumer impact cannot be assessed | Treat as `high` severity. Require human approval. |

---

## Cross-References

| Artifact | Purpose |
|----------|---------|
| `governance/schemas/breaking-change.schema.json` | Breaking change audit record schema |
| `governance/schemas/panel-output.schema.json` | Example of a versioned enforcement artifact |
| `governance/schemas/runtime-di.schema.json` | Example of schema with version constraints |
| `governance/policy/default.yaml` | Example of policy with profile_version |
| `governance/prompts/startup.md` | Startup sequence that invokes this workflow |
| `CLAUDE.md` | Source of backward compatibility convention |
