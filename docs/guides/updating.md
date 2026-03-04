# Updating the Governance Framework

This guide covers how to update the `.ai` governance submodule in your project.

## Quick Update

```bash
bash .ai/bin/update.sh
```

This single command:
1. Checks for available updates
2. Shows a changelog of what changed
3. Detects breaking changes (schema/policy modifications, deleted files)
4. Detects local drift (your customizations that may conflict)
5. Applies the update (`git submodule update --remote .ai`)
6. Runs `init.sh --refresh` to re-apply structural setup

## Check for Updates

To see if an update is available without applying it:

```bash
bash .ai/bin/update.sh --check
```

## Dry Run

To see what would happen without making changes:

```bash
bash .ai/bin/update.sh --dry-run
```

## Force Update

To update even when no changes are detected:

```bash
bash .ai/bin/update.sh --force
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (or already up to date) |
| 1 | Breaking changes detected (update applied, review warnings) |
| 2 | Local drift detected (update applied, review warnings) |
| 3 | Update failed |

## Drift Detection

The framework tracks SHA256 hashes of key governance files to detect when your local copies diverge from upstream.

### Create a Baseline

After a fresh update, snapshot the current state:

```bash
bash .ai/governance/bin/drift-detection.sh --snapshot
```

### Check for Drift

```bash
bash .ai/governance/bin/drift-detection.sh
```

### Tracked Files

Drift detection monitors:
- Policy profiles (`governance/policy/*.yaml`)
- JSON schemas (`governance/schemas/*.json`)
- Agent protocol (`governance/prompts/agent-protocol.md`)
- Startup prompt (`governance/prompts/startup.md`)
- CLAUDE.md

## Breaking Change Detection

The update script automatically checks for:
- Deleted files that your project may reference
- Renamed schema files
- Removed schema properties or required fields
- Changed policy profile keys

You can also run this manually between two versions:

```bash
bash .ai/governance/bin/breaking-change-check.sh OLD_SHA NEW_SHA
```

## Manual Update (Legacy)

If you prefer the manual approach:

```bash
git submodule update --remote .ai
bash .ai/bin/init.sh --refresh
```

## Auto-Update via CI

The `propagate-submodule.yml` workflow can automatically create PRs when the governance submodule is updated. Configure it by adding your consuming repos to the workflow matrix.

## Semantic Versioning

The governance framework uses git tags for version tracking. Pin a specific version:

```bash
cd .ai
git checkout v1.5.0
cd ..
git add .ai
git commit -m "chore: pin governance to v1.5.0"
```
