# Plan: Expand MCP server with full IDE prompt distribution

**Issue:** #594
**Type:** Feature
**Priority:** Medium

## Problem

MCP server provides governance review and ADO skills but doesn't distribute all 21 review prompts, personas, or developer prompts as individual MCP prompts.

## Solution

1. Register each review panel as an individual MCP prompt (not just via the generic governance_review prompt)
2. Register persona definitions as MCP prompts for IDE-based agent config
3. Add search_catalog tool for finding prompts by keyword
4. Add list_personas tool
5. Register developer prompts from prompts/global/ as MCP prompts

## Deliverables

1. Update `mcp-server/src/prompts.ts` — register all review panels and personas as prompts
2. Update `mcp-server/src/tools.ts` — add search_catalog and list_personas tools
3. Update `mcp-server/src/resources.ts` — add developer prompts as resources
4. Run tests
