Manage governance plans. Argument routing based on `$ARGUMENTS`:

## Argument Parsing

Parse `$ARGUMENTS` to determine the mode:

| Input | Mode | Action |
|-------|------|--------|
| `list` | List plans | Lists plans in `.artifacts/plans/` with issue number, description, status |
| `create <N>` (e.g., `create 42`) | Create plan | Creates plan from template for issue #N |
| `show <N>` (e.g., `show 42`) | Show plan | Reads and displays existing plan for issue #N |
| *(empty / no args)* | Help | Show help text with available subcommands |

## Execution Steps

### Mode: `list`

1. Scan `.artifacts/plans/*.md` for all plan files.
2. For each file: extract the plan title, status, issue reference, and date from the frontmatter (the metadata lines at the top of the plan: `**Status:**`, `**Issue:**`, `**Date:**`, and the `# [Plan Title]` heading).
3. Display as a table:

   | Issue | Title | Status | Date |
   |-------|-------|--------|------|

4. If no plans exist, inform the user that no plans were found.

### Mode: `create <N>`

1. Extract the issue number N from the argument.
2. Verify the issue is open: `gh issue view N --json state --jq '.state'`.
3. If the issue is closed, inform the user and stop.
4. Fetch issue details: `gh issue view N --json number,title,body`.
5. Check if a plan already exists for issue #N in `.artifacts/plans/` (pattern: `N-*.md`).
6. If a plan already exists, warn the user and ask if they want to overwrite.
7. Read the plan template: `governance/templates/prompts/plan-template.md` (or `.ai/governance/templates/prompts/plan-template.md` if in a consuming repo).
8. Generate a plan following the template structure, pre-filling:
   - **Title** from the issue title
   - **Date** as today's date
   - **Status** as `draft`
   - **Issue** as a link to issue #N
   - **Objective** from the issue body
9. Save to `.artifacts/plans/{N}-{slugified-description}.md`.
10. Display confirmation with the file location.

### Mode: `show <N>`

1. Extract the issue number N from the argument.
2. Search `.artifacts/plans/` for a file matching issue #N (pattern: `N-*.md`).
3. If not found, inform the user that no plan exists for issue #N and suggest running `/plan create N`.
4. Read and display the full plan content.

### Mode: help (no args)

1. Display the following help text:

   ```
   /plan — Governance plan management

   Subcommands:
     list          List all plans with issue number, title, status, and date
     create <N>    Create a new plan from template for issue #N
     show <N>      Display the existing plan for issue #N

   Examples:
     /plan list
     /plan create 42
     /plan show 42
   ```

## Output

After completing the action:
1. Display the results in the conversation.
2. Confirm any file locations created or read.
3. For `create` mode, remind the user that the plan status is `draft` and should be reviewed before implementation.
