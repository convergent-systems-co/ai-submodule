# Plan: Complete MCP server tool surface

**Issue:** #561
**Type:** Feature
**Priority:** High

## Problem

MCP server has 5 built-in tools + 2 skills. Missing critical tools for the complete governance workflow.

## Solution

Add the missing tools:
1. create_plan — write plans to .governance/plans/
2. write_emission — write validated emissions to .governance/panels/
3. read_checkpoint / write_checkpoint — checkpoint CRUD
4. get_governance_status — aggregate project governance posture
5. validate_project_yaml — schema validation for project.yaml
6. health_check — verify server, governance root, Python availability

Make list_policy_profiles dynamic. Add comprehensive documentation.

## Deliverables

1. Update mcp-server/src/tools.ts with new tools
2. Update docs/guides/mcp-server-usage.md with tool inventory
3. Run tests
