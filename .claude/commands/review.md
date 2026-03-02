Run a governance review panel. Argument routing based on `$ARGUMENTS`:

## Argument Parsing

Parse `$ARGUMENTS` to determine the mode:

| Input | Mode | Action |
|-------|------|--------|
| `list` | List panels | List all review prompts with name, purpose, and participant count |
| `perspectives` | List perspectives | List shared perspectives with role and focus area |
| `run <panel>` | Run panel (current branch) | Run panel against the current branch's PR diff |
| `run <panel> pr=N` | Run panel (specific PR) | Run panel against PR #N's diff |
| `status` | Emission status | Show current panel emissions with verdicts and scores |
| *(empty / no args)* | List panels | Default: same as `list` |

## Execution Steps

### Mode: `list`

1. Scan for review prompts: `governance/prompts/reviews/*.md` (or `.ai/governance/prompts/reviews/*.md` if in a consuming repo).
2. For each file:
   - Extract the panel name from the filename (e.g., `code-review.md` -> `code-review`).
   - Extract the title from the first `# ` heading.
   - Extract the purpose from the paragraph immediately following `## Purpose`.
   - Count the number of perspectives/participants listed under `## Perspectives` (each `### ` heading is one participant).
3. Display as a table:

   | Panel | Purpose | Participants |
   |-------|---------|-------------|

### Mode: `perspectives`

1. Read `governance/prompts/shared-perspectives.md` (or `.ai/governance/prompts/shared-perspectives.md` if in a consuming repo).
2. Extract each perspective definition: the `## ` heading is the perspective name, the **Role:** line is the focus area.
3. Display as a table:

   | Perspective | Focus Area |
   |-------------|-----------|

### Mode: `run <panel>` (current branch)

1. Determine the current branch: `git branch --show-current`.
2. Find the PR for the current branch: `gh pr list --head $(git branch --show-current) --json number --jq '.[0].number'`.
3. If no PR exists, inform the user and suggest creating one first.
4. Fetch the PR diff: `gh pr diff <number>`.
5. Read the panel prompt: `governance/prompts/reviews/<panel>.md` (or `.ai/governance/prompts/reviews/<panel>.md` if in a consuming repo).
6. Execute the review against the diff, following the panel prompt's structure, perspectives, and scoring criteria.
7. Save output to `.governance/panels/<panel>.md`.
8. Save structured emission JSON to `.governance/panels/<panel>.json`.

### Mode: `run <panel> pr=N`

1. Extract the PR number N from the argument.
2. Verify the PR exists: `gh pr view N --json number,title,state`.
3. If the PR is closed/merged, warn the user and ask if they want to proceed.
4. Fetch the PR diff: `gh pr diff N`.
5. Read the panel prompt: `governance/prompts/reviews/<panel>.md` (or `.ai/governance/prompts/reviews/<panel>.md` if in a consuming repo).
6. Execute the review against the diff, following the panel prompt's structure, perspectives, and scoring criteria.
7. Save output to `.governance/panels/<panel>.md`.
8. Save structured emission JSON to `.governance/panels/<panel>.json`.

### Mode: `status`

1. Scan `.governance/panels/*.json` for structured emissions.
2. For each emission file, parse the following fields: `panel_name`, `panel_version`, `confidence_score`, `risk_level`, number of `findings`, and the aggregate `verdict`.
3. Display as a table:

   | Panel | Version | Confidence | Risk Level | Findings | Verdict |
   |-------|---------|-----------|------------|----------|---------|

4. If no emission files exist, inform the user that no panel reviews have been run yet.

## Output

After completing the analysis:
1. Display the results in the conversation.
2. Confirm the output file locations (`.governance/panels/<panel>.md` and `.governance/panels/<panel>.json`).
3. Report the confidence score and aggregate verdict from the structured emission.
