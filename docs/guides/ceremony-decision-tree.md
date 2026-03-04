# Ceremony Decision Tree

This guide shows how change type determines the governance ceremony level: which policy profile applies, which panels are required, and whether a formal plan is needed.

## Decision Flowchart

```mermaid
flowchart TD
    A[Incoming Change] --> B{Classify change type}

    B -->|docs_only| C[Documentation Only]
    B -->|typo_fix| D[Typo / Formatting Fix]
    B -->|chore| E[Chore / Maintenance]
    B -->|test_only| F[Test Only]
    B -->|source / infra / api| G[Standard Change]
    B -->|security / compliance| H[High-Risk Change]

    C --> FT[Fast-Track Profile]
    D --> FT
    E --> FT
    F --> FT

    G --> DP[Default Profile]
    H --> HP{Risk classification?}

    HP -->|PII / financial data| FPH[fin_pii_high Profile]
    HP -->|Infrastructure| IC[infrastructure_critical Profile]
    HP -->|Mature repo, routine| RT[reduced_touchpoint Profile]

    FT --> FT_PANELS[Required Panels:<br/>code-review + security-review]
    FT_PANELS --> FT_PLAN{Files changed < 3?}
    FT_PLAN -->|Yes| FT_NOPLAN[No plan required]
    FT_PLAN -->|No| FT_LIGHT[Lightweight plan<br/>plan-template-light.md]
    FT_NOPLAN --> FT_MERGE[Auto-merge<br/>confidence >= 0.75]
    FT_LIGHT --> FT_MERGE

    DP --> DP_PANELS[Required Panels:<br/>code-review, security-review,<br/>threat-modeling, cost-analysis,<br/>documentation-review,<br/>data-governance-review]
    DP_PANELS --> DP_PLAN[Full plan required<br/>plan-template.md]
    DP_PLAN --> DP_MERGE[Auto-merge<br/>confidence >= 0.85]

    FPH --> FPH_PANELS[All default panels +<br/>mandatory architecture review]
    FPH_PANELS --> FPH_PLAN[Full plan required]
    FPH_PLAN --> FPH_MERGE[No auto-merge<br/>3 approvers required]

    IC --> IC_PANELS[All default panels +<br/>architecture + SRE review]
    IC_PANELS --> IC_PLAN[Full plan required]
    IC_PLAN --> IC_MERGE[Manual review required]

    RT --> RT_PANELS[Same panels as default]
    RT_PANELS --> RT_PLAN[Full plan required]
    RT_PLAN --> RT_MERGE[Auto-merge<br/>confidence >= 0.75<br/>accepts medium risk]
```

## Change Type Classification

| Change Type | Description | Example |
|-------------|-------------|---------|
| `docs_only` | Only documentation files changed (`.md`, `docs/`) | README update, guide addition |
| `typo_fix` | Typo or formatting corrections | Fix spelling in comments |
| `chore` | Maintenance tasks with no behavior change | Dependency bump, CI config tweak |
| `test_only` | Only test files added or modified | New unit test, test refactor |
| Standard | Application source, libraries, packages | Feature implementation, bug fix |
| High-risk | Security, compliance, infrastructure, data | Auth changes, DB migrations, IaC |

## Panel Requirements by Profile

| Panel | fast-track | default | reduced_touchpoint | fin_pii_high | infrastructure_critical |
|-------|:----------:|:-------:|:------------------:|:------------:|:----------------------:|
| code-review | Required | Required | Required | Required | Required |
| security-review | Required | Required | Required | Required | Required |
| threat-modeling | -- | Required | Required | Required | Required |
| cost-analysis | -- | Required | Required | Required | Required |
| documentation-review | Optional | Required | Required | Required | Required |
| data-governance-review | -- | Required | Required | Required | Required |

## Panel Overrides by Change Type (default profile)

When using the default profile, the required panels can be narrowed based on change type:

| Change Type | Required Panels | Optional Panels |
|-------------|-----------------|-----------------|
| `docs_only` | documentation-review, security-review | code-review |
| `chore` | code-review, security-review | documentation-review |
| `test_only` | testing-review, code-review, security-review | -- |

These overrides are defined in `governance/policy/default.yaml` under `panel_overrides_by_change_type`.

## Plan Requirements

| Profile | Plan Required | Template |
|---------|:------------:|----------|
| fast-track (< 3 files) | No | -- |
| fast-track (>= 3 files) | Yes | `plan-template-light.md` |
| default | Yes | `plan-template.md` |
| reduced_touchpoint | Yes | `plan-template.md` |
| fin_pii_high | Yes | `plan-template.md` |
| infrastructure_critical | Yes | `plan-template.md` |

## Auto-Merge Thresholds

| Profile | Confidence Threshold | Accepts Medium Risk | Human Approval |
|---------|:-------------------:|:-------------------:|:--------------:|
| fast-track | 0.75 | Yes | No |
| default | 0.85 | No | On escalation |
| reduced_touchpoint | 0.75 | Yes | Override only |
| fin_pii_high | -- | -- | Always required |
| infrastructure_critical | -- | -- | Always required |

## Security-Review Is Non-Negotiable

Regardless of change type, profile, or ceremony level, `security-review` is **always required**. This is enforced at every level:

- All policy profiles include `security-review` in `required_panels`
- All `panel_overrides_by_change_type` entries include `security-review`
- The fast-track profile requires `security-review` even for documentation-only changes
