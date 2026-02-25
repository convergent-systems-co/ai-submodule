# Startup: Agentic Improvement Loop

Execute this on agent launch. This is the Code Manager's entry point for autonomous operation.

<!-- ANCHOR: This instruction must survive context resets -->

## Context Capacity — MANDATORY (Read First)

**This section overrides all other work. If context is under pressure, stop and checkpoint.**

### Detection Signals

Watch for these signals that context is filling up:

1. **Token count warnings** — Claude Code shows token usage in verbose mode (right side). Copilot surfaces similar warnings. When total tokens exceed 80% of the model's context window, stop immediately.
2. **System warnings** — The runtime emits warnings when approaching context limits. These are non-negotiable stop signals.
3. **Conversation length heuristic** — If you have completed 3 issues, or made more than 50 tool calls, or the conversation exceeds ~100 exchanges, assume you are at or near 80% regardless of other signals.
4. **Degraded recall** — If you find yourself re-reading files you already read, forgetting earlier decisions, or producing inconsistent output, context pressure is likely the cause.

### Hard Limits

- **Maximum 3 issues per session** — non-negotiable safety net
- **Mandatory checkpoint after every issue** — before starting the next issue, always write a checkpoint (see Step 7i below)
- **Two-tier capacity threshold**: at ~70%, do not start a new issue (finish the current one, checkpoint, request `/clear`); at ~80%, stop immediately and execute the full shutdown protocol regardless of current step

### When Triggered

Execute the **Context Capacity Shutdown Protocol** (see end of this file). Do not start the next issue. Do not finish the current step. Stop, clean, checkpoint, report.

<!-- /ANCHOR -->

## In-Session Work

When the user provides work directly (bug reports, feature requests, feedback, or tasks) that does not correspond to an existing GitHub issue:

1. **Create a GitHub issue first** — capture the work as a trackable issue with acceptance criteria
2. **Then enter the Startup Sequence** at Step 4 (Validate Intent) with that issue
3. Never execute work without a corresponding issue — issues are the audit trail

When the user identifies a problem with a previously-created PR (e.g., failing checks, unresolved Copilot recommendations):

1. Check out the existing branch for that PR
2. Enter the Startup Sequence at Step 7 (PR Monitoring & Review Loop)

## Issue State Validation (Checkpoint Restore)

When resuming from a checkpoint (`.checkpoints/` file), **before continuing any work**:

1. For each issue listed in `current_issue` and `issues_remaining`, verify it is still open:
   ```bash
   gh issue view <number> --json state --jq '.state'
   ```
2. If `current_issue` is **closed**, do not resume work on it. Remove it from the work queue and proceed to the next remaining issue.
3. If any `issues_remaining` are closed, remove them from the queue.
4. If all issues are closed, proceed to Step 1 (Scan Open Issues) for a fresh scan.

Closed issues represent a user decision. Continuing work on them wastes compute and creates noise.

## Startup Sequence

### Pre-flight: Update .ai Submodule

Before any other pre-flight checks, ensure the `.ai` governance submodule is at the latest version:

1. **Detect submodule context** — check if `.ai` is a git submodule:
   ```bash
   git submodule status .ai 2>/dev/null
   ```
   If this fails (not a submodule, e.g., running inside the ai-submodule repo itself), skip this section.

2. **Check for dirty state in `.ai`:**
   ```bash
   if [ -n "$(git -C .ai status --porcelain)" ]; then
     echo "Warning: .ai submodule has uncommitted changes; skipping automatic update."
   fi
   ```
   If dirty, skip the update and log a warning. Do not attempt to update over uncommitted changes.

3. **Fetch latest and check for updates** (only if not dirty):
   ```bash
   git -C .ai fetch origin main --quiet 2>/dev/null
   ```
   If the fetch fails (network error), warn and continue — this is non-blocking.
   ```bash
   LOCAL_SHA=$(git -C .ai rev-parse HEAD)
   REMOTE_SHA=$(git -C .ai rev-parse origin/main)
   ```

4. **If behind, update:**
   ```bash
   git submodule update --remote .ai
   ```
   If the submodule pointer changed (`LOCAL_SHA != REMOTE_SHA`):
   - Commit the update: `git add .ai && git commit -m "chore: update .ai submodule to latest"`
   - Log: ".ai submodule updated from {LOCAL_SHA} to {REMOTE_SHA}"

   If already current, log: ".ai submodule is up to date"

5. **If update fails**, warn and continue — this is non-blocking but should be noted in the session log.

### Pre-flight: Repository Configuration

Before scanning issues, verify the repository supports the agentic workflow:

1. Check `allow_auto_merge` is enabled:
   ```bash
   gh api repos/{owner}/{repo} --jq '.allow_auto_merge'
   ```
2. Check CODEOWNERS is present and non-empty:
   ```bash
   test -s CODEOWNERS && echo "OK" || echo "MISSING"
   ```
3. Check governance workflow is present, enabled, and healthy:

   **3a. File exists:**
   ```bash
   test -f .github/workflows/dark-factory-governance.yml && echo "OK" || echo "MISSING"
   ```
   If running inside the ai-submodule repo itself (not a consuming repo), check `.github/workflows/` directly.

   **3b. Workflow is enabled:**
   ```bash
   gh api repos/{owner}/{repo}/actions/workflows --jq '.workflows[] | select(.path == ".github/workflows/dark-factory-governance.yml") | .state'
   ```
   Expected result: `active`. If the state is `disabled_manually` or `disabled_inactivity`, warn: "Governance workflow is disabled. Re-enable it in the repository's Actions settings or via `gh workflow enable dark-factory-governance.yml`." If the workflow is not found in the API response (but the file exists), it may not have been triggered yet — warn and continue.

   **3c. Recent run health:**
   ```bash
   gh api repos/{owner}/{repo}/actions/workflows/dark-factory-governance.yml/runs --jq '[.workflow_runs[:5] | .[] | .conclusion]'
   ```
   Evaluate the last 5 workflow run conclusions:
   - If **all 5 are `failure`**: Warn: "Governance workflow has failed 5 consecutive times. Investigate recent failures before relying on governance decisions." Log the URL of the most recent failed run for debugging.
   - If **no runs exist** (empty array): Warn: "Governance workflow has never run. The first PR will trigger it — governance decisions may be delayed on the first cycle."
   - If **at least 1 of the last 5 is `success`**: The workflow is considered healthy. Log: "Governance workflow health: OK ({N}/5 recent runs succeeded)."
   - Conclusions of `cancelled` or `skipped` are neutral — count only `success` and `failure` for the health assessment.

   **3d. Failure handling summary:**
   - Workflow file missing → suggest `bash .ai/init.sh`
   - Workflow disabled → suggest re-enabling via Actions settings or `gh workflow enable`
   - Workflow consistently failing → suggest investigating failure logs; note that governance decisions on PRs may be unreliable
   - All checks are **non-blocking** — warn and continue. The agent may still do useful work even with degraded governance, but PRs may not receive valid governance reviews.

4. If any check fails:
   - Warn the user: "Repository is not configured for the agentic loop."
   - Suggest running `bash .ai/init.sh` to apply settings from `config.yaml`
   - Continue with the startup sequence (non-blocking) but note that PR auto-merge may fail

### Step 0: Resolve Open PRs

**All open PRs must be resolved before the loop processes new issues.** This applies to PRs created by the agentic loop and PRs created by humans or other tools — all require panel evaluation.

1. **List open PRs:**
   ```bash
   gh pr list --state open --json number,title,author,headRefName,createdAt,reviews --limit 20
   ```

2. **Categorize each PR:**
   - **Agent PRs** (branch matches `itsfwcp/*/*`): Enter the full Step 7 review loop (7a through 7g) to resolve CI, Copilot recommendations, and merge.
   - **Non-agent PRs** (created by humans or other tools): Evaluate using the review loop steps 7a-7c (CI checks, Copilot recommendations, review classification). Do not merge — leave for the human author. Post a review summary comment on the PR.

3. **Resolution order:** Process PRs by creation date (oldest first). For each PR:
   a. Check out the PR branch: `gh pr checkout <pr-number>`
   b. Enter the Step 7 review loop at Step 7a
   c. For agent PRs: complete through Step 7g (merge) or escalate after 3 review cycles
   d. For non-agent PRs: complete through Step 7e (update comment), then move to the next PR
   e. Return to `main` after each PR: `git checkout main`

4. **Session accounting:** Each resolved PR (merged or escalated) counts toward the 3-issue session cap. If the cap is reached during PR resolution, execute the Context Capacity Shutdown Protocol — do not proceed to issue scanning.

5. **No open PRs:** If no open PRs exist, proceed directly to Step 1.

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
- It is not labeled `blocked`, `wontfix`, `duplicate`
- It is not assigned to a human (or is assigned to an agentic persona)
- It has not been updated in the last 24 hours by a human (avoid conflicts)
- **For `refine`-labeled issues**: see Step 2a below

#### Step 2a: Re-evaluate `refine` Issues

**Critical: Always query current issue state from the GitHub API. Never rely on cached assessments from earlier in the session or previous sessions.**

For each open issue currently labeled `refine`, check whether a human has updated it since the `refine` label was applied:

```bash
gh issue view {number} --json labels,comments,updatedAt
```

A `refine` issue should be **re-evaluated** (treated as potentially actionable) if ANY of:
- A human has added new comments since the agent's `refine` comment
- The issue body has been edited since the `refine` label was applied
- A human has removed and re-added the `refine` label (indicating they reviewed it)

If a human has removed the `refine` label entirely, the issue is already actionable — it will pass the standard filter above. **Never re-add `refine` to an issue where a human removed it** unless the agent reads the updated issue and independently determines the intent is still unclear.

For re-evaluable `refine` issues:
1. Re-read the full issue body and all comments (not cached versions)
2. If the human's updates provide the clarification that was requested, remove the `refine` label and treat the issue as actionable
3. If the updates are insufficient, leave the `refine` label and move on

### Step 3: Prioritize

Sort actionable issues by:
1. Label priority (`P0` > `P1` > `P2` > `P3` > `P4`)
2. If no priority label, use creation date (oldest first)
3. Issues labeled `bug` take precedence over `enhancement` at the same priority

### Step 4: Validate Intent (Layer 1)

For the highest-priority actionable issue:
1. **Verify the issue is still open** before any other validation:
   ```bash
   gh issue view <number> --json state --jq '.state'
   ```
   If the issue is closed, skip it and move to the next actionable issue. Do not start or continue work on closed issues — even if a branch or checkpoint exists for it.
2. Read the issue body
3. Validate it has clear acceptance criteria or a reproducible description
4. If the intent is unclear, has too many decision points, or lacks sufficient detail for action:
   - Label the issue `refine`
   - Comment on the issue explaining what needs clarification or which decisions must be made by the user
   - Move to the next issue
   - **Important**: The `refine` label is a request for human input, not a permanent exclusion. When a human updates the issue (adds comments, edits the body, or removes the label), Step 2a will re-evaluate it in the next session. Never treat `refine` as cached state that persists across sessions — always re-check against the live API.
5. If the intent is clear, proceed to Step 5

### Step 5: Create Plan

1. Create a branch: `itsfwcp/{issue-type}/{issue-number}/{branch-name}` (e.g., `itsfwcp/feat/42/add-auth`)
   - `{issue-type}` maps from the issue's conventional commit type: `feat`, `fix`, `refactor`, `docs`, `chore`
2. Write a plan using the plan template (`governance/prompts/templates/plan-template.md`)
3. Save the plan to `.plans/{issue-number}-{short-description}.md`
4. If the issue is low risk and well-defined, proceed to implementation
5. If the issue is high risk or ambiguous, comment the plan on the issue and wait for approval

### Step 6: Execute & Push PR

1. Adopt the Coder persona (`governance/personas/agentic/coder.md`)
2. Implement the plan
3. Write tests (if applicable to the change type)
4. **Update documentation (mandatory)** — Review all changes made in steps 2–3 and update every affected documentation file in the same commit(s). This is not optional and must not be deferred to a follow-up PR. Check each category:
   - **`GOALS.md`** — Check off completed items (`- [x]`), add issue/PR to the "Completed Work" section if the work closes a goals item
   - **`CLAUDE.md`** (root and `.ai/`) — Update if personas, panels, phases, conventions, architecture descriptions, or counts changed
   - **`README.md`** — Update if bootstrap process, architecture overview, or policy descriptions changed
   - **`DEVELOPER_GUIDE.md`** — Update if onboarding-relevant information, setup steps, or workflow descriptions changed
   - **`governance/docs/*.md`** — Update architecture docs if governance layers, persona/panel definitions, context management, or policy logic changed
   - **Schema files** (`governance/schemas/`) — Update if structured emission formats, manifest structures, or panel output contracts changed
   - **Policy files** (`governance/policy/`) — Update if merge decision logic, thresholds, or profile configurations changed
   - **`instructions/*.md`** — Update if code quality, security, testing, or communication guidance changed

   If no documentation files are affected (e.g., a purely internal refactor with no user-facing or governance-facing changes), explicitly note this in the commit message body: `Docs: no documentation updates required — [reason]`.
5. Commit with conventional commit messages — one logical change per commit (Git Commit Isolation)
6. **Run the Test Coverage Gate (mandatory)** — Execute `governance/prompts/test-coverage-gate.md` before pushing. This gate runs the full test suite, enforces 80% minimum coverage, and verifies test completeness for changed files. The push **must not proceed** until the gate passes. If the gate blocks after 3 fix attempts, escalate to the Code Manager — do not push broken or under-tested code.
7. Push the branch
8. Create a PR referencing the issue:
   ```bash
   gh pr create --title "<type>: <description>" --body "Closes #<issue-number>\n\n## Summary\n<description>\n\n## Plan\nSee .plans/<issue-number>-<description>.md"
   ```
9. Comment on the issue that the PR has been created:
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

After checks complete, fetch Copilot findings from **all three comment sources** (each source is disjoint).

##### Diagnostic Pre-Fetch (Mandatory)

Before running any filtered query, fetch **unfiltered** comment counts from all three endpoints to establish a baseline:

```bash
# Unfiltered counts — run these FIRST
INLINE_TOTAL=$(gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --jq 'length')
REVIEW_TOTAL=$(gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews --jq 'length')
ISSUE_TOTAL=$(gh api repos/{owner}/{repo}/issues/{pr_number}/comments --jq 'length')
```

Log all three counts. After running the filtered queries below, compare filtered vs. unfiltered counts. If **any** filtered result is empty but its corresponding unfiltered count is non-zero, emit a **filter-mismatch warning** and inspect the unfiltered results manually to determine whether the jq filter missed bot comments due to an unexpected `user.login` value.

##### Filtered Queries

The jq filter combines a username regex with a user-type check for defense in depth:

```
select(
  (.user.login | test("^copilot$|copilot-pull-request-reviewer|github-advanced-security|github-copilot"; "i"))
  or ((.user.type == "Bot" or (.user.login | test("\\[bot\\]$"))) and (.user.login | test("copilot"; "i")))
)
```

Apply this filter to each endpoint:

1. **Inline code comments** (Copilot posts line-level suggestions and review thread comments here):
   ```bash
   gh api repos/{owner}/{repo}/pulls/{pr_number}/comments --jq '[.[] | select((.user.login | test("^copilot$|copilot-pull-request-reviewer|github-advanced-security|github-copilot"; "i")) or ((.user.type == "Bot" or (.user.login | test("\\[bot\\]$"))) and (.user.login | test("copilot"; "i"))))]'
   ```

2. **PR reviews** (Copilot may post a top-level review summary):
   ```bash
   gh api repos/{owner}/{repo}/pulls/{pr_number}/reviews --jq '[.[] | select((.user.login | test("^copilot$|copilot-pull-request-reviewer|github-advanced-security|github-copilot"; "i")) or ((.user.type == "Bot" or (.user.login | test("\\[bot\\]$"))) and (.user.login | test("copilot"; "i"))))]'
   ```

3. **Issue-level comments** (some bots post here instead of as reviews):
   ```bash
   gh api repos/{owner}/{repo}/issues/{pr_number}/comments --jq '[.[] | select((.user.login | test("^copilot$|copilot-pull-request-reviewer|github-advanced-security|github-copilot"; "i")) or ((.user.type == "Bot" or (.user.login | test("\\[bot\\]$"))) and (.user.login | test("copilot"; "i"))))]'
   ```

##### Minimum Polling Requirement

The agent **MUST** execute at least 2 polling attempts separated by at least 2 minutes before concluding no Copilot comments exist. A single empty poll is **NOT** sufficient to confirm absence — timing gaps between PR creation and Copilot analysis mean early polls frequently return empty results even when Copilot will comment.

**Waiting protocol:** Treat the wait window as the first 10 minutes after PR creation (using `created_at`). First, check all sources immediately. If no Copilot comments exist from any source, you **must** poll at least one more time after waiting at least 2 minutes. You may continue polling **only while** (a) it is still less than 10 minutes since PR creation, (b) the remaining time until `created_at + 10 minutes` is at least 2 minutes, and (c) you have performed fewer than 5 total polling attempts. Between polls, sleep for up to 2 minutes but **never longer than the remaining time** before the 10-minute deadline (i.e., `sleep = min(2 minutes, remaining)`). Once either the 10-minute window has elapsed or you have reached 5 polling attempts (with a minimum of 2), proceed without Copilot input (per `missing_panel_behavior: redistribute` in policy).

**Do NOT merge until all sources have been checked.** The absence of Copilot findings must be confirmed, not assumed.

#### 7c: Review Recommendations

For each Copilot recommendation and any panel emission finding:

1. **Classify severity** using the rules in `governance/prompts/reviews/copilot-review.md`:
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

1. **Run the Test Coverage Gate** — Execute `governance/prompts/test-coverage-gate.md` before pushing. All tests must pass and coverage must meet the 80% threshold. If the gate blocks, fix the issues before pushing.
2. Push the updated branch: `git push`
3. Return to **Step 7a** — the governance workflow will re-trigger on the push
4. Repeat the entire 7a-7f cycle until:
   - All CI checks pass
   - All Copilot recommendations are addressed (implemented or dismissed)
   - The governance-review workflow produces an `APPROVE` decision

Maximum review cycles: **3**. If after 3 cycles the PR still has blocking findings, comment on the issue requesting human review and move to the next issue.

#### 7f-bis: Pre-Merge Review Thread Verification (Safety Net)

This step is the **critical safety net** that catches review comments missed by the Copilot-specific filter in Step 7b. It is author-agnostic and uses GitHub's GraphQL API to inspect all review threads on the PR, regardless of who created them. **This step must pass before merge.**

1. **Fetch all review threads** using the GraphQL `reviewThreads` query:

   ```bash
   gh api graphql -f query='
     query($owner: String!, $repo: String!, $pr: Int!) {
       repository(owner: $owner, name: $repo) {
         pullRequest(number: $pr) {
           reviewThreads(first: 100) {
             nodes {
               isResolved
               isOutdated
               comments(first: 1) {
                 nodes {
                   author { login }
                   body
                 }
               }
             }
           }
         }
       }
     }
   ' -f owner='{owner}' -f repo='{repo}' -F pr={pr_number}
   ```

2. **Count active unresolved threads** — threads where `isResolved == false` AND `isOutdated == false`. Outdated threads (on code that has been subsequently changed) do not block merge.

3. **Evaluate result:**
   - **Zero active unresolved threads:** Proceed to Step 7g (merge).
   - **Non-zero active unresolved threads:** Process each unresolved thread as if it were a new finding — classify per Step 7c, implement or dismiss per Step 7d, then return to Step 7a to re-run the full cycle.
   - **GraphQL query fails:** Block merge. Do not fall through to Step 7g. Comment on the issue requesting human review and escalate.

This gate catches: Copilot comments missed by the jq filter, human review comments added between cycles, and feedback from any other bot or integration. It is intentionally redundant with Step 7b — the two mechanisms must independently agree that no unresolved feedback exists before merge proceeds.

#### 7g: Merge to Main

**Precondition:** Step 7f-bis must have completed with zero active unresolved threads. If Step 7f-bis was skipped or did not execute, do not proceed — return to Step 7f-bis.

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

#### 7h: Retrospective

After merge and before marking the plan as completed, run a lightweight retrospective per `governance/prompts/retrospective.md`:

1. Evaluate planning accuracy, review cycle count, and token cost observations
2. **Verify documentation completeness** — Confirm that all documentation categories from Step 6.4 were addressed during implementation. Explicitly check each of the four primary docs (`GOALS.md`, `README.md`, `DEVELOPER_GUIDE.md`, `CLAUDE.md`) for consistency with the merged change — phase status, feature claims, file structure listings, persona/panel counts, and architecture descriptions must agree across all four files. If any were missed (e.g., `GOALS.md` not updated for a goals-related issue, `README.md` phase status not updated when a phase is completed, `CLAUDE.md` counts not updated after adding personas), create a follow-up issue labeled `docs` to track the gap. Do not re-open or amend the merged PR.
3. Post findings as a comment on the closed issue (include documentation verification status)
4. If findings warrant governance changes, create a new issue labeled `enhancement`
5. Skip retrospective detail if the issue was trivial or context capacity is above 70% — but **never skip the documentation verification in substep 2**

6. Update the plan status to `completed` in `.plans/{issue-number}-*.md`.

#### 7i: Mandatory Checkpoint (Between Issues)

**This step is not optional. Execute it after every issue, before starting the next.**

1. Write a checkpoint to `.checkpoints/{timestamp}-{branch}.json` with current session state
2. Record the just-completed issue in the checkpoint's `issues_completed` array; the session issue counter is implicitly the length of this array
3. **If 3 issues have been completed this session**: execute the full Context Capacity Shutdown Protocol and request `/clear`. Do not start a 4th issue.
4. **If any context pressure signal is present** (see "Context Capacity — MANDATORY" at top of file): execute shutdown protocol regardless of issue count
5. **If neither limit is hit**: proceed to Step 8

### Step 8: Continue or Fall Back to Goals

Return to Step 1. Pick the next actionable issue.

If **no actionable issues remain** after Step 3 (all issues are closed, blocked, in `refine`, or otherwise excluded):

1. Read `GOALS.md` and scan for unchecked items (lines starting with `- [ ]`) in the Phase 4b and Phase 5 sections (or any section with pending items).
2. **Filter out items that already have an open issue** — for each GOALS.md item, check the open issue list and treat it as a duplicate if there is (a) an open issue whose title is an exact or very close match to the item text, or (b) an open issue whose description clearly references the same capability or work item.
3. **Prioritize by phase** — Phase 4b items before Phase 5 items (closer to current maturity).
4. For the highest-priority unchecked item that is sufficiently clear to act on:
   a. **Create a GitHub issue** from the GOALS.md item, with a title matching the item text and a body describing the scope from the surrounding context in GOALS.md. Label it with the appropriate label (`enhancement` for features, `bug` for defects).
   b. **Enter the Startup Sequence at Step 4** (Validate Intent) with the newly created issue.
5. `GOALS.md` updates for the completed item are handled by the mandatory documentation step (Step 6.4) as part of the implementation commit. The retrospective (Step 7h) verifies completeness.
6. If the highest-priority unchecked item is too vague to act on, skip it and move to the next unchecked item. Do not create an issue for vague items — note them for a future planning pass.
7. If no unchecked GOALS.md items remain (or all remaining items are too vague), the loop exits.

Repeat until no actionable issues or goals remain, or a hard limit is reached.

## Constraints

- **Resolve all open PRs before starting new issues** — Step 0 is mandatory; never skip to Step 1 while open PRs exist
- Never work on more than one issue simultaneously (sequential, not parallel)
- Always create a plan before writing code
- **Always update documentation before committing** — Step 6.4 documentation review is mandatory for every issue
- Always comment on the issue before starting work (announce intent)
- Always create an issue before starting work (even for in-session tasks)
- If any step fails, log the failure and move to the next issue
- **Maximum 3 issues per session** — hard cap, non-negotiable. Resolved PRs from Step 0 count toward this cap.
- Maximum 3 review cycles per PR before escalating to human review
- **Mandatory checkpoint after every issue** — Step 7i is never skipped
- **Context capacity is a hard constraint** — if any detection signal triggers, execute the shutdown protocol immediately

## Context Capacity Shutdown Protocol

**This protocol is mandatory. Violating it causes irrecoverable loss of instructions and working context.**

**Trigger conditions** (any one is sufficient):
- Token count at or above 80% of context window (visible in verbose mode)
- System warning about approaching context limits
- 3 issues completed this session (hard cap)
- Conversation exceeds ~100 exchanges or ~50 tool calls
- Agent notices degraded recall or inconsistent output

When triggered:

1. **Stop immediately** — do not start the next issue or step
2. **Clean git state** — commit pending changes, abort any in-progress merges or rebases, ensure `git status` shows a clean working tree on every branch you touched
3. **Write checkpoint** — save to `.checkpoints/{timestamp}-{branch}.json`:
   ```json
   {
     "timestamp": "ISO-8601",
     "branch": "current branch name",
     "issues_completed": ["#N", "#M"],
     "prs_resolved": ["#P", "#Q"],
     "issues_remaining": ["#X", "#Y"],
     "prs_remaining": ["#R"],
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
- No open PRs to resolve **and** no actionable issues remain **and** no unchecked GOALS.md items can be converted to issues
- **3 issues/PRs have been completed this session** — execute shutdown protocol, checkpoint, request `/clear`
- **Any context pressure signal triggers** — execute shutdown protocol immediately
- A human sends a message (human input takes priority)
