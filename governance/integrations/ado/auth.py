"""Authentication providers for the Azure DevOps client."""

from __future__ import annotations

import base64
import os
from abc import ABC, abstractmethod

from governance.integrations.ado._exceptions import AdoAuthError, AdoConfigError
from governance.integrations.ado._types import AuthMethod


class AuthProvider(ABC):
    """Abstract base class for ADO authentication strategies."""

    @abstractmethod
    def get_auth_header(self) -> str:
        """Return the Authorization header value."""


class PatAuth(AuthProvider):
    """Personal Access Token authentication (Basic auth)."""

    def __init__(self, pat: str) -> None:
        if not pat:
            raise AdoConfigError("PAT cannot be empty")
        self._pat = pat

    def get_auth_header(self) -> str:
        encoded = base64.b64encode(f":{self._pat}".encode()).decode()
        return f"Basic {encoded}"


class ServicePrincipalAuth(AuthProvider):
    """Entra ID (Azure AD) Service Principal authentication.

    Lazily imports azure-identity — only required when this provider is used.
    """

    def __init__(
        self,
        tenant_id: str,
        client_id: str,
        client_secret: str,
    ) -> None:
        if not all([tenant_id, client_id, client_secret]):
            raise AdoConfigError(
                "Service principal requires tenant_id, client_id, and client_secret"
            )
        self._tenant_id = tenant_id
        self._client_id = client_id
        self._client_secret = client_secret
        self._credential = None

    def _get_credential(self):
        if self._credential is None:
            try:
                from azure.identity import ClientSecretCredential
            except ImportError:
                raise AdoConfigError(
                    "azure-identity is required for service_principal auth. "
                    "Install with: pip install azure-identity>=1.15.0"
                )
            self._credential = ClientSecretCredential(
                tenant_id=self._tenant_id,
                client_id=self._client_id,
                client_secret=self._client_secret,
            )
        return self._credential

    def get_auth_header(self) -> str:
        credential = self._get_credential()
        try:
            token = credential.get_token("499b84ac-1321-427f-aa17-267ca6975798/.default")
        except Exception as exc:
            raise AdoAuthError(f"Failed to acquire token: {exc}")
        return f"Bearer {token.token}"


class ManagedIdentityAuth(AuthProvider):
    """Azure Managed Identity authentication.

    Lazily imports azure-identity — only required when this provider is used.
    """

    def __init__(self, client_id: str | None = None) -> None:
        self._client_id = client_id
        self._credential = None

    def _get_credential(self):
        if self._credential is None:
            try:
                from azure.identity import DefaultAzureCredential
            except ImportError:
                raise AdoConfigError(
                    "azure-identity is required for managed_identity auth. "
                    "Install with: pip install azure-identity>=1.15.0"
                )
            kwargs = {}
            if self._client_id:
                kwargs["managed_identity_client_id"] = self._client_id
            self._credential = DefaultAzureCredential(**kwargs)
        return self._credential

    def get_auth_header(self) -> str:
        credential = self._get_credential()
        try:
            token = credential.get_token("499b84ac-1321-427f-aa17-267ca6975798/.default")
        except Exception as exc:
            raise AdoAuthError(f"Failed to acquire token: {exc}")
        return f"Bearer {token.token}"


def create_auth_provider(
    method: AuthMethod | str,
    *,
    pat: str | None = None,
    tenant_id: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
) -> AuthProvider:
    """Factory to create the appropriate auth provider.

    Falls back to environment variables when explicit values are not provided:
    - PAT: ADO_PAT
    - Service Principal: AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
    - Managed Identity: AZURE_CLIENT_ID (optional)
    """
    if isinstance(method, str):
        try:
            method = AuthMethod(method)
        except ValueError:
            valid = ", ".join(m.value for m in AuthMethod)
            raise AdoConfigError(f"Invalid auth method '{method}'. Valid: {valid}")

    if method == AuthMethod.PAT:
        resolved_pat = pat or os.environ.get("ADO_PAT", "")
        if not resolved_pat:
            raise AdoConfigError(
                "PAT auth requires a token. Pass pat= or set ADO_PAT env var."
            )
        return PatAuth(resolved_pat)

    if method == AuthMethod.SERVICE_PRINCIPAL:
        return ServicePrincipalAuth(
            tenant_id=tenant_id or os.environ.get("AZURE_TENANT_ID", ""),
            client_id=client_id or os.environ.get("AZURE_CLIENT_ID", ""),
            client_secret=client_secret or os.environ.get("AZURE_CLIENT_SECRET", ""),
        )

    if method == AuthMethod.MANAGED_IDENTITY:
        return ManagedIdentityAuth(
            client_id=client_id or os.environ.get("AZURE_CLIENT_ID"),
        )

    raise AdoConfigError(f"Unsupported auth method: {method}")
