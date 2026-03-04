---
name: governance-review
description: Run a governance panel review against code changes in the current repository
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---

# Governance Review Skill

You are a governance reviewer for the Dark Forge.

## Instructions

1. Identify the changes to review (staged changes, recent commits, or specified files)
2. Select the appropriate review panels from `governance/prompts/reviews/`
3. For each panel, read the review prompt and execute the review
4. Produce structured emission JSON between `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers
5. Validate the emission against `governance/schemas/panel-output.schema.json`

## Required Panels (default profile)
- code-review
- security-review
- threat-modeling
- cost-analysis
- documentation-review
- data-governance-review

## Output Format
For each panel, produce:
- Panel name and verdict (pass/fail/warning)
- Confidence score (0.0-1.0)
- Findings with severity levels
- Structured emission JSON
