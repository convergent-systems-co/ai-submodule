# Plan: Skills System with .skill.md Support and MCP Auto-Discovery

**Issue:** #473
**Type:** Feature
**Status:** In Progress

## Objective

Add a skills system to the MCP server that enables `.skill.md` files to be auto-discovered and registered as MCP tools. Each skill file uses YAML frontmatter for metadata and Markdown body for instructions, allowing extensible skill-based tool registration.

## Scope

1. **`mcp-server/src/skills.ts`** -- New module implementing:
   - Zod schema for skill YAML frontmatter validation
   - Skill file loading and parsing (via existing `parseMarkdownWithFrontmatter`)
   - Directory scanning for `*.skill.md` files
   - MCP tool definition generation from loaded skills
   - Skill tool call handling (instruction + task concatenation)

2. **`mcp-server/skills/governance-review.skill.md`** -- First bundled skill:
   - Governance panel review execution instructions
   - Declares allowed tools (Read, Glob, Grep, Bash)
   - Documents the six required default-profile panels

3. **`mcp-server/src/tools.ts`** -- Integration:
   - Import skill discovery and registration functions
   - Make `registerTools` async to support skill discovery
   - Register discovered skills as `skill_*` MCP tools

4. **`mcp-server/src/index.ts`** -- Await updated async `registerTools`

5. **`mcp-server/package.json`** -- Add `skills/` to `files` array

6. **`mcp-server/tests/skills.test.ts`** -- Test coverage:
   - Valid skill loading
   - Invalid frontmatter rejection
   - Tool name generation (hyphen-to-underscore)
   - Skill discovery from directory
   - Tool call output construction

## Design Decisions

- Skills directory defaults to `mcp-server/skills/` (resolved relative to dist or src)
- Tool names use `skill_` prefix with hyphens converted to underscores
- Skill tool calls produce concatenated instruction + task text (no AI inference in the MCP server itself)
- Validation warnings are logged to stderr; invalid files are skipped, not fatal

## Risk Assessment

- **Low risk**: Additive feature, no existing behavior changes
- **Backward compatible**: Existing 5 tools remain unchanged
- **No breaking changes**: `registerTools` signature change is internal
