---
name: global-dev-context-summary
description: "Summarize current codebase context for session handoff or checkpoint"
status: production
tags: [dev, context, handoff, checkpoint]
model: null
---

# Context Summary

Generate a concise summary of the current working context for handoff to another developer, AI agent, or future session.

## When to Use

- Before reaching context window limits (80% capacity checkpoint)
- Handing off work to another developer or agent
- Pausing work that will be resumed later
- Documenting the current state for a status update

## Workflow

1. **Capture the current state** by gathering information from git and the working directory.
2. **Summarize in-progress work** -- what has been done and what remains.
3. **Document known issues** encountered during the session.
4. **List open questions** that need answers before work can continue.
5. **Write the summary** using the structure below.

## Information to Gather

Run these commands to collect state:

```bash
git branch --show-current                     # Current branch
git log --oneline -10                          # Recent commits
git status                                    # Working tree state
git stash list                                # Any stashed changes
git diff --stat HEAD~5..HEAD                  # Files changed recently
```

Also check:
- Any open TODO/FIXME comments you added during this session
- Test results from the last run
- Build or linter errors that are unresolved

## Output Format

```markdown
# Context Summary

**Date:** YYYY-MM-DD HH:MM
**Branch:** branch-name
**Issue:** #NNN — issue title
**Session goal:** One sentence describing what this session set out to accomplish

## Completed Work
- [x] Step or task that is done
- [x] Another completed step
- [x] Files created/modified: list key files

## In Progress
- [ ] Current step being worked on
  - What is done so far
  - What remains

## Remaining Work
- [ ] Step not yet started
- [ ] Another future step

## Current State
- **Build:** passing / failing (describe errors if failing)
- **Tests:** N passing, M failing (list failing tests)
- **Working tree:** clean / dirty (list uncommitted files)
- **Stash:** empty / N entries (describe what is stashed)

## Key Decisions Made
- Decision 1: what was decided and why
- Decision 2: what was decided and why

## Open Questions
- Question that needs an answer before continuing
- Another unresolved question

## Known Issues
- Issue encountered during work (with file:line if applicable)
- Workaround applied (if any)

## Files to Review
Key files that the next person should read to get up to speed:
- `path/to/file` — why it is important
- `path/to/other/file` — why it is important

## How to Resume
Step-by-step instructions for picking up where this session left off:
1. Check out branch `branch-name`
2. Ensure dependencies are installed
3. Start with [specific task]
4. Refer to [plan or issue] for full requirements
```

## Guidelines

- Be specific about file paths and line numbers, not vague ("I was working on the auth stuff").
- Include exact error messages if there are failing tests or build errors.
- Distinguish between "done and committed" vs. "done but uncommitted" vs. "partially done."
- The summary should be self-contained -- a reader should not need to ask follow-up questions to understand the state.
- Keep it under 100 lines. If you need more, the scope is too large for a single handoff.
