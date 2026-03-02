# Plan: Implement tiered threat modeling based on change risk (#568)

## Objective

Add a fast-path risk classifier to the threat-modeling prompt so low-risk PRs (docs, config, <10 lines) receive an abbreviated 4-section model instead of the full 15-section template.

## Scope

| File | Action |
|------|--------|
| `governance/prompts/reviews/threat-modeling.md` | Modify — add tiered classifier and abbreviated template |
| `governance/prompts/reviews/threat-model-system.md` | Modify — add scope clarification vs per-PR threat-modeling |
| `governance/policy/default.yaml` | Modify — add threat model tier configuration |

## Approach

1. Add a "Risk Classification" section at the top of threat-modeling.md that classifies changes
2. Define two tiers: Standard (abbreviated) and Full
3. Standard: 4 required sections (Attack Surface Summary, Trust Boundary Impact, Mitigation Recommendations, Structured Emission)
4. Full: all 15 sections (auth, infra, data handling changes)
5. Add classification criteria based on file types, line count, and content patterns
6. Add scope note to threat-model-system.md clarifying it's for on-demand system-level assessment
