# Unified Deployment Pipeline Guide

This guide explains how to adopt the unified deployment pipeline template for consuming repos.

## Problem

Consuming repos often have multiple manually-triggered deployment workflows:
- `build.yml` — Build artifacts
- `infra.yml` — Provision infrastructure (Terraform, Bicep)
- `private-endpoints.yml` — Configure networking
- `deploy.yml` — Deploy application (Helm, kubectl, az webapp)

Operators must run these in sequence, with no enforced ordering, no way to skip inapplicable phases, and duplicated promotion validation logic.

## Solution

A single orchestrating `pipeline.yml` that calls existing workflows via `workflow_call`, with:
- Conditional job phases with skip flags
- Centralized promotion validation
- Environment concurrency guards
- Summary reporting

## Quick Start

### 1. Copy the pipeline template

```bash
cp .ai/governance/templates/workflows/pipeline.yml .github/workflows/pipeline.yml
```

### 2. Copy the promotion validation action (optional)

```bash
mkdir -p .github/actions/validate-promotion
cp .ai/governance/templates/actions/validate-promotion/action.yml \
   .github/actions/validate-promotion/action.yml
```

### 3. Add `workflow_call` triggers to existing workflows

Each phase workflow needs a `workflow_call` trigger alongside its existing `workflow_dispatch`:

```yaml
# In .github/workflows/build.yml
on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [dev, staging, production]
  workflow_call:
    inputs:
      environment:
        type: string
        required: true
      ref:
        type: string
        required: false
```

### 4. Update pipeline.yml to call your workflows

Uncomment the `uses:` lines in each phase and remove the inline placeholder steps:

```yaml
  build:
    needs: [validate-promotion]
    if: |
      needs.validate-promotion.outputs.proceed == 'true' &&
      github.event.inputs.skip_build != 'true'
    uses: ./.github/workflows/build.yml
    with:
      environment: ${{ github.event.inputs.environment }}
      ref: ${{ github.event.inputs.build_ref || github.ref }}
```

### 5. Customize promotion validation

Edit the `validate-promotion` step or action to match your promotion rules. Options:
- **GitHub Deployments API** (default) — checks for successful deployment to previous environment
- **Git tags** — check for environment-specific tags (e.g., `staging-v1.2.3`)
- **External system** — query your deployment tracker

## Template Structure

### Pipeline Phases

| Phase | Default | Purpose |
|-------|---------|---------|
| `validate-promotion` | Always runs | Verify environment promotion order |
| `build` | Enabled | Build application artifacts |
| `infra` | Enabled | Provision infrastructure |
| `private-endpoints` | Skipped | Configure private networking |
| `deploy` | Enabled | Deploy application |
| `summary` | Always runs | Report phase results |

### Skip Flags

Each phase has a corresponding skip flag:

| Input | Default | Effect |
|-------|---------|--------|
| `skip_build` | false | Skip the build phase |
| `skip_infra` | false | Skip the infrastructure phase |
| `skip_private_endpoints` | true | Skip private endpoints (opt-in) |
| `skip_deploy` | false | Skip the deployment phase |

### Promotion Order

The default promotion order is `dev -> staging -> production`. Customize in the pipeline or the composite action:

```yaml
- uses: ./.github/actions/validate-promotion
  with:
    environment: ${{ github.event.inputs.environment }}
    promotion_order: 'dev,qa,staging,production'
```

## Design Principles

1. **Existing workflows remain usable** — Individual workflows still work via `workflow_dispatch`
2. **No step duplication** — Pipeline delegates via `workflow_call`, not by copying steps
3. **Promotion validation is centralized** — Single source of truth for environment ordering
4. **Skip flags for flexibility** — Operators can bypass phases that do not apply
5. **Destructive operations stay standalone** — Environment destruction workflows are not included in the pipeline
6. **Language/framework agnostic** — Template works for any tech stack

## Related

- Pipeline template: `governance/templates/workflows/pipeline.yml`
- Promotion validation action: `governance/templates/actions/validate-promotion/action.yml`
- CI gating: `docs/configuration/ci-gating.md`
