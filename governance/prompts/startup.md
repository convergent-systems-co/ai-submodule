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
2. Write a plan using the plan template (`governance/prompts/plan-template.md`)
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
6. Push the branch
7. Create a PR referencing the issue:
   ```bash
   gh pr create --title "<type>: <description>" --body "Closes #<issue-number>\n\n## Summary\n<description>\n\n## Plan\nSee .plans/<issue-number>-<description>.md"
   ```
8. Comment on the issue that the PR has been created:
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

1. **Classify severity** using the rules in `governance/personas/panels/copilot-review.md`:
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

#### 7h: Retrospective

After merge and before marking the plan as completed, run a lightweight retrospective per `governance/prompts/retrospective.md`:

1. Evaluate planning accuracy, review cycle count, and token cost observations
2. **Verify documentation completeness** — Confirm that all documentation categories from Step 6.4 were addressed during implementation. If any were missed (e.g., `GOALS.md` not updated for a goals-related issue, `CLAUDE.md` counts not updated after adding personas), create a follow-up issue labeled `docs` to track the gap. Do not re-open or amend the merged PR.
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

- Never work on more than one issue simultaneously (sequential, not parallel)
- Always create a plan before writing code
- **Always update documentation before committing** — Step 6.4 documentation review is mandatory for every issue
- Always comment on the issue before starting work (announce intent)
- Always create an issue before starting work (even for in-session tasks)
- If any step fails, log the failure and move to the next issue
- **Maximum 3 issues per session** — hard cap, non-negotiable
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
- No actionable issues remain **and** no unchecked GOALS.md items can be converted to issues
- **3 issues have been completed this session** — execute shutdown protocol, checkpoint, request `/clear`
- **Any context pressure signal triggers** — execute shutdown protocol immediately
- A human sends a message (human input takes priority)
