# Plan: Compress persona files to header-only format with on-demand loading (#556)

## Objective

Reduce persona file sizes from 5-10x the 500-token budget to near-budget by extracting headers, removing duplicated content, and referencing shared definitions.

## Approach

1. Add tier markers to persona files: `<!-- TIER_1_START -->` / `<!-- TIER_1_END -->`
2. Extract duplicated content to shared references:
   - CANCEL handling -> reference agent-protocol.md
   - Containment policy -> reference agent-containment.yaml
   - Capacity thresholds -> reference context-management.md
3. Move anti-patterns, mermaid diagrams, and interaction models below the Tier 1 boundary
4. Document the tiered loading protocol
