# Developer Prompt Library with Dynamic Discovery

**Author:** Team Lead (agent)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/469
**Branch:** NETWORK_ID/feat/469/developer-prompt-library

---

## 1. Objective

Add a developer prompt library to the MCP server that dynamically discovers `*.prompt.md` files from the `prompts/` directory and registers them as MCP prompts. Ship 12 global developer prompts covering common workflows (code review, debugging, planning, PR creation, etc.).

## 2. Rationale

The MCP server currently has only 3 hardcoded governance prompts. Developers need reusable, high-quality prompts for everyday tasks. A file-based discovery system allows prompts to be added by dropping a markdown file with YAML frontmatter into the `prompts/` directory without modifying server code.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Hardcode all prompts in prompts.ts | Yes | Does not scale; requires code changes for each new prompt |
| JSON config file listing prompts | Yes | Redundant — frontmatter in the markdown files already provides metadata |
| Dynamic discovery from `prompts/**/*.prompt.md` | Yes — **selected** | Zero-config, convention-based, extensible |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `.governance/plans/469-developer-prompt-library.md` | This plan |

### Files to Modify

| File | Change |
|------|--------|
| `mcp-server/src/prompts.ts` | Add `discoverAndRegisterPrompts()` function |
| `mcp-server/src/index.ts` | Call `discoverAndRegisterPrompts` after `registerPrompts` |
| `mcp-server/package.json` | Add `prompts/` to `files` array for npm distribution |

### Files Already Created (by previous agent)

| File | Purpose |
|------|---------|
| `prompts/global/*.prompt.md` (12 files) | Global developer prompt library |

## 4. Implementation Details

The `discoverAndRegisterPrompts` function will:
1. Recursively scan `{governanceRoot}/prompts/` for `*.prompt.md` files
2. Parse YAML frontmatter using existing `parseMarkdownWithFrontmatter` from `utils.ts`
3. Register each file as an MCP prompt where `name` from frontmatter is the prompt ID and `description` is the description
4. The prompt handler returns the full markdown content (after frontmatter) as the prompt message

## 5. Testing

- Build verification: `npm run build` must succeed
- Manual: connect MCP client and verify all 15 prompts are listed (3 static + 12 discovered)

## 6. Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Malformed frontmatter in a prompt file | Skip file with stderr warning, do not crash server |
| Missing `name` field in frontmatter | Skip file with stderr warning |
| Duplicate name conflicts with static prompts | Discovered prompts run after static registration; log warning if duplicate detected |

## 7. Rollback

Revert the commit. Static prompts remain unaffected.
