"""Extension discovery — auto-discover custom phases, panels, and hooks.

Scans convention directories in the consuming repo for extensions that can be
loaded without any configuration changes. This enables a DACH-style
single-file-drop extensibility model.

Convention directories (relative to project root):
    .governance/extensions/panels/        — custom review panel prompts (.md)
    .governance/extensions/phases/        — custom orchestrator phase scripts (.sh/.py)
    .governance/extensions/hooks/         — lifecycle hooks in subdirectories:
        pre_dispatch/                     — run before Coder dispatch
        post_merge/                       — run after PR merge
        post_review/                      — run after panel reviews

The extension catalog (catalog.json) is auto-generated listing all discovered
extensions with metadata for discoverability.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Extension dataclasses
# ---------------------------------------------------------------------------


@dataclass
class PanelExtension:
    """A discovered custom panel prompt."""

    name: str
    path: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": "panel",
            "path": self.path,
            "description": self.description,
            "version": self.version,
            "author": self.author,
        }


@dataclass
class PhaseExtension:
    """A discovered custom orchestrator phase script."""

    name: str
    path: str
    description: str = ""
    after_phase: int | None = None
    timeout_seconds: int = 300
    interpreter: str = "bash"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": "phase",
            "path": self.path,
            "description": self.description,
            "after_phase": self.after_phase,
            "timeout_seconds": self.timeout_seconds,
            "interpreter": self.interpreter,
        }


@dataclass
class HookExtension:
    """A discovered lifecycle hook script."""

    name: str
    path: str
    hook_point: str  # pre_dispatch | post_merge | post_review
    description: str = ""
    timeout_seconds: int = 60

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": "hook",
            "path": self.path,
            "hook_point": self.hook_point,
            "description": self.description,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass
class DiscoveredExtensions:
    """All extensions discovered from convention directories."""

    panels: list[PanelExtension] = field(default_factory=list)
    phases: list[PhaseExtension] = field(default_factory=list)
    hooks: list[HookExtension] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return len(self.panels) + len(self.phases) + len(self.hooks)

    @property
    def is_empty(self) -> bool:
        return self.total_count == 0

    def panel_names(self) -> list[str]:
        return [p.name for p in self.panels]

    def hook_names_for(self, hook_point: str) -> list[str]:
        return [h.name for h in self.hooks if h.hook_point == hook_point]


# ---------------------------------------------------------------------------
# Frontmatter parser
# ---------------------------------------------------------------------------

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def _parse_frontmatter(content: str) -> dict[str, str]:
    """Parse YAML-like frontmatter from a markdown file.

    Supports simple key: value pairs (no nested structures).
    Returns an empty dict if no frontmatter found.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}

    result: dict[str, str] = {}
    for line in match.group(1).strip().split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()

    return result


def _extract_description_from_script(content: str) -> str:
    """Extract description from a script file's first comment block or docstring."""
    lines = content.strip().split("\n")

    # Skip shebang
    start = 0
    if lines and lines[0].startswith("#!"):
        start = 1

    # Collect comment lines
    desc_lines = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("#"):
            desc_lines.append(stripped.lstrip("# ").strip())
        elif stripped.startswith('"""') or stripped.startswith("'''"):
            # Python docstring
            doc = stripped.strip("\"'").strip()
            if doc:
                return doc
            # Multi-line docstring
            for next_line in lines[start + 1:]:
                if '"""' in next_line or "'''" in next_line:
                    break
                desc_lines.append(next_line.strip())
            break
        else:
            break

    return " ".join(desc_lines)[:200] if desc_lines else ""


# ---------------------------------------------------------------------------
# Discovery functions
# ---------------------------------------------------------------------------

VALID_HOOK_POINTS = {"pre_dispatch", "post_merge", "post_review"}


def discover_panels(panels_dir: Path) -> list[PanelExtension]:
    """Discover custom panel prompts from the panels directory.

    Each .md file is treated as a panel. Frontmatter provides metadata:
        ---
        name: my-custom-review
        description: Reviews custom business logic
        version: 1.0.0
        author: team-name
        ---
    """
    if not panels_dir.is_dir():
        return []

    panels: list[PanelExtension] = []
    for md_file in sorted(panels_dir.glob("*.md")):
        try:
            content = md_file.read_text()
        except OSError:
            continue

        fm = _parse_frontmatter(content)
        name = fm.get("name", md_file.stem)

        panels.append(PanelExtension(
            name=name,
            path=str(md_file),
            description=fm.get("description", ""),
            version=fm.get("version", "1.0.0"),
            author=fm.get("author", ""),
        ))

    return panels


def discover_phases(phases_dir: Path) -> list[PhaseExtension]:
    """Discover custom phase scripts from the phases directory.

    Supported file types: .sh, .py
    Metadata is extracted from frontmatter comments or docstrings.
    """
    if not phases_dir.is_dir():
        return []

    phases: list[PhaseExtension] = []
    for ext in ("*.sh", "*.py"):
        for script in sorted(phases_dir.glob(ext)):
            try:
                content = script.read_text()
            except OSError:
                continue

            description = _extract_description_from_script(content)
            interpreter = "python3" if script.suffix == ".py" else "bash"

            # Try to extract after_phase from filename pattern: 03-my-phase.sh
            after_phase = None
            name_match = re.match(r"^(\d+)-", script.stem)
            if name_match:
                after_phase = int(name_match.group(1))

            phases.append(PhaseExtension(
                name=script.stem,
                path=str(script),
                description=description,
                after_phase=after_phase,
                interpreter=interpreter,
            ))

    return phases


def discover_hooks(hooks_dir: Path) -> list[HookExtension]:
    """Discover lifecycle hooks from hook subdirectories.

    Expected structure:
        hooks/
            pre_dispatch/
                my-hook.sh
            post_merge/
                cleanup.sh
            post_review/
                notify.py
    """
    if not hooks_dir.is_dir():
        return []

    hooks: list[HookExtension] = []
    for hook_point in VALID_HOOK_POINTS:
        point_dir = hooks_dir / hook_point
        if not point_dir.is_dir():
            continue

        for ext in ("*.sh", "*.py"):
            for script in sorted(point_dir.glob(ext)):
                try:
                    content = script.read_text()
                except OSError:
                    continue

                description = _extract_description_from_script(content)

                hooks.append(HookExtension(
                    name=script.stem,
                    path=str(script),
                    hook_point=hook_point,
                    description=description,
                ))

    return hooks


def discover_extensions(base_dir: str | Path) -> DiscoveredExtensions:
    """Discover all extensions from the convention directories.

    Args:
        base_dir: Path to the .governance/extensions/ directory.

    Returns:
        DiscoveredExtensions with all discovered panels, phases, and hooks.
    """
    base = Path(base_dir)

    return DiscoveredExtensions(
        panels=discover_panels(base / "panels"),
        phases=discover_phases(base / "phases"),
        hooks=discover_hooks(base / "hooks"),
    )


# ---------------------------------------------------------------------------
# Catalog generation
# ---------------------------------------------------------------------------


def generate_catalog(extensions: DiscoveredExtensions) -> dict[str, Any]:
    """Generate an extension catalog dict listing all discovered extensions.

    The catalog is intended to be written as catalog.json for discoverability.
    """
    return {
        "$schema": "extension-catalog.schema.json",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_extensions": extensions.total_count,
        "panels": [p.to_dict() for p in extensions.panels],
        "phases": [p.to_dict() for p in extensions.phases],
        "hooks": [h.to_dict() for h in extensions.hooks],
    }


def write_catalog(extensions: DiscoveredExtensions, output_path: str | Path) -> Path:
    """Generate and write the extension catalog to disk.

    Args:
        extensions: Discovered extensions.
        output_path: Path where catalog.json will be written.

    Returns:
        Path to the written catalog file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    catalog = generate_catalog(extensions)
    with open(path, "w") as f:
        json.dump(catalog, f, indent=2)
        f.write("\n")

    return path
