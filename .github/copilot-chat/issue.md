Quick issue triage and planning without the full startup loop. Argument routing based on `$ARGUMENTS`:

## Argument Parsing

Parse `$ARGUMENTS` to determine the mode:

| Input | Mode | Action |
|-------|------|--------|
| `next` | Show next issue | Shows highest-priority actionable issue with triage details |
| `plan <N>` (e.g., `plan 42`) | Plan issue | Creates branch and plan for issue #N without implementing |
| *(empty / no args)* | Show next issue | Default: same as `next` |

## Execution Steps

### Mode: `next`

1. Run `gh issue list --state open --json number,title,labels,assignees,body --limit 50`.
2. Filter for actionable issues:
   - No existing branch matching `*/feat/*`, `*/fix/*`, `*/chore/*`, or `feature/*` pattern for that issue number
   - Not labeled `blocked`, `wontfix`, `duplicate`
   - Not assigned to a human (empty assignees or assigned to a bot)
3. Prioritize: P0 > P1 > P2 > P3 > P4 (by label), then by creation date (oldest first). Bugs take precedence over enhancements at same priority level.
4. Display the top issue with:
   - Number and title
   - Labels
   - Body summary (first 200 characters)
   - Recommended branch name: `itsfwcp/{type}/{number}/{slug}` (derive type from labels: `bug` -> `fix`, `enhancement` -> `feat`, default `feat`; slug is a lowercase kebab-case summary of the title, max 40 chars)
5. If no actionable issues found: report "No actionable issues found."

### Mode: `plan <N>`

1. Extract the issue number N from the argument.
2. Verify issue is open: `gh issue view <N> --json state --jq '.state'`.
3. If closed, inform the user and stop.
4. Read issue details: `gh issue view <N> --json number,title,body,labels`.
5. Create branch: `itsfwcp/{type}/{N}/{slug}` (derive type from labels: `bug` -> `fix`, `enhancement` -> `feat`, default `feat`; slug from title).
6. Read plan template: `governance/templates/prompts/plan-template.md` (or `.ai/governance/templates/prompts/plan-template.md` if in a consuming repo).
7. Create plan following the template structure, filling in details from the issue body.
8. Save to `.artifacts/plans/{N}-{slug}.md`.
9. Do NOT implement — stop after plan creation.

## Output

After completing the action:
1. Display results in the conversation.
2. For `next` mode: show the recommended issue with triage details and suggested next step (`/issue plan <N>`).
3. For `plan` mode: confirm the branch name and plan file location. Report that implementation is deferred — use `/startup` or implement manually.
