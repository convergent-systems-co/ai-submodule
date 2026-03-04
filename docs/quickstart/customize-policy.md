# Quickstart: Customize Policy Profiles

**Time:** 5 minutes | **Prerequisites:** Governance installed ([setup guide](add-governance.md))

---

## What Are Policy Profiles?

Policy profiles control how strictly governance reviews your PRs. Each profile sets thresholds for:
- Which panels must run
- What severity levels block merges
- Required confidence thresholds

## Available Profiles

| Profile | Use Case | Strictness |
|---------|----------|:----------:|
| `default` | General-purpose projects | Medium |
| `fin_pii_high` | Financial data, PII handling | High |
| `infrastructure_critical` | IaC, cloud resources, networking | High |
| `fast_track` | Low-risk documentation changes | Low |

## Step 1: Open project.yaml

Your project configuration is at the repo root:

```bash
# View current config
cat project.yaml
```

## Step 2: Change the Profile

Edit the `governance.policy_profile` field:

```yaml
governance:
  policy_profile: fin_pii_high   # Changed from 'default'
```

## Step 3: Commit and Push

```bash
git add project.yaml
git commit -m "feat: upgrade governance to fin_pii_high policy profile"
git push
```

Future PRs will use the new profile.

## Profile Details

### `default`
- All standard panels run (code-review, security-review, documentation-review)
- Critical and high findings block merge
- Medium findings generate warnings

### `fin_pii_high`
- All standard panels plus data-governance-review
- Critical, high, AND medium findings block merge
- PII detection is mandatory
- Stricter confidence thresholds

### `infrastructure_critical`
- All standard panels plus cost-analysis
- Threat modeling is mandatory
- Blast radius assessment for infrastructure changes
- Critical and high findings block merge

### `fast_track`
- Documentation review only
- Only critical findings block merge
- Faster CI turnaround for low-risk changes

## Custom Panel Selection

Add or remove specific panels in project.yaml:

```yaml
governance:
  policy_profile: default
  panels:
    - code-review
    - security-review
    - documentation-review
    - cost-analysis          # Added: reviews cost implications
    - data-governance-review # Added: checks PII handling
```

## Verify Your Config

```bash
bash .ai/bin/governance-status.sh
```

This shows the active profile and configured panels.

---

## Next Steps

- [Run the agentic loop](run-agentic-loop.md) - Automated issue resolution
- [View all policy options](../reference/policy-profiles.md) - Complete profile reference
