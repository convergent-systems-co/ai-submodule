Read and execute the agentic improvement loop defined in `.ai/governance/prompts/startup.md`. Follow these steps sequentially:

## Phase 1: Pre-flight & Triage

1. Check `.ai` submodule freshness (respect `project.yaml` pin if set).
2. Verify repository configuration (auto-merge, CODEOWNERS, governance workflow).
3. Resolve all open PRs before starting new issues:
   ```bash
   gh pr list --state open --json number,title,author,headRefName,createdAt,reviews --limit 20
   ```
4. Scan and prioritize open GitHub issues:
   ```bash
   gh issue list --state open --json number,title,labels,assignees,body --limit 50
   ```
5. Filter for actionable issues (no existing branch, not blocked/wontfix/duplicate, not assigned to a human).
6. Prioritize: P0 > P1 > P2 > P3 > P4, then by creation date. Bugs before enhancements at same priority.

## Phase 2: Planning

For each actionable issue (up to 5 per session):

1. Verify issue is still open: `gh issue view <number> --json state --jq '.state'`
2. Read the issue body and validate clear acceptance criteria. If unclear, label `refine` and comment.
3. Select review panels based on change type (see `.ai/governance/prompts/startup.md` Phase 2c).
4. Create branch: `itsfwcp/{type}/{number}/{name}`
5. Write plan using `.ai/governance/prompts/templates/plan-template.md` and save to .governance/plans/{number}-{description}.md`.

## Phase 3: Implementation

For each planned issue (sequentially, since Copilot does not support parallel Task dispatch):

1. Follow the Coder persona (`.ai/governance/personas/agentic/coder.md`).
2. Implement the plan following project conventions.
3. Write tests meeting coverage targets.
4. Update affected documentation (GOALS.md, CLAUDE.md, README.md, docs/).
5. Commit with conventional commit messages.

## Phase 4: Review & PR

1. Run security review (`.ai/governance/prompts/reviews/security-review.md`).
2. Run context-specific review panels selected in Phase 2.
3. Push branch and create PR:
   ```bash
   gh pr create --title "<type>: <description>" --body "Closes #<number>"
   ```
4. Monitor CI checks: `gh pr checks <pr-number> --watch --fail-fast`
5. Address any failures, then re-push.

## Phase 5: Merge & Loop

1. Merge: `gh pr merge <pr-number> --squash --delete-branch`
2. Close issue with comment.
3. If no hard-stop condition (5 issues completed, context pressure): return to Phase 1 immediately.
4. If hard-stop: write checkpoint to `.governance/checkpoints/`, execute shutdown protocol, request `/clear`.

## Context Capacity

Monitor for context pressure throughout. If the conversation exceeds ~30 turns, ~200K characters, or responses degrade in quality:

1. Stop all work.
2. Clean git state (commit WIP, abort merges).
3. Write checkpoint to .governance/checkpoints/{timestamp}-{branch}.json`.
4. Report to user and suggest starting a new Copilot Chat thread with: `Resume from checkpoint: .governance/checkpoints/{checkpoint-file}`

## Constraints

- Maximum 5 issues per session.
- Maximum 3 review cycles per PR before escalating.
- Plans before code -- always.
- Documentation with every change -- mandatory.
- Never modify `jm-compliance.yml` (enterprise-locked).
