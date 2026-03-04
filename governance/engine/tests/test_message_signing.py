"""Tests for governance.engine.message_signing — cryptographic protocol message signing."""

import pytest

from governance.engine.message_signing import (
    InvalidSignatureError,
    MessageSigner,
    MissingSignatureError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def signer():
    return MessageSigner(session_secret="test-session-secret-2026")


@pytest.fixture
def sample_message():
    return {
        "message_type": "APPROVE",
        "source_agent": "test-evaluator",
        "target_agent": "tech-lead",
        "correlation_id": "issue-42",
        "payload": {
            "summary": "All tests pass",
            "test_gate_passed": True,
            "files_reviewed": ["src/main.py"],
            "acceptance_criteria_met": [{"criterion": "tests pass", "met": True}],
            "coverage_percentage": 94.5,
            "conditions": [],
        },
    }


@pytest.fixture
def assign_message():
    return {
        "message_type": "ASSIGN",
        "source_agent": "tech-lead",
        "target_agent": "coder",
        "correlation_id": "issue-100",
        "payload": {
            "task": "Implement feature X",
            "context": {"issue_number": 100},
            "constraints": {"plan": ".artifacts/plans/100-feature-x.md"},
            "priority": "P1",
        },
    }


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------

class TestSigning:
    def test_sign_adds_signature(self, signer, sample_message):
        signed = signer.sign(sample_message, persona="test-evaluator")
        assert "signature" in signed
        assert isinstance(signed["signature"], str)
        assert len(signed["signature"]) == 64  # SHA256 hex = 64 chars

    def test_sign_preserves_original(self, signer, sample_message):
        signed = signer.sign(sample_message, persona="test-evaluator")
        # Original should not have signature
        assert "signature" not in sample_message
        # Signed should have all original fields
        for key in sample_message:
            assert signed[key] == sample_message[key]

    def test_sign_different_personas_different_sigs(self, signer):
        msg1 = {
            "message_type": "STATUS",
            "source_agent": "coder",
            "target_agent": "tech-lead",
            "correlation_id": "issue-1",
            "payload": {"phase": "implementing"},
        }
        msg2 = {
            "message_type": "STATUS",
            "source_agent": "iac-engineer",
            "target_agent": "tech-lead",
            "correlation_id": "issue-1",
            "payload": {"phase": "implementing"},
        }
        sig1 = signer.sign(msg1, persona="coder")["signature"]
        sig2 = signer.sign(msg2, persona="iac-engineer")["signature"]
        assert sig1 != sig2

    def test_sign_deterministic(self, signer, sample_message):
        sig1 = signer.sign(sample_message, persona="test-evaluator")["signature"]
        sig2 = signer.sign(sample_message, persona="test-evaluator")["signature"]
        assert sig1 == sig2

    def test_sign_invalid_persona_raises(self, signer, sample_message):
        with pytest.raises(ValueError, match="Unknown persona"):
            signer.sign(sample_message, persona="hacker")

    def test_sign_mismatched_persona_raises(self, signer, sample_message):
        # source_agent is "test-evaluator", but trying to sign as "coder"
        with pytest.raises(ValueError, match="cannot sign"):
            signer.sign(sample_message, persona="coder")

    def test_sign_all_message_types(self, signer):
        for msg_type in ["ASSIGN", "STATUS", "RESULT", "FEEDBACK", "ESCALATE",
                         "APPROVE", "BLOCK", "CANCEL", "WATCH"]:
            msg = {
                "message_type": msg_type,
                "source_agent": "tech-lead",
                "target_agent": "coder",
                "correlation_id": "issue-1",
                "payload": {},
            }
            signed = signer.sign(msg, persona="tech-lead")
            assert "signature" in signed


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

class TestVerification:
    def test_verify_valid_signature(self, signer, sample_message):
        signed = signer.sign(sample_message, persona="test-evaluator")
        assert signer.verify(signed) is True

    def test_verify_with_explicit_persona(self, signer, sample_message):
        signed = signer.sign(sample_message, persona="test-evaluator")
        assert signer.verify(signed, expected_persona="test-evaluator") is True

    def test_verify_wrong_persona_fails(self, signer, sample_message):
        signed = signer.sign(sample_message, persona="test-evaluator")
        with pytest.raises(InvalidSignatureError):
            signer.verify(signed, expected_persona="coder")

    def test_verify_missing_signature_raises(self, signer, sample_message):
        with pytest.raises(MissingSignatureError):
            signer.verify(sample_message)

    def test_verify_tampered_payload_fails(self, signer, sample_message):
        signed = signer.sign(sample_message, persona="test-evaluator")
        signed["payload"]["test_gate_passed"] = False
        with pytest.raises(InvalidSignatureError):
            signer.verify(signed)

    def test_verify_tampered_message_type_fails(self, signer, sample_message):
        signed = signer.sign(sample_message, persona="test-evaluator")
        signed["message_type"] = "BLOCK"
        with pytest.raises(InvalidSignatureError):
            signer.verify(signed)

    def test_verify_tampered_source_agent_fails(self, signer, sample_message):
        signed = signer.sign(sample_message, persona="test-evaluator")
        # Change source_agent but keep the test-evaluator signature
        signed["source_agent"] = "coder"
        with pytest.raises(InvalidSignatureError):
            signer.verify(signed)


# ---------------------------------------------------------------------------
# is_valid (non-throwing)
# ---------------------------------------------------------------------------

class TestIsValid:
    def test_valid_message(self, signer, sample_message):
        signed = signer.sign(sample_message, persona="test-evaluator")
        assert signer.is_valid(signed) is True

    def test_unsigned_message(self, signer, sample_message):
        assert signer.is_valid(sample_message) is False

    def test_tampered_message(self, signer, sample_message):
        signed = signer.sign(sample_message, persona="test-evaluator")
        signed["payload"]["test_gate_passed"] = False
        assert signer.is_valid(signed) is False

    def test_wrong_persona(self, signer, sample_message):
        signed = signer.sign(sample_message, persona="test-evaluator")
        assert signer.is_valid(signed, expected_persona="coder") is False


# ---------------------------------------------------------------------------
# Key derivation
# ---------------------------------------------------------------------------

class TestKeyDerivation:
    def test_different_sessions_different_keys(self, sample_message):
        signer1 = MessageSigner(session_secret="secret-1")
        signer2 = MessageSigner(session_secret="secret-2")
        sig1 = signer1.sign(sample_message, persona="test-evaluator")["signature"]
        sig2 = signer2.sign(sample_message, persona="test-evaluator")["signature"]
        assert sig1 != sig2

    def test_all_personas_have_unique_keys(self, signer):
        # Verify each persona derives a different key
        personas = ["project-manager", "devops-engineer", "tech-lead",
                     "coder", "iac-engineer", "test-writer",
                     "test-evaluator", "document-writer", "documentation-reviewer"]
        keys = set()
        for p in personas:
            key = signer._derive_key(p)
            keys.add(key)
        assert len(keys) == len(personas)

    def test_invalid_persona_key_derivation_raises(self, signer):
        with pytest.raises(ValueError, match="Unknown persona"):
            signer._derive_key("unknown-agent")


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_session_secret_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            MessageSigner(session_secret="")

    def test_sign_assign_message(self, signer, assign_message):
        signed = signer.sign(assign_message, persona="tech-lead")
        assert signer.verify(signed) is True

    def test_sign_message_without_source_agent(self, signer):
        # Message without source_agent — persona param is authoritative
        msg = {
            "message_type": "STATUS",
            "source_agent": "coder",
            "target_agent": "tech-lead",
            "correlation_id": "issue-1",
            "payload": {},
        }
        signed = signer.sign(msg, persona="coder")
        assert signer.verify(signed, expected_persona="coder") is True

    def test_signature_not_in_canonical_form(self, signer, sample_message):
        """Ensure existing signature doesn't affect re-signing."""
        signed = signer.sign(sample_message, persona="test-evaluator")
        # Re-signing should produce the same signature
        re_signed = signer.sign(signed, persona="test-evaluator")
        assert re_signed["signature"] == signed["signature"]
