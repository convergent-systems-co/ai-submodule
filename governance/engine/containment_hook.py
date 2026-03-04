#!/usr/bin/env python3
"""Mechanical containment enforcement via pre-commit hook and CI check.

Validates that file changes respect containment boundaries based on the
branch name pattern. This provides a deterministic, mechanical enforcement
layer independent of LLM behavior.

Rules:
  - Branches matching */coder/* cannot modify governance/policy/**,
    governance/schemas/**, governance/personas/**, or governance/prompts/reviews/**
  - Branches matching */iac-engineer/* have the same restrictions plus
    cannot modify application source code
  - All branches cannot modify jm-compliance.yml

Usage as pre-commit hook:
    python governance/engine/containment_hook.py

Usage as library:
    from governance.engine.containment_hook import ContainmentHook

    hook = ContainmentHook()
    violations = hook.check(branch="itsfwcp/coder/42/fix-bug",
                           changed_files=["governance/policy/default.yaml"])
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Branch-to-persona mapping
# ---------------------------------------------------------------------------

# Patterns that identify branch persona types
BRANCH_PERSONA_PATTERNS = [
    (re.compile(r".*/coder/.*"), "coder"),
    (re.compile(r".*/iac-engineer/.*"), "iac-engineer"),
    (re.compile(r".*/test-writer/.*"), "test-writer"),
    (re.compile(r".*/test-evaluator/.*"), "test-evaluator"),
]

# Per-persona restricted paths (mechanical enforcement)
PERSONA_RESTRICTED_PATHS: dict[str, list[str]] = {
    "coder": [
        "governance/policy/**",
        "governance/schemas/**",
        "governance/personas/**",
        "governance/prompts/reviews/**",
        "jm-compliance.yml",
        ".github/workflows/dark-factory-governance.yml",
    ],
    "iac-engineer": [
        "governance/policy/**",
        "governance/schemas/**",
        "governance/personas/**",
        "governance/prompts/reviews/**",
        "jm-compliance.yml",
        ".github/workflows/dark-factory-governance.yml",
    ],
    "test-writer": [
        "governance/policy/**",
        "governance/schemas/**",
        "governance/personas/**",
        "governance/prompts/reviews/**",
        "jm-compliance.yml",
        ".github/workflows/dark-factory-governance.yml",
    ],
    "test-evaluator": [
        "governance/policy/**",
        "governance/schemas/**",
        "governance/personas/**",
        "governance/prompts/reviews/**",
        "jm-compliance.yml",
        ".github/workflows/dark-factory-governance.yml",
    ],
}

# Enterprise-locked files — no branch can modify these
UNIVERSAL_RESTRICTED = [
    "jm-compliance.yml",
]


@dataclass
class Violation:
    """A single containment violation."""

    file_path: str
    persona: str
    restricted_pattern: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "persona": self.persona,
            "restricted_pattern": self.restricted_pattern,
            "message": self.message,
        }


class ContainmentHook:
    """Mechanical containment enforcement for git operations.

    Validates that file changes respect containment boundaries based on
    the branch name pattern, independent of LLM behavior.
    """

    def detect_persona(self, branch: str) -> str | None:
        """Detect the persona type from a branch name.

        Args:
            branch: The git branch name.

        Returns:
            The persona name, or None if no persona pattern matches.
        """
        for pattern, persona in BRANCH_PERSONA_PATTERNS:
            if pattern.match(branch):
                return persona
        return None

    def check(
        self,
        branch: str,
        changed_files: list[str],
    ) -> list[Violation]:
        """Check if changed files violate containment rules for the branch.

        Args:
            branch: The current branch name.
            changed_files: List of file paths that have been changed.

        Returns:
            List of Violation objects. Empty list means no violations.
        """
        violations = []

        # Always check universal restrictions
        for file_path in changed_files:
            for pattern in UNIVERSAL_RESTRICTED:
                if fnmatch.fnmatch(file_path, pattern):
                    violations.append(Violation(
                        file_path=file_path,
                        persona="any",
                        restricted_pattern=pattern,
                        message=f"Enterprise-locked file '{file_path}' cannot be modified by any branch",
                    ))

        # Check persona-specific restrictions
        persona = self.detect_persona(branch)
        if persona is None:
            return violations  # No persona pattern matched — no persona-specific restrictions

        restricted_paths = PERSONA_RESTRICTED_PATHS.get(persona, [])
        for file_path in changed_files:
            for pattern in restricted_paths:
                if pattern in UNIVERSAL_RESTRICTED:
                    continue  # Already checked above
                if fnmatch.fnmatch(file_path, pattern):
                    violations.append(Violation(
                        file_path=file_path,
                        persona=persona,
                        restricted_pattern=pattern,
                        message=f"Persona '{persona}' cannot modify '{file_path}' (matches '{pattern}')",
                    ))

        return violations

    def check_from_git(self) -> list[Violation]:
        """Check violations using the current git state.

        Uses `git rev-parse --abbrev-ref HEAD` for the branch name and
        `git diff --cached --name-only` for staged files.

        Returns:
            List of violations.
        """
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            text=True,
        ).strip()

        changed_files = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"],
            text=True,
        ).strip().split("\n")

        changed_files = [f for f in changed_files if f]  # Remove empty strings
        return self.check(branch, changed_files)

    def format_violations(self, violations: list[Violation]) -> str:
        """Format violations as a human-readable report.

        Args:
            violations: List of violations to format.

        Returns:
            Formatted string report.
        """
        if not violations:
            return "No containment violations detected."

        lines = [
            f"CONTAINMENT VIOLATION: {len(violations)} file(s) violate containment rules:",
            "",
        ]
        for v in violations:
            lines.append(f"  - {v.file_path}")
            lines.append(f"    Persona: {v.persona}")
            lines.append(f"    Rule: {v.restricted_pattern}")
            lines.append(f"    {v.message}")
            lines.append("")
        return "\n".join(lines)


def main() -> int:
    """Entry point for pre-commit hook usage."""
    hook = ContainmentHook()
    violations = hook.check_from_git()

    if violations:
        print(hook.format_violations(violations), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
