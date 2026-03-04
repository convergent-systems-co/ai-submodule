"""Pre-flight validation for project.yaml.

Validates YAML syntax, schema conformance, and language template coverage.
Called during orchestrator init (Phase 0) before any work begins.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# jsonschema is optional — degrade gracefully if not installed
try:
    import jsonschema

    _HAS_JSONSCHEMA = True
except ImportError:  # pragma: no cover
    _HAS_JSONSCHEMA = False


@dataclass
class PreflightFinding:
    """A single preflight check result."""

    level: str  # "error" or "warning"
    check: str  # e.g. "yaml_syntax", "schema", "template_coverage"
    message: str

    def to_dict(self) -> dict:
        return {"level": self.level, "check": self.check, "message": self.message}


@dataclass
class PreflightResult:
    """Aggregated preflight validation result."""

    valid: bool = True
    findings: list[PreflightFinding] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    templates_available: list[str] = field(default_factory=list)
    templates_missing: list[str] = field(default_factory=list)

    def add(self, level: str, check: str, message: str) -> None:
        self.findings.append(PreflightFinding(level=level, check=check, message=message))
        if level == "error":
            self.valid = False

    @property
    def errors(self) -> list[PreflightFinding]:
        return [f for f in self.findings if f.level == "error"]

    @property
    def warnings(self) -> list[PreflightFinding]:
        return [f for f in self.findings if f.level == "warning"]

    def summary(self) -> str:
        lines = []
        if self.errors:
            lines.append(f"  ERRORS ({len(self.errors)}):")
            for f in self.errors:
                lines.append(f"    [{f.check}] {f.message}")
        if self.warnings:
            lines.append(f"  WARNINGS ({len(self.warnings)}):")
            for f in self.warnings:
                lines.append(f"    [{f.check}] {f.message}")
        if not lines:
            lines.append("  All checks passed.")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "languages": self.languages,
            "templates_available": self.templates_available,
            "templates_missing": self.templates_missing,
            "findings": [f.to_dict() for f in self.findings],
        }


def _resolve_governance_root(project_yaml_path: Path) -> Path:
    """Walk up from project.yaml to find the governance root.

    The governance root is the directory containing governance/templates/.
    Typically project.yaml sits at the repo root (which is the governance root
    for the dark-forge itself) or one level above .ai/.
    """
    # If project.yaml is inside the governance repo itself
    candidate = project_yaml_path.parent
    if (candidate / "governance" / "templates").is_dir():
        return candidate

    # If project.yaml is in a consuming repo, templates are in .ai/governance/templates/
    ai_dir = candidate / ".ai"
    if (ai_dir / "governance" / "templates").is_dir():
        return ai_dir

    return candidate


def _discover_templates(governance_root: Path) -> list[str]:
    """Return list of available language template names."""
    languages_dir = governance_root / "governance" / "templates" / "languages"
    if not languages_dir.is_dir():
        # Legacy fallback: flat structure under governance/templates/
        templates_dir = governance_root / "governance" / "templates"
        if not templates_dir.is_dir():
            return []
        return sorted(
            d.name
            for d in templates_dir.iterdir()
            if d.is_dir() and (d / "project.yaml").exists()
        )

    return sorted(
        d.name
        for d in languages_dir.iterdir()
        if d.is_dir() and (d / "project.yaml").exists()
    )


def _extract_languages(data: dict) -> list[str]:
    """Extract the language list from parsed project.yaml data.

    Supports both:
      language: "python"          -> ["python"]
      languages: [python, json]   -> ["python", "json"]
    """
    languages = data.get("languages")
    if isinstance(languages, list):
        return [str(lang).lower() for lang in languages]

    language = data.get("language")
    if isinstance(language, str) and language:
        return [language.lower()]

    return []


# Map from language name to template directory name
# (handles cases where the template dir name differs from the language value)
_LANGUAGE_TO_TEMPLATE: dict[str, str] = {
    "typescript": "node",
    "javascript": "node",
    "c#": "csharp",
    "hcl": "terraform",
    "bicep": "bicep",
    "html": "html",
    "markdown": "markdown-json",
    "json": "markdown-json",
    "yaml": "markdown-json",
}


def _language_to_template_name(language: str) -> str:
    """Map a language name to its template directory name."""
    return _LANGUAGE_TO_TEMPLATE.get(language, language)


def validate_project_yaml(
    project_yaml_path: str | Path,
    governance_root: str | Path | None = None,
) -> PreflightResult:
    """Run all preflight checks on project.yaml.

    Args:
        project_yaml_path: Path to the project.yaml file.
        governance_root: Root directory containing governance/. Auto-detected if None.

    Returns:
        PreflightResult with all findings.
    """
    result = PreflightResult()
    path = Path(project_yaml_path)

    # --- Check 1: File exists ---
    if not path.exists():
        result.add("error", "file_missing", f"project.yaml not found at {path}")
        return result

    # --- Check 2: YAML syntax ---
    raw = path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as e:
        result.add("error", "yaml_syntax", f"YAML parse error: {e}")
        return result  # Can't continue without valid YAML

    if not isinstance(data, dict):
        result.add("error", "yaml_syntax", "project.yaml must be a YAML mapping (dict), got "
                    f"{type(data).__name__}")
        return result

    # --- Check 3: Schema validation ---
    if _HAS_JSONSCHEMA:
        gov_root = Path(governance_root) if governance_root else _resolve_governance_root(path)
        schema_path = gov_root / "governance" / "schemas" / "project.schema.json"
        if schema_path.exists():
            try:
                schema = json.loads(schema_path.read_text(encoding="utf-8"))
                validator = jsonschema.Draft202012Validator(schema)
                for error in validator.iter_errors(data):
                    json_path = ".".join(str(p) for p in error.absolute_path) or "(root)"
                    result.add("error", "schema", f"{json_path}: {error.message}")
            except (json.JSONDecodeError, jsonschema.SchemaError) as e:
                result.add("warning", "schema", f"Could not load schema: {e}")
        else:
            result.add("warning", "schema", f"Schema file not found at {schema_path}")

    # --- Check 4: Duplicate top-level keys ---
    # yaml.safe_load silently drops duplicates; scan raw text for them
    seen_keys: dict[str, int] = {}
    for line in raw.splitlines():
        stripped = line.lstrip()
        # Top-level key: no leading whitespace, ends with ':'
        if line and not line[0].isspace() and not stripped.startswith("#"):
            key = stripped.split(":")[0].strip()
            if key:
                seen_keys[key] = seen_keys.get(key, 0) + 1
    for key, count in seen_keys.items():
        if count > 1:
            result.add("error", "duplicate_key",
                        f"Duplicate top-level key '{key}' appears {count} times "
                        "(YAML silently uses last occurrence)")

    # --- Check 5: Both language and languages ---
    has_language = "language" in data
    has_languages = "languages" in data
    if has_language and has_languages:
        result.add("warning", "language_field",
                    "Both 'language' and 'languages' are set. 'languages' takes precedence; "
                    "consider removing 'language' to avoid confusion.")

    # --- Check 6: Language template coverage ---
    languages = _extract_languages(data)
    result.languages = languages

    if languages:
        gov_root = Path(governance_root) if governance_root else _resolve_governance_root(path)
        available_templates = _discover_templates(gov_root)

        for lang in languages:
            template_name = _language_to_template_name(lang)
            if template_name in available_templates:
                if template_name not in result.templates_available:
                    result.templates_available.append(template_name)
            else:
                result.templates_missing.append(lang)
                result.add("warning", "template_coverage",
                            f"Language '{lang}' has no matching template in "
                            f"governance/templates/ (looked for '{template_name}/'). "
                            "Consider creating one for language-specific conventions.")

    # --- Check 7: Orphaned keys (commented parent, uncommented children) ---
    # Detect indented keys that appear right after a commented-out mapping key
    lines = raw.splitlines()
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("# ") and stripped.endswith(":"):
            # This looks like a commented-out mapping key
            commented_key = stripped[2:].rstrip(":")
            # Check if next non-empty, non-comment line is indented (child)
            for j in range(i + 1, min(i + 5, len(lines))):
                next_line = lines[j]
                next_stripped = next_line.lstrip()
                if not next_stripped or next_stripped.startswith("#"):
                    continue
                if next_line[0].isspace() and ":" in next_stripped:
                    result.add("warning", "orphaned_keys",
                                f"Line {j + 1}: key appears to be a child of commented-out "
                                f"'{commented_key}:' on line {i + 1}. This key is parsed as a "
                                "sibling of the previous mapping, which may cause unexpected "
                                "structure.")
                break

    return result
