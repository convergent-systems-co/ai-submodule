# Developer Prompt Library

The platform includes 12 production-ready developer prompts in `prompts/global/` that provide standardized workflows for common development tasks. These prompts are available via the MCP server and directly from the filesystem.

## Available Prompts

| Name | File | Description | Tags | Status |
|------|------|-------------|------|--------|
| global-dev-code-review | `prompts/global/global-dev-code-review.prompt.md` | Review code for quality, security, performance | dev, review, security, quality | production |
| global-dev-context-summary | `prompts/global/global-dev-context-summary.prompt.md` | Generate brief code context summary | dev, summary, context | production |
| global-dev-debug | `prompts/global/global-dev-debug.prompt.md` | Debug issues and troubleshoot errors | dev, debug, troubleshooting | production |
| global-dev-explain | `prompts/global/global-dev-explain.prompt.md` | Explain code sections and design patterns | dev, explain, documentation | production |
| global-dev-git-review | `prompts/global/global-dev-git-review.prompt.md` | Review git history and commit changes | dev, review, git, history | production |
| global-dev-plan-create | `prompts/global/global-dev-plan-create.prompt.md` | Create implementation plans | dev, planning, strategy | production |
| global-dev-plan-execute | `prompts/global/global-dev-plan-execute.prompt.md` | Execute plans and track progress | dev, execution, tracking | production |
| global-dev-pr-create | `prompts/global/global-dev-pr-create.prompt.md` | Create pull requests with structured summaries | dev, pr, review | production |
| global-dev-pr-review | `prompts/global/global-dev-pr-review.prompt.md` | Review pull requests | dev, pr, review, quality | production |
| global-dev-refactor | `prompts/global/global-dev-refactor.prompt.md` | Refactor code for clarity and performance | dev, refactor, improvement | production |
| global-dev-release-notes | `prompts/global/global-dev-release-notes.prompt.md` | Generate release notes and changelogs | dev, docs, release | production |
| global-dev-write-tests | `prompts/global/global-dev-write-tests.prompt.md` | Write comprehensive tests | dev, testing, quality | production |

## Frontmatter Schema

Every prompt file uses YAML frontmatter with the following fields:

```yaml
---
name: global-dev-code-review          # Machine-readable identifier (kebab-case)
description: Review code for quality   # Short purpose description
status: production                     # Maturity: draft | production | deprecated
tags: [dev, review, security]          # Categorization tags
model: null                            # Model override (null = system default)
---
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Machine-readable prompt identifier (kebab-case) |
| `description` | string | Yes | Short description of what the prompt does |
| `status` | enum | Yes | Maturity level: `draft`, `production`, or `deprecated` |
| `tags` | array of strings | Yes | Categorization keywords |
| `model` | string \| null | No | Model override; `null` uses the system default |

## Usage

### Via MCP Server

When the MCP server is running, prompts are available as resources:

```
governance://prompts/global/{prompt-name}
```

The MCP server reads prompt files, extracts frontmatter metadata, and serves the content to any MCP-compatible IDE or AI assistant.

### Via Filesystem

Read prompts directly from the `prompts/global/` directory:

```bash
# In this repository
cat prompts/global/global-dev-code-review.prompt.md

# In a consuming repository
cat .ai/prompts/global/global-dev-code-review.prompt.md
```

## Prompt Catalog

The prompt catalog system auto-generates a machine-readable JSON index of all prompts.

### Catalog File

`catalog/prompt-catalog.json` contains:

```json
{
  "version": "1.0.0",
  "generated_at": "2026-01-15T10:30:00Z",
  "prompt_count": 12,
  "prompts": [
    {
      "id": "global/global-dev-code-review",
      "name": "global-dev-code-review",
      "description": "Review code for quality, security, performance",
      "status": "production",
      "tags": ["dev", "review", "security", "quality"],
      "model": null,
      "file_path": "prompts/global/global-dev-code-review.prompt.md",
      "content_hash": "a1b2c3...",
      "last_modified": "2026-01-15T10:00:00Z"
    }
  ]
}
```

### Generating the Catalog

```bash
# Generate catalog (default paths)
python bin/generate-prompt-catalog.py

# Custom paths
python bin/generate-prompt-catalog.py \
  --prompts-dir prompts/ \
  --output catalog/prompt-catalog.json

# Validate only (no write)
python bin/generate-prompt-catalog.py --validate
```

The generator:
1. Scans `prompts/` recursively for `*.prompt.md` files
2. Extracts YAML frontmatter from each file
3. Computes SHA-256 content hashes
4. Queries git for last-modified timestamps (falls back to filesystem mtime)
5. Validates output against `governance/schemas/prompt-catalog.schema.json`
6. Writes pretty-printed JSON to `catalog/prompt-catalog.json`

### CI Automation

The `prompt-catalog.yml` workflow automatically regenerates the catalog when prompts change:

- **Trigger:** Push to `main` with changes in `prompts/**`
- **Action:** Runs `generate-prompt-catalog.py --validate`, commits if catalog changed
- **Commit message:** `chore: regenerate prompt catalog [skip ci]`

### Catalog Schema

The catalog JSON is validated against `governance/schemas/prompt-catalog.schema.json`. Each prompt entry includes:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Derived from file path (e.g., `global/global-dev-code-review`) |
| `name` | string | From frontmatter `name` field |
| `description` | string | From frontmatter `description` field |
| `status` | enum | `draft`, `production`, or `deprecated` |
| `tags` | array | From frontmatter `tags` field |
| `model` | string \| null | From frontmatter `model` field |
| `file_path` | string | Relative path to the prompt file |
| `content_hash` | string | SHA-256 hex digest (64 characters) |
| `last_modified` | string | ISO 8601 UTC timestamp |

## Adding a New Prompt

1. Create a file in `prompts/global/` following the naming convention: `global-dev-{purpose}.prompt.md`

2. Add YAML frontmatter:
   ```yaml
   ---
   name: global-dev-my-task
   description: Short description of what this prompt does
   status: draft
   tags: [dev, relevant-tag]
   model: null
   ---
   ```

3. Write the prompt body in Markdown below the frontmatter

4. Regenerate the catalog:
   ```bash
   python bin/generate-prompt-catalog.py
   ```

5. The `prompt-catalog.yml` CI workflow will also regenerate on push to `main`

## Related Documents

- [Prompt Index](../reference/prompt-index.md) — Complete index of all governance prompts
- [MCP Server Usage](mcp-server-usage.md) — Accessing prompts via MCP
- [Skills Development](skills-development.md) — Building MCP skills
