"""FastAPI application — Governance-as-a-Service REST API.

Entry point for the governance service container. Exposes the policy
engine as an HTTP API for CI integrations and container-based evaluation.

Run locally:
    uvicorn governance.engine.api.app:app --reload --port 8080

Or via Docker:
    docker run -p 8080:8080 governance-service
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from governance.engine.api.routes import router

app = FastAPI(
    title="Dark Forge API",
    description=(
        "REST API for the Dark Forge policy engine. "
        "Evaluate panel emissions, validate schemas, and query policy profiles."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for CI integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure per deployment
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint — redirect to docs."""
    return {
        "service": "Dark Forge API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
