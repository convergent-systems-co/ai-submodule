# Startup: Agentic Improvement Loop

Execute this on agent launch. This is the Code Manager's entry point for autonomous operation.

## In-Session Work

When the user provides work directly (bug reports, feature requests, feedback, or tasks) that does not correspond to an existing GitHub issue:

1. **Create a GitHub issue first** — capture the work as a trackable issue with acceptance criteria
2. **Then enter the Startup Sequence** at Step 4 (Validate Intent) with that issue
3. Never execute work without a corresponding issue — issues are the audit trail

When the user identifies a problem with a previously-created PR (e.g., failing checks, unresolved Copilot recommendations):

1. Check out the existing branch for that PR
2. Enter the Startup Sequence at Step 7 (PR Monitoring & Review Loop)

## Startup Sequence

### Step 1: Scan Open Issues

Query GitHub for open issues that are not yet being worked on:

```bash
gh issue list --state open --json number,title,labels,assignees,body --limit 50
```

### Step 2: Filter for Unimplemented Issues

For each open issue, check if a branch already exists:

```bash
gh api repos/{owner}/{repo}/branches --jq '.[].name'
```

An issue is **actionable** if:
- It has no associated branch matching `itsfwcp/*/*` or `feature/*` patterns
- It is not labeled `blocked`, `wontfix`, `duplicate`, or `refine`
- It is not assigned to a human (or is assigned to an agentic persona)
- It has not been updated in the last 24 hours by a human (avoid conflicts)

### Step 3: Prioritize

Sort actionable issues by:
1. Label priority (`P0` > `P1` > `P2` > `P3` > `P4`)
2. If no priority label, use creation date (oldest first)
3. Issues labeled `bug` take precedence over `enhancement` at the same priority

### Step 4: Validate Intent (Layer 1)

For the highest-priority actionable issue:
1. Read the issue body
2. Validate it has clear acceptance criteria or a reproducible description
3. If the intent is unclear, has too many decision points, or lacks sufficient detail for action:
   - Label the issue `refine`
   - Comment on the issue explaining what needs clarification or which decisions must be made by the user
   - Move to the next issue (the `refine` label excludes it from actionable issues until a human updates it)
4. If the intent is clear, proceed to Step 5

### Step 5: Create Plan

1. Create a branch: `itsfwcp/{issue-type}/{issue-number}/{branch-name}` (e.g., `itsfwcp/feat/42/add-auth`)
   - `{issue-type}` maps from the issue's conventional commit type: `feat`, `fix`, `refactor`, `docs`, `chore`
2. Write a plan using the plan template (`prompts/plan-template.md`)
3. Save the plan to `.plans/{issue-number}-{short-description}.md`
4. If the issue is low risk and well-defined, proceed to implementation
5. If the issue is high risk or ambiguous, comment the plan on the issue and wait for approval

### Step 6: Execute & Push PR

1. Adopt the Coder persona (`personas/agentic/coder.md`)
2. Implement the plan
3. Write tests (if applicable to the change type)
4. Commit with conventional commit messages — one logical change per commit (Git Commit Isolation)
5. Push the branch
6. Create a PR referencing the issue:
   ```bash
   gh pr create --title "<type>: <description>" --body "Closes #<issue-number>\n\n## Summary\n<description>\n\n## Plan\nSee .plans/<issue-number>-<description>.md"
   ```
7. Comment on the issue that the PR has been created:
   ```bash
   gh issue comment <issue-number> --body "PR #<pr-number> created. Entering monitoring loop."
   ```

### Step 7: PR Monitoring & Review Loop

This is the critical loop that ensures the PR reaches a merge-ready state. Do not skip any sub-step.

#### 7a: Wait for CI Checks

Poll PR check status until all checks complete or timeout (10 minutes):

```bash
gh pr checks <pr-number> --watch --fail-fast
```

If checks fail:
1. Read the failure logs: `gh pr checks <pr-number> --json name,state,description`
2. Identify the root cause
3. Adopt the Coder persona to fix the failure
4. Commit the fix (conventional commit, isolated)
5. Push the updated branch
6. Return to Step 7a (re-poll checks)

#### 7b: Fetch Copilot Recommendations

After checks complete, fetch Copilot findings from **all three comment sources** (each source is disjoint):

1. **Inline code comments** (Copilot posts line-level suggestions and review thread comments here):
   ```bash
   gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --jq '[.[] | select(.user.login | test("copilot|github-advanced-security|copilot-pull-request-reviewer"; "i"))]'
   ```

2. **PR reviews** (Copilot may post a top-level review summary):
   ```bash
   gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews --jq '[.[] | select(.user.login | test("copilot|github-advanced-security|copilot-pull-request-reviewer"; "i"))]'
   ```

3. **Issue-level comments** (some bots post here instead of as reviews):
   ```bash
   gh api repos/{owner}/{repo}/issues/{pr_number}/comments --jq '[.[] | select(.user.login | test("copilot|github-advanced-security|copilot-pull-request-reviewer"; "i"))]'
   ```

**Waiting protocol:** Treat the wait window as the first 10 minutes after PR creation (using `created_at`). First, check all sources immediately. If no Copilot comments exist from any source, you may poll again **only while** (a) it is still less than 10 minutes since PR creation, (b) the remaining time until `created_at + 10 minutes` is at least 2 minutes, and (c) you have performed fewer than 5 total polling attempts. Between polls, sleep for up to 2 minutes but **never longer than the remaining time** before the 10-minute deadline (i.e., `sleep = min(2 minutes, remaining)`). Once either the 10-minute window has elapsed or you have reached 5 polling attempts, proceed without Copilot input (per `missing_panel_behavior: redistribute` in policy).

**Do NOT merge until all sources have been checked.** The absence of Copilot findings must be confirmed, not assumed.

#### 7c: Review Recommendations

For each Copilot recommendation and any panel emission finding:

1. **Classify severity** using the rules in `personas/panels/copilot-review.md`:
   - `critical`: Security vulnerability, injection, auth bypass → **must fix**
   - `high`: Bug, incorrect logic, null reference, race condition → **must fix**
   - `medium`: Performance concern, N+1 query → **should fix**
   - `low`: Style, naming, readability → **evaluate and decide**
   - `info`: Question, clarification → **respond or acknowledge**

2. **Decide action** for each recommendation:
   - **Implement**: Fix the issue in code
   - **Dismiss with rationale**: Reply to the comment explaining why the recommendation does not apply

All `critical` and `high` items must be implemented. `medium` items should be implemented unless there is a documented technical reason not to. `low` and `info` items are at the Coder's discretion but must be explicitly acknowledged.

#### 7d: Implement Recommendations

For each recommendation marked "Implement":

1. Adopt the Coder persona
2. Make the fix in an isolated commit (one recommendation per commit where practical)
3. Reply to the Copilot comment confirming the fix:
   ```bash
   gh api repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies -f body="Fixed in <commit-sha>."
   ```

For each recommendation marked "Dismiss":

1. Reply to the Copilot comment with the rationale:
   ```bash
   gh api repos/{owner}/{repo}/pulls/{pr_number}/comments/{comment_id}/replies -f body="Dismissed: <rationale>"
   ```

#### 7e: Update the Issue

After handling all recommendations, update the issue with a status comment:

```bash
gh issue comment <issue-number> --body "## PR Update

**Checks:** <pass/fail>
**Copilot recommendations:** <N> total — <X> implemented, <Y> dismissed
**Changes made:**
- <list of changes>

**Status:** <ready for merge / needs another review cycle>"
```

#### 7f: Push and Re-run Governance

If any code changes were made in Steps 7d:

1. Push the updated branch: `git push`
2. Return to **Step 7a** — the governance workflow will re-trigger on the push
3. Repeat the entire 7a-7f cycle until:
   - All CI checks pass
   - All Copilot recommendations are addressed (implemented or dismissed)
   - The governance-review workflow produces an `APPROVE` decision

Maximum review cycles: **3**. If after 3 cycles the PR still has blocking findings, comment on the issue requesting human review and move to the next issue.

#### 7g: Merge to Main

Once governance approves (all checks pass, aggregate confidence meets threshold, no blocking policy flags):

1. Verify the branch is up to date with main:
   ```bash
   git fetch origin main && git merge origin/main
   ```
   If there are conflicts, resolve them in an isolated commit.

2. Do a final push if any merge was needed.

3. Wait for the final governance run to complete (Step 7a polling).

4. Merge the PR:
   ```bash
   gh pr merge <pr-number> --squash --delete-branch
   ```

5. Update and close the issue:
   ```bash
   gh issue close <issue-number> --comment "Merged via PR #<pr-number>. All governance checks passed."
   ```

6. Update the plan status to `completed` in `.plans/{issue-number}-*.md`.

### Step 8: Continue

Return to Step 1. Pick the next actionable issue. Repeat until no actionable issues remain.

## Constraints

- Never work on more than one issue simultaneously (sequential, not parallel)
- Always create a plan before writing code
- Always comment on the issue before starting work (announce intent)
- Always create an issue before starting work (even for in-session tasks)
- If any step fails, log the failure and move to the next issue
- Respect rate limits: maximum 5 issues per session
- Maximum 3 review cycles per PR before escalating to human review
- **Context capacity is a hard constraint** — check before starting each new issue and after every major step (plan, implement, review, merge)

## Context Capacity Shutdown Protocol

**This protocol is mandatory. Violating it causes irrecoverable loss of instructions and working context.**

Check context capacity before every new issue and after every major step. When at or above 80%:

1. **Stop immediately** — do not start the next issue or step
2. **Clean git state** — commit pending changes, abort any in-progress merges or rebases, ensure `git status` shows a clean working tree on every branch you touched
3. **Write checkpoint** — save to `.checkpoints/{timestamp}-{branch}.json`:
   ```json
   {
     "timestamp": "ISO-8601",
     "branch": "current branch name",
     "issues_completed": ["#N", "#M"],
     "issues_remaining": ["#X", "#Y"],
     "current_issue": "#Z or null",
     "current_step": "Step N description",
     "git_state": "clean",
     "pending_work": "description of what remains",
     "prs_created": ["#A", "#B"],
     "manifests_written": ["manifest-id-1"],
     "review_cycle": "current review cycle number if in Step 7"
   }
   ```
4. **Report to user** — summarize completed work, remaining work, and the checkpoint location
5. **Request context reset** — tell the user to run `/clear` and reference the checkpoint file path to resume

**Never allow context to reach compaction.** A compaction with uncommitted changes, merge conflicts, or in-progress operations destroys instructions that cannot be recovered.

## Exit Conditions

Stop the loop when:
- No actionable issues remain
- 5 issues have been processed in this session
- **Context window is at or above 80% capacity** — execute the shutdown protocol above before doing anything else
- A human sends a message (human input takes priority)
