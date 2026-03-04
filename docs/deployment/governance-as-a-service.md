# Governance-as-a-Service Deployment Guide

This guide covers deploying the governance policy engine as a containerized REST API service on Azure Kubernetes Service (AKS).

## Architecture

```
CI Pipeline -> REST API -> Policy Engine -> Verdict
                  |
           Azure Container Registry (ACR)
                  |
           Azure Kubernetes Service (AKS)
```

## Prerequisites

- Azure subscription with ACR and AKS
- Docker for building images
- Helm 3.x for Kubernetes deployment
- `kubectl` configured for your AKS cluster

## Container Image

### Build Locally

```bash
docker build -t governance-service .
docker run -p 8080:8080 governance-service
```

### Publish to ACR

```bash
# Login to ACR
az acr login --name <acr-name>

# Tag and push
docker tag governance-service <acr-name>.azurecr.io/governance-service:v1.0.0
docker push <acr-name>.azurecr.io/governance-service:v1.0.0
```

### CI/CD Publishing

The `docker-publish.yml` workflow automatically builds and pushes on every release tag:

1. Configure GitHub secrets:
   - `ACR_LOGIN_SERVER`: Your ACR login server (e.g., `myacr.azurecr.io`)
   - `ACR_USERNAME`: Service principal client ID
   - `ACR_PASSWORD`: Service principal client secret

2. Create a release tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

## REST API

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/evaluate` | Evaluate emissions against policy |
| POST | `/api/v1/validate` | Validate emission schema |
| GET | `/api/v1/profiles` | List available policy profiles |
| GET | `/docs` | Swagger UI (auto-generated) |
| GET | `/redoc` | ReDoc documentation |

### Evaluate Emissions

```bash
curl -X POST http://localhost:8080/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "emissions": [
      {
        "panel_name": "code-review",
        "verdict": "pass",
        "confidence_score": 0.92,
        "risk_level": "low"
      },
      {
        "panel_name": "security-review",
        "verdict": "pass",
        "confidence_score": 0.88,
        "risk_level": "low"
      }
    ],
    "profile": "default"
  }'
```

Response:
```json
{
  "decision": "auto_merge",
  "confidence": 0.9,
  "risk_level": "low",
  "panels_evaluated": 2,
  "panels_passed": 2,
  "panels_failed": 0
}
```

## Helm Deployment

### Install

```bash
helm install governance helm/governance-service/ \
  --set image.repository=<acr-name>.azurecr.io/governance-service \
  --set image.tag=v1.0.0
```

### Custom Values

Create a `values-production.yaml`:

```yaml
replicaCount: 3

image:
  repository: myacr.azurecr.io/governance-service
  tag: v1.0.0

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: governance.mycompany.com
      paths:
        - path: /
          pathType: Prefix

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 250m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
```

```bash
helm install governance helm/governance-service/ -f values-production.yaml
```

### Upgrade

```bash
helm upgrade governance helm/governance-service/ \
  --set image.tag=v1.1.0
```

## GitHub Action

Use the governance check in your CI pipeline without requiring the submodule:

```yaml
- name: Run Governance Check
  uses: convergent-systems-co/dark-forge/.github/actions/governance-check@main
  with:
    emissions-dir: .governance/panels/
    policy-profile: default
    acr-login-server: ${{ secrets.ACR_LOGIN_SERVER }}
    acr-username: ${{ secrets.ACR_USERNAME }}
    acr-password: ${{ secrets.ACR_PASSWORD }}
```

## Security

- Container runs as non-root user
- Read-only root filesystem
- No privilege escalation
- Trivy security scan on every build
- CORS configurable per deployment
