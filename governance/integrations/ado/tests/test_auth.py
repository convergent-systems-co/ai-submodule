"""Tests for ADO authentication providers."""

from __future__ import annotations

import base64
import os
from unittest.mock import MagicMock, patch

import pytest

from governance.integrations.ado._exceptions import AdoAuthError, AdoConfigError
from governance.integrations.ado._types import AuthMethod
from governance.integrations.ado.auth import (
    ManagedIdentityAuth,
    PatAuth,
    ServicePrincipalAuth,
    create_auth_provider,
)


class TestPatAuth:
    def test_basic_header(self):
        auth = PatAuth("my-token")
        header = auth.get_auth_header()
        expected = base64.b64encode(b":my-token").decode()
        assert header == f"Basic {expected}"

    def test_empty_pat_raises(self):
        with pytest.raises(AdoConfigError, match="PAT cannot be empty"):
            PatAuth("")


class TestServicePrincipalAuth:
    def test_missing_fields_raises(self):
        with pytest.raises(AdoConfigError, match="tenant_id, client_id, and client_secret"):
            ServicePrincipalAuth("", "client", "secret")

    def test_lazy_import_failure(self):
        auth = ServicePrincipalAuth("tenant", "client", "secret")
        with patch.dict("sys.modules", {"azure": None, "azure.identity": None}):
            with pytest.raises(AdoConfigError, match="azure-identity is required"):
                auth.get_auth_header()

    def test_token_acquisition_failure(self):
        auth = ServicePrincipalAuth("tenant", "client", "secret")
        mock_cred = MagicMock()
        mock_cred.get_token.side_effect = Exception("token error")
        auth._credential = mock_cred
        with pytest.raises(AdoAuthError, match="Failed to acquire token"):
            auth.get_auth_header()

    def test_successful_token(self):
        auth = ServicePrincipalAuth("tenant", "client", "secret")
        mock_cred = MagicMock()
        mock_token = MagicMock()
        mock_token.token = "bearer-token-value"
        mock_cred.get_token.return_value = mock_token
        auth._credential = mock_cred
        header = auth.get_auth_header()
        assert header == "Bearer bearer-token-value"


class TestManagedIdentityAuth:
    def test_lazy_import_failure(self):
        auth = ManagedIdentityAuth()
        with patch.dict("sys.modules", {"azure": None, "azure.identity": None}):
            with pytest.raises(AdoConfigError, match="azure-identity is required"):
                auth.get_auth_header()

    def test_successful_token(self):
        auth = ManagedIdentityAuth()
        mock_cred = MagicMock()
        mock_token = MagicMock()
        mock_token.token = "mi-token"
        mock_cred.get_token.return_value = mock_token
        auth._credential = mock_cred
        assert auth.get_auth_header() == "Bearer mi-token"


class TestCreateAuthProvider:
    def test_pat_from_arg(self):
        provider = create_auth_provider(AuthMethod.PAT, pat="tok")
        assert isinstance(provider, PatAuth)

    def test_pat_from_env(self):
        with patch.dict(os.environ, {"ADO_PAT": "env-tok"}):
            provider = create_auth_provider("pat")
            assert isinstance(provider, PatAuth)

    def test_pat_missing_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            # Ensure ADO_PAT is not set
            os.environ.pop("ADO_PAT", None)
            with pytest.raises(AdoConfigError, match="PAT auth requires"):
                create_auth_provider("pat")

    def test_service_principal_from_env(self):
        env = {
            "AZURE_TENANT_ID": "t",
            "AZURE_CLIENT_ID": "c",
            "AZURE_CLIENT_SECRET": "s",
        }
        with patch.dict(os.environ, env):
            provider = create_auth_provider("service_principal")
            assert isinstance(provider, ServicePrincipalAuth)

    def test_managed_identity(self):
        provider = create_auth_provider("managed_identity")
        assert isinstance(provider, ManagedIdentityAuth)

    def test_invalid_method_string(self):
        with pytest.raises(AdoConfigError, match="Invalid auth method"):
            create_auth_provider("invalid_method")

    def test_string_method_accepted(self):
        provider = create_auth_provider("pat", pat="tok")
        assert isinstance(provider, PatAuth)
