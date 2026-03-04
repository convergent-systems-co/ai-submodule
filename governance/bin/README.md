# Dark Forge Tools

## Policy Engine

The policy engine source has moved to `governance/engine/policy_engine.py` as part of a proper Python package (`governance/engine/`). This directory retains a backward-compatible wrapper at `policy-engine.py` so existing CI workflows and consuming repos continue to work without changes.

### Requirements

- Python 3.12+
- Dependencies defined in `governance/engine/pyproject.toml`

### Usage

```bash
# Via the backward-compatible wrapper (existing behavior):
python governance/bin/policy-engine.py \
    --emissions-dir governance/emissions/ \
    --profile governance/policy/default.yaml \
    --output manifest.json \
    --commit-sha "$(git rev-parse HEAD)" \
    --pr-number 42 \
    --repo "owner/repo"

# Or as a Python package:
python -m governance.engine.policy_engine \
    --emissions-dir governance/emissions/ \
    --profile governance/policy/default.yaml \
    --output manifest.json
```

### Flags

| Flag | Required | Description |
|------|----------|-------------|
| `--emissions-dir` | Yes | Directory containing panel emission JSON files |
| `--profile` | Yes | Path to YAML policy profile |
| `--output` | Yes | Path to write the run manifest JSON |
| `--log-file` | No | Path to write evaluation log (defaults to stderr) |
| `--ci-checks-passed` | No | `true` or `false` (default: `true`) |
| `--commit-sha` | No | Git commit SHA for manifest |
| `--pr-number` | No | PR number for manifest context |
| `--repo` | No | Repository name (`owner/repo`) for manifest context |

### Exit Codes

| Code | Decision |
|------|----------|
| 0 | `auto_merge` |
| 1 | `block` |
| 2 | `human_review_required` |
| 3 | `auto_remediate` |

### Evaluation Sequence

1. Load and validate emissions against `governance/schemas/panel-output.schema.json`
2. Load and parse policy profile YAML
3. Check required panels present
4. Compute weighted aggregate confidence (with redistribution for missing optional panels)
5. Compute aggregate risk via risk aggregation rules
6. Collect policy flags across all emissions
7. Evaluate block conditions
8. Evaluate escalation rules
9. Evaluate auto-merge conditions
10. Evaluate auto-remediate conditions
11. Default to `human_review_required`

Every step logs its evaluation with pass/fail/skip to stderr (or `--log-file`).

### Supported Policy Profiles

- `governance/policy/default.yaml` — Standard risk tolerance
- `governance/policy/fin_pii_high.yaml` — SOC2/PCI-DSS/HIPAA/GDPR compliance
- `governance/policy/infrastructure_critical.yaml` — Mandatory architecture and SRE review
