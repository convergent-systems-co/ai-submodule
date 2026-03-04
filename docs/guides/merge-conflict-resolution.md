# AI-Based Merge Conflict Resolution

When N parallel Coders produce PRs that modify overlapping files, merge conflicts are inevitable during Phase 5 (Merge). The Safe Push pattern automates resolution using a three-tier strategy.

## How It Works

### Safe Push Flow

```
git push
  |
  v
Push accepted? ─── Yes ──> Done
  |
  No (rejected)
  |
  v
git fetch + git rebase
  |
  v
Rebase clean? ─── Yes ──> Retry push
  |
  No (conflicts)
  |
  v
Classify each conflicted file
  |
  ├── Protected? ──> ESCALATE (human review)
  ├── Generated? ──> REGENERATE (accept theirs)
  └── Code? ────────> AI RESOLVE (LLM agent)
  |
  v
All resolved? ─── Yes ──> git rebase --continue, retry push
  |
  No
  |
  v
Abort rebase, escalate to human
```

### Three-Tier Resolution Strategy

| Tier | File Type | Strategy | Example Files |
|------|-----------|----------|---------------|
| 1 | Protected | Escalate | `jm-compliance.yml`, `governance/policy/**`, `governance/schemas/**` |
| 2 | Generated | Regenerate | `governance/integrity-manifest.json`, `*-lock.json` |
| 3 | Code | AI Resolve | `*.py`, `*.ts`, `*.md`, all other files |

**Protected files** are never auto-resolved. They require human review. This includes governance policy, schemas, personas, review prompts, and enterprise-locked files.

**Generated files** are resolved by accepting the incoming version, since they will be regenerated in a follow-up step (integrity manifests, lock files).

**Code files** are resolved by an LLM agent that receives both sides of the conflict and produces a merged version. The LLM is instructed to preserve the intent of both sides.

## Usage

### Shell Script

```bash
# Standard safe push (3 retries, then force-with-lease)
bash governance/bin/safe-push.sh

# Custom branch and remote
bash governance/bin/safe-push.sh --branch feature/my-change --remote upstream

# Increase retry limit
bash governance/bin/safe-push.sh --max-retries 5

# Dry run (no git operations)
bash governance/bin/safe-push.sh --dry-run

# Skip retries, go straight to force-with-lease
bash governance/bin/safe-push.sh --force-with-lease
```

### Python API

```python
from governance.engine.conflict_resolver import ConflictResolver, safe_push

# Full safe-push operation
result = safe_push(repo_root="/path/to/repo", branch="my-branch")
print(f"Success: {result.success}")
print(f"Resolved: {result.conflicts_resolved}/{result.conflicts_found}")

# Manual conflict resolution
resolver = ConflictResolver(repo_root="/path/to/repo")
conflicted = resolver.get_conflicted_files()
result = resolver.resolve_all(conflicted)

for record in result.resolution_records:
    print(f"{record.file_path}: {record.outcome} ({record.strategy})")
```

## Integration with Phase 5

The Safe Push is invoked during the Tech Lead's Phase 5 merge workflow:

1. Tech Lead selects PRs for merge (ordered by `merge-sequencing.yaml`)
2. For each PR, merge into the target branch
3. If the merge produces conflicts, invoke the Safe Push resolver
4. If all conflicts resolve, continue with governance checks
5. If any conflict escalates, flag the PR for human review

## Audit Trail

Every resolution produces a JSON audit record in `.artifacts/state/conflict-resolutions/`:

```json
{
  "success": true,
  "push_attempts": 2,
  "conflicts_found": 3,
  "conflicts_resolved": 2,
  "conflicts_escalated": 1,
  "resolution_records": [
    {
      "file_path": "src/main.py",
      "classification": "code",
      "strategy": "ai_resolve",
      "outcome": "resolved",
      "timestamp": "2026-03-02T14:30:00Z",
      "hunks_resolved": 2,
      "hunks_total": 2
    }
  ]
}
```

## Protected File Handling

The following file patterns are governance-protected and can never be AI-resolved:

- `jm-compliance.yml` (enterprise-locked)
- `governance/policy/**` (deterministic policy profiles)
- `governance/schemas/**` (JSON Schema enforcement)
- `governance/personas/**` (agent persona definitions)
- `governance/prompts/reviews/**` (review panel prompts)
- `.github/workflows/dark-factory-governance.yml` (governance CI)

If any of these files have conflicts, the entire resolution escalates to human review. This aligns with the containment hook (`governance/engine/containment_hook.py`) that prevents persona branches from modifying these files.

## Configuration

The Safe Push script uses sensible defaults:

| Setting | Default | Override |
|---------|---------|----------|
| Max retries | 3 | `--max-retries N` |
| Remote | `origin` | `--remote NAME` |
| Branch | current | `--branch NAME` |
| LLM timeout | 120s | (code constant) |
| Audit dir | `.artifacts/state/conflict-resolutions/` | (code constant) |
