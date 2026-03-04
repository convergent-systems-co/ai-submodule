# Plan: Automated Document Writer Thread (#630)

## Objective

Add an automated Document Writer agent thread to the governance framework that ensures documentation stays current with code changes. This includes a new agentic persona, a staleness detection script, and startup.md integration.

## Rationale

Documentation consistently drifts from implementation. Issues #12, #15, and #267 were all caused by stale docs. The framework enforces code review, security review, and cost analysis, but documentation freshness has no automated enforcement.

## Scope

| File | Action |
|------|--------|
| `governance/personas/agentic/document-writer.md` | Create — new persona definition |
| `bin/check-doc-staleness.py` | Create — staleness detection script |
| `governance/prompts/startup.md` | Modify — add Document Writer dispatch to Phase 4 |
| `governance/prompts/reviews/documentation-review.md` | Modify — add staleness enforcement |
| `CLAUDE.md` | Modify — update persona count (6 -> 7) |

## Approach

1. Create the Document Writer persona following the pattern of existing personas (coder.md, tester.md)
2. Create `bin/check-doc-staleness.py` to detect stale counts, paths, and descriptions in markdown files
3. Update `governance/prompts/startup.md` Phase 4 to dispatch Document Writer
4. Enhance documentation-review.md with staleness enforcement
5. Update CLAUDE.md persona count

## Testing Strategy

- Run existing test suite to ensure no regressions
- Verify `check-doc-staleness.py` runs without errors on the repo

## Risk Assessment

- Low risk: additive changes, no existing code modified destructively
- Persona file follows established patterns
- Staleness script is standalone with no dependencies on engine internals

## Dependencies

None — additive feature.
