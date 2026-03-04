#!/usr/bin/env python3
"""Two-stage prompt injection defense — Stage 1: Deterministic pre-filter.

Scans untrusted content (issue bodies, PR descriptions, commit messages, file
contents) for known prompt injection patterns using regex and entropy analysis.
Runs before any LLM processing at zero token cost.

Stage 2 is the existing Tester persona scanning (defense in depth).

Pattern categories:
  1. Direct instruction overrides
  2. HTML comment injection (agent protocol markers)
  3. Base64 payloads (Shannon entropy threshold)
  4. Markdown injection (hidden links, data URIs)
  5. Delimiter smuggling (agent message markers, protocol JSON)
  6. System prompt exfiltration attempts

Usage:
    from governance.engine.security_prefilter import SecurityPrefilter

    prefilter = SecurityPrefilter()
    findings = prefilter.scan(content)
    if findings:
        # Block or flag for human review
        for f in findings:
            print(f"{f['category']}: {f['description']}")
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Finding structure
# ---------------------------------------------------------------------------

@dataclass
class PrefilterFinding:
    """A single finding from the deterministic pre-filter."""

    category: str          # Pattern category (e.g., "instruction_override")
    severity: str          # "critical", "high", "medium", "low"
    description: str       # Human-readable description
    matched_text: str      # The text that triggered the finding (truncated)
    line_number: int | None = None  # Line number where the match occurred

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for policy engine consumption."""
        return {
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "matched_text": self.matched_text[:200],  # Truncate for safety
            "line_number": self.line_number,
        }


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# Category 1: Direct instruction overrides
_INSTRUCTION_OVERRIDE_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules?|directives?)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:a|an|the)\b", re.IGNORECASE),
    re.compile(r"act\s+as\s+(?:a|an|the|if)\b", re.IGNORECASE),
    re.compile(r"forget\s+(everything|all|your)\s+(you|instructions?|rules?|training)", re.IGNORECASE),
    re.compile(r"override\s+(your|the|all)\s+(instructions?|rules?|guidelines?|policies?|constraints?)", re.IGNORECASE),
    re.compile(r"disregard\s+(your|the|all|any)\s+(previous|prior)?\s*(instructions?|rules?|guidelines?|policies?)", re.IGNORECASE),
    re.compile(r"new\s+instructions?\s*:", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),
    re.compile(r"<\|?(system|im_start)\|?>", re.IGNORECASE),
]

# Category 2: HTML comment injection (agent protocol markers in untrusted content)
_HTML_COMMENT_INJECTION_PATTERNS = [
    re.compile(r"<!--\s*AGENT_MSG_START\s*-->", re.IGNORECASE),
    re.compile(r"<!--\s*AGENT_MSG_END\s*-->", re.IGNORECASE),
    re.compile(r"<!--\s*(APPROVE|BLOCK|ASSIGN|CANCEL|ESCALATE|FEEDBACK|RESULT|STATUS)\b", re.IGNORECASE),
]

# Category 4: Markdown injection
_MARKDOWN_INJECTION_PATTERNS = [
    re.compile(r"!\[([^\]]*)\]\(data:", re.IGNORECASE),  # Image with data URI
    re.compile(r"\[([^\]]*)\]\(javascript:", re.IGNORECASE),  # JS link
    re.compile(r"<img[^>]+src\s*=\s*['\"]data:", re.IGNORECASE),  # HTML img with data URI
    re.compile(r"<script\b", re.IGNORECASE),  # Script tag
    re.compile(r"<iframe\b", re.IGNORECASE),  # Iframe tag
]

# Category 5: Delimiter smuggling (protocol message structures in untrusted content)
_DELIMITER_SMUGGLING_PATTERNS = [
    re.compile(r'"message_type"\s*:\s*"(ASSIGN|APPROVE|BLOCK|CANCEL|ESCALATE|FEEDBACK|RESULT|STATUS)"', re.IGNORECASE),
    re.compile(r'"source_agent"\s*:\s*"(devops-engineer|tech-lead|coder|iac-engineer|test-writer|test-evaluator|document-writer|documentation-reviewer|project-manager)"', re.IGNORECASE),
    re.compile(r'"target_agent"\s*:\s*"(devops-engineer|tech-lead|coder|iac-engineer|test-writer|test-evaluator|document-writer|documentation-reviewer|project-manager)"', re.IGNORECASE),
]

# Category 6: System prompt exfiltration
_EXFILTRATION_PATTERNS = [
    re.compile(r"(repeat|show|print|output|display|reveal)\s+(your|the)\s+(system\s+prompt|instructions?|rules?|guidelines?|persona)", re.IGNORECASE),
    re.compile(r"what\s+(are|is)\s+your\s+(system\s+prompt|instructions?|rules?|guidelines?|persona)", re.IGNORECASE),
    re.compile(r"(dump|leak|extract|exfiltrate)\s+(your|the|all)\s+(instructions?|context|prompt|config)", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Entropy calculation for base64 detection
# ---------------------------------------------------------------------------

_BASE64_PATTERN = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")
_ENTROPY_THRESHOLD = 4.5


def _shannon_entropy(data: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not data:
        return 0.0
    counts = Counter(data)
    length = len(data)
    return -sum(
        (count / length) * math.log2(count / length)
        for count in counts.values()
    )


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

class SecurityPrefilter:
    """Deterministic pre-filter for prompt injection detection.

    Scans content against known attack patterns using regex and entropy
    analysis. Returns structured findings for policy engine consumption.
    """

    def __init__(self, entropy_threshold: float = _ENTROPY_THRESHOLD):
        self.entropy_threshold = entropy_threshold

    def scan(self, content: str) -> list[dict[str, Any]]:
        """Scan content for prompt injection patterns.

        Args:
            content: The untrusted content to scan.

        Returns:
            List of finding dicts. Empty list means no issues detected.
        """
        if not content:
            return []

        findings: list[PrefilterFinding] = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            # Category 1: Instruction overrides
            for pattern in _INSTRUCTION_OVERRIDE_PATTERNS:
                match = pattern.search(line)
                if match:
                    findings.append(PrefilterFinding(
                        category="instruction_override",
                        severity="critical",
                        description=f"Direct instruction override attempt detected: '{match.group()}'",
                        matched_text=match.group(),
                        line_number=line_num,
                    ))

            # Category 2: HTML comment injection
            for pattern in _HTML_COMMENT_INJECTION_PATTERNS:
                match = pattern.search(line)
                if match:
                    findings.append(PrefilterFinding(
                        category="html_comment_injection",
                        severity="high",
                        description=f"Agent protocol marker found in untrusted content: '{match.group()}'",
                        matched_text=match.group(),
                        line_number=line_num,
                    ))

            # Category 3: Base64 payloads (entropy check)
            for match in _BASE64_PATTERN.finditer(line):
                candidate = match.group()
                entropy = _shannon_entropy(candidate)
                if entropy >= self.entropy_threshold:
                    findings.append(PrefilterFinding(
                        category="base64_payload",
                        severity="medium",
                        description=f"High-entropy base64-like string detected (entropy={entropy:.2f})",
                        matched_text=candidate[:80],
                        line_number=line_num,
                    ))

            # Category 4: Markdown injection
            for pattern in _MARKDOWN_INJECTION_PATTERNS:
                match = pattern.search(line)
                if match:
                    findings.append(PrefilterFinding(
                        category="markdown_injection",
                        severity="high",
                        description=f"Markdown/HTML injection pattern detected: '{match.group()}'",
                        matched_text=match.group(),
                        line_number=line_num,
                    ))

            # Category 5: Delimiter smuggling
            for pattern in _DELIMITER_SMUGGLING_PATTERNS:
                match = pattern.search(line)
                if match:
                    findings.append(PrefilterFinding(
                        category="delimiter_smuggling",
                        severity="high",
                        description=f"Agent protocol message structure found in untrusted content: '{match.group()}'",
                        matched_text=match.group(),
                        line_number=line_num,
                    ))

            # Category 6: System prompt exfiltration
            for pattern in _EXFILTRATION_PATTERNS:
                match = pattern.search(line)
                if match:
                    findings.append(PrefilterFinding(
                        category="exfiltration_attempt",
                        severity="high",
                        description=f"System prompt exfiltration attempt detected: '{match.group()}'",
                        matched_text=match.group(),
                        line_number=line_num,
                    ))

        return [f.to_dict() for f in findings]

    def scan_multiple(self, contents: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
        """Scan multiple content sources.

        Args:
            contents: Mapping of source label to content string.
                     e.g., {"issue_body": "...", "pr_description": "..."}

        Returns:
            Mapping of source label to findings list.
            Only includes sources with findings.
        """
        results = {}
        for label, content in contents.items():
            findings = self.scan(content)
            if findings:
                results[label] = findings
        return results

    def has_critical_findings(self, findings: list[dict[str, Any]]) -> bool:
        """Check if any findings are critical severity."""
        return any(f.get("severity") == "critical" for f in findings)

    def has_high_or_critical_findings(self, findings: list[dict[str, Any]]) -> bool:
        """Check if any findings are high or critical severity."""
        return any(f.get("severity") in ("critical", "high") for f in findings)
