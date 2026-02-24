# Panel: Governance Compliance Review

## Purpose

Evaluate whether a pull request followed the required governance steps defined in `governance/prompts/startup.md`. This panel detects skipped governance gates — missing plans, missing panel evaluations, skipped Copilot reviews, missing documentation updates, and untracked work — and reports violations with severity classifications.

This panel acts as the governance step observer requested in issue #176. It enriches the Code Manager's monitoring capabilities by providing structured compliance evidence that the policy engine can evaluate.

## Participants

- **Governance Auditor** — Evaluates process compliance against the governance checklist
- **Code Manager** — Provides context on expected governance steps for the change type
- **Documentation Reviewer** — Verifies documentation completeness

## Process

1. Read the governance compliance checklist (`governance/prompts/governance-compliance-checklist.md`)
2. For each required step, gather evidence from the PR:
   - **Plan:** Check `.plans/` directory for a plan matching the issue number
   - **Panels:** Check `governance/emissions/` for required panel output files
   - **Copilot:** Check PR comments for Copilot polling evidence and recommendation responses
   - **Documentation:** Analyze the PR diff for documentation file changes
   - **Issue tracking:** Check PR body for issue references
   - **Review threads:** Query GraphQL for unresolved review threads
   - **CI checks:** Check PR check status
3. Classify each step as `passed`, `failed`, `skipped`, or `not_applicable`
4. Assign severity to any violations per the checklist
5. Determine overall compliance level (compliant, partially_compliant, non_compliant)
6. Emit structured output conforming to `governance/schemas/governance-compliance.schema.json`

## Output Format

### Per Step
- Step name
- Status (passed/failed/skipped/not_applicable)
- Evidence description
- Violation severity (if failed)

### Consolidated
- Overall compliance level
- Violation count by severity
- Specific remediation steps for each violation
- Confidence score

## Pass/Fail Criteria

| Criterion | Threshold | Blocked If |
|-----------|-----------|------------|
| Confidence score | >= 0.80 | Below 0.80 |
| Critical violations | 0 allowed | Any critical violation present |
| High violations | 0 allowed | Any high violation present |
| Medium violations | 2 max allowed | More than 2 medium violations |

When blocked, the panel emits a `block` verdict listing each violation with its severity and remediation path.

## Confidence Score Calculation

```
confidence = 0.95  (base — governance compliance is binary per step)
           - (critical_violations x 0.30)
           - (high_violations x 0.20)
           - (medium_violations x 0.05)
           - (low_violations x 0.01)
           = max(confidence, 0.0)  (floor)
```

| Violation Severity | Deduction | Example: 1 violation |
|-------------------|-----------|---------------------|
| Critical | -0.30 | 0.95 -> 0.65 |
| High | -0.20 | 0.95 -> 0.75 |
| Medium | -0.05 | 0.95 -> 0.90 |
| Low | -0.01 | 0.95 -> 0.94 |

## Evidence Sources

| Step | Primary Evidence | Secondary Evidence |
|------|-----------------|-------------------|
| Plan created | `.plans/{issue}-*.md` in PR diff | Plan referenced in PR body |
| Panel evaluation | `governance/emissions/*.json` files | Governance workflow run results |
| Copilot review | PR comments with Copilot polling | Copilot inline comments and responses |
| Documentation | Doc files in PR diff | Commit message `Docs:` annotation |
| Issue tracking | `Closes #N` in PR body | Issue comments referencing PR |
| Review threads | GraphQL `reviewThreads` query | PR review state |
| CI checks | `gh pr checks` status | Workflow run conclusions |

## Constraints

- Evaluate evidence, not intent — check for artifacts, not promises
- Do not re-run other panels; only verify their emissions exist
- Respect policy profile exceptions (e.g., `skip_panel_validation`)
- Report all violations, not just the first one found
- Provide actionable remediation for every violation
