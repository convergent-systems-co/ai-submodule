# Startup: Agentic Improvement Loop

Execute this on agent launch. This is the Code Manager's entry point for autonomous operation.

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
- It has no associated branch matching `itsfwcp/*` or `feature/*` patterns
- It is not labeled `blocked`, `wontfix`, or `duplicate`
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
3. If the intent is unclear, comment on the issue asking for clarification and move to the next issue
4. If the intent is clear, proceed to Step 5

### Step 5: Create Plan

1. Create a branch: `itsfwcp/{issue-number}-{short-description}`
2. Write a plan using the plan template (`prompts/plan-template.md`)
3. Save the plan to `.plans/{issue-number}-{short-description}.md`
4. If the issue is low risk and well-defined, proceed to implementation
5. If the issue is high risk or ambiguous, comment the plan on the issue and wait for approval

### Step 6: Execute

1. Adopt the Coder persona (`personas/agentic/coder.md`)
2. Implement the plan
3. Write tests
4. Commit with conventional commit messages
5. Push the branch
6. Create a PR referencing the issue

### Step 7: Review Loop

1. Invoke the appropriate panel based on the change type
2. If the panel requests changes, fix them and re-run
3. If the panel approves with sufficient confidence, the policy engine evaluates
4. Log the run manifest

### Step 8: Continue

Return to Step 1. Pick the next actionable issue. Repeat until no actionable issues remain.

## Constraints

- Never work on more than one issue simultaneously (sequential, not parallel)
- Always create a plan before writing code
- Always comment on the issue before starting work (announce intent)
- If any step fails, log the failure and move to the next issue
- Respect rate limits: maximum 5 issues per session
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
     "manifests_written": ["manifest-id-1"]
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
