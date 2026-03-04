# Cross-Repo Issue Escalation Workflow

This workflow enables consuming repositories to detect framework-level issues in the `.ai` governance submodule and escalate them to the upstream [Dark Forge](https://github.com/convergent-systems-co/dark-forge) repository. It runs as part of the agentic loop when a framework-level issue is encountered.

## Prerequisites

- Consuming repo has `escalation.enabled: true` in `project.yaml`
- A GitHub token with `repo` scope on the target repository is available (see Authentication section)
- The `.ai` submodule is present and initialized

## Detection Criteria

### Framework-Level Signals (Escalate)

An issue is **framework-level** if ANY of these criteria match:

1. **Path-based** — The issue involves files under `.ai/governance/` (schemas, policies, personas, panels, prompts). This includes:
   - Schema validation errors against governance schemas
   - Policy evaluation errors in governance YAML files
   - Panel definition issues (missing fields, invalid format)
   - Prompt references to non-existent files

2. **Workflow failure** — The `dark-factory-governance.yml` workflow fails with errors originating in governance framework code (not project code). Indicators:
   - Error traces pointing to `.ai/` paths
   - Policy engine (`governance/policy-engine.py`) errors
   - Schema validation failures in the governance workflow steps

3. **Policy gap** — The agent encounters a scenario not covered by any policy rule:
   - A risk level or condition falls through all policy rules without matching
   - The policy engine produces an `UNKNOWN` or `NO_MATCH` result
   - A new finding category has no severity mapping

4. **Schema validation** — A panel emission or run manifest fails validation against a governance schema:
   - `panel-output.schema.json` validation failure on a required field
   - `run-manifest.schema.json` missing required sections
   - Any governance schema rejects a valid-looking artifact

5. **Init failure** — `init.sh` (or `init.ps1`) fails during bootstrap:
   - Symlink creation fails due to missing source files
   - Workflow copy fails due to missing governance workflows
   - Submodule state is inconsistent

### Project-Local Signals (Do NOT Escalate)

- Issue involves only project source code (not `.ai/` paths)
- CI failure in project-specific tests or linting
- Copilot recommendations on project code
- Missing project-level configuration (not governance config)
- Dependency or build failures unrelated to governance

## Escalation Flow

### Step 1: Detect

During normal agentic operation (startup loop, PR monitoring, governance evaluation), the agent encounters an error or anomaly. Before proceeding, check if the issue matches any framework-level detection criteria above.

```
IF error_path starts with ".ai/governance/" → path_based
IF governance_workflow_failed AND error_in_framework_code → workflow_failure
IF policy_engine_result == "NO_MATCH" → policy_gap
IF schema_validation_failed ON governance_schema → schema_validation
IF init_script_failed → init_failure
ELSE → project-local (do not escalate)
```

### Step 2: Classify Severity

| Detection Type | Default Severity | Override Condition |
|---------------|-----------------|-------------------|
| workflow_failure | high | critical if governance cannot produce any merge decision |
| schema_validation | high | critical if core schema (panel-output, run-manifest) |
| policy_gap | medium | high if gap is in security or compliance rules |
| path_based | medium | high if persona/panel definition is broken |
| init_failure | low | medium if consuming repo cannot bootstrap at all |

### Step 3: Check Rate Limit

Before escalating, verify the session has not exceeded the escalation rate limit (default: 3 per session, configurable via `escalation.rate_limit` in `project.yaml`).

```bash
# Count escalations in current session (tracked in session state)
if [ "$SESSION_ESCALATION_COUNT" -ge "$RATE_LIMIT" ]; then
  echo "Rate limit reached. Logging locally but not escalating."
  # Record with status: "skipped"
  exit 0
fi
```

If rate-limited, record the escalation locally with `status: "skipped"` and continue the agentic loop.

### Step 4: Compute Dedup Key

Generate a deterministic dedup key from the detection criteria:

```bash
DEDUP_KEY=$(echo -n "${CRITERIA_TYPE}:${CRITERIA_DETAIL}" | sha256sum | cut -c1-16)
```

The dedup key ensures that the same framework issue detected by multiple consuming repos (or across multiple sessions) creates only one upstream issue.

### Step 5: Check for Duplicates

Search the target repository for an existing open issue with the same dedup key:

```bash
EXISTING=$(gh search issues \
  --repo "${TARGET_REPOSITORY}" \
  "dedup:${DEDUP_KEY}" \
  --state open \
  --json number,title \
  --limit 1)
```

The dedup key is embedded in the upstream issue body as an HTML comment: `<!-- dedup:{key} -->`. GitHub search indexes issue body text including HTML comments.

- **If duplicate found:** Record with `status: "duplicate"` and `upstream_issue_number` set to the existing issue. Comment on the existing upstream issue noting the additional consuming repo that encountered the same issue.
- **If no duplicate:** Proceed to Step 6.

### Step 6: Create Upstream Issue

```bash
gh issue create \
  --repo "${TARGET_REPOSITORY}" \
  --title "escalation(${SOURCE_REPO_SHORT}): ${SUMMARY}" \
  --label "escalation" \
  --body "$(cat <<'EOF'
## Escalated from ${SOURCE_REPOSITORY}

**Source issue:** ${SOURCE_REPOSITORY}#${SOURCE_ISSUE_NUMBER}
**Detection type:** ${CRITERIA_TYPE}
**Severity:** ${SEVERITY}

<!-- dedup:${DEDUP_KEY} -->

## Description

${DESCRIPTION}

## Detection Detail

${CRITERIA_DETAIL}

## Error Output

```
${ERROR_OUTPUT}
```

## Affected Files

${AFFECTED_FILES}

---

*This issue was automatically escalated by the Dark Forge governance agent in ${SOURCE_REPOSITORY}.*
EOF
)"
```

Capture the created issue number from the command output.

### Step 7: Link Back to Source

Comment on the source issue (in the consuming repo) referencing the upstream escalation:

```bash
gh issue comment ${SOURCE_ISSUE_NUMBER} \
  --body "Escalated to upstream: ${TARGET_REPOSITORY}#${UPSTREAM_ISSUE_NUMBER}

This appears to be a framework-level issue in the governance submodule. Tracking resolution upstream."
```

### Step 8: Record Escalation

Write an escalation record conforming to `governance/schemas/cross-repo-escalation.schema.json`:

```json
{
  "escalation_id": "esc-${SHORT_HASH}",
  "source_repository": "${SOURCE_REPOSITORY}",
  "source_issue_number": ${SOURCE_ISSUE_NUMBER},
  "target_repository": "${TARGET_REPOSITORY}",
  "detection_criteria": {
    "type": "${CRITERIA_TYPE}",
    "detail": "${CRITERIA_DETAIL}",
    "affected_files": ["${FILE1}", "${FILE2}"],
    "error_output": "${ERROR_OUTPUT}"
  },
  "dedup_key": "${DEDUP_KEY}",
  "severity": "${SEVERITY}",
  "description": "${DESCRIPTION}",
  "upstream_issue_number": ${UPSTREAM_ISSUE_NUMBER},
  "status": "escalated",
  "timestamp": "${ISO_TIMESTAMP}"
}
```

Save to `.artifacts/emissions/escalation-${ESCALATION_ID}.json` in the consuming repo (not committed — ephemeral session artifact).

## Authentication

The escalation workflow requires a GitHub token with permission to create issues on the target repository. Three approaches are supported:

### Option 1: GITHUB_TOKEN with Cross-Repo Scope (Recommended for GitHub Actions)

If the consuming repo's GitHub Actions workflow uses a `GITHUB_TOKEN` with `issues: write` permission and the target repo is in the same organization, no additional configuration is needed. The default `GITHUB_TOKEN` in GitHub Actions has organization-level visibility.

### Option 2: Fine-Grained Personal Access Token (PAT)

Create a fine-grained PAT with:
- **Repository access:** `convergent-systems-co/dark-forge` (or the configured target)
- **Permissions:** `Issues: Read and write`

Store as a repository secret (e.g., `ESCALATION_TOKEN`) and configure in `project.yaml`:

```yaml
escalation:
  enabled: true
  auth_method: PAT
  token_secret: ESCALATION_TOKEN
```

### Option 3: GitHub App

For organizations with stricter token policies, install a GitHub App with `Issues: Read & write` permission on both the source and target repositories. Configure the App ID and private key as secrets.

```yaml
escalation:
  enabled: true
  auth_method: GITHUB_APP
  app_id_secret: ESCALATION_APP_ID
  private_key_secret: ESCALATION_APP_KEY
```

## Configuration Reference

All configuration lives in the consuming repo's `project.yaml`:

```yaml
escalation:
  enabled: false                          # Must be explicitly enabled
  target_repository: "convergent-systems-co/dark-forge"  # Default upstream target
  auth_method: "GITHUB_TOKEN"             # GITHUB_TOKEN | PAT | GITHUB_APP
  token_secret: "ESCALATION_TOKEN"        # Secret name for PAT auth
  rate_limit: 3                           # Max escalations per agentic session
  criteria:                               # Which detection criteria to activate
    path_based: true
    workflow_failure: true
    policy_gap: true
    schema_validation: true
    init_failure: true
```

## Integration with Startup Loop

This workflow integrates into `startup.md` at failure points — it is not a separate loop. When the agentic startup sequence encounters a framework-level error:

1. The agent calls the detection criteria check
2. If a match is found, the escalation flow runs inline (Steps 1-8)
3. The agent then continues normal operation (the escalation does not block the agentic loop)
4. Escalation failures are non-blocking — if the upstream issue cannot be created (auth failure, network error), log locally and continue

## Relationship to Other Components

- **Governance compliance monitoring (#176)** — Compliance tracking may surface governance step failures that trigger escalation
- **Agentic Monitor (#42)** — A future always-on monitor could trigger escalation automatically on detected framework issues
- **Policy engine** — Policy gap detection feeds directly into the escalation criteria
