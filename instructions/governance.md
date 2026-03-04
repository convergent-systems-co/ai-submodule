# Governance Instructions

<!-- PHASE:governance -->

Loaded for governance pipeline tasks — panel coordination, policy evaluation, manifest generation.

## Pipeline Enforcement — All Modes

The governance pipeline is mandatory in every operating mode. The workflow is identical; only the transport layer differs.

### Required Default Panels

These panels must execute on every change (defined in `governance/policy/default.yaml`):

1. **code-review** — Code quality, logic, patterns
2. **security-review** — Security vulnerabilities, auth, injection
3. **threat-modeling** — MITRE ATT&CK mapping, attack surface
4. **cost-analysis** — Resource usage, budget impact
5. **documentation-review** — Docs completeness, accuracy
6. **data-governance-review** — Canonical model compliance, naming conventions, data standards from [dach-canonical-models](https://github.com/SET-Apps/dach-canonical-models)

If any required panel is missing from `governance/emissions/`, the change is **not governance-approved**. The CI workflow will block the PR. In local mode, the agent must not proceed past the review step without panel emissions.

### Local-Mode Enforcement

When no GitHub remote is available (local-only development):

- **Plan-first is still mandatory** — Write a plan to `.governance/plans/` (consuming repos) or `governance/plans/` (Dark Forge repo) before any implementation.
- **Panel evaluation still applies** — Run the policy engine locally:
  ```bash
  python governance/bin/policy-engine.py \
    --emissions-dir governance/emissions/ \
    --profile governance/policy/default.yaml \
    --output manifest.json
  ```
- **Commit conventions still apply** — Conventional commits, isolated changes, documentation updates.
- **Skip only GitHub-specific steps** — Issue creation, PR creation, Copilot polling, issue comments. All other governance steps execute identically.

### Panel Validation

Before any merge decision, validate that required panels have emissions:

1. Check `governance/emissions/` for JSON files matching required panel names
2. If any required panel is missing:
   - **In CI:** The workflow posts a request-changes review and fails the check
   - **In local mode:** The agent must not commit to main without panel coverage
   - **Remediation:** Run the missing panel(s) or set `governance.skip_panel_validation: true` in `project.yaml` if the project intentionally opts out
3. The `missing_panel_behavior: redistribute` policy allows auto-merge when missing panels are non-required, but required panels cannot be redistributed

### Evaluating Additional Panels

When configuring governance for a project (during `init.sh` or `project.yaml` setup), evaluate which additional panels beyond the defaults should run:

- **architecture-review** — If the project has `src/`, `lib/`, or modifies `.github/workflows/`
- **testing-review** — If the project has test files
- **performance-review** — If the project has benchmarks or performance-sensitive code
- **data-design-review** — If the project has database schemas or migrations
- **ai-expert-review** — If the project modifies governance personas or prompts

These conditional panels are defined in `governance/policy/default.yaml` under `weighting.weights`.

## Structured Emissions

- All panel output must include JSON between `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers
- Validate emissions against `governance/schemas/panel-output.schema.json`
- Missing markers or invalid JSON means panel execution failed

## Policy

- Policy profiles are evaluated programmatically — never interpret policy rules as prose
- Use the active profile from `project.yaml` governance configuration
- Escalate to human review when confidence is below profile thresholds

## Manifests

- Run manifests are immutable — never edit after creation
- Every merge decision must produce a manifest conforming to `governance/schemas/run-manifest.schema.json`
- Record the persona set commit, policy profile, and all panel emissions
