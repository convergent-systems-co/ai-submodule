# Deployment Phases (6-7)

The orchestrator can optionally extend beyond merge with two deployment phases. These phases are capacity-gated and audited like all other orchestrator phases.

## Overview

| Phase | Name | Responsibility |
|-------|------|---------------|
| 6 | Build & Package | Docker build, artifact publish, security scan |
| 7 | Deploy & Verify | IaC apply, container deploy, rollout verification, smoke tests |

## Enabling Deployment

Add `deployment` to the `governance` section of `project.yaml`:

```yaml
governance:
  parallel_coders: 5
  deployment:
    enabled: true
    target: aks               # aks, ecs, lambda, static, custom
    environments:
      - dev
      - staging
      - production
    rollback_on_failure: true
    artifact_registry: myregistry.azurecr.io
    helm_chart: charts/myapp
    iac_path: infra/bicep
    smoke_test_command: "curl -sf https://myapp.dev/health"
```

When `deployment.enabled` is `false` (default), the orchestrator skips directly from Phase 5 (Merge) to the loop decision.

## Phase Flow

```
Phase 5 (Merge)
  |
  v
Deployment configured? ── No ──> Loop/Done
  |
  Yes
  |
  v
Phase 6 (Build & Package)
  |
  v
Phase 7 (Deploy & Verify)
  |
  v
Loop/Done
```

## Gate Actions

| Phase | GREEN | YELLOW | ORANGE | RED |
|-------|-------|--------|--------|-----|
| 6 (Build) | PROCEED | PROCEED | CHECKPOINT | EMERGENCY_STOP |
| 7 (Deploy) | PROCEED | SKIP_DISPATCH | CHECKPOINT | EMERGENCY_STOP |

- At Yellow tier, Phase 7 is skipped (artifacts are built but not deployed).
- At Orange tier, both phases checkpoint (save state and stop).
- At Red tier, emergency stop applies.

## Skip Flags

```yaml
governance:
  deployment:
    enabled: true
    skip_build: true   # Skip Phase 6 (e.g., builds handled by external CI)
    skip_deploy: false  # Phase 7 still runs
```

## Rollback

When `rollback_on_failure` is `true` (default), the orchestrator automatically rolls back if deployment verification fails. The rollback outcome is recorded in the audit trail.

## State Machine Transitions

```
Phase 5 → Phase 6 → Phase 7 → Phase 1 (loop)
```

Phase 0 (checkpoint recovery) can resume directly to Phase 6 or 7.

## Deployment Targets

| Target | Description |
|--------|-------------|
| `aks` | Azure Kubernetes Service (Helm + Bicep IaC) |
| `ecs` | AWS Elastic Container Service |
| `lambda` | AWS Lambda (serverless) |
| `static` | Static site deployment (CDN, S3, Azure Blob) |
| `custom` | Custom deployment script (default) |

## Environment Promotion

Environments must follow promotion order: `dev` -> `staging` -> `production`. The orchestrator validates this at configuration load time.

## Schema

The deployment configuration is validated against the `governance.deployment` section in `governance/schemas/project.schema.json`.
