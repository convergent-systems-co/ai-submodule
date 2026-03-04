# Workflow: Documentation

Creating or updating technical documentation, from audience analysis through published content.

## Prerequisites

- Subject to document (feature, system, process, API, etc.)
- Access to the relevant codebase or system
- Knowledge of the target audience (or willingness to define it)

## Phases

1. **Audience Analysis** → `[DOC-1]`
2. **Content Inventory** → `[DOC-2]` — **GATE**
3. **Draft** → `[DOC-3]` — **GATE**
4. **Review** → `[DOC-4]` — **GATE**
5. **Publish** → `[DOC-5]`

---

## Phase 1: Audience Analysis

> **Adopt persona:** `governance/personas/documentation/documentation-writer.md`
> **Secondary persona:** `governance/personas/leadership/product-manager.md`

### Input

- Subject to document
- Any existing documentation on this subject
- Known audience (or "determine audience")

### Process

1. Identify the primary audience(s) and their skill level
2. Determine what the audience needs to accomplish (goals, not just information)
3. Identify what the audience already knows vs. what they need to learn
4. Define the documentation type (tutorial, how-to, reference, explanation)
5. Establish tone and depth appropriate to the audience

### Output

**Artifact `[DOC-1]: Audience Analysis`**

```
## Subject
<What is being documented>

## Primary Audience
<Who will read this and their skill level>

## Audience Goals
- <What they need to accomplish>
- ...

## Prior Knowledge (assumed)
- <What readers already know>

## Documentation Type
<Tutorial / How-to / Reference / Explanation>

## Tone & Depth
<e.g., "Technical, detailed, assumes familiarity with REST APIs">
```

---

## Phase 2: Content Inventory

> **Adopt persona:** `governance/personas/documentation/documentation-writer.md`
> **Invoke prompt:** `governance/prompts/explain.md`

### Input

- `[DOC-1]: Audience Analysis`
- Codebase or system access (to understand what needs documenting)
- Existing documentation (to identify gaps)

### Process

1. Survey the subject area — what exists, what's missing, what's outdated
2. Create an outline structured around audience goals from `[DOC-1]`
3. Identify code examples, diagrams, or screenshots needed
4. Estimate content sections and their priority

### Output

**Artifact `[DOC-2]: Content Plan`**

```
## Outline

### 1. <Section>
- <Key points to cover>
- **Assets needed:** <code example / diagram / screenshot / none>

### 2. <Section>
- <Key points to cover>
- **Assets needed:** <code example / diagram / screenshot / none>

...

## Existing Documentation
- <doc path> — <status: current / outdated / partial>
- ...

## Gaps Identified
- <Missing content>
- ...
```

### GATE

**Stop.** Present `[DOC-2]` for review.

**Approval criteria:** Outline covers audience goals. Structure is logical. Required assets are identified.

- **Approved** → proceed to Phase 3
- **Revise** → adjust outline, re-present `[DOC-2]`

---

## Phase 3: Draft

> **Adopt persona:** `governance/personas/documentation/documentation-writer.md`

### Input

- `[DOC-1]: Audience Analysis`
- `[DOC-2]: Content Plan`
- Codebase access (for accurate code examples)

### Process

1. Write each section following the outline from `[DOC-2]`
2. Create code examples that are accurate and runnable
3. Maintain consistent tone from `[DOC-1]`
4. Lead with what the reader needs to do, not implementation details
5. Keep paragraphs short, use lists and headings liberally

### Output

**Artifact `[DOC-3]: Draft Document`**

```
## Document
<The full draft content>

## Assets Created
- <code example / diagram / screenshot> — <location>

## Notes for Reviewers
- <Areas of uncertainty>
- <Decisions made about scope or depth>
```

### GATE

**Stop.** Present `[DOC-3]` for review.

**Approval criteria:** Content is accurate. Code examples work. Tone matches audience. Structure follows the approved outline.

- **Approved** → proceed to Phase 4
- **Revise** → address feedback, re-present `[DOC-3]`

---

## Phase 4: Review

> **Invoke panel:** `governance/prompts/reviews/documentation-review.md`

### Input

- `[DOC-1]: Audience Analysis`
- `[DOC-2]: Content Plan`
- `[DOC-3]: Draft Document`

### Process

1. Review for technical accuracy
2. Review for clarity and readability from the target audience's perspective
3. Verify code examples are correct and follow project conventions
4. Check for completeness against the content plan
5. Flag jargon, ambiguity, or assumed knowledge not listed in `[DOC-1]`

### Output

**Artifact `[DOC-4]: Review Feedback`**

```
## Technical Accuracy
- <Finding or "No issues">
- ...

## Clarity & Readability
- <Finding or "No issues">
- ...

## Code Examples
- <Finding or "All correct">
- ...

## Completeness
- <Missing section or "Complete per plan">
- ...

## Verdict
<Approved / Changes Requested>

## Required Changes (if any)
- <Change>
```

### GATE

**Stop.** Present `[DOC-4]` for review.

**Approval criteria:** Verdict is "Approved." No technical inaccuracies. Content is complete per plan.

- **Approved** → proceed to Phase 5
- **Changes Requested** → revise in Phase 3, re-present at Phase 4

---

## Phase 5: Publish

> **Invoke prompt:** `governance/prompts/commit.md`

### Input

- `[DOC-3]: Draft Document` (final approved version)
- `[DOC-4]: Review Feedback`

### Process

1. Place the document in the correct location in the project
2. Update any indexes, tables of contents, or navigation
3. Commit with a descriptive message

### Output

**Artifact `[DOC-5]: Publication Record`**

```
## Document Location
<path>

## Related Updates
- <index/nav file updated>
- ...

## Commit
<hash> — <commit message>
```
