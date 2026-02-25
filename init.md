# Initialize Dark Factory Governance

> **Bootstrap script:** [`bin/init.sh`](bin/init.sh)

This guide covers setting up the Dark Factory Governance Platform as a git submodule in your project.

## Quick Start

### 1. Add the Submodule

```bash
git submodule add git@github.com:SET-Apps/ai-submodule.git .ai
```

### 2. Run the Bootstrap Script

```bash
bash .ai/bin/init.sh
```

This creates symlinks in your project root:
- `CLAUDE.md` → `.ai/instructions.md` (Claude Code instructions)
- `.cursorrules` → `.ai/instructions.md` (Cursor instructions)
- `.github/copilot-instructions.md` → `.ai/instructions.md` (GitHub Copilot instructions)

### 3. Commit the Submodule

```bash
git add .ai .gitmodules CLAUDE.md .cursorrules .github/copilot-instructions.md
git commit -m "chore: add Dark Factory governance submodule"
```

## Updating the Submodule

```bash
git submodule update --remote .ai
```

Then re-run `bash .ai/bin/init.sh` if the symlink configuration has changed.

## What's Included

| Directory | Contents |
|-----------|----------|
| `governance/personas/` | 42 AI reasoning roles + 2 agentic personas |
| `governance/personas/panels/` | 15 multi-persona review workflows |
| `governance/policy/` | 3 deterministic policy profiles (default, fin_pii_high, infrastructure_critical) |
| `governance/schemas/` | JSON schemas for structured emissions and panel configuration |
| `governance/prompts/` | Workflow prompts, templates (plan, runtime DI), startup loop |
| `docs/` | Architecture docs, context management, governance model |

## Configuration

- **`config.yaml`** — Defines symlinks created by `init.sh`
- **`panels.local.json`** — Optional per-project panel overrides (place in your project root). See `governance/schemas/panels.schema.json` for the format.
- **`instructions.md`** — Base instructions distributed to all AI tools via symlinks

## Next Steps

- Read [`governance/prompts/startup.md`](governance/prompts/startup.md) for the agentic improvement loop
- Review [`GOALS.md`](GOALS.md) for project roadmap
- See [`DEVELOPER_GUIDE.md`](DEVELOPER_GUIDE.md) for architecture overview
