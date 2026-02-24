# Panel: Test Generation Review

## Purpose
Evaluate test coverage, verification requirements, and proof-of-correctness criteria for code changes. Emits structured test requirements as JSON that consuming repos validate via their own CI. This panel does not execute tests — it assesses whether the change has adequate test governance.

## Participants
- **Quality Engineer** — Test coverage, test patterns, edge cases
- **Security Auditor** — Security-relevant test coverage, fuzz testing
- **Domain Expert** — Business logic verification, acceptance criteria mapping

## Evaluate For
Changes that modify executable code or business logic:
- `src/**`, `lib/**`, `pkg/**`, `app/**`
- Files matching language-specific source patterns
- Excludes: documentation-only changes, config files, governance artifacts

## Output Format
### Per Participant
- Perspective name
- Test coverage assessment
- Missing test scenarios
- Verification level recommendation
- Risk level

### Consolidated
- Current test coverage estimate (if CI reports are available)
- Coverage gap analysis
- Required test types (unit, integration, e2e, property, fuzz)
- Proof-of-correctness assessment
- Mutation testing recommendation
- Test generation requirements (structured JSON per `governance/schemas/test-governance.schema.json`)

## Pass/Fail Criteria

This panel **passes** when all of the following are met:

| Criterion | Threshold | Blocked If |
|-----------|-----------|------------|
| Confidence score | >= 0.70 | Below 0.70 |
| Critical findings | 0 allowed | Any critical finding present |
| High findings | <= 2 | More than 2 high findings |
| Aggregate verdict | approve | Block or abstain majority |
| Coverage assessment | adequate | Grossly inadequate coverage |

When blocked, the panel emits a `block` verdict with a structured explanation listing missing tests.

Local overrides via `panels.local.json` can increase these thresholds (more restrictive) but never decrease them. See `governance/schemas/panels.schema.json` for the override format.

## Confidence Score Calculation

```
confidence = 0.85  (base)
           - (critical_findings x 0.25)
           - (high_findings x 0.15)
           - (medium_findings x 0.05)
           - (low_findings x 0.01)
           = max(confidence, 0.0)  (floor)
```

| Finding Severity | Deduction | Example: 1 finding |
|-----------------|-----------|-------------------|
| Critical | -0.25 | 0.85 -> 0.60 |
| High | -0.15 | 0.85 -> 0.70 |
| Medium | -0.05 | 0.85 -> 0.80 |
| Low | -0.01 | 0.85 -> 0.84 |

## Verification Levels

The panel recommends a verification level based on the policy profile and change characteristics:

| Level | When Applied | Requirements |
|-------|-------------|-------------|
| **none** | Documentation, config changes | No test requirements |
| **basic** | Low-risk code changes (default profile) | Unit tests for modified functions |
| **standard** | Medium-risk or business logic changes | Unit + integration tests, type checking |
| **strict** | High-risk, financial, PII, infrastructure | Unit + integration + property tests + contract checks |

## Proof-of-Correctness Criteria

For `strict` verification level, the panel evaluates:

1. **Type safety** — Static type checking passes (TypeScript strict, mypy, etc.)
2. **Property tests** — Randomized property-based tests for core logic (Hypothesis, fast-check, etc.)
3. **Contract checks** — Pre/post-condition assertions on public APIs
4. **Invariant proofs** — Key invariants documented and tested
5. **Integration coverage** — All component boundaries have integration tests

## Constraints
- Never approve a change to business-critical code without test coverage assessment
- For `fin_pii_high` profile: always recommend `strict` verification level
- For `infrastructure_critical` profile: always recommend `standard` or higher
- This panel assesses requirements — it does not execute tests
- Consuming repos are responsible for running their own test suites
