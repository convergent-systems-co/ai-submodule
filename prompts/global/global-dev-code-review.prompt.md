---
name: global-dev-code-review
description: "Review code for quality, security, and performance"
status: production
tags: [dev, review, security, quality]
model: null
---

# Code Review

Review the provided code for quality, security, and performance issues. This prompt is for reviewing code in-place (not tied to a PR or diff).

## Workflow

1. **Read the code in full** before making any judgments. Understand the overall structure and purpose.
2. **Identify the language and framework** to apply language-specific best practices.
3. **Evaluate against each dimension** listed below.
4. **Report findings** in priority order with actionable suggestions.

## Evaluation Dimensions

### 1. Correctness
- Does the logic produce correct results for all inputs?
- Are error states handled gracefully (try/catch, Result types, error returns)?
- Are nullable/optional values checked before use?
- Are resource handles (files, connections, locks) properly closed/released?
- Are async operations properly awaited or chained?

### 2. Security
- **Input validation**: Are all external inputs validated (type, length, format, range)?
- **Injection**: Is user input ever interpolated into SQL, shell commands, HTML, or file paths?
- **Authentication/Authorization**: Are access checks present where needed?
- **Secrets**: Are credentials, keys, or tokens hardcoded or logged?
- **Dependencies**: Are imports from trusted, maintained packages?
- **Cryptography**: Are standard algorithms used (no custom crypto)?

### 3. Performance
- Are there O(n^2) or worse algorithms where O(n log n) or O(n) is possible?
- Are database queries or API calls inside loops (N+1)?
- Are large objects cloned unnecessarily?
- Is there unbounded memory growth (growing arrays, caches without eviction)?
- Are expensive computations memoized where appropriate?

### 4. Readability and Maintainability
- Are variable and function names descriptive and consistent?
- Is the code organized logically (related code together)?
- Are magic numbers and strings extracted as named constants?
- Is nesting depth reasonable (< 4 levels)?
- Are functions short enough to understand at a glance (< 40 lines preferred)?

### 5. Design
- Does each function/class have a single responsibility?
- Are abstractions at the right level (not too abstract, not too concrete)?
- Is there unnecessary coupling between components?
- Could any code be reused from existing utilities?
- Are interfaces/contracts well-defined?

## Output Format

For each finding:

```
[SEVERITY] file:line — Brief title
  Description of the issue.
  Why it matters.
  Suggested fix or approach.
```

Severity levels: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`.

End with a summary: total findings by severity and an overall quality assessment (1-10 scale with brief justification).
