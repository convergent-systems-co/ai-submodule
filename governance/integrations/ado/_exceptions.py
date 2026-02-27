"""Exception hierarchy for the Azure DevOps client."""

from __future__ import annotations

from typing import Any


class AdoError(Exception):
    """Base exception for all ADO client errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_body: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class AdoAuthError(AdoError):
    """Authentication or authorization failure (401/403)."""


class AdoNotFoundError(AdoError):
    """Resource not found (404)."""


class AdoRateLimitError(AdoError):
    """Rate limit exceeded (429). Check retry_after_seconds."""

    def __init__(
        self,
        message: str,
        retry_after_seconds: float | None = None,
        status_code: int | None = 429,
        response_body: Any = None,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body)
        self.retry_after_seconds = retry_after_seconds


class AdoValidationError(AdoError):
    """Request validation failure (400)."""


class AdoServerError(AdoError):
    """Server-side error (5xx)."""


class AdoConfigError(AdoError):
    """Configuration error — missing or invalid settings."""
