# Panel: Data Governance Review

## Purpose
Enforce enterprise canonical data model standards from dach-canonical-models. Validate that data changes comply with naming conventions, schema structure, external reference discipline, and deployment governance.

## Reference Repository
**Source of truth:** [SET-Apps/dach-canonical-models](https://github.com/SET-Apps/dach-canonical-models)

All data governance standards are defined in the canonical models repository. This panel evaluates changes against those standards. When canonicals are missing or outdated, the missing-canonical workflow (`governance/prompts/data-governance-workflow.md`) must be followed.

## Participants
- **Data Architect** — Schema structure, canonical compliance, naming conventions
- **Compliance Officer** — Data standards adherence, audit trail completeness
- **Domain Expert** — Business domain alignment, model accuracy
- **Security Auditor** — Data classification, access control, PII handling

## Evaluate For
Changes that affect data models, schemas, data pipelines, or any file referencing canonical data structures:
- `models/**`, `schemas/**`, `data/**`, `db/**`, `migrations/**`
- Files containing schema definitions, data contracts, or event structures
- Changes that introduce or modify data fields, entities, or relationships

## Standards Enforced

### Naming Conventions
| Artifact | Required Pattern | Example |
|----------|-----------------|---------|
| Model file | `<domain>.hck.json` | `product.hck.json` |
| Schema group | `<domain>-<product>` | `product-model` |
| Document name | `<group-name>` or `<group-name>-<suffix>` | `product-model-header` |
| Schema file | `<domain>-<product>.json` | `product-model.json` |

### External Reference Discipline
- Standard fields (Audit, Vehicle, Model, Dealer, Parts, Accessory, Series) must use external references (`$ref`) from `Data Standards.hck.json`
- Duplicating standard field definitions is a **critical** finding
- Changes to standard fields must be made in the canonical `Data Standards.hck.json`, never in consuming models

### Field Constraints (from Data Standards)
| Field | Constraint |
|-------|-----------|
| VIN | Fixed 17 characters |
| ModelNumber | Fixed 4-digit string |
| ModelYear | Range 1900-3000 |
| UnitId | Range 100000000-999999999 |
| DealerNumber | Fixed 5-digit string (2-digit state + 3-digit sequential) |
| PartNumber | Max 15 alphanumeric characters |
| SeriesCode | Fixed 3-character string |
| DateTime fields | ISO 8601 format |

### Deployment Governance
- New schemas default to `deploy_*=FALSE` across all environments
- Progressive deployment: dev → stg → uat → prod
- Deployment CSV must exist for each domain with correct structure
- Dual registration: canonical name + message-specific names

### Model Validation Rules
| Rule | Severity | Description |
|------|----------|-------------|
| Model name matches filename | Critical | `modelName` must equal filename (case-sensitive) |
| No placeholder names | Critical | Forbidden: "New Model", "Untitled", "Test Model" |
| Document name includes domain prefix | Critical | Must match `<group>` or `<group>-<suffix>` |
| Model has definitions | Warning | At least one schema group required |
| External references for standard fields | Critical | Must use `$ref` for enterprise-standard fields |

## Output Format
### Per Participant
- Perspective name
- Canonical compliance assessment
- Naming convention violations
- External reference violations
- Risk level
- Recommended changes

### Consolidated
- Canonical compliance score
- Naming convention adherence
- External reference discipline
- Deployment governance status
- Missing canonical models (triggers workflow)
- Data governance recommendations

## Pass/Fail Criteria

This panel **passes** when all of the following are met:

| Criterion | Threshold | Blocked If |
|-----------|-----------|------------|
| Confidence score | >= 0.70 | Below 0.70 |
| Critical findings | 0 allowed | Any critical finding present |
| High findings | <= 1 | More than 1 high finding |
| Aggregate verdict | approve | Block or abstain majority |
| Canonical compliance score | >= 0.80 | Below 0.80 |

When blocked, the panel emits a `block` verdict with a structured explanation of which criterion failed. The PR comment includes specific scores and finding counts.

Local overrides via `panels.local.json` can increase these thresholds (more restrictive) but never decrease them. See `governance/schemas/panels.schema.json` for the override format.

## Confidence Score Calculation

```
confidence = 0.85  (base)
           - (critical_findings x 0.25)
           - (high_findings x 0.15)
           - (medium_findings x 0.05)
           - (low_findings x 0.01)
           = max(confidence, 0.0)  (floor)
```

| Finding Severity | Deduction | Example: 1 finding |
|-----------------|-----------|-------------------|
| Critical | -0.25 | 0.85 -> 0.60 |
| High | -0.15 | 0.85 -> 0.70 |
| Medium | -0.05 | 0.85 -> 0.80 |
| Low | -0.01 | 0.85 -> 0.84 |

## Missing Canonical Workflow

When this panel detects that a data change references a canonical model that does not exist in dach-canonical-models:

1. Follow the workflow in `governance/prompts/data-governance-workflow.md`
2. The PR is **blocked** until the canonical model exists
3. An issue is created on the canonical repository
4. The consuming repo issue is updated with cross-reference

## Constraints
- Never approve a PR that duplicates standard field definitions
- Never approve a PR with incorrect naming conventions for data artifacts
- Always verify canonical model existence before approving data changes
- Deployment configuration changes require explicit environment-by-environment review
