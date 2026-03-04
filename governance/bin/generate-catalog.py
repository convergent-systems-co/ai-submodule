#!/usr/bin/env python3
"""Generate governance reference pages from source artifacts.

Scans review panels, policy profiles, and workflow prompts to produce
three markdown reference files:

  - docs/reference/panel-catalog.md
  - docs/reference/policy-comparison.md
  - docs/reference/prompt-index.md

Requires Python 3.12+ with no external dependencies (stdlib only).
YAML is parsed with regex since PyYAML may not be installed.
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (relative to repository root)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REVIEWS_DIR = REPO_ROOT / "governance" / "prompts" / "reviews"
POLICY_DIR = REPO_ROOT / "governance" / "policy"
PROMPTS_DIR = REPO_ROOT / "governance" / "prompts"
OUTPUT_DIR = REPO_ROOT / "docs" / "reference"

# ---------------------------------------------------------------------------
# Category mapping
# ---------------------------------------------------------------------------

CATEGORY_MAP: dict[str, str] = {
    "security-review": "security",
    "threat-modeling": "security",
    "threat-model-system": "security",
    "cost-analysis": "cost",
    "data-governance-review": "data",
    "data-design-review": "data",
    "documentation-review": "documentation",
    "code-review": "code-quality",
    "ai-expert-review": "code-quality",
    "technical-debt-review": "code-quality",
    "architecture-review": "architecture",
    "api-design-review": "architecture",
    "migration-review": "architecture",
    "testing-review": "testing",
    "test-generation-review": "testing",
    "performance-review": "operations",
    "production-readiness-review": "operations",
    "incident-post-mortem": "operations",
    "copilot-review": "operations",
    "governance-compliance-review": "operations",
}

# Four main policy profiles
PROFILE_FILES = [
    "default.yaml",
    "fin_pii_high.yaml",
    "infrastructure_critical.yaml",
    "reduced_touchpoint.yaml",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def extract_purpose(text: str) -> str:
    """Return the first paragraph after the ## Purpose heading."""
    match = re.search(r"^## Purpose\s*\n+(.*?)(?:\n\n|\n##)", text, re.MULTILINE | re.DOTALL)
    if match:
        purpose = match.group(1).strip()
        # Collapse to single line
        purpose = re.sub(r"\s+", " ", purpose)
        # Truncate for table display
        if len(purpose) > 120:
            purpose = purpose[:117] + "..."
        return purpose
    return "N/A"


def count_perspectives(text: str) -> int:
    """Count perspectives in a panel file.

    Standard panels use ### headings under ## Perspectives.
    Threat-model panels use Review Tracks with participant tables.
    Copilot is a single-participant integration panel.
    """
    # Check for track-based panels (threat-model-*)
    tracks = re.findall(r"^### Track \d+:", text, re.MULTILINE)
    if tracks:
        return len(tracks)

    # Count ### headings inside ## Perspectives section
    in_perspectives = False
    count = 0
    for line in text.splitlines():
        if line.startswith("## Perspectives"):
            in_perspectives = True
            continue
        if in_perspectives and re.match(r"^## [^#]", line):
            break
        if in_perspectives and line.startswith("### "):
            count += 1

    # Copilot has no Perspectives section but is a single participant
    if count == 0:
        if "copilot" in text.lower() and "Role" in text:
            return 1

    return count


def parse_yaml_field(text: str, field: str) -> str:
    """Extract a simple scalar YAML field value with regex."""
    match = re.search(rf'^{field}:\s*["\']?([^"\'\n]+)["\']?', text, re.MULTILINE)
    return match.group(1).strip() if match else "N/A"


def parse_required_panels(text: str) -> list[str]:
    """Extract the required_panels list from a YAML policy file."""
    panels: list[str] = []
    in_section = False
    for line in text.splitlines():
        if re.match(r"^required_panels:", line):
            in_section = True
            continue
        if in_section:
            m = re.match(r"^\s+-\s+(.+)", line)
            if m:
                panels.append(m.group(1).strip())
            elif line.strip() and not line.startswith("#"):
                break
    return panels


def parse_auto_merge_enabled(text: str) -> str:
    """Determine if auto_merge is enabled."""
    # Look for auto_merge.enabled
    in_auto_merge = False
    for line in text.splitlines():
        if re.match(r"^auto_merge:", line):
            in_auto_merge = True
            continue
        if in_auto_merge and "enabled:" in line:
            val = line.split("enabled:")[-1].strip()
            return "Yes" if val == "true" else "No"
        if in_auto_merge and re.match(r"^\S", line):
            break
    return "N/A"


def parse_auto_merge_confidence(text: str) -> str:
    """Extract auto-merge confidence threshold from conditions."""
    if parse_auto_merge_enabled(text) == "No":
        return "N/A"
    match = re.search(r"aggregate_confidence\s*>=\s*([\d.]+)", text)
    return match.group(1) if match else "N/A"


def parse_escalation_threshold(text: str) -> str:
    """Extract the low_confidence escalation threshold."""
    # Find escalation rules section, look for low_confidence condition
    match = re.search(r"name:\s*low_confidence.*?condition:\s*aggregate_confidence\s*<\s*([\d.]+)", text, re.DOTALL)
    if match:
        return match.group(1)
    # For reduced_touchpoint, escalation is policy-override only
    if "policy_override_requested" in text and "low_confidence" not in text:
        return "policy override only"
    return "N/A"


def parse_block_confidence(text: str) -> str:
    """Extract the block confidence threshold from the block section."""
    # Find the block: section and look for confidence threshold within it
    block_match = re.search(r"^block:\s*\n((?:[ \t].*\n)*)", text, re.MULTILINE)
    if block_match:
        block_section = block_match.group(1)
        match = re.search(r"aggregate_confidence\s*<\s*([\d.]+)", block_section)
        if match:
            return match.group(1)
    return "N/A"


def parse_risk_aggregation(text: str) -> str:
    """Summarize the risk aggregation model."""
    model = parse_yaml_field(text.split("risk_aggregation:")[-1] if "risk_aggregation:" in text else "", "model")
    return model if model != "N/A" else "highest_severity"


def parse_override_approvals(text: str) -> str:
    """Extract min_approvals from override section."""
    match = re.search(r"min_approvals:\s*(\d+)", text)
    return match.group(1) if match else "N/A"


def _extract_yaml_description(text: str) -> str:
    """Extract only the description value from a YAML file.

    Handles both block-scalar (>) and plain multi-line descriptions,
    stopping at the next top-level key or comment line.
    """
    desc_lines: list[str] = []
    in_desc = False
    for line in text.splitlines():
        if re.match(r"^description:\s*>?\s*$", line):
            in_desc = True
            continue
        if re.match(r"^description:\s+\S", line):
            # Single-line description
            return line.split("description:", 1)[1].strip().strip("\"'")
        if in_desc:
            # Stop at non-indented, non-empty lines (next YAML key or blank)
            stripped = line.strip()
            if line and not line[0].isspace():
                break
            # Stop at comment-only lines within the indented block
            if stripped.startswith("#"):
                break
            if not stripped:
                # Blank line terminates a block scalar
                break
            desc_lines.append(stripped)
    result = " ".join(desc_lines).strip()
    return result


def parse_override_roles(text: str) -> str:
    """Extract required_roles from override section."""
    roles: list[str] = []
    in_section = False
    in_roles = False
    for line in text.splitlines():
        if re.match(r"^override:", line):
            in_section = True
            continue
        if in_section and "required_roles:" in line:
            in_roles = True
            continue
        if in_roles:
            m = re.match(r"^\s+-\s+(.+)", line)
            if m:
                roles.append(m.group(1).strip())
            elif line.strip() and not line.startswith("#"):
                break
    return ", ".join(roles) if roles else "N/A"


# ---------------------------------------------------------------------------
# Generator: Panel Catalog
# ---------------------------------------------------------------------------


def generate_panel_catalog() -> str:
    """Generate docs/reference/panel-catalog.md content."""
    lines = [
        "# Panel Catalog",
        "",
        "Searchable catalog of all governance review panels. Each panel implements",
        "Anthropic's Parallelization (Voting) pattern with multiple independent",
        "perspectives producing structured emissions.",
        "",
        "> **Auto-generated** by `governance/bin/generate-catalog.py`.",
        "> Do not edit manually -- regenerate with `python governance/bin/generate-catalog.py`.",
        "",
    ]

    # Collect all panel data
    panels: list[dict[str, str]] = []

    # Load required panels per profile
    profile_panels: dict[str, list[str]] = {}
    for pf in PROFILE_FILES:
        path = POLICY_DIR / pf
        if path.exists():
            content = path.read_text()
            name = parse_yaml_field(content, "profile_name")
            profile_panels[name] = parse_required_panels(content)

    for panel_file in sorted(REVIEWS_DIR.glob("*.md")):
        name = panel_file.stem
        content = panel_file.read_text()
        purpose = extract_purpose(content)
        perspectives = count_perspectives(content)
        category = CATEGORY_MAP.get(name, "other")

        # Determine which profiles require this panel
        required_in: list[str] = []
        for profile_name, req_panels in profile_panels.items():
            if name in req_panels:
                required_in.append(profile_name)

        status = "Required" if required_in else "Optional"
        required_str = ", ".join(required_in) if required_in else "conditional"

        panels.append({
            "name": name,
            "category": category,
            "required_in": required_str,
            "perspectives": str(perspectives),
            "status": status,
            "purpose": purpose,
        })

    # Group by category
    categories = sorted(set(p["category"] for p in panels))

    for cat in categories:
        cat_panels = [p for p in panels if p["category"] == cat]
        lines.append(f"## {cat.replace('-', ' ').title()}")
        lines.append("")
        lines.append("| Panel | Required In | Perspectives | Status |")
        lines.append("|-------|------------|--------------|--------|")
        for p in cat_panels:
            panel_link = f"[{p['name']}](../../governance/prompts/reviews/{p['name']}.md)"
            lines.append(f"| {panel_link} | {p['required_in']} | {p['perspectives']} | {p['status']} |")
        lines.append("")

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- **Total panels:** {len(panels)}")
    lines.append(f"- **Categories:** {len(categories)}")
    for cat in categories:
        count = sum(1 for p in panels if p["category"] == cat)
        lines.append(f"  - {cat.replace('-', ' ').title()}: {count}")
    lines.append("")

    # Full detail table
    lines.append("## All Panels")
    lines.append("")
    lines.append("| Panel | Category | Required In | Perspectives | Purpose |")
    lines.append("|-------|----------|------------|--------------|---------|")
    for p in sorted(panels, key=lambda x: x["name"]):
        panel_link = f"[{p['name']}](../../governance/prompts/reviews/{p['name']}.md)"
        lines.append(
            f"| {panel_link} | {p['category']} | {p['required_in']} | {p['perspectives']} | {p['purpose']} |"
        )
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generator: Policy Comparison
# ---------------------------------------------------------------------------


def generate_policy_comparison() -> str:
    """Generate docs/reference/policy-comparison.md content."""
    lines = [
        "# Policy Comparison",
        "",
        "Side-by-side comparison of the four deterministic policy profiles.",
        "All profiles are evaluated programmatically by the policy engine --",
        "AI models never interpret policy rules.",
        "",
        "> **Auto-generated** by `governance/bin/generate-catalog.py`.",
        "> Do not edit manually -- regenerate with `python governance/bin/generate-catalog.py`.",
        "",
    ]

    # Load all profiles
    profiles: dict[str, str] = {}
    for pf in PROFILE_FILES:
        path = POLICY_DIR / pf
        if path.exists():
            profiles[pf] = path.read_text()

    # Extract data per profile
    data: dict[str, dict[str, str]] = {}
    for pf, content in profiles.items():
        name = parse_yaml_field(content, "profile_name")
        data[name] = {
            "version": parse_yaml_field(content, "profile_version"),
            "required_panels": str(len(parse_required_panels(content))),
            "auto_merge": parse_auto_merge_enabled(content),
            "confidence": parse_auto_merge_confidence(content),
            "escalation": parse_escalation_threshold(content),
            "block": parse_block_confidence(content),
            "risk_agg": parse_risk_aggregation(content),
            "override_approvals": parse_override_approvals(content),
            "override_roles": parse_override_roles(content),
        }

    profile_names = list(data.keys())
    header = "| Feature | " + " | ".join(f"**{n}**" for n in profile_names) + " |"
    separator = "|---------|" + "|".join("------" for _ in profile_names) + "|"

    rows = [
        ("Profile Version", "version"),
        ("Required Panels (count)", "required_panels"),
        ("Auto-merge Enabled", "auto_merge"),
        ("Auto-merge Confidence Threshold", "confidence"),
        ("Escalation Threshold", "escalation"),
        ("Block Threshold", "block"),
        ("Risk Aggregation", "risk_agg"),
        ("Override Min Approvals", "override_approvals"),
        ("Override Required Roles", "override_roles"),
    ]

    lines.append(header)
    lines.append(separator)
    for label, key in rows:
        vals = " | ".join(data[n].get(key, "N/A") for n in profile_names)
        lines.append(f"| {label} | {vals} |")
    lines.append("")

    # Profile descriptions
    lines.append("## Profile Descriptions")
    lines.append("")
    for name, content in profiles.items():
        profile_name = parse_yaml_field(content, "profile_name")
        desc = _extract_yaml_description(content)
        lines.append(f"### {profile_name}")
        lines.append("")
        lines.append(desc if desc else "No description available.")
        lines.append("")

    # Required panels detail
    lines.append("## Required Panels by Profile")
    lines.append("")
    for name, content in profiles.items():
        profile_name = parse_yaml_field(content, "profile_name")
        panels = parse_required_panels(content)
        lines.append(f"### {profile_name}")
        lines.append("")
        for p in panels:
            lines.append(f"- {p}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generator: Prompt Index
# ---------------------------------------------------------------------------


def generate_prompt_index() -> str:
    """Generate docs/reference/prompt-index.md content."""
    lines = [
        "# Prompt Index",
        "",
        "Complete index of all governance prompts organized by type.",
        "",
        "> **Auto-generated** by `governance/bin/generate-catalog.py`.",
        "> Do not edit manually -- regenerate with `python governance/bin/generate-catalog.py`.",
        "",
    ]

    # Section 1: Review Panels
    lines.append("## Review Panels")
    lines.append("")
    lines.append("| Name | File | Purpose |")
    lines.append("|------|------|---------|")

    for panel_file in sorted(REVIEWS_DIR.glob("*.md")):
        name = panel_file.stem
        content = panel_file.read_text()
        purpose = extract_purpose(content)
        rel_path = f"governance/prompts/reviews/{panel_file.name}"
        lines.append(f"| {name} | `{rel_path}` | {purpose} |")

    lines.append("")

    # Section 2: Workflow Templates
    workflows_dir = PROMPTS_DIR / "workflows"
    if workflows_dir.exists():
        lines.append("## Workflow Prompts")
        lines.append("")
        lines.append("| Name | File | Purpose |")
        lines.append("|------|------|---------|")

        for wf_file in sorted(workflows_dir.glob("*.md")):
            if wf_file.name == "index.md":
                continue
            name = wf_file.stem.replace("-", " ").title()
            content = wf_file.read_text()
            purpose = extract_purpose(content)
            rel_path = f"governance/prompts/workflows/{wf_file.name}"
            lines.append(f"| {name} | `{rel_path}` | {purpose} |")

        lines.append("")

    # Section 3: Templates
    templates_dir = REPO_ROOT / "governance" / "templates" / "prompts"
    if templates_dir.exists():
        lines.append("## Templates")
        lines.append("")
        lines.append("| Name | File |")
        lines.append("|------|------|")

        for tmpl_file in sorted(templates_dir.glob("*.md")):
            name = tmpl_file.stem.replace("-", " ").title()
            rel_path = f"governance/templates/prompts/{tmpl_file.name}"
            lines.append(f"| {name} | `{rel_path}` |")

        lines.append("")

    # Section 4: Other Prompts (top-level governance/prompts/*.md)
    lines.append("## Other Prompts")
    lines.append("")
    lines.append("| Name | File |")
    lines.append("|------|------|")

    skip_names = {"shared-perspectives"}
    for prompt_file in sorted(PROMPTS_DIR.glob("*.md")):
        if prompt_file.stem in skip_names:
            continue
        name = prompt_file.stem.replace("-", " ").title()
        rel_path = f"governance/prompts/{prompt_file.name}"
        lines.append(f"| {name} | `{rel_path}` |")

    lines.append("")

    # Section 5: Shared Perspectives
    shared_path = PROMPTS_DIR / "shared-perspectives.md"
    if shared_path.exists():
        lines.append("## Shared Perspectives")
        lines.append("")
        lines.append(
            "Canonical definitions for perspectives appearing in 2+ review prompts."
        )
        lines.append(
            "Serves as the authoring-time DRY mechanism; compiled prompts have"
        )
        lines.append("full locality at runtime.")
        lines.append("")
        lines.append(f"- [`governance/prompts/shared-perspectives.md`](../../governance/prompts/shared-perspectives.md)")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    catalog = generate_panel_catalog()
    (OUTPUT_DIR / "panel-catalog.md").write_text(catalog)
    print(f"  Generated {OUTPUT_DIR / 'panel-catalog.md'}")

    comparison = generate_policy_comparison()
    (OUTPUT_DIR / "policy-comparison.md").write_text(comparison)
    print(f"  Generated {OUTPUT_DIR / 'policy-comparison.md'}")

    index = generate_prompt_index()
    (OUTPUT_DIR / "prompt-index.md").write_text(index)
    print(f"  Generated {OUTPUT_DIR / 'prompt-index.md'}")

    print("Done.")


if __name__ == "__main__":
    main()
