---
name: global-dev-write-tests
description: "Generate comprehensive tests for code under test"
status: production
tags: [dev, testing, quality]
model: null
---

# Write Tests

Generate comprehensive, well-structured tests for the specified code.

## Workflow

1. **Read the code under test** to understand its purpose, inputs, outputs, and side effects.
2. **Identify the testing framework** used in the project (look for existing test files, package.json, pytest.ini, etc.). Match the project's testing conventions.
3. **Determine the test scope**:
   - **Unit tests**: isolated function/method behavior
   - **Integration tests**: interaction between components
   - **Edge case tests**: boundary conditions and error paths
4. **Write tests** following the structure below.

## Test Generation Strategy

### For each function/method, test:

**Happy path** -- normal expected usage
- Valid inputs produce correct outputs
- Expected side effects occur (database writes, API calls, events emitted)
- Return types match the contract

**Edge cases**
- Empty inputs (empty string, empty array, empty object, zero)
- Boundary values (min/max int, string length limits, array size limits)
- Null/undefined/None where applicable
- Single-element collections
- Unicode and special characters in string inputs

**Error handling**
- Invalid input types (string where number expected, etc.)
- Missing required parameters
- External service failures (network errors, timeouts, 500 responses)
- File not found, permission denied
- Concurrent access / race conditions (if applicable)

**State transitions** (for stateful code)
- Initial state is correct
- Valid transitions produce correct new state
- Invalid transitions are rejected
- State is consistent after error recovery

## Test Naming Convention

Use descriptive names that document the behavior:
```
test_<function>_<scenario>_<expected_result>
```

Examples:
- `test_parse_config_with_empty_file_returns_defaults`
- `test_auth_login_with_expired_token_throws_unauthorized`
- `should return empty array when no items match filter`

## Test Structure

Use the Arrange-Act-Assert pattern:

```
// Arrange: set up test data and dependencies
// Act: call the function under test
// Assert: verify the result
```

## Guidelines

- Each test should verify one behavior. Prefer many small tests over few large ones.
- Tests must be deterministic -- no reliance on time, random values, or external services without mocking.
- Use mocks/stubs for external dependencies (databases, APIs, file system) in unit tests.
- Include both positive and negative assertions (`expect(x).toBe(y)` and `expect(fn).toThrow()`).
- If the existing test suite has patterns or helpers, reuse them.
- Add brief comments explaining **why** a test exists for non-obvious cases.
- Name test files to match the source file (e.g., `auth.ts` -> `auth.test.ts`).

## Output Format

Provide the complete test file with all imports, setup/teardown, and test cases. Include a summary comment at the top listing what is covered:

```
// Tests for: <module/function>
// Coverage: happy path, edge cases, error handling
// Total: N test cases
```
