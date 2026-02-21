# AI Instructions

Base instructions for AI assistants across all projects.

## Core Principles

- Be concise and direct
- Show, don't tell - prefer code over explanations
- Follow project conventions (see project-specific instructions)
- Ask clarifying questions when requirements are ambiguous
- Prefer iterative changes over large rewrites

## Code Quality

- Write idiomatic code for the language
- Include error handling
- Write testable code
- Follow existing patterns in the codebase

## Communication

- Use markdown formatting
- Link to relevant files when discussing code
- Provide context for suggestions

## Tools

- Use available MCP tools when they exist
- Prefer project-specific tooling over generic approaches
- Check `.ai/project.yaml` for project configuration

## Context Capacity Protocol

<!-- ANCHOR: This instruction must survive context resets -->

**Hard stop at 80% context capacity. No exceptions.**

When approaching 80% of context window:
1. Stop current work immediately — do not start new tasks
2. Ensure git working tree is clean (commit, stash, or abort in-progress merges)
3. Write a checkpoint to `.checkpoints/` with: current task, completed work, remaining work, git branch state
4. Summarize the checkpoint to the user
5. Request a context reset (`/clear`)

Never allow context to reach compaction with uncommitted changes, merge conflicts, or untracked state. A dirty compaction loses instructions and context that cannot be recovered.

<!-- /ANCHOR -->

---

*This file is inherited by all projects. Project-specific instructions extend this.*
