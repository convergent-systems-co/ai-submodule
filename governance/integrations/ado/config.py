"""Configuration for the Azure DevOps client."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

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


def validate_config_schema(data: dict) -> dict:
    """Validate an ADO config dict against the ado-integration JSON Schema.

    Args:
        data: A dict representing the ado_integration configuration
              (the section contents, not the full project.yaml).

    Returns:
        A dict with keys:
        - ``valid`` (bool): Whether validation passed.
        - ``errors`` (list[str]): List of validation error messages (empty if valid).

    Raises:
        AdoConfigError: If the schema file cannot be found or loaded.
    """
    try:
        from jsonschema import validate as jschema_validate, ValidationError
    except ImportError:
        raise AdoConfigError(
            "jsonschema package is required for schema validation. "
            "Install it with: pip install jsonschema"
        )

    schema_path = (
        Path(__file__).resolve().parent.parent.parent
        / "schemas"
        / "ado-integration.schema.json"
    )
    if not schema_path.exists():
        raise AdoConfigError(f"ADO integration schema not found at {schema_path}")

    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        raise AdoConfigError(f"Failed to load ADO integration schema: {e}")

    result: dict = {"valid": True, "errors": []}
    try:
        jschema_validate(instance=data, schema=schema)
    except ValidationError as e:
        result["valid"] = False
        result["errors"].append(e.message)

    return result


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
