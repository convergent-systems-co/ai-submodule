# Extension Authoring Guide

Create custom panels, phases, and hooks by dropping files into convention directories. No configuration changes required.

## Convention Directories

All extensions live under `.governance/extensions/` in your project root:

```
.governance/extensions/
  panels/          # Custom review panel prompts (.md)
  phases/          # Custom orchestrator phase scripts (.sh, .py)
  hooks/
    pre_dispatch/  # Run before Coder dispatch
    post_merge/    # Run after PR merge
    post_review/   # Run after panel reviews
```

## Custom Panels

Drop a `.md` file in `.governance/extensions/panels/`. Use frontmatter for metadata:

```markdown
---
name: business-logic-review
description: Reviews changes against business domain rules
version: 1.0.0
author: platform-team
---

# Business Logic Review

You are a reviewer specializing in business domain logic...

## Instructions

1. Check that business rules are correctly implemented
2. Verify domain model consistency
3. Ensure backward compatibility of domain events

## Output Format

Produce structured emission JSON per governance/schemas/panel-output.schema.json.
```

**Requirements:**
- File extension must be `.md`
- Frontmatter `name` is optional (defaults to filename stem)
- Panel output must follow `governance/schemas/panel-output.schema.json`

## Custom Phases

Drop a `.sh` or `.py` script in `.governance/extensions/phases/`:

```bash
#!/bin/bash
# Run custom linting after phase 3
set -euo pipefail

echo "Running business-specific linting..."
# Your linting logic here
```

**Naming convention:** Prefix with a phase number to control ordering:
- `03-lint.sh` — runs after phase 3
- `05-validate.py` — runs after phase 5
- `check.sh` — no automatic ordering (must be triggered explicitly)

**Requirements:**
- Must have a shebang line (`#!/bin/bash` or `#!/usr/bin/env python3`)
- Must exit 0 on success, non-zero on failure
- Default timeout: 300 seconds

## Custom Hooks

Drop scripts into hook-point subdirectories under `.governance/extensions/hooks/`:

| Hook Point | When It Runs | Use Case |
|------------|-------------|----------|
| `pre_dispatch` | Before Coder agents are dispatched | Environment setup, dependency checks |
| `post_merge` | After a PR is merged | Notifications, deployments, cleanup |
| `post_review` | After panel reviews complete | Custom reporting, metric collection |

Example:

```bash
#!/bin/bash
# Send Slack notification after merge
curl -X POST "$SLACK_WEBHOOK" -d '{"text": "PR merged successfully"}'
```

## Extension Catalog

The orchestrator automatically generates `.governance/extensions/catalog.json` listing all discovered extensions. This catalog is regenerated on every session init.

## Security Model

Extensions run within the same containment constraints as the governance pipeline. They do not have elevated privileges. Treat extension directories with the same security posture as your CI scripts.
