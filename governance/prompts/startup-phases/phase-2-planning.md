# Phase 2: Parallel Planning

**Persona:** Tech Lead (`governance/personas/agentic/tech-lead.md`)

> **Context Gate -- Phase 2 Entry:** Execute the Context Gate protocol from startup.md before proceeding. Yellow tier: proceed (planning does not dispatch Coders). Orange/Red: execute Shutdown Protocol.

The Tech Lead receives the full batch of prioritized issues and plans **all of them** before any implementation begins. This front-loads the planning work in the main context window (where the Tech Lead has full codebase visibility) before dispatching to parallel Coder agents.

### 2a: Ensure `project.yaml`

Before any work, verify the project has a valid `project.yaml` in the project root.

1. **If `project.yaml` exists:** Analyze the current repository contents (scan for languages, frameworks, IaC files, API definitions, documentation) and compare with the `project.yaml` configuration. If the repo has evolved (e.g., new language, IaC introduced, API endpoints added), update `project.yaml` to reflect current state. Commit the update.

2. **If `project.yaml` does not exist:** Check if the repository has existing code:
   - **Has code:** Analyze the repo to detect languages, frameworks, test tools, and conventions. Generate `project.yaml` from the most appropriate template in `governance/templates/` (e.g., `python/project.yaml`, `go/project.yaml`). Commit the new file.
   - **Empty/new repo:** Prompt the developer: "What kind of work will live in this repository?" Use the answer to select the appropriate template and generate `project.yaml`.

This ensures `project.yaml` always reflects the actual repository composition. Developers should not need to manually copy templates.

### 2b: Validate Intent

1. **Verify issue is still open:**
   ```bash
   gh issue view <number> --json state --jq '.state'
   ```
   If closed, skip and return to Phase 1 for the next issue.
2. **Read the issue body and all comments.** Full issue details (including comments) were fetched during Phase 1d. Comments may contain additional requirements, refined acceptance criteria, scope changes, or clarifications that supersede or extend the original issue body. All comments must be read before evaluating intent.
   - **Comment authority policy:** Comments from the issue author or repository members/collaborators are **authoritative** -- treat them as amendments to the issue specification. Comments from other users are **advisory** -- consider them but do not treat them as binding requirements.
3. Validate clear acceptance criteria, considering both the issue body and all authoritative comments.
4. If unclear: label `refine`, comment explaining what needs clarification, return to Phase 1.
5. If clear: proceed to 2c (Select Review Panels).

### 2c: Select Review Panels

Analyze the codebase and change type to determine which reviews to invoke:

- **Always required** (per active policy profile): security-review, threat-modeling, cost-analysis, documentation-review, data-governance-review
- **Context-specific** (selected based on change type):
  - Documentation-only changes -> documentation-review (primary), skip code-review
  - API endpoint changes -> API review, security-review (enhanced)
  - Infrastructure/IaC changes -> cost-analysis (enhanced), infrastructure review
  - Data model changes -> data-governance-review (enhanced)
  - UI changes -> accessibility review (if panel exists)

If a needed review panel or persona does not exist, create a GitHub issue in the Dark Forge repository describing the gap, using `governance/prompts/cross-repo-escalation-workflow.md`.

### 2d: Create Plans (for all issues)

**Repeat for each issue in the batch:**

1. Create branch: `NETWORK_ID/{type}/{number}/{name}`
2. Write plan using `governance/templates/prompts/plan-template.md`
3. Save to `.artifacts/plans/{number}-{description}.md`
4. **Plan Validation**: After creating a plan, verify it contains the required sections:
   - **Objective** (`## 1. Objective`) -- the plan must state what the change accomplishes
   - **Scope** (`## 3. Scope`) -- the plan must define files to create, modify, or delete
   - **Approach** (`## 4. Approach`) -- the plan must include step-by-step implementation strategy

   If a newly created plan is missing any required section, warn and re-create the plan. If validation fails after **2 attempts**, skip the issue: emit a BLOCK message with `"reason": "plan_validation_failed"`, comment on the issue explaining the failure, and continue to the next issue. Plan validation failures are **non-blocking** -- a failure on one issue must not prevent planning of other issues.
5. High risk -> comment plan on issue, wait for approval before dispatching

After all plans are written, proceed to Phase 3 (Parallel Dispatch).
