# Migrate

Plan and execute a migration (dependency upgrade, framework change, API version bump, data schema change).

## Process

1. **Assess** - What is changing and why? What's the blast radius?
2. **Inventory** - List all affected files, APIs, data stores, and consumers.
3. **Strategy** - Choose an approach:
   - **Big bang** — change everything at once (small scope only)
   - **Strangler fig** — incrementally replace behind an abstraction
   - **Parallel run** — run old and new simultaneously, compare results
4. **Sequence** - Order changes so each step is independently deployable and rollback-safe.
5. **Validate** - Define verification criteria for each step.
6. **Rollback** - Document how to revert at every stage.

## Output Format

```
## Migration: <from> → <to>

## Impact Assessment
- Files affected: <count>
- APIs affected: <list>
- Data changes: <yes/no, details>
- Breaking changes: <list>

## Strategy
<chosen approach with rationale>

## Steps
1. <step> — rollback: <how>
2. <step> — rollback: <how>
...

## Validation Checklist
- [ ] <criterion>
- [ ] <criterion>

## Rollback Plan
<how to fully revert if needed>
```

## When to Use
Before any dependency upgrade, framework migration, API version change, or schema migration.
