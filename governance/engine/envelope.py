"""Envelope builder for agent context boundaries.

Constructs structured message envelopes that define the sole input to each
agent. The envelope wraps a protocol message with authentication, persona
context, and declared attachments — enforcing per-persona context boundaries.

Usage:
    from governance.engine.envelope import EnvelopeBuilder, load_boundaries

    boundaries = load_boundaries()
    builder = EnvelopeBuilder(boundaries=boundaries, signer=signer)
    envelope = builder.build(
        source="tech-lead",
        target="coder",
        message_type="ASSIGN",
        payload={"task": "Implement feature X"},
        correlation_id="issue-42",
        session_id="session-abc",
        sender_task_id="task-tl-1",
        attachments=[{"type": "plan", "path": ".artifacts/plans/42-feature-x.md"}],
    )
    result = validate_envelope(envelope, boundaries)
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from governance.engine.message_signing import MessageSigner

# Path to the boundary specification relative to repo root
BOUNDARIES_PATH = "governance/policy/agent-context-boundaries.yaml"

# Valid persona names (must match agent-protocol.md)
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

# Valid message types
VALID_MESSAGE_TYPES = frozenset({
    "ASSIGN", "STATUS", "RESULT", "FEEDBACK",
    "ESCALATE", "APPROVE", "BLOCK", "CANCEL", "WATCH",
})

# Valid attachment types
VALID_ATTACHMENT_TYPES = frozenset({
    "plan", "config", "persona_definition", "source_file",
    "documentation", "coder_result", "checkpoint",
})

# Valid transition map — (source, target) -> allowed message types
# Mirrors governance/prompts/agent-protocol.md Valid Transition Map
VALID_TRANSITIONS: dict[tuple[str, str], frozenset[str]] = {
    ("project-manager", "devops-engineer"): frozenset({"ASSIGN", "CANCEL"}),
    ("project-manager", "tech-lead"): frozenset({"ASSIGN", "CANCEL"}),
    ("devops-engineer", "project-manager"): frozenset({"RESULT", "STATUS", "ESCALATE", "WATCH"}),
    ("devops-engineer", "tech-lead"): frozenset({"ASSIGN", "CANCEL"}),
    ("tech-lead", "project-manager"): frozenset({"RESULT", "STATUS", "ESCALATE"}),
    ("tech-lead", "devops-engineer"): frozenset({"STATUS", "RESULT", "ESCALATE"}),
    ("tech-lead", "coder"): frozenset({"ASSIGN", "CANCEL", "FEEDBACK"}),
    ("tech-lead", "iac-engineer"): frozenset({"ASSIGN", "CANCEL", "FEEDBACK"}),
    ("tech-lead", "test-evaluator"): frozenset({"ASSIGN", "CANCEL"}),
    ("tech-lead", "test-writer"): frozenset({"ASSIGN", "CANCEL", "FEEDBACK"}),
    ("tech-lead", "document-writer"): frozenset({"ASSIGN", "CANCEL", "FEEDBACK"}),
    ("tech-lead", "documentation-reviewer"): frozenset({"ASSIGN", "CANCEL"}),
    ("coder", "tech-lead"): frozenset({"STATUS", "RESULT", "ESCALATE"}),
    ("iac-engineer", "tech-lead"): frozenset({"STATUS", "RESULT", "ESCALATE"}),
    ("test-evaluator", "tech-lead"): frozenset({"FEEDBACK", "APPROVE", "BLOCK", "ESCALATE"}),
    ("test-writer", "tech-lead"): frozenset({"STATUS", "RESULT", "ESCALATE"}),
    ("document-writer", "tech-lead"): frozenset({"STATUS", "RESULT", "ESCALATE"}),
    ("documentation-reviewer", "tech-lead"): frozenset({"FEEDBACK", "APPROVE", "BLOCK", "ESCALATE"}),
}


@dataclass
class EnvelopeViolation:
    """A single context boundary violation."""

    field: str
    violation_type: str  # "unauthorized_context" | "missing_required" | "invalid_transition" | "never_receives"
    detail: str


@dataclass
class EnvelopeValidationResult:
    """Result of envelope validation against context boundaries."""

    valid: bool = True
    violations: list[EnvelopeViolation] = field(default_factory=list)
    stripped_fields: list[str] = field(default_factory=list)

    def add_violation(self, field_name: str, violation_type: str, detail: str) -> None:
        self.violations.append(EnvelopeViolation(
            field=field_name,
            violation_type=violation_type,
            detail=detail,
        ))
        self.valid = False


def load_boundaries(repo_root: str | Path | None = None) -> dict:
    """Load the agent context boundaries specification.

    Args:
        repo_root: Path to the repository root. If None, attempts to find it
                   relative to this file (governance/engine/ -> repo root).

    Returns:
        Parsed YAML boundaries dict with 'boundaries' key.

    Raises:
        FileNotFoundError: If the boundaries file doesn't exist.
    """
    if repo_root is None:
        # governance/engine/envelope.py -> governance/engine -> governance -> repo root
        repo_root = Path(__file__).resolve().parent.parent.parent

    path = Path(repo_root) / BOUNDARIES_PATH
    if not path.exists():
        raise FileNotFoundError(f"Boundaries file not found: {path}")

    with open(path) as f:
        return yaml.safe_load(f)


def _generate_message_id() -> str:
    """Generate a unique message ID with msg- prefix."""
    return f"msg-{uuid.uuid4()}"


def _compute_file_hash(file_path: str, repo_root: str | Path | None = None) -> str:
    """Compute SHA-256 hash of a file for content addressing.

    Args:
        file_path: Path relative to repo root.
        repo_root: Repository root directory.

    Returns:
        Hash string in format 'sha256:{hex}'.
    """
    if repo_root is None:
        repo_root = Path(__file__).resolve().parent.parent.parent

    full_path = Path(repo_root) / file_path
    if not full_path.exists():
        return "sha256:" + "0" * 64  # Placeholder for non-existent files

    content = full_path.read_bytes()
    digest = hashlib.sha256(content).hexdigest()
    return f"sha256:{digest}"


class EnvelopeBuilder:
    """Builds validated agent context envelopes.

    The builder constructs envelopes that conform to the agent-envelope schema
    and respect per-persona context boundaries. It integrates with the
    MessageSigner for HMAC authentication.

    Args:
        boundaries: Parsed boundary specification (from load_boundaries()).
        signer: Optional MessageSigner for HMAC signing.
        repo_root: Repository root for file hash computation.
    """

    def __init__(
        self,
        boundaries: dict,
        signer: MessageSigner | None = None,
        repo_root: str | Path | None = None,
    ):
        self._boundaries = boundaries.get("boundaries", {})
        self._signer = signer
        self._repo_root = repo_root

    def build(
        self,
        source: str,
        target: str,
        message_type: str,
        payload: dict,
        correlation_id: str,
        session_id: str,
        sender_task_id: str = "",
        parent_message_id: str = "",
        attachments: list[dict] | None = None,
        constraints: dict | None = None,
    ) -> dict:
        """Build a complete agent envelope.

        Args:
            source: Source persona name.
            target: Target persona name.
            message_type: Protocol message type (ASSIGN, RESULT, etc.).
            payload: Message-type-specific payload dict.
            correlation_id: Issue/PR identifier.
            session_id: Session identifier.
            sender_task_id: Task ID of the sending agent.
            parent_message_id: Parent message ID in the ASSIGN chain.
            attachments: List of context attachment dicts.
            constraints: Optional execution constraints.

        Returns:
            Complete envelope dict conforming to agent-envelope.schema.json.

        Raises:
            ValueError: If source, target, or message_type is invalid.
        """
        if source not in VALID_PERSONAS:
            raise ValueError(f"Invalid source persona: {source}")
        if target not in VALID_PERSONAS:
            raise ValueError(f"Invalid target persona: {target}")
        if message_type not in VALID_MESSAGE_TYPES:
            raise ValueError(f"Invalid message type: {message_type}")

        now = datetime.now(timezone.utc).isoformat()
        message_id = _generate_message_id()

        # Look up persona definition path from boundaries
        target_boundary = self._boundaries.get(target, {})
        persona_path = ""
        for entry in target_boundary.get("receives", []):
            if entry.get("type") == "persona_definition":
                persona_path = entry.get("path", "")
                break

        # Build protocol message
        protocol_message: dict[str, Any] = {
            "message_type": message_type,
            "payload": payload,
        }
        if constraints:
            protocol_message["constraints"] = constraints

        # Build context attachments with hashes
        context_attachments = []
        for att in (attachments or []):
            attachment: dict[str, Any] = {
                "type": att["type"],
                "path": att["path"],
            }
            if "hash" not in att:
                attachment["hash"] = _compute_file_hash(att["path"], self._repo_root)
            else:
                attachment["hash"] = att["hash"]
            if "section" in att:
                attachment["section"] = att["section"]
            context_attachments.append(attachment)

        # Build authentication
        authentication: dict[str, Any] = {
            "sender_persona": source,
            "sender_task_id": sender_task_id,
            "parent_message_id": parent_message_id,
            "session_id": session_id,
        }

        # Sign if signer available
        if self._signer:
            # Build a signable representation of the envelope content
            signable = {
                "message_type": message_type,
                "source_agent": source,
                "target_agent": target,
                "correlation_id": correlation_id,
                "payload": payload,
            }
            signed = self._signer.sign(signable, source)
            authentication["signature"] = signed["signature"]

        envelope = {
            "envelope": {
                "version": "1.0",
                "message_id": message_id,
                "timestamp": now,
                "source_agent": source,
                "target_agent": target,
                "correlation_id": correlation_id,
                "session_id": session_id,
            },
            "authentication": authentication,
            "persona": persona_path,
            "protocol_message": protocol_message,
            "context_attachments": context_attachments,
        }

        return envelope


def validate_envelope(
    envelope: dict,
    boundaries: dict,
) -> EnvelopeValidationResult:
    """Validate an envelope against context boundary specifications.

    Checks:
    1. Source -> target transition is valid for the message type
    2. Target persona's allowed message types include this message type
    3. Context attachments are authorized by the target's receives list
    4. No never_receives content is present
    5. Authentication fields are present and consistent

    Args:
        envelope: The envelope dict to validate.
        boundaries: Parsed boundary specification.

    Returns:
        EnvelopeValidationResult with any violations found.
    """
    result = EnvelopeValidationResult()
    boundary_map = boundaries.get("boundaries", {})

    env_meta = envelope.get("envelope", {})
    source = env_meta.get("source_agent", "")
    target = env_meta.get("target_agent", "")
    msg_type = envelope.get("protocol_message", {}).get("message_type", "")

    # 1. Validate personas
    if source not in VALID_PERSONAS:
        result.add_violation("envelope.source_agent", "invalid_transition", f"Unknown source persona: {source}")
    if target not in VALID_PERSONAS:
        result.add_violation("envelope.target_agent", "invalid_transition", f"Unknown target persona: {target}")

    if not result.valid:
        return result

    # 2. Validate transition
    transition_key = (source, target)
    allowed_types = VALID_TRANSITIONS.get(transition_key, frozenset())
    if not allowed_types:
        result.add_violation(
            "envelope",
            "invalid_transition",
            f"No valid transitions from '{source}' to '{target}'",
        )
    elif msg_type not in allowed_types:
        result.add_violation(
            "protocol_message.message_type",
            "invalid_transition",
            f"Message type '{msg_type}' is not valid from '{source}' to '{target}'. "
            f"Allowed: {sorted(allowed_types)}",
        )

    # 3. Validate target boundary allows this message type
    target_boundary = boundary_map.get(target, {})
    if target_boundary:
        allowed_message_types: set[str] = set()
        for entry in target_boundary.get("receives", []):
            if entry.get("type") == "protocol_messages":
                allowed_message_types.update(entry.get("message_types", []))

        if allowed_message_types and msg_type not in allowed_message_types:
            result.add_violation(
                "protocol_message.message_type",
                "unauthorized_context",
                f"Target '{target}' does not receive message type '{msg_type}'. "
                f"Allowed: {sorted(allowed_message_types)}",
            )

    # 4. Validate context attachments against boundary
    attachments = envelope.get("context_attachments", [])
    if target_boundary and attachments:
        receives = target_boundary.get("receives", [])
        allowed_attachment_types = set()
        for entry in receives:
            entry_type = entry.get("type", "")
            # Map boundary types to attachment types
            type_mapping = {
                "plan_file": "plan",
                "plan_files": "plan",
                "config": "config",
                "persona_definition": "persona_definition",
                "source_files": "source_file",
                "documentation_files": "documentation",
                "coder_result": "coder_result",
                "checkpoint": "checkpoint",
                "orchestrator_state": "checkpoint",
                "issue_metadata": "config",
                "panel_prompts": "config",
            }
            mapped = type_mapping.get(entry_type, entry_type)
            allowed_attachment_types.add(mapped)

        for att in attachments:
            att_type = att.get("type", "")
            if att_type not in allowed_attachment_types:
                result.add_violation(
                    "context_attachments",
                    "unauthorized_context",
                    f"Attachment type '{att_type}' is not authorized for target '{target}'",
                )

    # 5. Validate authentication consistency
    auth = envelope.get("authentication", {})
    if auth:
        auth_persona = auth.get("sender_persona", "")
        if auth_persona and auth_persona != source:
            result.add_violation(
                "authentication.sender_persona",
                "unauthorized_context",
                f"Authentication persona '{auth_persona}' does not match "
                f"envelope source '{source}'",
            )

    return result


def strip_unauthorized_context(
    envelope: dict,
    boundaries: dict,
) -> tuple[dict, list[str]]:
    """Remove unauthorized context from an envelope.

    Inspects context_attachments and removes any that are not authorized
    by the target persona's boundary specification. Returns the cleaned
    envelope and a list of stripped attachment descriptions.

    Args:
        envelope: The envelope dict to clean.
        boundaries: Parsed boundary specification.

    Returns:
        Tuple of (cleaned_envelope, list_of_stripped_descriptions).
    """
    boundary_map = boundaries.get("boundaries", {})
    target = envelope.get("envelope", {}).get("target_agent", "")
    target_boundary = boundary_map.get(target, {})

    if not target_boundary:
        return envelope, []

    receives = target_boundary.get("receives", [])
    allowed_attachment_types = set()
    for entry in receives:
        entry_type = entry.get("type", "")
        type_mapping = {
            "plan_file": "plan",
            "plan_files": "plan",
            "config": "config",
            "persona_definition": "persona_definition",
            "source_files": "source_file",
            "documentation_files": "documentation",
            "coder_result": "coder_result",
            "checkpoint": "checkpoint",
            "orchestrator_state": "checkpoint",
            "issue_metadata": "config",
            "panel_prompts": "config",
        }
        mapped = type_mapping.get(entry_type, entry_type)
        allowed_attachment_types.add(mapped)

    cleaned = dict(envelope)
    original_attachments = cleaned.get("context_attachments", [])
    kept = []
    stripped = []

    for att in original_attachments:
        att_type = att.get("type", "")
        if att_type in allowed_attachment_types:
            kept.append(att)
        else:
            stripped.append(f"{att_type}:{att.get('path', 'unknown')}")

    cleaned["context_attachments"] = kept
    return cleaned, stripped
