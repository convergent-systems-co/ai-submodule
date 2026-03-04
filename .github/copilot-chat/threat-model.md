Run a threat model analysis. Argument routing based on `$ARGUMENTS`:

## Argument Parsing

Parse `$ARGUMENTS` to determine the mode:

| Input | Mode | Action |
|-------|------|--------|
| `system` | System-level | Full platform/application threat model |
| `pr` | PR-level (current branch) | Threat model scoped to current branch's PR diff |
| `pr=N` (e.g., `pr=345`) | PR-level (specific PR) | Threat model scoped to PR #N's diff |
| *(empty / no args)* | PR-level (current branch) | Default: same as `pr` |

## Execution Steps

### Mode: `system`

1. Read the system-level threat model prompt: `governance/prompts/reviews/threat-model-system.md` (or `.ai/governance/prompts/reviews/threat-model-system.md` if in a consuming repo).
2. Analyze the full codebase/system according to the prompt's 15-section template.
3. Save output to `.artifacts/panels/threat-model-system.md`.
4. Save structured emission JSON to `.artifacts/emissions/threat-model-system.json`.

### Mode: `pr` (current branch)

1. Determine the current branch: `git branch --show-current`.
2. Find the PR for the current branch: `gh pr list --head $(git branch --show-current) --json number --jq '.[0].number'`.
3. If no PR exists, inform the user and offer to run in `system` mode instead.
4. Fetch the PR diff: `gh pr diff <number>`.
5. Read the PR-level threat model prompt: `governance/prompts/reviews/threat-modeling.md` (or `.ai/governance/prompts/reviews/threat-modeling.md` if in a consuming repo).
6. Analyze the diff according to the prompt's 15-section template.
7. Save output to `.artifacts/panels/threat-modeling.md`.
8. Save structured emission JSON to `.artifacts/emissions/threat-modeling.json`.

### Mode: `pr=N`

1. Extract the PR number N from the argument.
2. Verify the PR exists: `gh pr view N --json number,title,state`.
3. If the PR is closed/merged, warn the user and ask if they want to proceed.
4. Fetch the PR diff: `gh pr diff N`.
5. Read the PR-level threat model prompt: `governance/prompts/reviews/threat-modeling.md` (or `.ai/governance/prompts/reviews/threat-modeling.md` if in a consuming repo).
6. Analyze the diff according to the prompt's 15-section template.
7. Save output to `.artifacts/panels/threat-modeling.md`.
8. Save structured emission JSON to `.artifacts/emissions/threat-modeling.json`.

## Output

After completing the analysis:
1. Display the full threat model output in the conversation.
2. Confirm the output file location.
3. Report the confidence score and aggregate verdict from the structured emission.
