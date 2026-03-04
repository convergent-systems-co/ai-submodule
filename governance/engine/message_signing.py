#!/usr/bin/env python3
"""Cryptographic signing for inter-agent protocol messages.

Adds HMAC-SHA256 signatures to all agent protocol messages to prevent
protocol spoofing. Each persona derives its own signing key from a
shared session secret, ensuring messages can be attributed to their
claimed source.

Usage:
    from governance.engine.message_signing import MessageSigner

    signer = MessageSigner(session_secret="random-secret-per-session")
    signed = signer.sign(message, persona="test-evaluator")
    is_valid = signer.verify(signed, expected_persona="test-evaluator")
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


# Valid persona names for key derivation
VALID_PERSONAS = frozenset({
    "project-manager",
    "devops-engineer",
    "tech-lead",
    "coder",
    "iac-engineer",
    "test-writer",
    "test-evaluator",
    "document-writer",
    "documentation-reviewer",
})

# Valid message types per the agent protocol
VALID_MESSAGE_TYPES = frozenset({
    "ASSIGN", "STATUS", "RESULT", "FEEDBACK",
    "ESCALATE", "APPROVE", "BLOCK", "CANCEL", "WATCH",
})


class MessageSigningError(Exception):
    """Base exception for message signing errors."""
    pass


class InvalidSignatureError(MessageSigningError):
    """Raised when a message signature is invalid."""
    pass


class MissingSignatureError(MessageSigningError):
    """Raised when a message is missing its signature."""
    pass


class MessageSigner:
    """HMAC-SHA256 message signer for inter-agent protocol messages.

    Derives per-persona keys from a session secret to ensure messages
    can only be signed by the claimed source persona.

    Args:
        session_secret: A random secret generated at session start.
                       Should be unique per session for forward secrecy.
    """

    def __init__(self, session_secret: str):
        if not session_secret:
            raise ValueError("session_secret must not be empty")
        self._session_secret = session_secret.encode("utf-8")

    def _derive_key(self, persona: str) -> bytes:
        """Derive a per-persona signing key from the session secret.

        Uses HMAC-SHA256 with the persona name as the message to derive
        a unique key for each persona from the shared session secret.
        """
        if persona not in VALID_PERSONAS:
            raise ValueError(f"Unknown persona: {persona}")
        return hmac.new(
            self._session_secret,
            persona.encode("utf-8"),
            hashlib.sha256,
        ).digest()

    def _canonicalize(self, message: dict[str, Any]) -> bytes:
        """Produce a canonical byte representation of a message for signing.

        Removes the signature field if present, then serializes with
        sorted keys and no whitespace for deterministic output.
        """
        msg_copy = {k: v for k, v in message.items() if k != "signature"}
        return json.dumps(msg_copy, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def sign(self, message: dict[str, Any], persona: str) -> dict[str, Any]:
        """Sign a protocol message with the persona's derived key.

        Args:
            message: The protocol message dict (must contain message_type,
                    source_agent, target_agent, correlation_id, payload).
            persona: The persona signing the message (must match source_agent).

        Returns:
            A copy of the message with a 'signature' field added.

        Raises:
            ValueError: If persona is invalid or doesn't match source_agent.
        """
        if persona not in VALID_PERSONAS:
            raise ValueError(f"Unknown persona: {persona}")

        source = message.get("source_agent", "")
        if source and source != persona:
            raise ValueError(
                f"Persona '{persona}' cannot sign a message from '{source}'"
            )

        key = self._derive_key(persona)
        canonical = self._canonicalize(message)
        sig = hmac.new(key, canonical, hashlib.sha256).hexdigest()

        signed = dict(message)
        signed["signature"] = sig
        return signed

    def verify(
        self,
        message: dict[str, Any],
        expected_persona: str | None = None,
    ) -> bool:
        """Verify a signed protocol message.

        Args:
            message: The signed message dict (must contain 'signature').
            expected_persona: If provided, verify against this persona's key.
                            If None, uses the message's source_agent field.

        Returns:
            True if the signature is valid.

        Raises:
            MissingSignatureError: If the message has no signature.
            InvalidSignatureError: If the signature is invalid.
        """
        sig = message.get("signature")
        if not sig:
            raise MissingSignatureError("Message has no signature field")

        persona = expected_persona or message.get("source_agent", "")
        if persona not in VALID_PERSONAS:
            raise InvalidSignatureError(f"Unknown persona: {persona}")

        key = self._derive_key(persona)
        canonical = self._canonicalize(message)
        expected_sig = hmac.new(key, canonical, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(sig, expected_sig):
            raise InvalidSignatureError(
                f"Signature verification failed for message from '{persona}'"
            )
        return True

    def is_valid(
        self,
        message: dict[str, Any],
        expected_persona: str | None = None,
    ) -> bool:
        """Check if a signed message is valid without raising exceptions.

        Returns:
            True if valid, False otherwise.
        """
        try:
            return self.verify(message, expected_persona)
        except MessageSigningError:
            return False
