"""Tests for governance.engine.envelope — context boundary enforcement."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from governance.engine.envelope import (
    VALID_MESSAGE_TYPES,
    VALID_PERSONAS,
    VALID_TRANSITIONS,
    EnvelopeBuilder,
    EnvelopeValidationResult,
    EnvelopeViolation,
    load_boundaries,
    strip_unauthorized_context,
    validate_envelope,
)
from governance.engine.message_signing import MessageSigner

# Repo root for loading real boundary files
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def boundaries():
    """Load the real agent context boundaries spec."""
    return load_boundaries(REPO_ROOT)


@pytest.fixture
def signer():
    """Create a MessageSigner with a test session secret."""
    return MessageSigner(session_secret="test-session-secret-751")


@pytest.fixture
def builder(boundaries, signer):
    """Create an EnvelopeBuilder with real boundaries and a signer."""
    return EnvelopeBuilder(boundaries=boundaries, signer=signer, repo_root=REPO_ROOT)


@pytest.fixture
def builder_no_sign(boundaries):
    """Create an EnvelopeBuilder without signing."""
    return EnvelopeBuilder(boundaries=boundaries, repo_root=REPO_ROOT)


# ---------------------------------------------------------------------------
# Boundary spec loading
# ---------------------------------------------------------------------------


class TestLoadBoundaries:
    def test_load_from_repo_root(self):
        b = load_boundaries(REPO_ROOT)
        assert "boundaries" in b
        assert "schema_version" in b

    def test_all_personas_defined(self, boundaries):
        boundary_map = boundaries["boundaries"]
        for persona in VALID_PERSONAS:
            assert persona in boundary_map, f"Missing boundary for persona: {persona}"

    def test_each_persona_has_receives(self, boundaries):
        for persona, spec in boundaries["boundaries"].items():
            assert "receives" in spec, f"Persona {persona} missing receives"
            assert len(spec["receives"]) > 0, f"Persona {persona} has empty receives"

    def test_each_persona_has_never_receives(self, boundaries):
        for persona, spec in boundaries["boundaries"].items():
            assert "never_receives" in spec, f"Persona {persona} missing never_receives"
            assert len(spec["never_receives"]) > 0, f"Persona {persona} has empty never_receives"

    def test_each_persona_has_persona_definition(self, boundaries):
        for persona, spec in boundaries["boundaries"].items():
            has_persona_def = any(
                entry.get("type") == "persona_definition"
                for entry in spec["receives"]
            )
            assert has_persona_def, f"Persona {persona} missing persona_definition in receives"

    def test_each_persona_has_protocol_messages(self, boundaries):
        for persona, spec in boundaries["boundaries"].items():
            has_protocol = any(
                entry.get("type") == "protocol_messages"
                for entry in spec["receives"]
            )
            assert has_protocol, f"Persona {persona} missing protocol_messages in receives"

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_boundaries(tmp_path)


# ---------------------------------------------------------------------------
# Envelope building
# ---------------------------------------------------------------------------


class TestEnvelopeBuilder:
    def test_build_basic_envelope(self, builder):
        envelope = builder.build(
            source="tech-lead",
            target="coder",
            message_type="ASSIGN",
            payload={"task": "Implement feature"},
            correlation_id="issue-42",
            session_id="session-1",
            sender_task_id="task-tl-1",
        )

        assert envelope["envelope"]["version"] == "1.0"
        assert envelope["envelope"]["source_agent"] == "tech-lead"
        assert envelope["envelope"]["target_agent"] == "coder"
        assert envelope["envelope"]["correlation_id"] == "issue-42"
        assert envelope["envelope"]["session_id"] == "session-1"
        assert envelope["envelope"]["message_id"].startswith("msg-")
        assert envelope["protocol_message"]["message_type"] == "ASSIGN"
        assert envelope["protocol_message"]["payload"]["task"] == "Implement feature"

    def test_build_with_attachments(self, builder):
        envelope = builder.build(
            source="tech-lead",
            target="coder",
            message_type="ASSIGN",
            payload={"task": "Implement"},
            correlation_id="issue-42",
            session_id="session-1",
            attachments=[
                {"type": "plan", "path": ".artifacts/plans/42-feature.md"},
            ],
        )

        assert len(envelope["context_attachments"]) == 1
        att = envelope["context_attachments"][0]
        assert att["type"] == "plan"
        assert att["path"] == ".artifacts/plans/42-feature.md"
        assert att["hash"].startswith("sha256:")

    def test_build_with_constraints(self, builder):
        envelope = builder.build(
            source="tech-lead",
            target="coder",
            message_type="ASSIGN",
            payload={"task": "Implement"},
            correlation_id="issue-42",
            session_id="session-1",
            constraints={"timeout_seconds": 600},
        )

        assert envelope["protocol_message"]["constraints"]["timeout_seconds"] == 600

    def test_build_with_signing(self, builder):
        envelope = builder.build(
            source="tech-lead",
            target="coder",
            message_type="ASSIGN",
            payload={"task": "Implement"},
            correlation_id="issue-42",
            session_id="session-1",
            sender_task_id="task-tl-1",
        )

        assert "signature" in envelope["authentication"]
        assert len(envelope["authentication"]["signature"]) == 64  # hex SHA-256

    def test_build_without_signing(self, builder_no_sign):
        envelope = builder_no_sign.build(
            source="tech-lead",
            target="coder",
            message_type="ASSIGN",
            payload={"task": "Implement"},
            correlation_id="issue-42",
            session_id="session-1",
        )

        assert "signature" not in envelope["authentication"]

    def test_build_sets_persona_path(self, builder):
        envelope = builder.build(
            source="tech-lead",
            target="coder",
            message_type="ASSIGN",
            payload={"task": "Implement"},
            correlation_id="issue-42",
            session_id="session-1",
        )

        assert envelope["persona"] == "governance/personas/agentic/coder.md"

    def test_build_parent_message_id(self, builder):
        envelope = builder.build(
            source="tech-lead",
            target="coder",
            message_type="ASSIGN",
            payload={"task": "Implement"},
            correlation_id="issue-42",
            session_id="session-1",
            parent_message_id="msg-parent-123",
        )

        assert envelope["authentication"]["parent_message_id"] == "msg-parent-123"

    def test_invalid_source_raises(self, builder):
        with pytest.raises(ValueError, match="Invalid source persona"):
            builder.build(
                source="invalid-persona",
                target="coder",
                message_type="ASSIGN",
                payload={},
                correlation_id="issue-1",
                session_id="s-1",
            )

    def test_invalid_target_raises(self, builder):
        with pytest.raises(ValueError, match="Invalid target persona"):
            builder.build(
                source="tech-lead",
                target="invalid-persona",
                message_type="ASSIGN",
                payload={},
                correlation_id="issue-1",
                session_id="s-1",
            )

    def test_invalid_message_type_raises(self, builder):
        with pytest.raises(ValueError, match="Invalid message type"):
            builder.build(
                source="tech-lead",
                target="coder",
                message_type="INVALID",
                payload={},
                correlation_id="issue-1",
                session_id="s-1",
            )


# ---------------------------------------------------------------------------
# Envelope validation
# ---------------------------------------------------------------------------


class TestValidateEnvelope:
    def test_valid_assign_from_tech_lead_to_coder(self, builder, boundaries):
        envelope = builder.build(
            source="tech-lead",
            target="coder",
            message_type="ASSIGN",
            payload={"task": "Implement feature"},
            correlation_id="issue-42",
            session_id="session-1",
            attachments=[
                {"type": "plan", "path": ".artifacts/plans/42-feature.md"},
            ],
        )

        result = validate_envelope(envelope, boundaries)
        assert result.valid, f"Unexpected violations: {[v.detail for v in result.violations]}"

    def test_valid_result_from_coder_to_tech_lead(self, builder, boundaries):
        envelope = builder.build(
            source="coder",
            target="tech-lead",
            message_type="RESULT",
            payload={"summary": "Feature implemented"},
            correlation_id="issue-42",
            session_id="session-1",
        )

        result = validate_envelope(envelope, boundaries)
        assert result.valid

    def test_invalid_transition_coder_to_devops(self, builder_no_sign, boundaries):
        envelope = builder_no_sign.build(
            source="coder",
            target="devops-engineer",
            message_type="RESULT",
            payload={"summary": "Done"},
            correlation_id="issue-42",
            session_id="session-1",
        )

        result = validate_envelope(envelope, boundaries)
        assert not result.valid
        assert any(v.violation_type == "invalid_transition" for v in result.violations)

    def test_invalid_message_type_for_transition(self, builder_no_sign, boundaries):
        envelope = builder_no_sign.build(
            source="tech-lead",
            target="coder",
            message_type="APPROVE",
            payload={},
            correlation_id="issue-42",
            session_id="session-1",
        )

        result = validate_envelope(envelope, boundaries)
        assert not result.valid
        assert any("APPROVE" in v.detail for v in result.violations)

    def test_unauthorized_attachment_type(self, builder_no_sign, boundaries):
        envelope = builder_no_sign.build(
            source="tech-lead",
            target="coder",
            message_type="ASSIGN",
            payload={"task": "Implement"},
            correlation_id="issue-42",
            session_id="session-1",
            attachments=[
                {"type": "checkpoint", "path": ".artifacts/checkpoints/chk.json"},
            ],
        )

        result = validate_envelope(envelope, boundaries)
        assert not result.valid
        assert any(
            v.violation_type == "unauthorized_context"
            for v in result.violations
        )

    def test_authentication_persona_mismatch(self, boundaries):
        # Manually construct a bad envelope
        envelope = {
            "envelope": {
                "version": "1.0",
                "message_id": "msg-00000000-0000-0000-0000-000000000000",
                "timestamp": "2026-03-03T00:00:00+00:00",
                "source_agent": "tech-lead",
                "target_agent": "coder",
                "correlation_id": "issue-42",
                "session_id": "s-1",
            },
            "authentication": {
                "sender_persona": "coder",  # Mismatch!
                "sender_task_id": "task-1",
                "session_id": "s-1",
            },
            "persona": "governance/personas/agentic/coder.md",
            "protocol_message": {
                "message_type": "ASSIGN",
                "payload": {"task": "test"},
            },
            "context_attachments": [],
        }

        result = validate_envelope(envelope, boundaries)
        assert not result.valid
        assert any(
            "does not match" in v.detail
            for v in result.violations
        )

    def test_pm_to_tech_lead_assign(self, builder_no_sign, boundaries):
        envelope = builder_no_sign.build(
            source="project-manager",
            target="tech-lead",
            message_type="ASSIGN",
            payload={"task": "Handle batch"},
            correlation_id="issue-42",
            session_id="session-1",
        )

        result = validate_envelope(envelope, boundaries)
        assert result.valid

    def test_devops_watch_to_pm(self, builder_no_sign, boundaries):
        envelope = builder_no_sign.build(
            source="devops-engineer",
            target="project-manager",
            message_type="WATCH",
            payload={"issues": []},
            correlation_id="issue-0",
            session_id="session-1",
        )

        result = validate_envelope(envelope, boundaries)
        assert result.valid


# ---------------------------------------------------------------------------
# Strip unauthorized context
# ---------------------------------------------------------------------------


class TestStripUnauthorizedContext:
    def test_strip_removes_unauthorized_attachments(self, builder_no_sign, boundaries):
        envelope = builder_no_sign.build(
            source="tech-lead",
            target="coder",
            message_type="ASSIGN",
            payload={"task": "Implement"},
            correlation_id="issue-42",
            session_id="session-1",
            attachments=[
                {"type": "plan", "path": ".artifacts/plans/42-feature.md"},
                {"type": "checkpoint", "path": ".artifacts/checkpoints/chk.json"},
            ],
        )

        cleaned, stripped = strip_unauthorized_context(envelope, boundaries)
        assert len(cleaned["context_attachments"]) == 1
        assert cleaned["context_attachments"][0]["type"] == "plan"
        assert len(stripped) == 1
        assert "checkpoint" in stripped[0]

    def test_strip_keeps_authorized_attachments(self, builder_no_sign, boundaries):
        envelope = builder_no_sign.build(
            source="tech-lead",
            target="coder",
            message_type="ASSIGN",
            payload={"task": "Implement"},
            correlation_id="issue-42",
            session_id="session-1",
            attachments=[
                {"type": "plan", "path": ".artifacts/plans/42-feature.md"},
                {"type": "config", "path": "project.yaml", "section": "conventions"},
            ],
        )

        cleaned, stripped = strip_unauthorized_context(envelope, boundaries)
        assert len(cleaned["context_attachments"]) == 2
        assert len(stripped) == 0

    def test_strip_no_boundary_returns_unchanged(self, boundaries):
        envelope = {
            "envelope": {
                "version": "1.0",
                "message_id": "msg-00000000-0000-0000-0000-000000000000",
                "timestamp": "2026-03-03T00:00:00+00:00",
                "source_agent": "tech-lead",
                "target_agent": "unknown-persona",
                "correlation_id": "issue-42",
                "session_id": "s-1",
            },
            "authentication": {},
            "persona": "",
            "protocol_message": {"message_type": "ASSIGN", "payload": {}},
            "context_attachments": [
                {"type": "plan", "path": "test.md"},
            ],
        }

        cleaned, stripped = strip_unauthorized_context(envelope, boundaries)
        assert len(cleaned["context_attachments"]) == 1
        assert len(stripped) == 0


# ---------------------------------------------------------------------------
# Transition map completeness
# ---------------------------------------------------------------------------


class TestTransitionMap:
    def test_all_transitions_use_valid_personas(self):
        for (source, target), msg_types in VALID_TRANSITIONS.items():
            assert source in VALID_PERSONAS, f"Invalid source in transition: {source}"
            assert target in VALID_PERSONAS, f"Invalid target in transition: {target}"
            for mt in msg_types:
                assert mt in VALID_MESSAGE_TYPES, f"Invalid message type in transition: {mt}"

    def test_coder_cannot_send_to_devops(self):
        assert ("coder", "devops-engineer") not in VALID_TRANSITIONS

    def test_coder_cannot_send_to_pm(self):
        assert ("coder", "project-manager") not in VALID_TRANSITIONS

    def test_tech_lead_can_send_assign_to_all_workers(self):
        workers = ["coder", "iac-engineer", "test-evaluator", "test-writer",
                    "document-writer", "documentation-reviewer"]
        for worker in workers:
            key = ("tech-lead", worker)
            assert key in VALID_TRANSITIONS, f"Missing transition: tech-lead -> {worker}"
            assert "ASSIGN" in VALID_TRANSITIONS[key]


# ---------------------------------------------------------------------------
# Round-trip: build -> validate -> strip -> re-validate
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_full_round_trip(self, builder, boundaries):
        # Build
        envelope = builder.build(
            source="tech-lead",
            target="coder",
            message_type="ASSIGN",
            payload={"task": "Implement feature X", "context": {"issue_number": 42}},
            correlation_id="issue-42",
            session_id="session-abc",
            sender_task_id="task-tl-1",
            attachments=[
                {"type": "plan", "path": ".artifacts/plans/42-feature-x.md"},
                {"type": "config", "path": "project.yaml", "section": "conventions"},
            ],
        )

        # Validate
        result = validate_envelope(envelope, boundaries)
        assert result.valid, f"Violations: {[v.detail for v in result.violations]}"

        # Strip (should be no-op for valid envelope)
        cleaned, stripped = strip_unauthorized_context(envelope, boundaries)
        assert len(stripped) == 0
        assert len(cleaned["context_attachments"]) == 2

        # Re-validate
        result2 = validate_envelope(cleaned, boundaries)
        assert result2.valid
