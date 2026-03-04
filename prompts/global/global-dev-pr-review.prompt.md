---
name: global-dev-pr-review
description: "Perform a thorough code review on a pull request"
status: production
tags: [dev, git, pr, review, github]
model: null
---

# Pull Request Code Review

Perform a thorough, constructive code review on the given pull request.

## Workflow

1. **Read the PR description** to understand the intent, motivation, and scope of the change.
2. **Review every file in the diff** systematically. Do not skip files or skim.
3. **Evaluate each change** against the criteria below.
4. **Provide feedback** organized by severity.

## Review Criteria

### Correctness
- Does the code do what the PR description claims?
- Are edge cases handled (null, empty, boundary values, error states)?
- Are there off-by-one errors, race conditions, or logic flaws?
- Do new functions have correct return types and error handling?

### Security
- Are inputs validated and sanitized?
- Is there any risk of injection (SQL, XSS, command, path traversal)?
- Are secrets, tokens, or credentials hardcoded or logged?
- Are permissions and authorization checks in place?
- Are dependencies from trusted sources with no known vulnerabilities?

### Performance
- Are there unnecessary database queries or API calls (N+1 problems)?
- Are large collections processed efficiently?
- Is there potential for memory leaks or unbounded growth?
- Are expensive operations cached where appropriate?

### Maintainability
- Is the code readable without excessive comments?
- Are names descriptive and consistent with the codebase?
- Is there unnecessary duplication that should be extracted?
- Are functions and classes appropriately sized (single responsibility)?

### Testing
- Are new code paths covered by tests?
- Are edge cases tested?
- Do tests actually assert meaningful behavior (not just no-throw)?
- Are test names descriptive of what they verify?

### Documentation
- Are public APIs documented?
- Are complex algorithms or business logic explained?
- Is the README or relevant docs updated if behavior changes?

## Output Format

Organize findings by severity:

### Critical (must fix before merge)
Issues that would cause bugs, security vulnerabilities, or data loss.

### Important (should fix before merge)
Issues that affect maintainability, performance, or correctness in edge cases.

### Suggestions (nice to have)
Style improvements, alternative approaches, or minor enhancements.

### Positive Feedback
Call out things done well -- good patterns, thorough tests, clean abstractions.

For each finding, include:
- **File and line reference** (e.g., `src/auth.ts:42`)
- **What the issue is** (specific, not vague)
- **Why it matters**
- **Suggested fix** (code snippet if helpful)

End with a clear **verdict**: Approve, Request Changes, or Comment.
