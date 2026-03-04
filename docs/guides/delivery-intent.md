# Delivery Intent & Environment Verification

## What is a Delivery Intent?

A delivery intent is an immutable JSON manifest that records what files were delivered by a governance change, what configuration was modified, and what state a consumer repository should be in after the change is applied. It serves as the source of truth for drift detection.

Every time the document-writer persona runs during Phase 4 (Collect & Review), it emits a delivery intent alongside documentation updates. This creates an audit trail of "what governance delivered" that can be verified at any time.

## Workflow

```
Governance Change Flow:
  1. Code change lands in governance repo
  2. Document-writer generates delivery intent manifest
  3. Intent stored in .artifacts/delivery-intents/{intent_id}.json
  4. latest.json updated to point to new intent
  5. Consumer repo receives governance update
  6. CI runs: dark-governance verify-environment
  7. Drift detected? -> Fix or escalate
```

## Intent Schema

Delivery intents conform to `governance/schemas/delivery-intent.schema.json`. Key fields:

| Field | Description |
|-------|-------------|
| `schema_version` | Always `1.0.0` for this version |
| `intent_id` | Unique ID in format `di-YYYY-MM-DD-{random6}` |
| `created_at` | ISO 8601 timestamp |
| `source.pr` | Pull request reference |
| `source.branch` | Source branch name |
| `source.commit` | Commit SHA |
| `deliverables[]` | Array of files/directories with type, path, action, checksum |
| `expected_state` | Governance version, policy profile, required panels, workflows, directories |

### Example Intent

```json
{
  "schema_version": "1.0.0",
  "intent_id": "di-2026-03-03-abc123",
  "created_at": "2026-03-03T12:00:00Z",
  "source": {
    "pr": "#750",
    "branch": "itsfwcp/feat/750/new-feature",
    "commit": "abc123def456"
  },
  "deliverables": [
    {
      "type": "workflow",
      "path": ".github/workflows/dark-factory-governance.yml",
      "action": "create",
      "checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "version": "1.0.0"
    },
    {
      "type": "directory",
      "path": ".artifacts/plans",
      "action": "create",
      "expected_state": "exists"
    }
  ],
  "expected_state": {
    "governance_version": "1.0.0",
    "policy_profile": "default",
    "required_panels": ["code-review", "security-review"],
    "required_workflows": ["dark-factory-governance.yml"],
    "required_directories": [".artifacts/plans", ".artifacts/panels"]
  }
}
```

## `verify-environment` Command Reference

### Synopsis

```bash
dark-governance verify-environment [flags]
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--intent` | `.artifacts/delivery-intents/latest.json` | Path to a specific intent manifest |
| `--output` | `human` | Output format: `human` or `json` |
| `--fix` | `false` | Attempt auto-remediation of drift |

### What It Checks

| Check | Pass Condition |
|-------|----------------|
| File existence | All deliverables with `action: create/update` exist at declared paths |
| File checksums | Files match declared SHA-256 checksums (detects local edits) |
| Directory structure | All directory deliverables exist |
| Required directories | All `expected_state.required_directories` exist |
| Required workflows | All `expected_state.required_workflows` present in `.github/workflows/` |
| Deleted files | Files with `action: delete` no longer exist |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Environment matches delivery intent |
| 1 | Drift detected (fixable with `--fix`) |
| 2 | Critical error (invalid intent, read failure) |
| 3 | No delivery intent found |

### Examples

```bash
# Check current repo against latest delivery intent
dark-governance verify-environment

# Check against a specific intent
dark-governance verify-environment --intent .artifacts/delivery-intents/di-2026-03-03-abc123.json

# JSON output for CI pipelines
dark-governance verify-environment --output json

# Auto-fix missing directories
dark-governance verify-environment --fix
```

### Human Output

```
Environment Verification Report
================================
Intent: di-2026-03-03-abc123

  [PASS] file exists: .github/workflows/dark-factory-governance.yml
  [PASS] checksum matches: .github/workflows/dark-factory-governance.yml
  [PASS] directory exists: .artifacts/plans
  [FAIL] required directory missing: .artifacts/panels
         -> Create directory: mkdir -p .artifacts/panels

Summary: 3 passed, 1 failed, 0 warnings, 0 skipped

Overall: DRIFT DETECTED (1 issues)
Run 'dark-governance verify-environment --fix' to remediate.
```

### JSON Output

```json
{
  "intent_id": "di-2026-03-03-abc123",
  "passed": 3,
  "failed": 1,
  "warnings": 0,
  "skipped": 0,
  "results": [
    {
      "name": "file_exists:.github/workflows/dark-factory-governance.yml",
      "status": "pass",
      "message": "file exists: .github/workflows/dark-factory-governance.yml"
    },
    {
      "name": "required_dir:.artifacts/panels",
      "status": "fail",
      "message": "required directory missing: .artifacts/panels",
      "remediation": "Create directory: mkdir -p .artifacts/panels"
    }
  ],
  "overall_pass": false
}
```

## CI Integration

Add to your GitHub Actions workflow:

```yaml
- name: Verify governance environment
  run: dark-governance verify-environment --output json
```

To block PRs on drift:

```yaml
- name: Verify governance environment
  run: |
    dark-governance verify-environment --output json
    # Exit code 0 = pass, non-zero = fail
```

To auto-fix drift in a scheduled job:

```yaml
- name: Fix governance drift
  run: |
    dark-governance verify-environment --fix --output json
    if [ $? -eq 0 ]; then
      echo "Environment is in sync"
    else
      echo "Manual intervention required"
      exit 1
    fi
```

## Remediation

### Automatic (--fix)

The `--fix` flag performs safe auto-remediation:
- Creates missing directories
- Does **not** overwrite files with local edits
- Does **not** restore missing files (requires `dark-governance init`)

### Manual

For drift that cannot be auto-fixed:
1. Run `dark-governance verify-environment` to see the full report
2. For missing files: run `dark-governance init --force` to re-extract
3. For checksum mismatches: review the local edit and decide whether to keep or restore
4. For missing workflows: run `dark-governance init` to extract the CI workflow

## Troubleshooting

### "No delivery intent found"

The consumer repository does not have a delivery intent manifest. Run `dark-governance init` to initialize governance, which will create the `.artifacts/delivery-intents/` directory.

### Checksum mismatches

A file has been locally modified since the delivery intent was created. This is expected if the consumer repository has customized governance files. Review the diff and either:
- Accept the local edit (no action needed; the drift is intentional)
- Restore the original by running `dark-governance init --force`

### Policy profile mismatch

The `project.yaml` in the consumer repository has a different `governance.policy_profile` than what the delivery intent expects. Update `project.yaml` to match, or accept the difference if the consumer repo intentionally uses a different profile.

## Where Intents Live

```
.artifacts/
  delivery-intents/
    di-2026-03-03-abc123.json    # Individual intent manifests
    di-2026-03-04-def456.json
    latest.json                   # Most recent intent (updated on each change)
```

Each intent file is immutable once created. The `latest.json` file is updated to point to the most recent intent after each governance change.
