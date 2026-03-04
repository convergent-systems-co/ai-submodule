# Cross-Org CI Integration Guide

This guide explains how consuming repos in external GitHub organizations can run the full Dark Forge policy engine in CI without needing to clone the private `convergent-systems-co/dark-forge`.

## Problem

Consuming repos that reference `dark-forge` as a git submodule cannot clone it in CI when they reside in a different GitHub organization. Without the submodule, the governance workflow falls back to lightweight Tier 2 validation, which has reduced confidence (0.70 vs 0.85).

## Solution

The dark-forge publishes a self-contained governance engine tarball as a GitHub Release asset. A reusable composite GitHub Action downloads and runs this engine against your local panel emissions.

## Prerequisites

1. A GitHub token with read access to `convergent-systems-co/dark-forge` releases (fine-grained PAT or GitHub App token with `contents: read` on the dark-forge repo).
2. Panel emissions present in `.artifacts/panels/` or `governance/emissions/` in your repository.

## Quick Start

Add the governance check to your pull request workflow:

```yaml
name: Governance

on:
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  governance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run governance check
        id: governance
        uses: convergent-systems-co/dark-forge/.github/actions/governance-check@main
        with:
          token: ${{ secrets.AI_SUBMODULE_TOKEN }}

      - name: Report decision
        run: |
          echo "Decision: ${{ steps.governance.outputs.decision }}"
          echo "Confidence: ${{ steps.governance.outputs.confidence }}"
```

## Action Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `version` | No | `latest` | Release tag to download. Use `latest` for the most recent release, or pin to a specific tag (e.g., `v1.2.0`). |
| `governance-root` | No | `.governance` | Path to the `.governance` directory containing panel emissions. |
| `policy-profile` | No | `default` | Policy profile name to evaluate against (without `.yaml` extension). |
| `artifact-repo` | No | `convergent-systems-co/dark-forge` | Repository to download governance artifacts from. |
| `token` | Yes | -- | GitHub token with read access to the artifact repository. |

## Action Outputs

| Output | Description |
|--------|-------------|
| `decision` | Policy engine decision: `auto_merge`, `block`, `human_review_required`, or `auto_remediate`. |
| `confidence` | Aggregate confidence score from evaluated panels. |
| `manifest` | Path to the generated run manifest JSON file. |

## Pinning Versions

For reproducible CI, pin to a specific release tag rather than using `latest`:

```yaml
- uses: convergent-systems-co/dark-forge/.github/actions/governance-check@main
  with:
    version: "v1.2.0"
    token: ${{ secrets.AI_SUBMODULE_TOKEN }}
```

## Using a Custom Policy Profile

If your repository uses a non-default policy profile (e.g., `fin_pii_high`), specify it via the `policy-profile` input:

```yaml
- uses: convergent-systems-co/dark-forge/.github/actions/governance-check@main
  with:
    policy-profile: "fin_pii_high"
    token: ${{ secrets.AI_SUBMODULE_TOKEN }}
```

Available profiles are defined in `governance/policy/` within the dark-forge.

## Token Configuration

Create a fine-grained personal access token (PAT) or GitHub App token with:

- **Repository access:** `convergent-systems-co/dark-forge`
- **Permission:** `Contents: Read`

Store it as a repository secret named `AI_SUBMODULE_TOKEN`.

## Conditional Merge Based on Decision

Use the `decision` output to gate merges:

```yaml
- name: Block on governance failure
  if: steps.governance.outputs.decision == 'block'
  run: |
    echo "::error::Governance check failed — merge blocked"
    exit 1

- name: Request review on human_review_required
  if: steps.governance.outputs.decision == 'human_review_required'
  run: |
    echo "::warning::Governance requires human review before merge"
```

## Alternative: Vendored Engine (No Release Download)

If you prefer not to download artifacts at runtime, you can vendor the engine directly into your repository during `init.sh`:

```bash
bash .ai/governance/bin/vendor-engine.sh
```

This copies the engine into `.artifacts/engine/` and is kept up-to-date by `init.sh --refresh`. The governance workflow automatically detects and uses the vendored copy. See `governance/bin/vendor-engine.sh` for details.

## Packaging a Tarball Locally

To create a governance engine tarball locally (e.g., for manual distribution):

```bash
bash .ai/governance/bin/vendor-engine.sh --package
```

This creates `.artifacts/dist/governance-engine-{version}.tar.gz`.

## Troubleshooting

### No releases found

Ensure the token has read access to `convergent-systems-co/dark-forge`. Check that releases exist in the repository.

### No panel emissions found

The action looks for emissions in `.artifacts/panels/` and `governance/emissions/`. Ensure your governance panels have run and written their output before the governance check step.

### Policy profile not found

The action falls back to `default.yaml` if the requested profile is not found in the tarball. Check that the profile exists in `governance/policy/` in the dark-forge.
