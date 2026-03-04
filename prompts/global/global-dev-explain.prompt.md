---
name: global-dev-explain
description: "Explain code in detail with examples and context"
status: production
tags: [dev, explain, documentation, learning]
model: null
---

# Explain Code

Provide a clear, thorough explanation of the specified code for a developer who is unfamiliar with it.

## Workflow

1. **Read the entire file or section** before explaining. Context matters.
2. **Identify the audience level** -- if not specified, assume an intermediate developer who knows the language but not this codebase.
3. **Structure the explanation** using the framework below.

## Explanation Framework

### 1. Purpose (the "what")
- What does this code accomplish?
- What problem does it solve?
- Where does it fit in the larger system?
- What are its inputs and outputs?

### 2. Mechanism (the "how")
Walk through the code's logic in execution order:
- Entry point and control flow
- Key data structures and their roles
- Important algorithms or patterns used
- How state changes over time
- What external systems or dependencies are involved

Use line references to anchor explanations to specific code.

### 3. Design Decisions (the "why")
- Why was this approach chosen over alternatives?
- What tradeoffs were made?
- Are there known limitations or technical debt?
- What patterns or conventions does it follow (and why)?

### 4. Dependencies and Context
- What does this code depend on (imports, services, configuration)?
- What depends on this code (callers, consumers)?
- Are there related files or modules that should be read together?

### 5. Examples
Provide concrete examples of how this code is used:
- A typical invocation with realistic arguments
- What the output looks like
- An edge case and how it is handled

## Guidelines

- Use simple, direct language. Avoid jargon unless it is standard for the language/framework.
- Explain one concept at a time. Do not jump between unrelated parts.
- When explaining complex logic, break it into numbered steps.
- If the code uses a pattern (Observer, Strategy, Builder, etc.), name it and briefly describe why it applies here.
- If parts of the code are confusing or poorly written, say so constructively -- this helps the reader calibrate their understanding.
- Do not simply restate the code in English ("line 5 sets x to 3"). Explain the intent and significance.

## Output Format

```
## Overview
One-paragraph summary of what this code does and why it exists.

## Detailed Walkthrough
Section-by-section explanation following the framework above.

## Usage Examples
Concrete code examples showing how to use this code.

## Related Code
Links or references to files that should be read alongside this one.
```
