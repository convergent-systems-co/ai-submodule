# Testing Instructions

<!-- PHASE:test -->

Loaded for test authoring, review, and coverage tasks.

## Strategy

- Write tests that verify behavior, not implementation
- Cover happy path, error cases, and edge cases
- Use descriptive test names that document expected behavior
- Prefer integration tests for critical paths, unit tests for logic
- Mock external dependencies, not internal components

## Coverage

- Meet project coverage targets defined in `project.yaml`
- Prioritize coverage of high-risk code paths
- Treat flaky tests as bugs — fix or remove them
- Test failure messages should diagnose the problem without reading source
