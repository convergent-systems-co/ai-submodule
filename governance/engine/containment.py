#!/usr/bin/env python3
"""Agent containment enforcement engine.

Evaluates file paths and operations against per-persona containment rules
defined in governance/policy/agent-containment.yaml. In enforced mode,
violations are blocked; in advisory mode, they are logged but allowed.

Usage:
    from governance.engine.containment import ContainmentChecker

    checker = ContainmentChecker(policy)
    result = checker.check_path("coder", "governance/policy/default.yaml")
    if result.blocked:
        print(f"Blocked: {result.reason}")
"""

from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class ContainmentResult:
    """Result of a containment check."""

    allowed: bool
    blocked: bool
    persona: str
    action: str           # "path_check" or "operation_check"
    target: str           # file path or operation name
    reason: str           # Explanation of why it was blocked/allowed
    mode: str             # "enforced" or "advisory"
    violation: bool       # True if the action violates policy (even if advisory)

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "blocked": self.blocked,
            "persona": self.persona,
            "action": self.action,
            "target": self.target,
            "reason": self.reason,
            "mode": self.mode,
            "violation": self.violation,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class ContainmentViolation(Exception):
    """Raised when a containment rule is violated in enforced mode."""

    def __init__(self, result: ContainmentResult):
        self.result = result
        super().__init__(result.reason)


class ContainmentChecker:
    """Evaluates containment rules against persona actions.

    Args:
        policy: Parsed agent-containment.yaml dict.
        violations_log: Optional path to write violations JSONL.
    """

    def __init__(
        self,
        policy: dict[str, Any],
        violations_log: str | Path | None = None,
    ):
        self._policy = policy
        self._mode = policy.get("enforcement", {}).get("mode", "enforced")
        self._personas = policy.get("personas", {})
        self._global_limits = policy.get("global_limits", {})
        self._violations_log = Path(violations_log) if violations_log else None

    @property
    def mode(self) -> str:
        """Current enforcement mode."""
        return self._mode

    def check_path(self, persona: str, file_path: str) -> ContainmentResult:
        """Check if a persona is allowed to modify a file path.

        Args:
            persona: The persona name (e.g., "coder", "test-evaluator").
            file_path: The file path being modified (relative to repo root).

        Returns:
            ContainmentResult indicating if the action is allowed/blocked.
        """
        persona_config = self._personas.get(persona, {})

        # Check denied paths
        denied_paths = persona_config.get("denied_paths", [])
        for pattern in denied_paths:
            if fnmatch.fnmatch(file_path, pattern):
                result = ContainmentResult(
                    allowed=self._mode == "advisory",
                    blocked=self._mode == "enforced",
                    persona=persona,
                    action="path_check",
                    target=file_path,
                    reason=f"Path '{file_path}' matches denied pattern '{pattern}' for persona '{persona}'",
                    mode=self._mode,
                    violation=True,
                )
                self._log_violation(result)
                return result

        # Check allowed_paths if defined (IaC Engineer has an allow-list)
        allowed_paths = persona_config.get("allowed_paths")
        if allowed_paths is not None:
            matched = any(fnmatch.fnmatch(file_path, p) for p in allowed_paths)
            if not matched:
                result = ContainmentResult(
                    allowed=self._mode == "advisory",
                    blocked=self._mode == "enforced",
                    persona=persona,
                    action="path_check",
                    target=file_path,
                    reason=f"Path '{file_path}' not in allowed paths for persona '{persona}'",
                    mode=self._mode,
                    violation=True,
                )
                self._log_violation(result)
                return result

        # Check allowed_write_paths if defined (Tester has write restrictions)
        allowed_write = persona_config.get("allowed_write_paths")
        if allowed_write is not None:
            matched = any(fnmatch.fnmatch(file_path, p) for p in allowed_write)
            if not matched:
                result = ContainmentResult(
                    allowed=self._mode == "advisory",
                    blocked=self._mode == "enforced",
                    persona=persona,
                    action="path_check",
                    target=file_path,
                    reason=f"Path '{file_path}' not in allowed write paths for persona '{persona}'",
                    mode=self._mode,
                    violation=True,
                )
                self._log_violation(result)
                return result

        return ContainmentResult(
            allowed=True,
            blocked=False,
            persona=persona,
            action="path_check",
            target=file_path,
            reason="Path allowed",
            mode=self._mode,
            violation=False,
        )

    def check_operation(self, persona: str, operation: str) -> ContainmentResult:
        """Check if a persona is allowed to perform an operation.

        Args:
            persona: The persona name.
            operation: The operation name (e.g., "git_push", "modify_policy").

        Returns:
            ContainmentResult indicating if the operation is allowed/blocked.
        """
        persona_config = self._personas.get(persona, {})
        denied_ops = persona_config.get("denied_operations", [])

        if operation in denied_ops:
            result = ContainmentResult(
                allowed=self._mode == "advisory",
                blocked=self._mode == "enforced",
                persona=persona,
                action="operation_check",
                target=operation,
                reason=f"Operation '{operation}' is denied for persona '{persona}'",
                mode=self._mode,
                violation=True,
            )
            self._log_violation(result)
            return result

        # Check allowed_operations if defined (Team Lead, DevOps Engineer)
        allowed_ops = persona_config.get("allowed_operations")
        if allowed_ops is not None and operation not in allowed_ops:
            # If there is an allowed list and the operation is not in it,
            # it is implicitly denied only if it looks like a privileged operation.
            # We do not block arbitrary operations not in the allow list to
            # avoid false positives on normal actions.
            pass

        return ContainmentResult(
            allowed=True,
            blocked=False,
            persona=persona,
            action="operation_check",
            target=operation,
            reason="Operation allowed",
            mode=self._mode,
            violation=False,
        )

    def check_resource_limit(
        self, persona: str, limit_name: str, current_value: int
    ) -> ContainmentResult:
        """Check if a persona has exceeded a resource limit.

        Args:
            persona: The persona name.
            limit_name: Name of the limit (e.g., "max_files_per_pr").
            current_value: The current value to check against the limit.

        Returns:
            ContainmentResult indicating if the limit is exceeded.
        """
        persona_config = self._personas.get(persona, {})
        persona_limits = persona_config.get("resource_limits", {})

        # Use the more restrictive of persona and global limits
        persona_limit = persona_limits.get(limit_name)
        global_limit = self._global_limits.get(limit_name)

        effective_limit = None
        if persona_limit is not None and global_limit is not None:
            effective_limit = min(persona_limit, global_limit)
        elif persona_limit is not None:
            effective_limit = persona_limit
        elif global_limit is not None:
            effective_limit = global_limit

        if effective_limit is not None and current_value > effective_limit:
            result = ContainmentResult(
                allowed=self._mode == "advisory",
                blocked=self._mode == "enforced",
                persona=persona,
                action="resource_limit_check",
                target=limit_name,
                reason=f"Resource limit '{limit_name}' exceeded: {current_value} > {effective_limit} for persona '{persona}'",
                mode=self._mode,
                violation=True,
            )
            self._log_violation(result)
            return result

        return ContainmentResult(
            allowed=True,
            blocked=False,
            persona=persona,
            action="resource_limit_check",
            target=limit_name,
            reason=f"Within resource limit '{limit_name}'",
            mode=self._mode,
            violation=False,
        )

    def _log_violation(self, result: ContainmentResult) -> None:
        """Log a violation to the JSONL file if configured."""
        if self._violations_log is None:
            return
        self._violations_log.parent.mkdir(parents=True, exist_ok=True)
        with open(self._violations_log, "a") as f:
            f.write(json.dumps(result.to_dict(), separators=(",", ":")) + "\n")
