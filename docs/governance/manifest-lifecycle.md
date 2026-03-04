# Manifest Lifecycle

## Immutability

Manifests are **append-only audit artifacts**. Once a manifest is created, it must never be edited, overwritten, or deleted. Each manifest captures a complete, reproducible record of a governance decision -- including the policy profile, panel emissions, confidence scores, and final merge verdict.

Editing a manifest after creation would invalidate the audit trail and break reproducibility guarantees. If a governance decision needs correction, a new manifest must be created referencing the original.

## Enforcement Mechanisms

### CODEOWNERS

The `governance/manifests/` directory is protected by a CODEOWNERS rule requiring `@SET-Apps/approvers` review for any changes. This prevents unauthorized modifications to existing manifests.

### CI Enforcement (Planned)

A future CI check will validate that:
- No existing manifest files are modified in a PR (diff check on `governance/manifests/`)
- New manifests conform to `governance/schemas/run-manifest.schema.json`
- Manifest `manifest_id` values are unique across the repository

This CI check is not yet implemented. The CODEOWNERS rule provides the current enforcement layer.

## Retention Policy

### Git Repository

Manifests are retained **permanently** in the git repository. They are required for audit replay -- reconstructing the governance decision that approved any given change. Permanent retention ensures compliance audit periods are satisfied regardless of the regulatory framework.

### CI Artifacts

Panel emissions and governance workflow outputs stored as GitHub Actions artifacts follow the repository's CI artifact retention policy: **90 days** per the GitHub Actions configuration. These are supplementary to the git-committed manifests and are not the primary audit record.

## Panel Name Validation

Panel output emissions are validated against `governance/schemas/panel-output.schema.json`, which enforces the pattern `^[a-z][a-z0-9-]+$` for panel names (lowercase alphanumeric with hyphens).

`governance/schemas/panels.schema.json` currently accepts any string as a panel key. This inconsistency is documented here but not fixed in this change -- aligning the two schemas is tracked separately to avoid unintended breakage for consuming repos.
