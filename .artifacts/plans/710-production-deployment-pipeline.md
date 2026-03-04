# Production Deployment Pipeline (Azure AKS/Helm/Docker/ACR)

**Author:** Team Lead (batch-scoped PM mode)
**Date:** 2026-03-02
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/710
**Branch:** itsfwcp/feat/710/production-deployment-pipeline

---

## 1. Objective

Package the policy engine and orchestrator as a deployable Governance-as-a-Service container, published to Azure Container Registry (ACR), with a Helm chart for AKS deployment, a REST API for CI integrations, and a GitHub Action for marketplace consumption.

**CRITICAL: All container images MUST use Azure Container Registry (ACR). NOT GHCR. NOT Google. We are an Azure shop.**

## 2. Rationale

DACH has a complete build/packaging pipeline with AKS deployment (Bicep + Helm), Docker/ACR publishing. AI-Submodule deploys as a submodule with pytest CI. This closes the deployment maturity gap.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| GitHub Container Registry (GHCR) | Yes | Org standard is Azure; ACR integrates with AKS natively |
| Google Artifact Registry | Yes | We are an Azure shop |
| Serverless (Azure Functions) | Yes | Less portable; Helm/AKS is the org standard |
| Package as pip module only | Yes | Does not address REST API or CI integration needs |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage Docker build for policy engine service |
| `helm/governance-service/Chart.yaml` | Helm chart definition |
| `helm/governance-service/values.yaml` | Default Helm values (ACR image reference, replicas, resources) |
| `helm/governance-service/templates/deployment.yaml` | Kubernetes Deployment template |
| `helm/governance-service/templates/service.yaml` | Kubernetes Service template |
| `helm/governance-service/templates/configmap.yaml` | ConfigMap for policy profiles |
| `helm/governance-service/templates/ingress.yaml` | Ingress template (optional) |
| `helm/governance-service/templates/_helpers.tpl` | Helm template helpers |
| `governance/engine/api/app.py` | FastAPI REST API for policy evaluation |
| `governance/engine/api/routes.py` | API route definitions |
| `governance/engine/api/models.py` | Pydantic models for API request/response |
| `governance/engine/api/__init__.py` | Package init |
| `governance/engine/api/tests/test_api.py` | API tests |
| `.github/workflows/docker-publish.yml` | CI workflow: build, scan, push to ACR on release |
| `.github/actions/governance-check/action.yml` | GitHub Action definition wrapping container image |
| `.github/actions/governance-check/Dockerfile` | Action container (pulls from ACR) |
| `docs/deployment/governance-as-a-service.md` | Deployment guide |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/engine/orchestrator/deployment.py` | Add ACR-specific configuration, Helm chart reference |
| `project.yaml` | Add deployment configuration section (documented) |

### Files to Delete

None.

## 4. Approach

1. **Create root `Dockerfile`** — Multi-stage build:
   - Stage 1 (build): Python 3.11-slim, install dependencies, copy engine
   - Stage 2 (runtime): Minimal image with only runtime deps
   - Expose port 8080 for REST API
   - Health check endpoint at `/health`
   - Entrypoint: `uvicorn governance.engine.api.app:app`

2. **Create FastAPI REST API** (`governance/engine/api/`):
   - `POST /api/v1/evaluate` — Accept emissions JSON, run policy engine, return verdict
   - `GET /api/v1/health` — Health check
   - `GET /api/v1/profiles` — List available policy profiles
   - `POST /api/v1/validate` — Validate emissions against schema
   - Pydantic models for request/response
   - CORS configuration for CI integrations

3. **Create Helm chart** (`helm/governance-service/`):
   - ACR image reference: `<acr-name>.azurecr.io/governance-service`
   - Configurable replicas, resource limits
   - ConfigMap mounting for custom policy profiles
   - Ingress template for external access
   - Health/readiness probes pointing to `/api/v1/health`

4. **Create CI workflow** (`.github/workflows/docker-publish.yml`):
   - Trigger on release tag (e.g., `v*`)
   - Build Docker image
   - Run Trivy security scan
   - Login to ACR using service principal credentials (secrets: `ACR_LOGIN_SERVER`, `ACR_USERNAME`, `ACR_PASSWORD`)
   - Push to ACR with version tag and `latest`
   - **NOT GHCR** -- explicitly use ACR

5. **Create GitHub Action** (`.github/actions/governance-check/`):
   - Composite action that pulls the governance container from ACR
   - Runs policy evaluation against provided emissions
   - Outputs verdict, confidence, risk level
   - Inputs: emissions directory, policy profile, ACR credentials

6. **Extend `deployment.py`** — Add ACR-specific fields:
   - `artifact_registry_type: "acr"` (validate not ghcr/gcr)
   - `acr_login_server` configuration
   - `helm_chart_path` pointing to `helm/governance-service`

7. **Write documentation** — Deployment guide covering ACR setup, Helm installation, API usage

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `api/routes.py` | Test each endpoint with mock policy engine |
| Unit | `api/models.py` | Test Pydantic model validation |
| Unit | `deployment.py` | Test ACR config validation |
| Integration | API + policy engine | Test end-to-end: POST emissions -> evaluate -> return verdict |
| Container | Dockerfile | Build and run container, hit health endpoint |
| Helm | `helm/` | `helm lint` and `helm template` validation |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| ACR credentials not configured | High | Medium | Document setup; workflow fails gracefully with clear error |
| API exposes policy internals | Medium | Medium | Read-only API; no mutation endpoints; authentication recommended |
| Container image too large | Low | Low | Multi-stage build; minimal runtime image |
| Helm chart incompatible with cluster version | Low | Medium | Test against AKS 1.28+ |

## 7. Dependencies

- [ ] ACR credentials (secrets) must be configured in GitHub repo settings (blocking for CI)
- [ ] AKS cluster for deployment testing (non-blocking; Helm can be linted without cluster)
- [x] Policy engine exists (`governance/engine/policy_engine.py`) (non-blocking)
- [x] Deployment phase support exists (`deployment.py`) (non-blocking)

## 8. Backward Compatibility

Fully backward compatible. New files only. The REST API and Docker packaging are additive distribution methods. Submodule-based consumption is unchanged.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New API code |
| security-review | Yes | Container security, API exposure, ACR credentials |
| threat-modeling | Yes | New attack surface (REST API) |
| cost-analysis | Yes | ACR storage, AKS compute costs |
| architecture-review | Yes | New deployment architecture |

**Policy Profile:** infrastructure_critical
**Expected Risk Level:** high (new deployment surface, container security)

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-03-02 | Azure Container Registry (ACR), not GHCR | Org standard; native AKS integration |
| 2026-03-02 | FastAPI for REST API | Lightweight, async, auto-docs (Swagger), Python-native |
| 2026-03-02 | Helm chart, not raw Kubernetes manifests | Standard for AKS deployments; configurable values |
| 2026-03-02 | GitHub Action wraps container | Allows marketplace distribution without requiring submodule |
