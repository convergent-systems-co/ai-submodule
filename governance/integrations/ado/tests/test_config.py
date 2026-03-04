"""Tests for ADO configuration loading."""

import pytest

from governance.integrations.ado._exceptions import AdoConfigError
from governance.integrations.ado._types import AuthMethod
from governance.integrations.ado.config import AdoConfig, load_config


class TestAdoConfig:
    def test_base_url(self):
        cfg = AdoConfig(organization="myorg")
        assert cfg.base_url == "https://dev.azure.com/myorg"

    def test_defaults(self):
        cfg = AdoConfig(organization="org")
        assert cfg.default_project == ""
        assert cfg.auth_method == AuthMethod.PAT
        assert cfg.api_version == "7.1"
        assert cfg.max_retries == 5
        assert cfg.timeout == 30.0

    def test_frozen(self):
        cfg = AdoConfig(organization="org")
        with pytest.raises(AttributeError):
            cfg.organization = "other"


class TestLoadConfig:
    def test_minimal(self):
        cfg = load_config({"organization": "myorg"})
        assert cfg.organization == "myorg"
        assert cfg.auth_method == AuthMethod.PAT

    def test_full(self):
        cfg = load_config({
            "organization": "org",
            "default_project": "proj",
            "auth_method": "service_principal",
            "api_version": "7.0",
            "max_retries": 3,
            "timeout": 60.0,
        })
        assert cfg.organization == "org"
        assert cfg.default_project == "proj"
        assert cfg.auth_method == AuthMethod.SERVICE_PRINCIPAL
        assert cfg.api_version == "7.0"
        assert cfg.max_retries == 3
        assert cfg.timeout == 60.0

    def test_missing_organization(self):
        with pytest.raises(AdoConfigError, match="organization is required"):
            load_config({})

    def test_not_a_dict(self):
        with pytest.raises(AdoConfigError, match="must be a dictionary"):
            load_config("not a dict")

    def test_invalid_auth_method(self):
        with pytest.raises(AdoConfigError, match="Invalid auth_method"):
            load_config({"organization": "org", "auth_method": "invalid"})
