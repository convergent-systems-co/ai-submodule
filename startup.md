# Startup

> **Canonical source:** [`governance/prompts/startup.md`](governance/prompts/startup.md)

This file is a convenience entry point. The full agentic startup loop — including issue scanning, prioritization, validation, execution, review, and context capacity management — is defined in the canonical source above.

## Quick Start

To invoke the agentic improvement loop:

1. **Claude Code:** Run `/startup` or reference `governance/prompts/startup.md`
2. **Other agents:** Load `governance/prompts/startup.md` as the entry point instruction

## What the Startup Loop Does

1. Scans open GitHub issues
2. Filters for actionable (no branch, not blocked/refine/wontfix/duplicate)
3. Prioritizes by label (P0 > P1 > P2 > P3 > P4), then creation date
4. Validates intent clarity
5. Creates plan, executes via Coder persona
6. Monitors PR through CI checks and Copilot review
7. Merges when governance approves
8. Checkpoints after each issue (max 3 per session)

## Key Constraints

- **Maximum 3 issues per session** — hard cap
- **80% context capacity** — hard stop, checkpoint, request `/clear`
- **Sequential execution** — one issue at a time
- **Every issue gets a plan** before implementation
