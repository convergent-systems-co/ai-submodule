---
name: global-dev-pr-create
description: "Generate a well-structured PR description from branch diff"
status: production
tags: [dev, git, pr, github]
model: null
---

# Create Pull Request Description

Generate a comprehensive pull request title and description from the current branch's changes relative to the base branch.

## Workflow

1. **Determine the base branch** -- typically `main` or `master`. Check `git remote show origin` if unsure.
2. **Gather the full diff** by running `git log --oneline main..HEAD` and `git diff main...HEAD --stat`.
3. **Read through every commit** on the branch, not just the latest one. Understand the full arc of changes.
4. **Analyze the changes** to identify:
   - What is the primary goal of this PR?
   - What areas of the codebase are affected?
   - Are there any breaking changes?
   - What testing was done or needs to be done?
5. **Generate the PR title**:
   - Under 70 characters
   - Use imperative mood
   - Include the change type prefix if the project uses conventional commits (e.g., `feat:`, `fix:`)
   - Reference the issue number if applicable (e.g., `feat: add prompt library (#469)`)
6. **Generate the PR body** using this structure:

## Output Format

```markdown
## Summary
- Bullet point 1: primary change
- Bullet point 2: secondary change (if applicable)
- Bullet point 3: additional context (if applicable)

## Motivation
Why this change is needed. Link to the issue or design document.

## Changes
### Area 1
- Specific change description
- Another change

### Area 2
- Specific change description

## Testing
- How the changes were verified
- Any manual testing steps required
- Test coverage additions

## Breaking Changes
List any breaking changes and migration steps, or state "None."

## Checklist
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] No secrets or credentials committed
- [ ] Backward compatible (or migration documented)
```

If the project has a PR template, prefer that format over this one. Adapt the structure to match the repository's conventions.

## Guidelines

- Keep the summary concise -- 1 to 3 bullet points maximum.
- Put detail in the Changes section, not the Summary.
- Be explicit about what reviewers should pay attention to.
- If the PR is large, suggest splitting it and explain how.
