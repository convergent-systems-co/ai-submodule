#!/usr/bin/env python3
"""Generate an interactive HTML prompt catalog from prompt ``.md`` files.

Scans ``governance/prompts/reviews/`` and ``prompts/global/`` for ``.md``
files, extracts metadata (name, type, perspectives, pass/fail criteria),
computes SHA-256 content hashes, and produces:

1. A self-contained HTML catalog page with Nord theme, search, and filtering.
2. A ``catalog.json`` file with structured metadata for all prompts.

Standard library only — no third-party dependencies.

Usage::

    python bin/generate-html-catalog.py
    python bin/generate-html-catalog.py --output docs/catalog.html --catalog catalog.json
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

REVIEW_DIR = REPO_ROOT / "governance" / "prompts" / "reviews"
DEVELOPER_DIR = REPO_ROOT / "prompts" / "global"

DEFAULT_HTML_OUTPUT = REPO_ROOT / "docs" / "catalog.html"
DEFAULT_JSON_OUTPUT = REPO_ROOT / "catalog.json"

# Filenames to skip
EXCLUDED_FILENAMES = {"readme.md", "changelog.md", "index.md", "shared-perspectives.md"}

# ---------------------------------------------------------------------------
# Markdown / frontmatter parsing (stdlib only)
# ---------------------------------------------------------------------------


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown using regex (no PyYAML)."""
    match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return {}
    result: dict = {}
    for line in match.group(1).splitlines():
        m = re.match(r'^(\w[\w_-]*):\s*(.+)$', line)
        if m:
            key = m.group(1).strip()
            val = m.group(2).strip().strip("\"'")
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
            result[key] = val
    return result


def extract_h1(content: str) -> str:
    """Extract the first H1 heading from markdown content."""
    m = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return m.group(1).strip() if m else ""


def extract_purpose(content: str) -> str:
    """Extract the Purpose section text (first paragraph after ## Purpose)."""
    m = re.search(r"^##\s+Purpose\s*\n+(.+?)(?:\n\n|\n##|\Z)", content, re.MULTILINE | re.DOTALL)
    if m:
        text = m.group(1).strip()
        # Take first paragraph only
        text = text.split("\n\n")[0]
        # Clean markdown formatting
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        text = re.sub(r"\*([^*]+)\*", r"\1", text)
        return text.replace("\n", " ").strip()
    return ""


def extract_description_from_frontmatter(fm: dict) -> str:
    """Get description from frontmatter."""
    desc = fm.get("description", "")
    if isinstance(desc, str):
        return desc.strip().strip("\"'")
    return ""


def extract_perspectives(content: str, prompt_type: str) -> list[str]:
    """Extract perspective names from ## Perspectives section for review panels."""
    if prompt_type != "review":
        return []

    # Find the Perspectives section
    m = re.search(r"^##\s+Perspectives?\s*\n(.*?)(?=\n##\s[^#]|\Z)", content, re.MULTILINE | re.DOTALL)
    if not m:
        # Try looking at Review Tracks for threat-modeling style
        m = re.search(r"^##\s+Review Tracks.*?\n(.*?)(?=\n##\s+Process|\n---\s*\n##|\Z)", content, re.MULTILINE | re.DOTALL)

    if not m:
        return []

    section = m.group(1)
    perspectives = []

    # Match ### headings that are perspective names
    for match in re.finditer(r"^###\s+(?:\d+\.\s+)?(.+)$", section, re.MULTILINE):
        name = match.group(1).strip()
        # Filter out non-perspective headings
        skip_prefixes = (
            "Per ", "Consolidated", "Execution", "Example", "Grounding",
            "Structured", "Issue Update", "GitHub Pages",
        )
        skip_contains = (
            "Requirement", "Behavior", "Convention", "Discipline",
            "Constraint",
        )
        if any(name.startswith(p) for p in skip_prefixes):
            continue
        if any(s in name for s in skip_contains):
            continue
        # Track-level headings for threat modeling
        if name.startswith("Track "):
            continue
        perspectives.append(name)

    return perspectives


def extract_pass_fail(content: str) -> list[str]:
    """Extract pass/fail criteria from the markdown content."""
    criteria = []
    m = re.search(r"^##\s+Pass/Fail Criteria\s*\n(.*?)(?=\n##|\Z)", content, re.MULTILINE | re.DOTALL)
    if not m:
        return criteria

    section = m.group(1)
    # Parse table rows
    for row in re.finditer(r"\|\s*(.+?)\s*\|\s*(.+?)\s*\|", section):
        key = row.group(1).strip()
        val = row.group(2).strip()
        if key.lower() in ("criterion", "---", ""):
            continue
        if "---" in key:
            continue
        criteria.append(f"{key}: {val}")

    return criteria


def extract_categories(filename: str, content: str) -> list[str]:
    """Derive categories from filename and content patterns."""
    cats = []
    name_lower = filename.lower()

    if "security" in name_lower or "threat" in name_lower:
        cats.append("security")
    if "cost" in name_lower or "finops" in name_lower:
        cats.append("cost-optimization")
    if "code-review" in name_lower or "testing" in name_lower or "test-generation" in name_lower:
        cats.append("code-quality")
    if "architecture" in name_lower or "design" in name_lower:
        cats.append("architecture")
    if "data" in name_lower or "governance" in name_lower:
        cats.append("data-governance")
    if "documentation" in name_lower:
        cats.append("documentation")
    if "performance" in name_lower:
        cats.append("performance")
    if "compliance" in name_lower or "standards" in name_lower:
        cats.append("compliance")
    if "migration" in name_lower:
        cats.append("operations")
    if "production" in name_lower or "copilot" in name_lower:
        cats.append("operations")
    if "technical-debt" in name_lower or "refactor" in name_lower:
        cats.append("code-quality")
    if "ai-expert" in name_lower:
        cats.append("ai-safety")
    if "debug" in name_lower:
        cats.append("debugging")
    if "plan" in name_lower:
        cats.append("planning")
    if "explain" in name_lower or "context" in name_lower:
        cats.append("comprehension")
    if "pr-" in name_lower or "git-review" in name_lower:
        cats.append("workflow")
    if "release" in name_lower:
        cats.append("workflow")
    if "write-tests" in name_lower:
        cats.append("testing")

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for c in cats:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    return unique if unique else ["general"]


# ---------------------------------------------------------------------------
# Catalog entry builder
# ---------------------------------------------------------------------------


def compute_sha256(file_path: Path) -> str:
    """Return sha256:hex_digest for a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def build_entry(file_path: Path, prompt_type: str) -> dict:
    """Build a catalog entry dict from a prompt markdown file."""
    content = file_path.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)

    # Name: from frontmatter or H1 or filename
    h1 = extract_h1(content)
    stem = file_path.stem.replace(".prompt", "")
    name = fm.get("name", h1 if h1 else stem.replace("-", " ").title())
    if isinstance(name, list):
        name = name[0] if name else stem

    # Clean "Review: " prefix for display
    display_name = re.sub(r"^Review:\s*", "", str(name))

    # Description / purpose
    description = extract_description_from_frontmatter(fm)
    if not description:
        description = extract_purpose(content)

    rel_path = str(file_path.relative_to(REPO_ROOT)).replace("\\", "/")
    perspectives = extract_perspectives(content, prompt_type)
    pass_fail = extract_pass_fail(content)
    categories = extract_categories(file_path.stem, content)

    return {
        "name": stem,
        "display_name": display_name,
        "type": prompt_type,
        "path": rel_path,
        "description": description,
        "perspectives": perspectives,
        "perspective_count": len(perspectives),
        "categories": categories,
        "pass_fail_criteria": pass_fail,
        "content_hash": compute_sha256(file_path),
        "last_updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------


def scan_directory(directory: Path, prompt_type: str) -> list[dict]:
    """Scan a directory for prompt .md files and build entries."""
    entries = []
    if not directory.exists():
        print(f"  WARNING: directory not found: {directory}", file=sys.stderr)
        return entries

    for fp in sorted(directory.glob("*.md")):
        if not fp.is_file():
            continue
        if fp.name.lower() in EXCLUDED_FILENAMES:
            continue
        try:
            entry = build_entry(fp, prompt_type)
            entries.append(entry)
        except Exception as exc:
            print(f"  WARNING: skipping {fp.name}: {exc}", file=sys.stderr)

    return entries


def build_catalog() -> list[dict]:
    """Build the full catalog from both prompt directories."""
    entries = []
    entries.extend(scan_directory(REVIEW_DIR, "review"))
    entries.extend(scan_directory(DEVELOPER_DIR, "developer"))
    return entries


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

NORD_CSS = """
:root {
  --nord0: #2e3440; --nord1: #3b4252; --nord2: #434c5e; --nord3: #4c566a;
  --nord4: #d8dee9; --nord5: #e5e9f0; --nord6: #eceff4;
  --nord7: #8fbcbb; --nord8: #88c0d0; --nord9: #81a1c1; --nord10: #5e81ac;
  --nord11: #bf616a; --nord12: #d08770; --nord13: #ebcb8b; --nord14: #a3be8c; --nord15: #b48ead;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  background: var(--nord0); color: var(--nord4); line-height: 1.6;
  min-height: 100vh;
}
.container { max-width: 1200px; margin: 0 auto; padding: 2rem 1.5rem; }
header { text-align: center; margin-bottom: 2.5rem; }
header h1 { font-size: 2rem; color: var(--nord6); margin-bottom: 0.5rem; }
header p { color: var(--nord3); font-size: 0.95rem; }
.controls { display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 2rem; align-items: center; }
.search-box {
  flex: 1; min-width: 250px; padding: 0.7rem 1rem; border-radius: 6px;
  border: 1px solid var(--nord3); background: var(--nord1); color: var(--nord6);
  font-size: 0.95rem; outline: none; transition: border-color 0.2s;
}
.search-box:focus { border-color: var(--nord8); }
.search-box::placeholder { color: var(--nord3); }
.filter-buttons { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.filter-btn {
  padding: 0.5rem 1rem; border-radius: 6px; border: 1px solid var(--nord3);
  background: var(--nord1); color: var(--nord4); cursor: pointer;
  font-size: 0.85rem; transition: all 0.2s;
}
.filter-btn:hover { background: var(--nord2); border-color: var(--nord8); }
.filter-btn.active { background: var(--nord10); border-color: var(--nord10); color: var(--nord6); }
.stats { display: flex; gap: 2rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.stat { font-size: 0.85rem; color: var(--nord3); }
.stat strong { color: var(--nord8); font-size: 1.1rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 1.25rem; }
.card {
  background: var(--nord1); border: 1px solid var(--nord2); border-radius: 8px;
  padding: 1.25rem; cursor: pointer; transition: all 0.2s;
  display: flex; flex-direction: column;
}
.card:hover { border-color: var(--nord8); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.6rem; }
.card-title { font-size: 1.05rem; font-weight: 600; color: var(--nord6); }
.badge {
  display: inline-block; padding: 0.15rem 0.55rem; border-radius: 4px;
  font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em;
  flex-shrink: 0; margin-left: 0.5rem;
}
.badge-review { background: var(--nord10); color: var(--nord6); }
.badge-developer { background: var(--nord14); color: var(--nord0); }
.card-desc { font-size: 0.85rem; color: var(--nord3); margin-bottom: 0.75rem; flex: 1;
  display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.card-meta { display: flex; gap: 1rem; font-size: 0.78rem; color: var(--nord3); flex-wrap: wrap; }
.card-meta span { display: inline-flex; align-items: center; gap: 0.3rem; }
.detail-overlay {
  display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6);
  z-index: 1000; justify-content: center; align-items: flex-start; padding: 3rem 1rem;
  overflow-y: auto;
}
.detail-overlay.active { display: flex; }
.detail-panel {
  background: var(--nord1); border: 1px solid var(--nord2); border-radius: 10px;
  max-width: 700px; width: 100%; padding: 2rem; position: relative;
  max-height: 85vh; overflow-y: auto;
}
.detail-close {
  position: absolute; top: 1rem; right: 1rem; background: none; border: none;
  color: var(--nord3); font-size: 1.5rem; cursor: pointer; line-height: 1;
}
.detail-close:hover { color: var(--nord11); }
.detail-panel h2 { color: var(--nord6); margin-bottom: 0.5rem; font-size: 1.3rem; }
.detail-panel .detail-type { margin-bottom: 1rem; }
.detail-section { margin-top: 1.25rem; }
.detail-section h3 { color: var(--nord8); font-size: 0.95rem; margin-bottom: 0.5rem; border-bottom: 1px solid var(--nord2); padding-bottom: 0.3rem; }
.detail-section ul { list-style: none; padding: 0; }
.detail-section li { padding: 0.25rem 0; font-size: 0.88rem; color: var(--nord4); }
.detail-section li::before { content: "\\2022"; color: var(--nord8); margin-right: 0.5rem; }
.detail-path { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.8rem; color: var(--nord3); background: var(--nord0); padding: 0.3rem 0.6rem; border-radius: 4px; display: inline-block; margin-top: 0.5rem; word-break: break-all; }
.detail-hash { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.75rem; color: var(--nord3); word-break: break-all; }
.tag-list { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.4rem; }
.tag {
  display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px;
  font-size: 0.72rem; background: var(--nord2); color: var(--nord4);
}
footer { text-align: center; margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid var(--nord2); color: var(--nord3); font-size: 0.8rem; }
.no-results { text-align: center; padding: 3rem 1rem; color: var(--nord3); font-size: 1rem; display: none; }
@media (max-width: 600px) {
  .grid { grid-template-columns: 1fr; }
  .controls { flex-direction: column; }
  header h1 { font-size: 1.5rem; }
}
"""

JS_CODE = """
const catalog = CATALOG_DATA_PLACEHOLDER;

let activeFilter = 'all';
let searchTerm = '';

function init() {
  renderCards(catalog);
  updateStats(catalog);
  document.getElementById('search').addEventListener('input', onSearch);
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => onFilter(btn));
  });
  document.getElementById('overlay').addEventListener('click', (e) => {
    if (e.target === e.currentTarget) closeDetail();
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeDetail();
  });
}

function onSearch(e) {
  searchTerm = e.target.value.toLowerCase();
  applyFilters();
}

function onFilter(btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  activeFilter = btn.dataset.filter;
  applyFilters();
}

function applyFilters() {
  const filtered = catalog.filter(item => {
    const matchType = activeFilter === 'all' || item.type === activeFilter;
    if (!matchType) return false;
    if (!searchTerm) return true;
    const haystack = [
      item.display_name, item.name, item.description,
      item.type, ...item.categories, ...(item.perspectives || [])
    ].join(' ').toLowerCase();
    return haystack.includes(searchTerm);
  });
  renderCards(filtered);
  updateStats(filtered);
}

function renderCards(items) {
  const grid = document.getElementById('grid');
  const noResults = document.getElementById('no-results');
  if (items.length === 0) {
    grid.innerHTML = '';
    noResults.style.display = 'block';
    return;
  }
  noResults.style.display = 'none';
  grid.innerHTML = items.map((item, i) => {
    const badgeClass = item.type === 'review' ? 'badge-review' : 'badge-developer';
    const badgeLabel = item.type === 'review' ? 'Review Panel' : 'Developer Prompt';
    const desc = escapeHtml(item.description || 'No description available.');
    const perspCount = item.perspective_count || 0;
    const catTags = (item.categories || []).map(c => '<span class="tag">' + escapeHtml(c) + '</span>').join('');
    return '<div class="card" onclick="showDetail(' + i + ')" data-idx="' + i + '">' +
      '<div class="card-header"><span class="card-title">' + escapeHtml(item.display_name) + '</span>' +
      '<span class="badge ' + badgeClass + '">' + badgeLabel + '</span></div>' +
      '<div class="card-desc">' + desc + '</div>' +
      '<div class="tag-list">' + catTags + '</div>' +
      '<div class="card-meta">' +
      (perspCount > 0 ? '<span>' + perspCount + ' perspectives</span>' : '') +
      '<span>' + escapeHtml(item.last_updated) + '</span>' +
      '</div></div>';
  }).join('');
}

function updateStats(items) {
  const total = items.length;
  const reviews = items.filter(i => i.type === 'review').length;
  const devs = items.filter(i => i.type === 'developer').length;
  document.getElementById('stats').innerHTML =
    '<div class="stat"><strong>' + total + '</strong> prompts</div>' +
    '<div class="stat"><strong>' + reviews + '</strong> review panels</div>' +
    '<div class="stat"><strong>' + devs + '</strong> developer prompts</div>';
}

function showDetail(idx) {
  const item = catalog[idx];
  if (!item) return;
  const overlay = document.getElementById('overlay');
  const panel = document.getElementById('detail-panel');
  const badgeClass = item.type === 'review' ? 'badge-review' : 'badge-developer';
  const badgeLabel = item.type === 'review' ? 'Review Panel' : 'Developer Prompt';

  let html = '<button class="detail-close" onclick="closeDetail()">&times;</button>';
  html += '<h2>' + escapeHtml(item.display_name) + '</h2>';
  html += '<div class="detail-type"><span class="badge ' + badgeClass + '">' + badgeLabel + '</span></div>';

  if (item.description) {
    html += '<p style="color:var(--nord4);font-size:0.9rem;margin-bottom:0.5rem;">' + escapeHtml(item.description) + '</p>';
  }

  html += '<div class="detail-path">' + escapeHtml(item.path) + '</div>';

  if (item.perspectives && item.perspectives.length > 0) {
    html += '<div class="detail-section"><h3>Perspectives (' + item.perspectives.length + ')</h3><ul>';
    item.perspectives.forEach(p => { html += '<li>' + escapeHtml(p) + '</li>'; });
    html += '</ul></div>';
  }

  if (item.categories && item.categories.length > 0) {
    html += '<div class="detail-section"><h3>Categories</h3><div class="tag-list">';
    item.categories.forEach(c => { html += '<span class="tag">' + escapeHtml(c) + '</span>'; });
    html += '</div></div>';
  }

  if (item.pass_fail_criteria && item.pass_fail_criteria.length > 0) {
    html += '<div class="detail-section"><h3>Pass/Fail Criteria</h3><ul>';
    item.pass_fail_criteria.forEach(c => { html += '<li>' + escapeHtml(c) + '</li>'; });
    html += '</ul></div>';
  }

  html += '<div class="detail-section"><h3>Version Info</h3>';
  html += '<p class="detail-hash">Hash: ' + escapeHtml(item.content_hash) + '</p>';
  html += '<p style="font-size:0.8rem;color:var(--nord3);margin-top:0.3rem;">Last updated: ' + escapeHtml(item.last_updated) + '</p>';
  html += '</div>';

  panel.innerHTML = html;
  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';
}

function closeDetail() {
  document.getElementById('overlay').classList.remove('active');
  document.body.style.overflow = '';
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str || '';
  return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', init);
"""


def generate_html(catalog_entries: list[dict], generated_at: str) -> str:
    """Generate a self-contained HTML page from catalog entries."""
    catalog_json = json.dumps(catalog_entries, indent=None, ensure_ascii=False)
    js = JS_CODE.replace("CATALOG_DATA_PLACEHOLDER", catalog_json)

    review_count = sum(1 for e in catalog_entries if e["type"] == "review")
    dev_count = sum(1 for e in catalog_entries if e["type"] == "developer")
    total = len(catalog_entries)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Governance Prompt Catalog</title>
<style>{NORD_CSS}</style>
</head>
<body>
<div class="container">
  <header>
    <h1>AI Governance Prompt Catalog</h1>
    <p>{total} prompts &mdash; {review_count} review panels + {dev_count} developer prompts</p>
  </header>

  <div class="controls">
    <input type="text" id="search" class="search-box" placeholder="Search prompts by name, category, or perspective..." />
    <div class="filter-buttons">
      <button class="filter-btn active" data-filter="all">All ({total})</button>
      <button class="filter-btn" data-filter="review">Review Panels ({review_count})</button>
      <button class="filter-btn" data-filter="developer">Developer Prompts ({dev_count})</button>
    </div>
  </div>

  <div class="stats" id="stats"></div>

  <div class="grid" id="grid"></div>
  <div class="no-results" id="no-results">No prompts match your search.</div>

  <div class="detail-overlay" id="overlay">
    <div class="detail-panel" id="detail-panel"></div>
  </div>

  <footer>
    Generated on {html.escape(generated_at)} &bull; AI Governance Platform &bull;
    <a href="https://github.com/convergent-systems-co/dark-forge" style="color:var(--nord8);text-decoration:none;">convergent-systems-co/dark-forge</a>
  </footer>
</div>
<script>{js}</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate an interactive HTML prompt catalog."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_HTML_OUTPUT,
        help=f"Output HTML file (default: {DEFAULT_HTML_OUTPUT.relative_to(REPO_ROOT)})",
    )
    parser.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_JSON_OUTPUT,
        help=f"Output catalog JSON file (default: {DEFAULT_JSON_OUTPUT.relative_to(REPO_ROOT)})",
    )
    args = parser.parse_args()

    # Resolve paths
    html_out = args.output if args.output.is_absolute() else REPO_ROOT / args.output
    json_out = args.catalog if args.catalog.is_absolute() else REPO_ROOT / args.catalog

    print(f"Scanning review panels: {REVIEW_DIR}")
    print(f"Scanning developer prompts: {DEVELOPER_DIR}")

    catalog = build_catalog()
    review_count = sum(1 for e in catalog if e["type"] == "review")
    dev_count = sum(1 for e in catalog if e["type"] == "developer")
    print(f"  Found {len(catalog)} prompts ({review_count} review panels, {dev_count} developer prompts)")

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Write catalog.json
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  Written: {json_out}")

    # Write HTML
    html_out.parent.mkdir(parents=True, exist_ok=True)
    html_content = generate_html(catalog, generated_at)
    html_out.write_text(html_content, encoding="utf-8")
    print(f"  Written: {html_out}")

    # Validation
    if len(catalog) == 0:
        print("  ERROR: No prompts found!", file=sys.stderr)
        return 1

    # Validate JSON is parseable
    try:
        json.loads(json_out.read_text(encoding="utf-8"))
        print("  catalog.json: valid JSON")
    except json.JSONDecodeError as exc:
        print(f"  ERROR: catalog.json is invalid JSON: {exc}", file=sys.stderr)
        return 1

    # Verify all entries have required fields
    required = {"name", "display_name", "type", "path", "content_hash", "last_updated"}
    for i, entry in enumerate(catalog):
        missing = required - set(entry.keys())
        if missing:
            print(f"  ERROR: entry {i} ({entry.get('name', '?')}) missing fields: {missing}", file=sys.stderr)
            return 1

    print(f"  All {len(catalog)} entries validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
