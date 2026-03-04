# Dockerfile — Governance-as-a-Service container
# Packages the policy engine + orchestrator as a deployable REST API service.
#
# Build:
#   docker build -t governance-service .
#
# Run:
#   docker run -p 8080:8080 governance-service
#
# Published to Azure Container Registry (ACR), NOT GHCR or Google.

# --- Stage 1: Build ---
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN pip install --no-cache-dir --upgrade pip

# Copy pyproject.toml first for better caching (requirements.txt does not exist)
COPY governance/engine/pyproject.toml ./governance/engine/pyproject.toml
RUN pip install --no-cache-dir --prefix=/install \
    jsonschema>=4.0 \
    pyyaml>=6.0 \
    fastapi==0.115.* \
    uvicorn[standard]==0.34.* \
    pydantic==2.*

# --- Stage 2: Runtime ---
FROM python:3.11-slim AS runtime

WORKDIR /app

# Security: run as non-root
RUN groupadd -r governance && useradd -r -g governance governance

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy governance engine
COPY governance/engine/ ./governance/engine/
COPY governance/policy/ ./governance/policy/
COPY governance/schemas/ ./governance/schemas/
COPY governance/bin/policy-engine.py ./governance/bin/policy-engine.py

# Copy API module
COPY governance/engine/api/ ./governance/engine/api/

# Ensure Python can find our modules
ENV PYTHONPATH=/app
ENV PORT=8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/v1/health')" || exit 1

# Switch to non-root user
USER governance

EXPOSE 8080

ENTRYPOINT ["uvicorn", "governance.engine.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
