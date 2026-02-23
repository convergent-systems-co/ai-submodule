# Data Governance: Missing Canonical Workflow

This workflow is triggered when the data-governance-review panel detects that a data change references a canonical model that does not exist in [SET-Apps/dach-canonical-models](https://github.com/SET-Apps/dach-canonical-models).

## When to Trigger

- A PR introduces or modifies data models, schemas, or event structures
- The referenced canonical model (domain, schema group, or entity) does not exist in dach-canonical-models
- A field is defined locally that should be an external reference to Data Standards

## Workflow Steps

### Step 1: Identify the Missing Canonical

Determine what is missing:
- **Missing domain model** — e.g., a new domain like `warranty` has no `warranty.hck.json` in canonical models
- **Missing schema group** — e.g., a new product line has no `product-newline` schema
- **Missing standard field** — e.g., a new enterprise-standard field is needed in `Data Standards.hck.json`

Document:
- The canonical model or field that is needed
- Why it is needed (business justification from the consuming repo's issue)
- Proposed structure (field names, types, constraints)

### Step 2: Create Issue on Canonical Repository

Create a GitHub issue on `SET-Apps/dach-canonical-models`:

```bash
gh issue create --repo SET-Apps/dach-canonical-models \
  --title "feat: add <canonical-name> canonical model" \
  --label "blocked" --label "data-governance" \
  --body "## Missing Canonical Model

**Requested by:** <consuming-repo-name> (issue #<issue-number>)
**Type:** <domain model | schema group | standard field>

### What is needed
<description of the canonical model or field needed>

### Business justification
<why this canonical is required>

### Proposed structure
<field definitions, types, constraints>

### Blocking
This issue blocks work in <consuming-repo> until the canonical model is created and published.

---
*Created automatically by the Dark Factory governance workflow.*"
```

### Step 3: Block Work on Consuming Repository

On the consuming repository's issue or PR:

1. Add `blocked` and `data-governance` labels to the issue
2. Comment with the cross-reference:

```bash
gh issue comment <consuming-issue-number> --body "## Data Governance: Blocked

**Reason:** Missing canonical model in dach-canonical-models.
**Canonical issue:** SET-Apps/dach-canonical-models#<canonical-issue-number>

This issue is blocked until the canonical model is created in the canonical repository. The data-governance-review panel will not approve changes that reference non-existent canonical models.

### What needs to happen
1. The canonical model must be created in [dach-canonical-models](https://github.com/SET-Apps/dach-canonical-models)
2. Once the canonical issue is resolved, remove the \`blocked\` label from this issue
3. Re-run the governance pipeline to verify compliance

---
*Automated by the Dark Factory data governance workflow.*"
```

### Step 4: Notify the User

Report to the user:
- What canonical model is missing
- The issue created on the canonical repository
- That work is blocked until the canonical is available
- What steps are needed to unblock

### Step 5: Monitor for Resolution

In subsequent sessions, when processing blocked issues:
1. Check if the canonical issue has been closed
2. If resolved, remove the `blocked` label from the consuming issue
3. Re-enter the governance pipeline at Step 4 (Validate Intent) with the unblocked issue

## Constraints

- Never create data models locally that should be canonicals — always request from the canonical repo
- Never remove the `blocked` label until the canonical issue is resolved
- Always include cross-references between the consuming repo issue and the canonical repo issue
- The data-governance-review panel must block the PR until the canonical exists
