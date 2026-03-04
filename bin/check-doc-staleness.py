#!/usr/bin/env python3
"""Documentation staleness detection script.

Parses markdown files for numeric claims (e.g., "21 review panels", "7 personas")
and path references, cross-references against actual file/directory counts in the
repository, and outputs a staleness report with specific line numbers and corrections.

Usage:
    python bin/check-doc-staleness.py [--fix] [--json] [--root PATH]

Options:
    --fix     Automatically fix stale values in-place
    --json    Output report as JSON (for CI integration)
    --root    Repository root path (default: auto-detect via git)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class StalenessIssue:
    """A single staleness issue found in documentation."""

    file: str
    line_number: int
    line_content: str
    category: str  # "count", "path", "description"
    description: str
    current_value: str
    expected_value: str
    auto_fixable: bool = True


@dataclass
class StalenessReport:
    """Complete staleness report."""

    issues: list[StalenessIssue] = field(default_factory=list)
    files_scanned: int = 0
    files_with_issues: int = 0

    def to_dict(self) -> dict:
        return {
            "issues": [
                {
                    "file": i.file,
                    "line_number": i.line_number,
                    "line_content": i.line_content,
                    "category": i.category,
                    "description": i.description,
                    "current_value": i.current_value,
                    "expected_value": i.expected_value,
                    "auto_fixable": i.auto_fixable,
                }
                for i in self.issues
            ],
            "summary": {
                "total_issues": len(self.issues),
                "files_scanned": self.files_scanned,
                "files_with_issues": self.files_with_issues,
                "auto_fixable": sum(1 for i in self.issues if i.auto_fixable),
            },
        }


# Known count patterns: maps a regex pattern to a function that returns the expected count.
# The regex must have a named group "count" for the numeric value.
COUNT_PATTERNS: list[tuple[str, str, str]] = [
    # (pattern, description, count_source_glob)
    (
        r"(?P<count>\d+)\s+agentic\s+personas?\s+in",
        "agentic persona count",
        "governance/personas/agentic/*.md",
    ),
    (
        r"(?:Six|Seven|Eight|Nine|Ten|\d+)\s+agentic\s+personas?\s+in",
        "agentic persona count (word form)",
        "governance/personas/agentic/*.md",
    ),
    (
        r"(?P<count>\d+)\s+review\s+prompts?\s+in",
        "review prompt count",
        "governance/prompts/reviews/*.md",
    ),
    (
        r"(?P<count>\d+)\s+review\s+panel\s+prompts?\s+in",
        "review panel prompt count",
        "governance/prompts/reviews/*.md",
    ),
    (
        r"(?P<count>\d+)\s+developer\s+prompts",
        "developer prompt count",
        "prompts/global/*.md",
    ),
    (
        r"(?P<count>\d+)\s+policy\s+profiles?\s+and",
        "policy profile count",
        "governance/policy/profiles/*.yaml",
    ),
    (
        r"(?:Five|Six|Seven|Eight|Nine|Ten|\d+)\s+policy\s+profiles?\s+and",
        "policy profile count (word form)",
        "governance/policy/profiles/*.yaml",
    ),
    (
        r"(?P<count>\d+)\s+supporting\s+policy\s+configurations",
        "supporting policy configuration count",
        "governance/policy/*.yaml",
    ),
]

# Word-to-number mapping for word-form counts
WORD_TO_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "twenty-one": 21,
}

NUM_TO_WORD = {v: k.capitalize() for k, v in WORD_TO_NUM.items()}


def get_repo_root(override: Optional[str] = None) -> Path:
    """Get the repository root directory."""
    if override:
        return Path(override).resolve()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        return Path.cwd()


def count_files(root: Path, glob_pattern: str) -> int:
    """Count files matching a glob pattern relative to root."""
    return len(list(root.glob(glob_pattern)))


def find_markdown_files(root: Path) -> list[Path]:
    """Find all markdown files to scan for staleness."""
    targets = [
        "CLAUDE.md",
        "README.md",
        "GOALS.md",
        "CONTRIBUTING.md",
    ]
    target_dirs = [
        "docs",
        "governance/prompts",
    ]

    files = []
    for t in targets:
        p = root / t
        if p.exists():
            files.append(p)

    for d in target_dirs:
        dp = root / d
        if dp.exists():
            files.extend(dp.rglob("*.md"))

    return sorted(set(files))


def check_count_staleness(
    root: Path, file_path: Path, lines: list[str]
) -> list[StalenessIssue]:
    """Check for stale numeric counts in a file."""
    issues = []
    rel_path = str(file_path.relative_to(root))

    for line_num, line in enumerate(lines, 1):
        for pattern, description, glob_pattern in COUNT_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if not match:
                continue

            expected_count = count_files(root, glob_pattern)

            # Extract current count (numeric or word form)
            if "count" in match.groupdict() and match.group("count"):
                current_count = int(match.group("count"))
            else:
                # Word form - extract the word
                word_match = re.search(
                    r"(Zero|One|Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|"
                    r"Eleven|Twelve|Thirteen|Fourteen|Fifteen|Sixteen|Seventeen|"
                    r"Eighteen|Nineteen|Twenty|Twenty-one|\d+)",
                    match.group(0),
                    re.IGNORECASE,
                )
                if word_match:
                    word = word_match.group(1).lower()
                    current_count = WORD_TO_NUM.get(word)
                    if current_count is None:
                        try:
                            current_count = int(word)
                        except ValueError:
                            continue
                else:
                    continue

            if current_count != expected_count:
                # Determine if the original used word form or numeric
                if "count" in match.groupdict() and match.group("count"):
                    expected_str = str(expected_count)
                    current_str = str(current_count)
                else:
                    expected_str = NUM_TO_WORD.get(expected_count, str(expected_count))
                    current_str = NUM_TO_WORD.get(current_count, str(current_count))

                issues.append(
                    StalenessIssue(
                        file=rel_path,
                        line_number=line_num,
                        line_content=line.rstrip(),
                        category="count",
                        description=f"Stale {description}: claims {current_count}, actual is {expected_count}",
                        current_value=current_str,
                        expected_value=expected_str,
                    )
                )

    return issues


def check_path_references(
    root: Path, file_path: Path, lines: list[str]
) -> list[StalenessIssue]:
    """Check for broken path references in a file."""
    issues = []
    rel_path = str(file_path.relative_to(root))

    # Pattern to match backtick-wrapped paths that look like file/directory references
    path_pattern = re.compile(
        r"`((?:governance|docs|bin|prompts|\.governance|\.github|mcp-server|tests)"
        r"/[a-zA-Z0-9_./-]+)`"
    )

    for line_num, line in enumerate(lines, 1):
        for match in path_pattern.finditer(line):
            ref_path = match.group(1)

            # Strip trailing glob patterns for existence check
            clean_path = re.sub(r"/\*\*?.*$", "", ref_path)
            if not clean_path:
                continue

            full_path = root / clean_path
            if not full_path.exists():
                issues.append(
                    StalenessIssue(
                        file=rel_path,
                        line_number=line_num,
                        line_content=line.rstrip(),
                        category="path",
                        description=f"Path reference `{ref_path}` does not exist",
                        current_value=ref_path,
                        expected_value="<path does not exist>",
                        auto_fixable=False,
                    )
                )

    return issues


def fix_count_issues(root: Path, issues: list[StalenessIssue]) -> int:
    """Apply automatic fixes for count staleness issues."""
    # Group issues by file
    by_file: dict[str, list[StalenessIssue]] = {}
    for issue in issues:
        if issue.auto_fixable and issue.category == "count":
            by_file.setdefault(issue.file, []).append(issue)

    fixed = 0
    for file_rel, file_issues in by_file.items():
        file_path = root / file_rel
        content = file_path.read_text()
        lines = content.split("\n")

        for issue in sorted(file_issues, key=lambda i: i.line_number, reverse=True):
            idx = issue.line_number - 1
            if idx < len(lines):
                old_line = lines[idx]
                new_line = old_line.replace(issue.current_value, issue.expected_value, 1)
                if old_line != new_line:
                    lines[idx] = new_line
                    fixed += 1

        file_path.write_text("\n".join(lines))

    return fixed


def run_check(root: Path, fix: bool = False, json_output: bool = False) -> StalenessReport:
    """Run the full staleness check."""
    report = StalenessReport()
    md_files = find_markdown_files(root)
    report.files_scanned = len(md_files)

    files_with_issues = set()
    for md_file in md_files:
        try:
            content = md_file.read_text()
        except (OSError, UnicodeDecodeError):
            continue

        lines = content.split("\n")

        # Check counts
        count_issues = check_count_staleness(root, md_file, lines)
        report.issues.extend(count_issues)

        # Check paths
        path_issues = check_path_references(root, md_file, lines)
        report.issues.extend(path_issues)

        if count_issues or path_issues:
            files_with_issues.add(str(md_file))

    report.files_with_issues = len(files_with_issues)

    if fix:
        fixed = fix_count_issues(root, report.issues)
        if not json_output:
            print(f"Auto-fixed {fixed} issue(s).")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect stale documentation references"
    )
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix stale values"
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output", help="Output as JSON"
    )
    parser.add_argument(
        "--root", type=str, default=None, help="Repository root path"
    )
    args = parser.parse_args()

    root = get_repo_root(args.root)
    report = run_check(root, fix=args.fix, json_output=args.json_output)

    if args.json_output:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        if not report.issues:
            print(f"No staleness issues found. Scanned {report.files_scanned} files.")
            return 0

        print(f"Staleness Report: {len(report.issues)} issue(s) in {report.files_with_issues} file(s)")
        print(f"Files scanned: {report.files_scanned}")
        print("-" * 72)

        for issue in report.issues:
            fixable = " [auto-fixable]" if issue.auto_fixable else " [manual fix needed]"
            print(f"\n  {issue.file}:{issue.line_number}{fixable}")
            print(f"  Category: {issue.category}")
            print(f"  {issue.description}")
            print(f"  Line: {issue.line_content}")
            if issue.auto_fixable:
                print(f"  Fix: replace '{issue.current_value}' with '{issue.expected_value}'")

    return 1 if report.issues else 0


if __name__ == "__main__":
    sys.exit(main())
