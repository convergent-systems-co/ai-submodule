Display a governance pipeline dashboard. Argument routing based on user input after the command:

## Argument Parsing

Parse the user's argument to determine the mode:

| Input | Mode | Action |
|-------|------|--------|
| `status` | Pipeline status | Shows governance state: policy profile, required vs present panels, compliance gaps |
| `policy` | Policy details | Shows active policy profile requirements, thresholds, scoring |
| `emissions` | List emissions | Lists all emissions in `.governance/panels/` with verdicts and scores |
| *(empty / no args)* | Pipeline status | Default: same as `status` |

## Execution Steps

### Mode: `status`

1. Read `project.yaml` (project root) to determine `governance.policy_profile`. If not set, default to `default`.
2. Read the active policy profile from `.ai/governance/policy/{profile}.yaml` to get the `required_panels` list.
3. Scan `.governance/panels/` for existing emission files (`*.json`).
4. For each JSON file found, parse the structured emission JSON (either direct JSON or between `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers) and extract `panel_name`.
5. Compare `required_panels` from the policy against present panel emissions.
6. Display a dashboard table:
   - **Profile**: active policy profile name and version
   - **Required Panels**: table with columns: Panel | Status (present/missing) | Confidence | Risk Level | Verdict
   - **Compliance Summary**: count of present vs required panels, aggregate compliance state (all present = compliant, any missing = gaps detected)

### Mode: `policy`

1. Read `project.yaml` (project root) to determine `governance.policy_profile`. If not set, default to `default`.
2. Read the active policy YAML file from `.ai/governance/policy/{profile}.yaml`.
3. Display the following sections:
   - **Profile Identity**: `profile_name`, `profile_version`, `description`
   - **Required Panels**: list of `required_panels`
   - **Confidence Weighting**: `weighting.model` and per-panel weights table (Panel | Weight)
   - **Risk Aggregation**: `risk_aggregation.model` and rules summary
   - **Auto-Merge Conditions**: `auto_merge.enabled` status and list of conditions
   - **Escalation Rules**: table of escalation rules (Name | Condition | Action)
   - **Block Rules**: list of hard-block conditions
   - **Override Requirements**: `override.requirements` (min approvals, required roles)

### Mode: `emissions`

1. Scan `.governance/panels/` for all `*.json` files.
2. For each file, parse the structured emission JSON (either direct JSON or between `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers).
3. Extract from each emission: `panel_name`, `panel_version`, `confidence_score`, `risk_level`, `compliance_score`, `requires_human_review`, `aggregate_verdict`, and count of `findings`.
4. Display a summary table: Panel | Version | Confidence | Risk Level | Compliance | Findings | Verdict | Human Review
5. Highlight any panels with `risk_level` of `critical` or `high`, or `confidence_score` below the policy threshold.
6. If no emission files are found, report that no panel emissions exist yet.

## Output

After completing the analysis:
1. Display the dashboard output in the conversation.
2. This is a read-only command — no files are written or modified.
