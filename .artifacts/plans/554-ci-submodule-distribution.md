# Plan: Fix CI submodule cloning for consuming repos

**Issue:** #554
**Type:** Fix / Feature
**Priority:** High

## Problem

Consuming repos in different GitHub orgs cannot clone the private `convergent-systems-co/dark-forge` in CI. The full Python policy engine is unavailable, forcing fallback to lightweight Tier 2 validation with reduced confidence.

## Solution

Enable consuming repos to run full governance checks in CI by distributing the policy engine as a self-contained tarball via GitHub Releases and a reusable composite GitHub Action.

## Deliverables

1. **Add `--package` flag to `governance/bin/vendor-engine.sh`** — Creates a self-contained tarball (`governance-engine-{version}.tar.gz`) in `.governance/dist/` containing policy engine, schemas, and policy profiles.

2. **Create `.github/workflows/publish-governance-artifacts.yml`** — Triggered on GitHub releases; runs `vendor-engine.sh --package` and uploads the tarball as a release asset.

3. **Create `.github/actions/governance-check/action.yml`** — Composite GitHub Action that downloads governance artifacts, extracts them, runs the policy engine, and sets the `decision` output.

4. **Create `docs/guides/cross-org-ci-integration.md`** — Documentation for cross-org CI setup.

5. **Update CLAUDE.md** — Add reference to the new cross-org CI guide.

## Implementation Steps

1. Modify `governance/bin/vendor-engine.sh` to accept `--package` flag
2. Create the publish workflow
3. Create the composite action
4. Write the documentation guide
5. Update CLAUDE.md

## Testing

- Verify `--package` flag creates a valid tarball with expected contents
- Verify the workflow YAML is valid
- Verify the action YAML is valid and inputs/outputs are correct
