"""Configuration for the Azure DevOps client."""

from __future__ import annotations

from dataclasses import dataclass

from governance.integrations.ado._exceptions import AdoConfigError
from governance.integrations.ado._types import AccessMethod, AuthMethod


@dataclass(frozen=True)
class AdoConfig:
    """ADO client configuration, typically loaded from project.yaml."""

    organization: str
    default_project: str = ""
    access_method: AccessMethod = AccessMethod.API
    auth_method: AuthMethod = AuthMethod.PAT
    api_version: str = "7.1"
    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 30.0
    timeout: float = 30.0

    @property
    def base_url(self) -> str:
        return f"https://dev.azure.com/{self.organization}"


def load_config(data: dict) -> AdoConfig:
    """Create an AdoConfig from a project.yaml ado_integration section.

    Args:
        data: The ado_integration dict from project.yaml.

    Returns:
        A frozen AdoConfig instance.

    Raises:
        AdoConfigError: If required fields are missing or invalid.
    """
    if not isinstance(data, dict):
        raise AdoConfigError("ado_integration must be a dictionary")

    organization = data.get("organization")
    if not organization:
        raise AdoConfigError("ado_integration.organization is required")

    access_method_str = data.get("access_method", "api")
    try:
        access_method = AccessMethod(access_method_str)
    except ValueError:
        valid = ", ".join(m.value for m in AccessMethod)
        raise AdoConfigError(
            f"Invalid access_method '{access_method_str}'. Valid: {valid}"
        )

    auth_method_str = data.get("auth_method", "pat")
    try:
        auth_method = AuthMethod(auth_method_str)
    except ValueError:
        valid = ", ".join(m.value for m in AuthMethod)
        raise AdoConfigError(
            f"Invalid auth_method '{auth_method_str}'. Valid: {valid}"
        )

    return AdoConfig(
        organization=organization,
        default_project=data.get("default_project", ""),
        access_method=access_method,
        auth_method=auth_method,
        api_version=data.get("api_version", "7.1"),
        max_retries=data.get("max_retries", 5),
        timeout=data.get("timeout", 30.0),
    )
