"""AI-based merge conflict resolution engine.

Provides automated conflict resolution for the Safe Push pattern used during
Phase 5 (Merge) when N parallel Coders produce PRs that conflict on the same
files. Resolution follows a three-tier strategy:

1. **Regenerate** — Known generated files (manifests, catalogs, lock files)
   are regenerated rather than merged.
2. **AI Resolve** — Code conflicts are resolved by an LLM agent with full
   context of both sides and the common ancestor.
3. **Escalate** — Governance-protected files are never auto-resolved; they
   escalate to human review.

All resolutions produce an audit record written to
``.artifacts/state/conflict-resolutions/``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Maximum number of push retry attempts before giving up.
MAX_PUSH_RETRIES = 3

#: File patterns that are known generated artifacts and should be regenerated
#: rather than AI-resolved.
GENERATED_FILE_PATTERNS: list[str] = [
    "governance/integrity-manifest.json",
    "governance/integrity/**/*.sha256",
    "**/*-lock.json",
    "**/package-lock.json",
    "**/yarn.lock",
    "**/*.lock",
]

#: Governance-protected file patterns — AI resolution is forbidden.
PROTECTED_FILE_PATTERNS: list[str] = [
    "jm-compliance.yml",
    "governance/policy/**",
    "governance/schemas/**",
    "governance/personas/**",
    "governance/prompts/reviews/**",
    ".github/workflows/dark-factory-governance.yml",
]

#: Regex for standard git conflict markers.
CONFLICT_MARKER_RE = re.compile(
    r"^<{7}\s+.*?\n"   # <<<<<<< ours
    r"(.*?)"            # ours content
    r"^={7}\n"          # =======
    r"(.*?)"            # theirs content
    r"^>{7}\s+.*?\n",   # >>>>>>> theirs
    re.MULTILINE | re.DOTALL,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class FileClassification(str, Enum):
    """Classification of a conflicted file for resolution strategy."""

    GENERATED = "generated"
    PROTECTED = "protected"
    CODE = "code"


class ResolutionStrategy(str, Enum):
    """Strategy used to resolve a conflict."""

    REGENERATE = "regenerate"
    AI_RESOLVE = "ai_resolve"
    ESCALATE = "escalate"
    MANUAL = "manual"


class ResolutionOutcome(str, Enum):
    """Outcome of a conflict resolution attempt."""

    RESOLVED = "resolved"
    ESCALATED = "escalated"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ConflictHunk:
    """A single conflict hunk extracted from a file."""

    file_path: str
    hunk_index: int
    ours: str
    theirs: str
    start_line: int = 0


@dataclass
class ResolutionRecord:
    """Audit record for a single file's conflict resolution."""

    file_path: str
    classification: str
    strategy: str
    outcome: str
    timestamp: str = ""
    details: str = ""
    hunks_resolved: int = 0
    hunks_total: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SafePushResult:
    """Result of a safe-push operation."""

    success: bool
    push_attempts: int = 0
    conflicts_found: int = 0
    conflicts_resolved: int = 0
    conflicts_escalated: int = 0
    resolution_records: list[ResolutionRecord] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["resolution_records"] = [r.to_dict() for r in self.resolution_records]
        return result


# ---------------------------------------------------------------------------
# Conflict parser
# ---------------------------------------------------------------------------


def parse_conflict_hunks(file_path: str, content: str) -> list[ConflictHunk]:
    """Parse git conflict markers from file content.

    Args:
        file_path: Path to the conflicted file.
        content: The file content containing conflict markers.

    Returns:
        List of ConflictHunk objects, one per conflict region.
    """
    hunks: list[ConflictHunk] = []
    for i, match in enumerate(CONFLICT_MARKER_RE.finditer(content)):
        start_line = content[:match.start()].count("\n") + 1
        hunks.append(ConflictHunk(
            file_path=file_path,
            hunk_index=i,
            ours=match.group(1),
            theirs=match.group(2),
            start_line=start_line,
        ))
    return hunks


def has_conflict_markers(content: str) -> bool:
    """Check if content contains git conflict markers.

    Args:
        content: File content to check.

    Returns:
        True if conflict markers are present.
    """
    return bool(CONFLICT_MARKER_RE.search(content))


# ---------------------------------------------------------------------------
# File classification
# ---------------------------------------------------------------------------


def _matches_pattern(file_path: str, patterns: list[str]) -> bool:
    """Check if a file path matches any of the given glob-like patterns.

    Supports ``**`` for recursive directory matching and ``*`` for
    single-component matching.
    """
    import fnmatch

    for pattern in patterns:
        if fnmatch.fnmatch(file_path, pattern):
            return True
        # Handle ** patterns by also checking without leading **
        if "**" in pattern:
            # Convert ** to a regex-friendly form
            regex_pattern = pattern.replace("**", ".*").replace("*", "[^/]*")
            # Fix: .*  replaced the ** but the single * replacements may overlap
            # Use a simpler approach: fnmatch with os.sep handling
            parts = pattern.split("**/")
            if len(parts) == 2 and fnmatch.fnmatch(file_path, parts[1]):
                return True
            if file_path.startswith(pattern.replace("/**", "/")) or \
               file_path.startswith(pattern.replace("**/*", "")):
                return True
    return False


def classify_file(file_path: str) -> FileClassification:
    """Classify a conflicted file for resolution strategy selection.

    Args:
        file_path: Relative path to the conflicted file.

    Returns:
        FileClassification indicating how to handle the conflict.
    """
    if _matches_pattern(file_path, PROTECTED_FILE_PATTERNS):
        return FileClassification.PROTECTED
    if _matches_pattern(file_path, GENERATED_FILE_PATTERNS):
        return FileClassification.GENERATED
    return FileClassification.CODE


def strategy_for_classification(classification: FileClassification) -> ResolutionStrategy:
    """Map a file classification to its resolution strategy.

    Args:
        classification: The file classification.

    Returns:
        The resolution strategy to use.
    """
    mapping = {
        FileClassification.PROTECTED: ResolutionStrategy.ESCALATE,
        FileClassification.GENERATED: ResolutionStrategy.REGENERATE,
        FileClassification.CODE: ResolutionStrategy.AI_RESOLVE,
    }
    return mapping[classification]


# ---------------------------------------------------------------------------
# Resolution engine
# ---------------------------------------------------------------------------


class ConflictResolver:
    """Orchestrates conflict resolution for a set of conflicted files.

    This class coordinates the three-tier resolution strategy: regenerate
    generated files, AI-resolve code conflicts, and escalate protected files.

    Args:
        repo_root: Absolute path to the repository root.
        audit_dir: Directory for writing audit records. Defaults to
            ``{repo_root}/.artifacts/state/conflict-resolutions/``.
        dry_run: If True, do not write files or invoke external commands.
    """

    def __init__(
        self,
        repo_root: str | Path,
        audit_dir: str | Path | None = None,
        dry_run: bool = False,
    ):
        self.repo_root = Path(repo_root)
        self.audit_dir = Path(audit_dir) if audit_dir else (
            self.repo_root / ".governance" / "state" / "conflict-resolutions"
        )
        self.dry_run = dry_run
        self._records: list[ResolutionRecord] = []

    @property
    def records(self) -> list[ResolutionRecord]:
        """All resolution records produced so far."""
        return list(self._records)

    def get_conflicted_files(self) -> list[str]:
        """Get list of files with merge conflicts from git.

        Returns:
            List of relative file paths with unresolved conflicts.
        """
        try:
            output = subprocess.check_output(
                ["git", "diff", "--name-only", "--diff-filter=U"],
                cwd=str(self.repo_root),
                text=True,
            ).strip()
            return [f for f in output.split("\n") if f]
        except subprocess.CalledProcessError:
            return []

    def resolve_all(self, conflicted_files: list[str] | None = None) -> SafePushResult:
        """Resolve all conflicts using the three-tier strategy.

        Args:
            conflicted_files: Explicit list of conflicted file paths. If None,
                detected from git.

        Returns:
            SafePushResult with resolution summary.
        """
        if conflicted_files is None:
            conflicted_files = self.get_conflicted_files()

        result = SafePushResult(
            success=True,
            conflicts_found=len(conflicted_files),
        )

        for file_path in conflicted_files:
            record = self._resolve_file(file_path)
            self._records.append(record)
            result.resolution_records.append(record)

            if record.outcome == ResolutionOutcome.RESOLVED.value:
                result.conflicts_resolved += 1
            elif record.outcome == ResolutionOutcome.ESCALATED.value:
                result.conflicts_escalated += 1
                result.success = False
            else:
                result.success = False

        self._write_audit_trail(result)
        return result

    def _resolve_file(self, file_path: str) -> ResolutionRecord:
        """Resolve conflicts in a single file.

        Args:
            file_path: Relative path to the conflicted file.

        Returns:
            ResolutionRecord for this file.
        """
        classification = classify_file(file_path)
        strategy = strategy_for_classification(classification)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        record = ResolutionRecord(
            file_path=file_path,
            classification=classification.value,
            strategy=strategy.value,
            outcome="",
            timestamp=timestamp,
        )

        if strategy == ResolutionStrategy.ESCALATE:
            record.outcome = ResolutionOutcome.ESCALATED.value
            record.details = (
                f"File '{file_path}' is governance-protected. "
                "AI resolution is forbidden. Escalating to human review."
            )
            return record

        if strategy == ResolutionStrategy.REGENERATE:
            return self._resolve_by_regeneration(file_path, record)

        if strategy == ResolutionStrategy.AI_RESOLVE:
            return self._resolve_by_ai(file_path, record)

        record.outcome = ResolutionOutcome.FAILED.value
        record.details = f"Unknown strategy: {strategy}"
        return record

    def _resolve_by_regeneration(
        self,
        file_path: str,
        record: ResolutionRecord,
    ) -> ResolutionRecord:
        """Resolve a generated file by accepting theirs and marking for regeneration.

        For generated files, the conflict is resolved by accepting the incoming
        (theirs) version, since the file will be regenerated anyway.

        Args:
            file_path: Relative path to the file.
            record: The resolution record to update.

        Returns:
            Updated ResolutionRecord.
        """
        if self.dry_run:
            record.outcome = ResolutionOutcome.RESOLVED.value
            record.details = "Dry run: would accept theirs for regeneration."
            return record

        try:
            subprocess.check_call(
                ["git", "checkout", "--theirs", file_path],
                cwd=str(self.repo_root),
            )
            subprocess.check_call(
                ["git", "add", file_path],
                cwd=str(self.repo_root),
            )
            record.outcome = ResolutionOutcome.RESOLVED.value
            record.details = (
                f"Generated file '{file_path}' resolved by accepting theirs. "
                "File should be regenerated in a follow-up step."
            )
        except subprocess.CalledProcessError as exc:
            record.outcome = ResolutionOutcome.FAILED.value
            record.details = f"Regeneration resolution failed: {exc}"

        return record

    def _resolve_by_ai(
        self,
        file_path: str,
        record: ResolutionRecord,
    ) -> ResolutionRecord:
        """Resolve code conflicts using an LLM agent.

        Reads the conflicted file, extracts conflict hunks, and invokes the
        LLM to produce a resolution. The resolved content is written back
        and staged.

        Args:
            file_path: Relative path to the file.
            record: The resolution record to update.

        Returns:
            Updated ResolutionRecord.
        """
        full_path = self.repo_root / file_path

        try:
            content = full_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            record.outcome = ResolutionOutcome.FAILED.value
            record.details = f"Cannot read file: {exc}"
            return record

        hunks = parse_conflict_hunks(file_path, content)
        record.hunks_total = len(hunks)

        if not hunks:
            record.outcome = ResolutionOutcome.RESOLVED.value
            record.details = "No conflict markers found in file."
            record.hunks_resolved = 0
            return record

        if self.dry_run:
            record.outcome = ResolutionOutcome.RESOLVED.value
            record.details = f"Dry run: would AI-resolve {len(hunks)} hunks."
            record.hunks_resolved = len(hunks)
            return record

        # Build the resolution prompt
        prompt = self._build_resolution_prompt(file_path, content, hunks)

        # Attempt LLM resolution
        resolved_content = self._invoke_llm(prompt, file_path)
        if resolved_content is None:
            record.outcome = ResolutionOutcome.FAILED.value
            record.details = "LLM invocation failed. Escalating to manual resolution."
            return record

        # Validate: resolved content should not contain conflict markers
        if has_conflict_markers(resolved_content):
            record.outcome = ResolutionOutcome.FAILED.value
            record.details = "LLM resolution still contains conflict markers."
            return record

        # Write resolved content
        try:
            full_path.write_text(resolved_content, encoding="utf-8")
            subprocess.check_call(
                ["git", "add", file_path],
                cwd=str(self.repo_root),
            )
            record.outcome = ResolutionOutcome.RESOLVED.value
            record.hunks_resolved = len(hunks)
            record.details = f"AI resolved {len(hunks)} conflict hunks."
        except (OSError, subprocess.CalledProcessError) as exc:
            record.outcome = ResolutionOutcome.FAILED.value
            record.details = f"Failed to write resolution: {exc}"

        return record

    def _build_resolution_prompt(
        self,
        file_path: str,
        content: str,
        hunks: list[ConflictHunk],
    ) -> str:
        """Build a structured prompt for LLM conflict resolution.

        Args:
            file_path: Path to the conflicted file.
            content: Full file content with conflict markers.
            hunks: Parsed conflict hunks.

        Returns:
            Prompt string for the LLM.
        """
        hunk_descriptions = []
        for h in hunks:
            hunk_descriptions.append(
                f"Hunk {h.hunk_index + 1} at line {h.start_line}:\n"
                f"  OURS:\n{_indent(h.ours, 4)}\n"
                f"  THEIRS:\n{_indent(h.theirs, 4)}"
            )

        return (
            f"Resolve the merge conflicts in the file '{file_path}'.\n\n"
            f"The file has {len(hunks)} conflict(s).\n\n"
            f"{''.join(hunk_descriptions)}\n\n"
            f"Full file content (with conflict markers):\n"
            f"```\n{content}\n```\n\n"
            "Rules:\n"
            "1. Preserve the intent of BOTH sides when possible.\n"
            "2. If one side adds functionality and the other modifies existing code, "
            "include both changes.\n"
            "3. If both sides modify the same lines differently, prefer the more "
            "complete or correct version.\n"
            "4. Do NOT include any conflict markers in your output.\n"
            "5. Return ONLY the resolved file content, nothing else.\n"
        )

    def _invoke_llm(self, prompt: str, file_path: str) -> str | None:
        """Invoke the LLM agent to resolve a conflict.

        Uses the ``claude`` CLI if available. Falls back to None (manual
        resolution required).

        Args:
            prompt: The resolution prompt.
            file_path: Path for logging context.

        Returns:
            Resolved file content, or None if invocation failed.
        """
        try:
            result = subprocess.run(
                ["claude", "--print", "--no-input", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.repo_root),
            )
            if result.returncode == 0 and result.stdout.strip():
                output = result.stdout.strip()
                # Strip markdown code fences if present
                if output.startswith("```"):
                    lines = output.split("\n")
                    # Remove first line (```lang) and last line (```)
                    if lines[-1].strip() == "```":
                        lines = lines[1:-1]
                    else:
                        lines = lines[1:]
                    output = "\n".join(lines)
                return output
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return None

    def _write_audit_trail(self, result: SafePushResult) -> None:
        """Write the resolution audit trail to disk.

        Args:
            result: The SafePushResult to persist.
        """
        if self.dry_run:
            return

        self.audit_dir.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
        audit_file = self.audit_dir / f"resolution-{timestamp}.json"

        try:
            audit_file.write_text(
                json.dumps(result.to_dict(), indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass  # Best effort — don't fail the merge over audit


# ---------------------------------------------------------------------------
# Safe Push orchestration
# ---------------------------------------------------------------------------


def safe_push(
    repo_root: str | Path,
    branch: str,
    remote: str = "origin",
    max_retries: int = MAX_PUSH_RETRIES,
    dry_run: bool = False,
) -> SafePushResult:
    """Execute the Safe Push pattern: push, rebase on failure, resolve conflicts.

    This is the main entry point for the Safe Push workflow:

    1. Attempt ``git push``
    2. On rejection, ``git fetch`` + ``git rebase``
    3. If conflicts arise, run the three-tier conflict resolver
    4. Retry push up to ``max_retries`` times
    5. Final fallback: ``git push --force-with-lease``

    Args:
        repo_root: Absolute path to the repository root.
        branch: Branch name to push.
        remote: Git remote name (default: ``origin``).
        max_retries: Maximum push attempts before force-push fallback.
        dry_run: If True, simulate without executing git commands.

    Returns:
        SafePushResult with the operation summary.
    """
    repo = Path(repo_root)
    resolver = ConflictResolver(repo_root=repo, dry_run=dry_run)
    result = SafePushResult(success=False)

    for attempt in range(1, max_retries + 1):
        result.push_attempts = attempt

        if dry_run:
            result.success = True
            return result

        # Attempt push
        push_result = subprocess.run(
            ["git", "push", remote, branch],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )
        if push_result.returncode == 0:
            result.success = True
            return result

        # Push rejected — fetch and rebase
        subprocess.run(
            ["git", "fetch", remote],
            cwd=str(repo),
            capture_output=True,
        )

        rebase_result = subprocess.run(
            ["git", "rebase", f"{remote}/{branch}"],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )

        if rebase_result.returncode == 0:
            # Rebase succeeded — retry push
            continue

        # Rebase had conflicts — attempt resolution
        conflicted = resolver.get_conflicted_files()
        if not conflicted:
            # Rebase failed for non-conflict reasons — abort and fail
            subprocess.run(
                ["git", "rebase", "--abort"],
                cwd=str(repo),
                capture_output=True,
            )
            result.error = f"Rebase failed (non-conflict): {rebase_result.stderr}"
            return result

        resolution = resolver.resolve_all(conflicted)
        result.conflicts_found += resolution.conflicts_found
        result.conflicts_resolved += resolution.conflicts_resolved
        result.conflicts_escalated += resolution.conflicts_escalated
        result.resolution_records.extend(resolution.resolution_records)

        if not resolution.success:
            # Could not resolve all conflicts — abort rebase
            subprocess.run(
                ["git", "rebase", "--abort"],
                cwd=str(repo),
                capture_output=True,
            )
            result.error = (
                f"Cannot resolve all conflicts: "
                f"{resolution.conflicts_escalated} escalated, "
                f"{resolution.conflicts_found - resolution.conflicts_resolved} unresolved"
            )
            return result

        # All conflicts resolved — continue rebase
        continue_result = subprocess.run(
            ["git", "rebase", "--continue"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            env={**os.environ, "GIT_EDITOR": "true"},
        )

        if continue_result.returncode != 0:
            subprocess.run(
                ["git", "rebase", "--abort"],
                cwd=str(repo),
                capture_output=True,
            )
            result.error = f"Rebase --continue failed: {continue_result.stderr}"
            return result

    # All retries exhausted — force-with-lease as final fallback
    if not dry_run:
        force_result = subprocess.run(
            ["git", "push", "--force-with-lease", remote, branch],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )
        result.success = force_result.returncode == 0
        if not result.success:
            result.error = f"Force-with-lease push failed: {force_result.stderr}"

    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _indent(text: str, spaces: int) -> str:
    """Indent each line of text by the given number of spaces."""
    prefix = " " * spaces
    return "\n".join(prefix + line for line in text.splitlines())
