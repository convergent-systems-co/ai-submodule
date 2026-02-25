# CI and Branch Protection Blueprint -- Dark Factory Governance

**Document Classification:** Enforcement Artifact
**Governance Layer:** Execution Governance
**Part Reference:** Phase 4 Foundation, Part 9
**Status:** Normative

---

## Preamble

This document defines the Continuous Integration gating architecture and branch protection configuration for the Dark Factory Governance system. It specifies the required artifacts, status checks, policy enforcement logic, and override procedures that collectively ensure every merge into a protected branch is deterministic, auditable, and reproducible.

**Enterprise Policy Constraint:** The existing workflow `.github/workflows/jm-compliance.yml` is locked by enterprise policy and MUST NOT be modified. All CI additions defined in this blueprint operate alongside it. The `jm-compliance.yml` workflow provides OWASP dependency checking, GHAS dependency review, and CodeQL code scanning. These capabilities are treated as upstream prerequisites; the governance workflow defined here consumes their results but never duplicates or overrides them.

---

## 1. Required Structured Outputs

Every pull request targeting a protected branch must produce the following artifacts before a merge can proceed. Missing or invalid artifacts constitute a hard block.

### 1.1 Panel Structured Emissions

Each AI review panel (including GitHub Copilot) must emit a structured JSON block conforming to `governance/schemas/panel-output.schema.json`.

**Required Fields:**

| Field                  | Type     | Constraint                                     |
|------------------------|----------|-------------------------------------------------|
| `panel_name`           | string   | Must match a registered panel identifier.       |
| `panel_version`        | string   | SemVer. Must match the panel file commit hash.  |
| `timestamp`            | string   | ISO 8601 UTC. Must be within the current run.   |
| `confidence_score`     | number   | Range `[0.0, 1.0]`. Precision to 3 decimals.   |
| `risk_level`           | string   | Enum: `low`, `medium`, `high`, `critical`.      |
| `compliance_score`     | number   | Range `[0.0, 1.0]`. Precision to 3 decimals.   |
| `policy_flags`         | string[] | Zero or more policy flag identifiers.           |
| `requires_human_review`| boolean  | Explicit human escalation signal from the panel.|
| `findings`             | object[] | Array of finding objects (see below).           |
| `reasoning_hash`       | string   | SHA-256 hash of the Markdown reasoning block.   |

**Finding Object Schema:**

| Field       | Type   | Constraint                                        |
|-------------|--------|---------------------------------------------------|
| `id`        | string | Unique within the emission.                       |
| `severity`  | string | Enum: `info`, `warning`, `error`, `critical`.     |
| `category`  | string | Free-form classification tag.                     |
| `message`   | string | Human-readable description.                       |
| `file_path` | string | Relative path to the affected file, if applicable.|
| `line_range`| object | `{ "start": int, "end": int }`, if applicable.   |

**Validation Rules:**

- The JSON block must be parseable as valid JSON.
- All required fields must be present and type-correct.
- `confidence_score` and `compliance_score` must be within `[0.0, 1.0]`.
- `risk_level` must be one of the enumerated values.
- `reasoning_hash` must correspond to the SHA-256 of the accompanying Markdown reasoning section. A mismatch indicates tampering or emission corruption and constitutes a hard block.
- Emissions with `confidence_score < 0.3` must set `requires_human_review` to `true`. If this invariant is violated, validation fails.

### 1.2 Policy Evaluation Result

The policy engine must produce a policy evaluation result for every pull request.

**Required Fields:**

| Field                    | Type     | Constraint                                              |
|--------------------------|----------|---------------------------------------------------------|
| `policy_profile`         | string   | Identifier of the policy profile applied.               |
| `policy_version`         | string   | SemVer of the policy engine.                            |
| `decision`               | string   | Enum: `auto_merge`, `auto_remediate`, `human_review_required`, `block`. |
| `aggregate_confidence`   | number   | Weighted aggregate across all panel emissions.          |
| `aggregate_risk`         | string   | Enum: `low`, `medium`, `high`, `critical`.              |
| `panel_emissions`        | string[] | List of panel emission artifact references (URIs).      |
| `flags_triggered`        | string[] | Union of all `policy_flags` from panel emissions.       |
| `escalation_reason`      | string   | Required when `decision` is `human_review_required` or `block`. |
| `timestamp`              | string   | ISO 8601 UTC.                                           |
| `jm_compliance_status`   | string   | Enum: `passed`, `failed`, `skipped`. Status of the upstream JM Compliance workflow. |

**Validation Rules:**

- `decision` must be deterministically reproducible from the input emissions and the policy profile. No stochastic evaluation.
- If any panel emission has `requires_human_review: true`, the decision must be at least `human_review_required`.
- If `jm_compliance_status` is `failed`, the decision must be `block` regardless of other inputs.
- `aggregate_confidence` must be computed using the weighting model defined in the active policy profile. The computation must be logged.

### 1.3 Run Manifest

A run manifest conforming to `governance/schemas/run-manifest.schema.json` must be produced for every merge event.

**Required Fields:**

| Field                   | Type     | Constraint                                              |
|-------------------------|----------|---------------------------------------------------------|
| `manifest_version`      | string   | SemVer of the manifest schema.                          |
| `run_id`                | string   | Unique identifier for this governance run (UUID v4).    |
| `persona_set_commit`    | string   | Git commit SHA of the persona set used.                 |
| `panel_graph_version`   | string   | Version of the panel execution graph.                   |
| `policy_profile_used`   | string   | Identifier of the policy profile.                       |
| `model_version`         | string   | Identifier of the AI model(s) used during panel execution. |
| `aggregate_confidence`  | number   | Final aggregate confidence score.                       |
| `risk_level`            | string   | Final aggregate risk level.                             |
| `human_intervention`    | boolean  | Whether a human intervened in the decision.             |
| `override_applied`      | boolean  | Whether an enterprise override was used.                |
| `policy_decision`       | string   | The policy engine decision.                             |
| `jm_compliance_ref`     | string   | GitHub Actions run ID of the JM Compliance workflow.    |
| `panel_emissions_refs`  | string[] | References to all panel emission artifacts.             |
| `timestamp`             | string   | ISO 8601 UTC.                                           |
| `merge_commit_sha`      | string   | The resulting merge commit SHA (populated post-merge).  |

**Validation Rules:**

- All reference fields must resolve to existing artifacts.
- `run_id` must be unique across the repository history.
- The manifest must be committed to the `governance/manifests/` directory as part of the merge.
- Manifests are append-only. Modification of a committed manifest is a policy violation detectable by audit.

### 1.4 Artifact Dependency Chain

The following dependency chain must be satisfied:

```
Panel Emissions (all panels complete)
        |
        v
Policy Evaluation (consumes all emissions + JM Compliance status)
        |
        v
Run Manifest (produced from policy evaluation result)
        |
        v
Merge Decision (gated by all of the above)
```

No artifact may be produced out of order. The governance workflow enforces this sequencing.

---

## 2. Required Status Checks

### 2.1 Existing Status Checks (Enterprise-Locked)

The following status checks are produced by `jm-compliance.yml` and must remain as required status checks:

| Check Name                              | Trigger Condition               |
|-----------------------------------------|---------------------------------|
| `JM Compliance / OWASP Dependency Check`| Non-PR events                   |
| `JM Compliance / Dependency Review`     | Pull request events             |
| `JM Compliance / Code Scanning`         | All events (when code detected) |

These checks are owned by enterprise policy. This blueprint does not alter their configuration.

### 2.2 New Status Checks

A new workflow `.github/workflows/dark-factory-governance.yml` introduces the following status checks:

| Check Name                                          | Purpose                                           | Pass Criteria                                                                                  |
|-----------------------------------------------------|---------------------------------------------------|-----------------------------------------------------------------------------------------------|
| `Dark Factory / Panel Emissions Validation`         | Validates all panel structured JSON emissions.     | All emissions conform to schema. No missing required fields. Reasoning hashes match.          |
| `Dark Factory / Copilot Review Gate`                | Parses and evaluates Copilot review feedback.      | No unresolved critical/error findings. Confidence score meets profile threshold.              |
| `Dark Factory / Policy Evaluation`                  | Runs the policy engine and produces a decision.    | Policy engine returns a valid decision. No runtime errors.                                    |
| `Dark Factory / Merge Gate`                         | Final merge gating check based on policy decision. | Policy decision is `auto_merge`. All upstream checks passed. Run manifest is valid.           |

### 2.3 Check Ordering and Dependencies

```
jm-compliance.yml (enterprise)
    |
    +-- JM Compliance / Dependency Review --------+
    +-- JM Compliance / Code Scanning ------------+
                                                   |
dark-factory-governance.yml                        |
    |                                              |
    +-- Dark Factory / Panel Emissions Validation  |
    |       |                                      |
    +-- Dark Factory / Copilot Review Gate         |
    |       |                                      |
    +-------+--------------------------------------+
            |
            v
    Dark Factory / Policy Evaluation
            |
            v
    Dark Factory / Merge Gate
```

**Dependency Rules:**

1. `Panel Emissions Validation` may run as soon as all panel emissions are available. It does not depend on JM Compliance.
2. `Copilot Review Gate` may run as soon as Copilot review data is available. It does not depend on JM Compliance.
3. `Policy Evaluation` depends on:
   - `Panel Emissions Validation` (must pass).
   - `Copilot Review Gate` (must pass).
   - All `JM Compliance` checks (must pass or be skipped per their own conditional logic).
4. `Merge Gate` depends on `Policy Evaluation` and re-validates the run manifest.

### 2.4 Configuring as Required Status Checks

All four `Dark Factory` checks and the applicable `JM Compliance` checks must be configured as required status checks in the branch protection rules for every protected branch. See Section 5 for the branch protection rule template.

The checks must be configured with `strict: true` to require branches to be up to date before merging. This prevents a TOCTOU race between check execution and the merge event.

---

## 3. Copilot Gating Logic

### 3.1 Copilot as a Formal Review Panel

GitHub Copilot is designated as a formal review panel within the Dark Factory governance model. Its review feedback on pull requests is consumed programmatically, not treated as advisory.

The Copilot review panel definition resides at `governance/personas/panels/copilot-review.md`. The governance workflow parses Copilot's output and produces a structured emission conforming to the same `panel-output.schema.json` as all other panels.

### 3.2 Consuming Copilot Review Feedback

The governance workflow retrieves Copilot review data via the GitHub API:

1. **Pull Request Reviews:** Query `GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews` filtered to reviews authored by `github-actions[bot]` or the Copilot identity.
2. **Review Comments:** Query `GET /repos/{owner}/{repo}/pulls/{pull_number}/comments` for inline Copilot suggestions.
3. **Check Run Annotations:** Query Copilot-generated check run annotations if available.

All Copilot feedback is aggregated into a single structured document for parsing.

### 3.3 Parsing Copilot Suggestions into Severity Ratings

Each Copilot suggestion is classified into a severity tier using the following deterministic mapping:

| Copilot Signal                                                     | Mapped Severity | Weight |
|--------------------------------------------------------------------|-----------------|--------|
| Security vulnerability identified (injection, auth bypass, etc.)   | `critical`      | 1.0    |
| Bug or logic error identified                                      | `error`         | 0.8    |
| Performance concern or code smell                                  | `warning`       | 0.4    |
| Style, naming, or documentation suggestion                         | `info`          | 0.1    |

**Classification Rules:**

- Keyword matching against Copilot suggestion text is the primary classification method. The keyword sets are defined in `governance/policy/copilot-severity-keywords.yaml`.
- If a suggestion contains multiple severity-relevant keywords, the highest severity takes precedence.
- Suggestions that cannot be classified default to `warning` severity (fail-safe, not fail-open).

### 3.4 Pass/Fail Criteria for Copilot Review Gate

The Copilot Review Gate status check passes when ALL of the following conditions are met:

1. **No unresolved critical findings.** Any Copilot suggestion mapped to `critical` severity that has not been resolved (via commit or explicit dismissal with justification) constitutes a failure.
2. **No unresolved error findings exceeding the threshold.** The active policy profile defines `copilot_error_threshold` (default: 0). Unresolved `error` findings exceeding this threshold constitute a failure.
3. **Aggregate Copilot confidence meets the minimum.** The Copilot panel emission's `confidence_score` must meet or exceed the `copilot_min_confidence` value defined in the active policy profile (default: `0.7`).
4. **Copilot review is present.** If no Copilot review data is found, the gate fails. The absence of Copilot review is not treated as a pass.

### 3.5 Integration with Policy Engine Confidence Scoring

The Copilot panel emission's `confidence_score` is computed as:

```
copilot_confidence = 1.0 - sum(severity_weight[i] * count[i]) / max_possible_weight
```

Where `severity_weight[i]` is the weight from the severity mapping table and `count[i]` is the count of unresolved findings at that severity level. The `max_possible_weight` is a normalizing constant defined per policy profile (default: `10.0`), representing the point at which confidence reaches zero.

This confidence score feeds into the policy engine's aggregate confidence computation with the weight assigned to the Copilot panel in the active policy profile.

---

## 4. Policy Gating Logic

### 4.1 Policy Engine Evaluation as a Merge Gate

The policy engine evaluation is the authoritative source for the merge decision. The governance workflow invokes the policy engine after all panel emissions (including the Copilot panel) have been validated. The policy engine produces exactly one of four decisions.

### 4.2 Mapping Policy Decisions to GitHub Status Check States

| Policy Decision          | `Dark Factory / Merge Gate` State | GitHub Merge Behavior                     |
|--------------------------|-----------------------------------|-------------------------------------------|
| `auto_merge`             | `success`                         | Auto-merge proceeds if enabled.           |
| `auto_remediate`         | `pending`                         | Merge blocked. Remediation loop triggers. |
| `human_review_required`  | `pending`                         | Merge blocked. Human review requested.    |
| `block`                  | `failure`                         | Merge blocked. Override required.         |

**State Transition Rules:**

- A `pending` state prevents merge but does not constitute a permanent failure. The check remains pending until the condition is resolved (remediation completes or human approves).
- A `failure` state requires either resolution of the blocking condition or an enterprise override (Section 6).
- Only `success` permits merge to proceed.

### 4.3 Escalation Path for `human_review_required`

When the policy engine returns `human_review_required`:

1. **Notification.** The governance workflow posts a structured comment on the pull request identifying:
   - The specific panel emissions that triggered escalation.
   - The `escalation_reason` from the policy evaluation result.
   - The required reviewer role(s) as defined in the policy profile.

2. **Reviewer Assignment.** The workflow uses the GitHub API to request review from the team(s) or individual(s) specified in the policy profile's `escalation_reviewers` field. If no escalation reviewers are configured, the repository's `CODEOWNERS` are used.

3. **Human Approval Capture.** A human reviewer must submit an approving pull request review. The reviewer's identity and timestamp are recorded in the run manifest (`human_intervention: true`).

4. **Re-evaluation.** After human approval, the policy engine is re-invoked. If the human approval satisfies the escalation condition, the decision transitions to `auto_merge`. The `Merge Gate` status check updates to `success`.

5. **Timeout.** If no human review is received within the `escalation_timeout` period defined in the policy profile (default: 72 hours), the `Merge Gate` status check transitions to `failure`. The pull request must be re-submitted or an override applied.

### 4.4 Block Conditions

The policy engine returns `block` when any of the following conditions are met:

1. **JM Compliance failure.** Any required JM Compliance check has failed.
2. **Critical risk level.** The aggregate risk level across all panels is `critical`.
3. **Policy flag hard-block.** A panel emission contains a policy flag listed in the profile's `hard_block_flags` set (e.g., `pii_exposure`, `credential_leak`, `license_violation`).
4. **Confidence floor breach.** The `aggregate_confidence` falls below the profile's `block_confidence_floor` (default: `0.2`).
5. **Emission integrity failure.** Any panel emission fails `reasoning_hash` validation.
6. **Manifest validation failure.** The run manifest cannot be produced or fails schema validation.

### 4.5 Override Mechanisms

A `block` decision can only be overridden through the Enterprise Override Procedure defined in Section 6. No automated path exists to convert a `block` to `auto_merge`.

---

## 5. Auto-merge Configuration

### 5.1 GitHub Auto-merge Settings

GitHub's native auto-merge feature must be enabled at the repository level. Auto-merge is activated on a per-pull-request basis by the governance workflow when the policy decision is `auto_merge`.

**Repository Settings Required:**

- `Settings > General > Pull Requests > Allow auto-merge`: Enabled.
- `Settings > General > Pull Requests > Automatically delete head branches`: Enabled (recommended for hygiene).
- `Settings > General > Pull Requests > Allow squash merging`: Enabled. Squash merge is the required merge strategy for governance traceability (single commit per PR with manifest reference).

### 5.2 Conditions for Auto-merge Activation

Auto-merge is enabled on a pull request when ALL of the following are true:

1. All `JM Compliance` required status checks have passed (or been skipped per their own conditional logic).
2. All `Dark Factory` required status checks have passed.
3. The policy engine decision is `auto_merge`.
4. The run manifest has been produced, validated, and committed.
5. The required number of approving reviews has been met (see below).
6. No changes have been pushed to the pull request branch after the governance checks completed (enforced by `strict: true` in branch protection).

### 5.3 Required Approvals Configuration

The required number of approving pull request reviews is a function of the aggregate risk level:

| Aggregate Risk Level | Required Approvals | Approval Source                                         |
|----------------------|--------------------|---------------------------------------------------------|
| `low`               | 0                  | Auto-merge permitted with no human approval.            |
| `medium`            | 1                  | Any repository collaborator with write access.          |
| `high`              | 2                  | At least one from the `CODEOWNERS` for affected paths.  |
| `critical`          | N/A                | `block` decision. No auto-merge. Override required.     |

Note: GitHub branch protection enforces a single `required_approving_review_count`. This must be set to the minimum (`0` if the governance system is trusted to enforce dynamically, or `1` as a safety net). The governance workflow enforces the risk-adjusted approval count independently through the `Merge Gate` check.

### 5.4 Branch Protection Rule Template

The following configuration must be applied to all protected branches (at minimum: `main`, `v*.*`).

```yaml
# Branch Protection Rule Configuration
# Apply via GitHub API: PUT /repos/{owner}/{repo}/branches/{branch}/protection
# Or configure via repository Settings > Branches > Branch protection rules

branch_protection:
  branch_pattern: "main"

  required_status_checks:
    strict: true
    contexts:
      # Enterprise-locked checks (from jm-compliance.yml)
      - "JM Compliance / Dependency Review"
      - "JM Compliance / Code Scanning"
      # Dark Factory governance checks
      - "Dark Factory / Panel Emissions Validation"
      - "Dark Factory / Copilot Review Gate"
      - "Dark Factory / Policy Evaluation"
      - "Dark Factory / Merge Gate"

  required_pull_request_reviews:
    dismiss_stale_reviews: true
    require_code_owner_reviews: true
    required_approving_review_count: 1
    dismissal_restrictions:
      teams:
        - "governance-admins"

  enforce_admins: true

  restrictions:
    teams:
      - "governance-admins"
    apps:
      - "github-actions"

  required_linear_history: false
  allow_force_pushes: false
  allow_deletions: false
  required_conversation_resolution: true
  lock_branch: false
  allow_fork_syncing: false
```

**Equivalent GitHub API JSON payload:**

```json
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "JM Compliance / Dependency Review",
      "JM Compliance / Code Scanning",
      "Dark Factory / Panel Emissions Validation",
      "Dark Factory / Copilot Review Gate",
      "Dark Factory / Policy Evaluation",
      "Dark Factory / Merge Gate"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1,
    "dismissal_restrictions": {
      "teams": ["governance-admins"]
    }
  },
  "restrictions": {
    "users": [],
    "teams": ["governance-admins"],
    "apps": ["github-actions"]
  },
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
```

---

## 6. Enterprise Override Procedure

### 6.1 Purpose

The enterprise override procedure exists for situations where a `block` decision or a timed-out `human_review_required` decision must be bypassed due to operational necessity (e.g., critical production incident remediation, time-sensitive regulatory compliance change). Overrides are exceptional events, not routine workflow.

### 6.2 Override Initiation

An override may be initiated by any member of the `governance-admins` team by applying the label `governance-override-requested` to the blocked pull request.

Upon label application, the governance workflow:

1. Posts a structured comment documenting the override request, including the current `block` reason and all panel emissions.
2. Requests review from the `governance-admins` team.
3. Sets the `Merge Gate` status check to `pending` with description: `Override requested. Awaiting 2+ senior engineer approvals.`

### 6.3 Required Approvals for Override

An override requires approving pull request reviews from at least **two (2)** members of the `governance-admins` team. These approvals must:

- Be submitted after the `governance-override-requested` label was applied.
- Include a review body containing the text `OVERRIDE APPROVED:` followed by a justification statement of at least 50 characters.
- Come from distinct GitHub users (a single user cannot provide both approvals).
- Not come from the author of the pull request.

### 6.4 Override Execution

Once two valid override approvals are received:

1. The governance workflow creates an **override record** containing:
   - Override request timestamp.
   - Requesting user identity.
   - Approving user identities.
   - Justification statements.
   - Original block reason.
   - All panel emission references.
   - Policy evaluation result at time of override.

2. The override record is committed to `governance/manifests/overrides/` as a JSON file named `override-{run_id}.json`.

3. The `Merge Gate` status check transitions to `success` with description: `Override approved. See override record.`

4. The run manifest is produced with `override_applied: true` and `human_intervention: true`.

5. Auto-merge proceeds (or the PR may be merged manually).

### 6.5 Audit Logging for Overrides

Override events are logged at multiple levels:

| Log Target                           | Content                                                    | Retention       |
|--------------------------------------|------------------------------------------------------------|-----------------|
| `governance/manifests/overrides/`               | Full override record (JSON).                               | Permanent (git).|
| Run manifest                         | `override_applied: true` flag.                             | Permanent (git).|
| GitHub Actions workflow run log      | Timestamped override approval events.                      | Per GH retention.|
| Pull request timeline                | Structured comments documenting override lifecycle.        | Permanent (GH). |
| Repository audit log (Enterprise)    | Branch protection bypass events (GitHub native).           | Per enterprise.  |

All override records are immutable once committed. Modification of an override record is a policy violation.

### 6.6 Post-Override Review Requirements

Within **5 business days** of an override merge:

1. A retrospective issue must be filed (automatically by the governance workflow) titled: `[Governance Override Retrospective] PR #{number} - {title}`.
2. The issue must be assigned to the `governance-admins` team.
3. The issue body must include:
   - Link to the pull request.
   - Link to the override record.
   - Full panel emissions summary.
   - Original block reason.
   - Override justification.
4. The issue must be closed with a retrospective comment documenting:
   - Whether the override was justified.
   - Whether the block condition represented a true positive or a false positive.
   - Any policy profile adjustments recommended.
   - Any panel or keyword set updates recommended.

Failure to close the retrospective issue within 10 business days triggers an automated escalation to the repository administrator.

### 6.7 Override Expiration and Cooldown

**Expiration:**

- An override approval is valid for **4 hours** from the time the second approval is received. If the pull request is not merged within this window, the override expires.
- Upon expiration, the `Merge Gate` status check reverts to `failure`. A new override request must be initiated.
- The expired override is logged in the override record with `expired: true`.

**Cooldown:**

- After an override is used for a given pull request, a cooldown period of **24 hours** applies before another override can be requested for the same pull request.
- During cooldown, the `governance-override-requested` label is automatically removed if re-applied.
- This cooldown prevents override cycling where repeated override attempts substitute for proper remediation.

**Rate Limiting:**

- A maximum of **3 overrides per protected branch per rolling 30-day period** is enforced. Exceeding this limit requires repository administrator intervention to reset the counter.
- The override count is tracked in `governance/manifests/overrides/override-counter.json` and updated atomically on each override.

---

## 7. Sample Governance Workflow

The following is the complete GitHub Actions workflow to be placed at `.github/workflows/dark-factory-governance.yml`. It runs alongside the enterprise-locked `jm-compliance.yml` without modifying it.

```yaml
name: "Dark Factory Governance"

on:
  pull_request:
    branches:
      - main
      - "v*.*"
  workflow_dispatch:
    inputs:
      override_mode:
        description: "Run in override validation mode"
        required: false
        default: "false"
        type: choice
        options:
          - "true"
          - "false"

permissions:
  actions: read
  checks: write
  contents: write
  issues: write
  pull-requests: write
  statuses: write
  security-events: read

concurrency:
  group: governance-${{ github.head_ref || github.ref }}
  cancel-in-progress: true

env:
  GOVERNANCE_VERSION: "1.0.0"
  MANIFESTS_DIR: "manifests"
  OVERRIDES_DIR: "manifests/overrides"
  SCHEMAS_DIR: "schemas"
  POLICY_DIR: "policy"

jobs:
  # -----------------------------------------------------------
  # Job 1: Validate all panel structured emissions
  # -----------------------------------------------------------
  panel-emissions-validation:
    name: "Dark Factory / Panel Emissions Validation"
    runs-on: ubuntu-latest
    outputs:
      emissions_valid: ${{ steps.validate.outputs.emissions_valid }}
      emissions_artifact: ${{ steps.validate.outputs.emissions_artifact }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install validation dependencies
        run: npm ci --prefix governance/bin/tools

      - name: Collect panel emissions
        id: collect
        run: |
          node governance/bin/tools/collect-emissions.js \
            --pr-number "${{ github.event.pull_request.number }}" \
            --output emissions.json

      - name: Validate emissions against schema
        id: validate
        run: |
          node governance/bin/tools/validate-emissions.js \
            --emissions emissions.json \
            --schema "${{ env.SCHEMAS_DIR }}/panel-output.schema.json" \
            --output validation-result.json

          VALID=$(jq -r '.all_valid' validation-result.json)
          echo "emissions_valid=${VALID}" >> "$GITHUB_OUTPUT"
          echo "emissions_artifact=emissions.json" >> "$GITHUB_OUTPUT"

          if [ "$VALID" != "true" ]; then
            echo "::error::Panel emissions validation failed. See validation-result.json for details."
            jq '.errors[]' validation-result.json
            exit 1
          fi

      - name: Upload emissions artifact
        uses: actions/upload-artifact@v4
        with:
          name: panel-emissions
          path: |
            emissions.json
            validation-result.json
          retention-days: 90

  # -----------------------------------------------------------
  # Job 2: Copilot review gate
  # -----------------------------------------------------------
  copilot-review-gate:
    name: "Dark Factory / Copilot Review Gate"
    runs-on: ubuntu-latest
    outputs:
      copilot_pass: ${{ steps.evaluate.outputs.copilot_pass }}
      copilot_confidence: ${{ steps.evaluate.outputs.copilot_confidence }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install dependencies
        run: npm ci --prefix governance/bin/tools

      - name: Fetch Copilot review data
        id: fetch
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          node governance/bin/tools/fetch-copilot-review.js \
            --repo "${{ github.repository }}" \
            --pr-number "${{ github.event.pull_request.number }}" \
            --output copilot-review.json

      - name: Parse and classify Copilot suggestions
        id: classify
        run: |
          node governance/bin/tools/classify-copilot.js \
            --review copilot-review.json \
            --keywords "${{ env.POLICY_DIR }}/copilot-severity-keywords.yaml" \
            --output copilot-classified.json

      - name: Evaluate Copilot gate
        id: evaluate
        run: |
          node governance/bin/tools/evaluate-copilot-gate.js \
            --classified copilot-classified.json \
            --policy-profile "${{ env.POLICY_DIR }}/default.yaml" \
            --schema "${{ env.SCHEMAS_DIR }}/panel-output.schema.json" \
            --output copilot-emission.json

          PASS=$(jq -r '.gate_passed' copilot-emission.json)
          CONFIDENCE=$(jq -r '.confidence_score' copilot-emission.json)
          echo "copilot_pass=${PASS}" >> "$GITHUB_OUTPUT"
          echo "copilot_confidence=${CONFIDENCE}" >> "$GITHUB_OUTPUT"

          if [ "$PASS" != "true" ]; then
            echo "::error::Copilot review gate failed. See copilot-emission.json for details."
            exit 1
          fi

      - name: Upload Copilot emission artifact
        uses: actions/upload-artifact@v4
        with:
          name: copilot-emission
          path: |
            copilot-review.json
            copilot-classified.json
            copilot-emission.json
          retention-days: 90

  # -----------------------------------------------------------
  # Job 3: Policy evaluation
  # -----------------------------------------------------------
  policy-evaluation:
    name: "Dark Factory / Policy Evaluation"
    runs-on: ubuntu-latest
    needs:
      - panel-emissions-validation
      - copilot-review-gate
    if: |
      always() &&
      needs.panel-emissions-validation.result == 'success' &&
      needs.copilot-review-gate.result == 'success'
    outputs:
      policy_decision: ${{ steps.evaluate.outputs.policy_decision }}
      aggregate_confidence: ${{ steps.evaluate.outputs.aggregate_confidence }}
      aggregate_risk: ${{ steps.evaluate.outputs.aggregate_risk }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install dependencies
        run: npm ci --prefix governance/bin/tools

      - name: Download panel emissions
        uses: actions/download-artifact@v4
        with:
          name: panel-emissions

      - name: Download Copilot emission
        uses: actions/download-artifact@v4
        with:
          name: copilot-emission

      - name: Query JM Compliance status
        id: jm-status
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          node governance/bin/tools/query-jm-compliance.js \
            --repo "${{ github.repository }}" \
            --sha "${{ github.event.pull_request.head.sha }}" \
            --output jm-status.json

      - name: Run policy engine
        id: evaluate
        run: |
          node governance/bin/tools/policy-engine.js \
            --emissions emissions.json \
            --copilot-emission copilot-emission.json \
            --jm-status jm-status.json \
            --profile "${{ env.POLICY_DIR }}/default.yaml" \
            --output policy-result.json

          DECISION=$(jq -r '.decision' policy-result.json)
          AGG_CONF=$(jq -r '.aggregate_confidence' policy-result.json)
          AGG_RISK=$(jq -r '.aggregate_risk' policy-result.json)

          echo "policy_decision=${DECISION}" >> "$GITHUB_OUTPUT"
          echo "aggregate_confidence=${AGG_CONF}" >> "$GITHUB_OUTPUT"
          echo "aggregate_risk=${AGG_RISK}" >> "$GITHUB_OUTPUT"

      - name: Upload policy result artifact
        uses: actions/upload-artifact@v4
        with:
          name: policy-result
          path: |
            policy-result.json
            jm-status.json
          retention-days: 90

  # -----------------------------------------------------------
  # Job 4: Merge gate (final decision)
  # -----------------------------------------------------------
  merge-gate:
    name: "Dark Factory / Merge Gate"
    runs-on: ubuntu-latest
    needs:
      - panel-emissions-validation
      - copilot-review-gate
      - policy-evaluation
    if: always()
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install dependencies
        run: npm ci --prefix governance/bin/tools

      - name: Download all governance artifacts
        uses: actions/download-artifact@v4

      - name: Check for override approval
        id: override-check
        if: contains(github.event.pull_request.labels.*.name, 'governance-override-requested')
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          node governance/bin/tools/check-override.js \
            --repo "${{ github.repository }}" \
            --pr-number "${{ github.event.pull_request.number }}" \
            --required-approvals 2 \
            --team "governance-admins" \
            --expiry-hours 4 \
            --output override-result.json

          OVERRIDE_VALID=$(jq -r '.override_valid' override-result.json)
          echo "override_valid=${OVERRIDE_VALID}" >> "$GITHUB_OUTPUT"

      - name: Evaluate merge gate
        id: gate
        env:
          POLICY_DECISION: ${{ needs.policy-evaluation.outputs.policy_decision }}
          PANEL_VALID: ${{ needs.panel-emissions-validation.outputs.emissions_valid }}
          COPILOT_PASS: ${{ needs.copilot-review-gate.outputs.copilot_pass }}
          OVERRIDE_VALID: ${{ steps.override-check.outputs.override_valid || 'false' }}
          UPSTREAM_POLICY: ${{ needs.policy-evaluation.result }}
        run: |
          # Determine final merge decision
          if [ "$UPSTREAM_POLICY" != "success" ]; then
            echo "::error::Upstream governance checks did not succeed."
            echo "gate_result=failure" >> "$GITHUB_OUTPUT"
            exit 1
          fi

          if [ "$POLICY_DECISION" = "auto_merge" ]; then
            echo "gate_result=success" >> "$GITHUB_OUTPUT"
            echo "Policy decision: auto_merge. Merge gate passed."
          elif [ "$POLICY_DECISION" = "block" ] && [ "$OVERRIDE_VALID" = "true" ]; then
            echo "gate_result=success" >> "$GITHUB_OUTPUT"
            echo "::warning::Policy decision was BLOCK but valid override approved. Merge gate passed with override."
          elif [ "$POLICY_DECISION" = "human_review_required" ]; then
            echo "::warning::Policy decision: human_review_required. Awaiting human approval."
            echo "gate_result=pending" >> "$GITHUB_OUTPUT"
            exit 1
          elif [ "$POLICY_DECISION" = "auto_remediate" ]; then
            echo "::warning::Policy decision: auto_remediate. Triggering remediation loop."
            echo "gate_result=pending" >> "$GITHUB_OUTPUT"
            exit 1
          else
            echo "::error::Policy decision: ${POLICY_DECISION}. Merge blocked."
            echo "gate_result=failure" >> "$GITHUB_OUTPUT"
            exit 1
          fi

      - name: Generate run manifest
        if: steps.gate.outputs.gate_result == 'success'
        run: |
          node governance/bin/tools/generate-manifest.js \
            --emissions panel-emissions/emissions.json \
            --copilot-emission copilot-emission/copilot-emission.json \
            --policy-result policy-result/policy-result.json \
            --override-result override-result.json \
            --pr-number "${{ github.event.pull_request.number }}" \
            --sha "${{ github.event.pull_request.head.sha }}" \
            --schema "${{ env.SCHEMAS_DIR }}/run-manifest.schema.json" \
            --output-dir "${{ env.MANIFESTS_DIR }}"

      - name: Commit run manifest
        if: steps.gate.outputs.gate_result == 'success'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          git config user.name "dark-factory-governance[bot]"
          git config user.email "dark-factory-governance[bot]@users.noreply.github.com"
          git add "${{ env.MANIFESTS_DIR }}/"
          git commit -m "chore(governance): add run manifest for PR #${{ github.event.pull_request.number }} [skip ci]"
          git push

      - name: Post escalation comment (human_review_required)
        if: |
          needs.policy-evaluation.outputs.policy_decision == 'human_review_required' &&
          steps.override-check.outputs.override_valid != 'true'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          node governance/bin/tools/post-escalation.js \
            --repo "${{ github.repository }}" \
            --pr-number "${{ github.event.pull_request.number }}" \
            --policy-result policy-result/policy-result.json \
            --emissions panel-emissions/emissions.json

      - name: File override retrospective issue
        if: steps.override-check.outputs.override_valid == 'true'
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          node governance/bin/tools/file-override-retrospective.js \
            --repo "${{ github.repository }}" \
            --pr-number "${{ github.event.pull_request.number }}" \
            --override-result override-result.json \
            --policy-result policy-result/policy-result.json
```

---

## 8. Implementation Checklist

The following items must be completed to operationalize this blueprint:

### 8.1 Repository Structure Additions

```
.github/
  workflows/
    jm-compliance.yml           # LOCKED -- do not modify
    dark-factory-governance.yml # NEW -- governance workflow
governance/bin/
  tools/
    package.json                # Dependencies for governance tooling
    collect-emissions.js        # Collects panel emissions from PR artifacts
    validate-emissions.js       # Validates emissions against schema
    fetch-copilot-review.js     # Fetches Copilot review data via GitHub API
    classify-copilot.js         # Classifies Copilot suggestions by severity
    evaluate-copilot-gate.js    # Evaluates Copilot gate pass/fail
    query-jm-compliance.js      # Queries JM Compliance check status
    policy-engine.js            # Core policy engine
    generate-manifest.js        # Generates run manifest
    check-override.js           # Validates override approvals
    post-escalation.js          # Posts escalation comment to PR
    file-override-retrospective.js # Files retrospective issue
schemas/
  panel-output.schema.json     # Panel emission schema
  run-manifest.schema.json     # Run manifest schema
  policy-result.schema.json    # Policy evaluation result schema
  override-record.schema.json  # Override record schema
policy/
  default.yaml                 # Default policy profile
  copilot-severity-keywords.yaml # Copilot severity classification keywords
manifests/                     # Run manifests (append-only)
  overrides/                   # Override records
    override-counter.json      # Override rate limit counter
personas/panels/
  copilot-review.md            # Copilot review panel definition
```

### 8.2 Branch Protection Configuration

1. Apply the branch protection rule template from Section 5.4 to `main` and all `v*.*` branches.
2. Create the `governance-admins` team with appropriate membership.
3. Verify that all six required status checks appear in the branch protection configuration after the first workflow run.

### 8.3 Operational Readiness

1. All schemas must be committed and validated before the governance workflow is activated.
2. The governance tooling (`/governance/bin/tools/`) must have passing unit tests with at least 90% line coverage.
3. A dry-run mode must be available via `workflow_dispatch` to test the governance pipeline without gating merges.
4. The `jm-compliance.yml` workflow must continue to function identically after the governance workflow is added. Verify by running both workflows on a test PR and comparing JM Compliance results against a baseline.

---

## 9. Failure Modes and Recovery

| Failure Mode                                      | Detection                                    | Recovery                                                         |
|---------------------------------------------------|----------------------------------------------|------------------------------------------------------------------|
| Panel emission missing for a registered panel     | `Panel Emissions Validation` check fails     | Re-run panel execution. Investigate panel failure logs.          |
| Copilot review data unavailable (API timeout)     | `Copilot Review Gate` check fails            | Retry workflow. If persistent, file GitHub Support ticket.       |
| JM Compliance check stuck in pending              | `Policy Evaluation` job does not start       | Manually re-run `jm-compliance.yml`. Investigate enterprise runner availability. |
| Policy engine runtime error                       | `Policy Evaluation` check fails              | Review policy engine logs. Fix and re-run.                       |
| Manifest commit fails (merge conflict)            | `Merge Gate` check fails at commit step      | Rebase PR branch and re-run governance workflow.                 |
| Override approvals do not arrive within 4 hours   | Override expires, `Merge Gate` remains failed | Initiate new override request after 24-hour cooldown.            |
| Override rate limit exceeded (3/30 days)           | Override request rejected by workflow         | Repository administrator must reset counter. Investigate root cause of frequent blocks. |
| Governance workflow and JM Compliance race condition | Both modify PR status simultaneously        | No conflict: workflows write independent status checks. No mitigation required. |

---

## 10. Audit and Compliance Traceability

Every merge into a protected branch produces the following audit trail:

1. **Panel emissions** -- stored as GitHub Actions artifacts with 90-day retention.
2. **Policy evaluation result** -- stored as GitHub Actions artifact with 90-day retention.
3. **Run manifest** -- committed to `governance/manifests/` in the repository (permanent).
4. **Override records** (if applicable) -- committed to `governance/manifests/overrides/` (permanent).
5. **GitHub pull request timeline** -- structured comments from the governance workflow (permanent on GitHub).
6. **GitHub Actions workflow run logs** -- retained per GitHub/enterprise retention policy.

For regulatory audit purposes, the run manifest serves as the single source of truth. It contains references to all upstream artifacts, enabling full reconstruction of the decision chain for any historical merge.

To replay a governance decision:

1. Retrieve the run manifest from `governance/manifests/`.
2. Retrieve the referenced panel emissions and policy result from GitHub Actions artifacts (or from cached copies if retention has expired).
3. Re-execute the policy engine with the same inputs and policy profile version.
4. Verify that the output decision matches the recorded decision.

Determinism guarantee: given identical inputs and the same policy profile version, the policy engine must produce an identical decision. This property must be verified by the governance tooling test suite.

---

*End of document.*
