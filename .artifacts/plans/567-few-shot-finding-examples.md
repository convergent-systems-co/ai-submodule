# Plan: Add finding-bearing few-shot examples to review panels (#567)

## Objective

Add concrete `request_changes` examples with findings, evidence, and remediation to the 8 review panels that currently only show "all approve" examples.

## Scope

8 panels need update:
1. jm-standards-compliance-review.md
2. threat-modeling.md
3. governance-compliance-review.md
4. data-governance-review.md
5. finops-review.md
6. threat-model-system.md
7. security-review.md
8. cost-analysis.md

## Approach

Replace the "all approve" emission example with a "request_changes" example showing:
- At least one `request_changes` verdict from a perspective
- 1-2 concrete findings with evidence
- Proper `policy_flags` with remediations
- Varying verdicts across perspectives (not all approve)
