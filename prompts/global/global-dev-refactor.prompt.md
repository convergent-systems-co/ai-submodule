---
name: global-dev-refactor
description: "Suggest and implement refactoring improvements for code"
status: production
tags: [dev, refactor, quality, maintainability]
model: null
---

# Refactor Code

Analyze code for refactoring opportunities and implement improvements while preserving existing behavior.

## Workflow

1. **Read and understand** the code's current behavior, public API, and callers.
2. **Identify refactoring opportunities** using the catalog below.
3. **Prioritize** by impact: correctness risks first, then maintainability, then style.
4. **Plan the refactoring** -- describe what changes and why before writing code.
5. **Implement incrementally** -- each step should leave the code in a working state.
6. **Verify** that behavior is unchanged (run existing tests; if none exist, note the risk).

## Refactoring Catalog

### Extract and Simplify
- **Extract function**: Long functions (> 40 lines) or repeated code blocks should become named functions.
- **Extract constant**: Magic numbers and repeated string literals should become named constants.
- **Extract type/interface**: Repeated object shapes should become named types.
- **Simplify conditionals**: Deeply nested if/else chains can often become early returns, guard clauses, or lookup tables.

### Reduce Complexity
- **Replace flag arguments**: Boolean parameters that change function behavior should become separate functions.
- **Replace temp with query**: Temporary variables used once can often be inlined or extracted to a descriptive function.
- **Decompose conditional**: Complex boolean expressions should become named predicates (`isEligible()` instead of `age >= 18 && hasConsent && !isBanned`).
- **Remove dead code**: Unused imports, unreachable branches, commented-out code, and unused variables should be deleted.

### Improve Structure
- **Move to appropriate module**: Code that is used by module B but lives in module A should move to where it belongs.
- **Introduce parameter object**: Functions with more than 3-4 parameters should accept an options object.
- **Replace inheritance with composition**: Deep class hierarchies can often become composition of smaller, focused objects.
- **Separate concerns**: Functions that do I/O and computation should be split so the computation is independently testable.

### Naming
- **Rename for clarity**: Names should describe what, not how (`getUsersByRole` instead of `filterList`).
- **Consistent vocabulary**: Use the same term for the same concept throughout the codebase.
- **Avoid abbreviations**: Unless they are universally understood in the domain (`id`, `url`, `http` are fine; `usr`, `mgr`, `proc` are not).

## Constraints

- **No behavior changes**: The refactored code must produce identical outputs for identical inputs. If the refactoring reveals a bug, report it separately -- do not fix it as part of the refactoring.
- **Preserve public API**: Do not change function signatures, exported names, or return types unless the caller is also updated.
- **One concept per commit**: Each refactoring step should be a separate, reviewable unit.
- **Test coverage**: If the code lacks tests, state this risk clearly. Consider writing tests before refactoring.

## Output Format

```
## Analysis
Current issues with severity (high/medium/low) and affected locations.

## Refactoring Plan
Numbered steps, each describing one atomic refactoring.

## Implementation
For each step:
- What changed and why
- Before/after code (abbreviated if large)
- How to verify the step preserves behavior

## Risks
Any risks introduced by the refactoring and how to mitigate them.
```
