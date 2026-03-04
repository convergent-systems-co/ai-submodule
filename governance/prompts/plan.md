# Plan

Decompose a task into an implementation plan before writing code.

## Process

1. **Clarify** - Restate the goal in your own words. Call out any ambiguity.
2. **Scope** - Define what's in and out of scope. Identify the minimal viable change.
3. **Inventory** - List the files, modules, and interfaces that will be touched.
4. **Sequence** - Order the changes so each step is independently testable.
5. **Risks** - Identify what could go wrong and how to mitigate it.
6. **Validation** - Define how to verify each step and the final result.

## Output Format

```
## Goal
<one sentence>

## Scope
- In: ...
- Out: ...

## Steps
1. <step> — verify by: <how>
2. <step> — verify by: <how>
...

## Risks
- <risk>: <mitigation>

## Open Questions
- <anything that needs clarification before starting>
```

## When to Use
Before any change that touches more than 2 files or involves architectural decisions.
