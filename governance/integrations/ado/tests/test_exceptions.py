"""Tests for the ADO exception hierarchy."""

from governance.integrations.ado._exceptions import (
    AdoAuthError,
    AdoConfigError,
    AdoError,
    AdoNotFoundError,
    AdoRateLimitError,
    AdoServerError,
    AdoValidationError,
)


class TestAdoError:
    def test_base_error_message(self):
        err = AdoError("something failed")
        assert str(err) == "something failed"
        assert err.status_code is None
        assert err.response_body is None

    def test_base_error_with_status(self):
        err = AdoError("bad", status_code=500, response_body={"detail": "x"})
        assert err.status_code == 500
        assert err.response_body == {"detail": "x"}

    def test_hierarchy(self):
        assert issubclass(AdoAuthError, AdoError)
        assert issubclass(AdoNotFoundError, AdoError)
        assert issubclass(AdoRateLimitError, AdoError)
        assert issubclass(AdoValidationError, AdoError)
        assert issubclass(AdoServerError, AdoError)
        assert issubclass(AdoConfigError, AdoError)


class TestAdoRateLimitError:
    def test_retry_after_seconds(self):
        err = AdoRateLimitError("slow down", retry_after_seconds=30.0)
        assert err.retry_after_seconds == 30.0
        assert err.status_code == 429

    def test_no_retry_after(self):
        err = AdoRateLimitError("slow down")
        assert err.retry_after_seconds is None
