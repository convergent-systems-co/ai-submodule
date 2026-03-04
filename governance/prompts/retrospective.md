# Retrospective: Post-Merge Process Evaluation

Run this prompt after merging a PR to evaluate the completed work for process improvements.

## Instructions

After completing an issue (Phase 5a merge), evaluate the work just finished. This is a lightweight self-assessment — keep it concise. Post the findings as a comment on the closed issue.

## Evaluation Criteria

### 1. Planning Effectiveness
- Was the plan accurate? Did the implementation match the plan or require significant deviation?
- Were the right files identified in scope?
- Was the risk assessment correct?

### 2. Review Cycle Efficiency
- How many review cycles did the PR require?
- Were CI failures caused by avoidable mistakes?
- Were Copilot recommendations substantive or trivial?

### 3. Token Cost Observations
- Were unnecessary personas or panels loaded?
- Was context managed well, or did the window approach capacity?
- Could any steps have used a cheaper model (e.g., classification, labeling)?

### 4. Process Improvement Candidates
Based on this issue, identify concrete improvements to:
- **Templates**: Missing sections, unclear guidance, unnecessary sections
- **Panels**: Missing coverage, redundant panels, incorrect triggers
- **Prompts**: Unclear instructions, missing context, over-specified behavior
- **Startup sequence**: Friction points, unnecessary steps, missing automation

## Output Format

Post as an issue comment:

```markdown
## Retrospective — Issue #N

**Review cycles:** N
**CI failures:** N (causes: ...)
**Copilot findings:** N implemented, N dismissed
**Plan accuracy:** [accurate | minor deviations | significant deviations]

### What went well
- ...

### What could improve
- ...

### Process improvement recommendations
- [ ] [Specific actionable recommendation]
- [ ] [Another recommendation]
```

## When to Skip

Skip the retrospective if:
- The issue was trivial (single commit, no review findings)
- Context capacity is above 70% (save the remaining budget for the next issue)

## When to Create Follow-Up Issues

If a recommendation requires changes to governance artifacts (templates, panels, prompts, policies), create a new GitHub issue with:
- Label: `enhancement`
- Title: `improve(governance): [short description]`
- Body: Reference this retrospective and describe the specific change
