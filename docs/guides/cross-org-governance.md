# Cross-Org Governance CI Integration

This guide covers running Dark Forge governance checks in CI for consuming repos that exist in a **different GitHub organization** from the `dark-forge`. In cross-org setups, CI runners typically cannot clone the private submodule, which breaks the standard governance pipeline.

## The Problem

When a consuming repo references `convergent-systems-co/dark-forge` as a git submodule at `.ai/`, CI environments in other organizations fail because:

1. **Private submodule inaccessible** -- The CI runner lacks credentials to clone `convergent-systems-co/dark-forge`
2. **Symlinks break** -- Legacy symlinks pointing into `.ai/` resolve to nothing when the submodule content is absent
3. **Policy engine unavailable** -- The governance workflow cannot find the policy engine at `.ai/governance/bin/policy-engine.py`

## Solution: Three-Tier Fallback

The governance workflow uses a progressive fallback strategy:

| Tier | Source | When Used | Capabilities |
|------|--------|-----------|-------------|
| **1** | `.ai/governance/` (submodule) | Submodule is accessible | Full policy engine, all schemas, all profiles |
| **1.5** | `.artifacts/engine/` (vendored) | Submodule unavailable, vendored copy present | Full policy engine with vendored profiles and schemas |
| **2** | Inline Python (workflow) | Neither available | Lightweight emission-only validation |

## Setup Instructions

### 1. Run `init.sh` Locally

After adding the submodule and before pushing to CI:

```bash
bash .ai/bin/init.sh
```

This copies (not symlinks) all necessary files into the consuming repo:
- `.github/workflows/dark-factory-governance.yml` -- governance workflow
- `.artifacts/engine/` -- vendored policy engine, schemas, and profiles
- `CLAUDE.md`, `.github/copilot-instructions.md` -- AI instructions (copies)

### 2. CI-Only Setup (Optional)

For CI pipelines that need a minimal setup without IDE configuration:

```bash
bash .ai/bin/init.sh --ci
```

This runs only:
- Governance directory creation (`.artifacts/plans/`, `.artifacts/panels/`, etc.)
- Emission validation
- Engine vendoring

Skipped in `--ci` mode: symlinks/copies for IDE files, submodule freshness checks, repo configuration, MCP server installation.

### 3. Verify Cross-Org Readiness

```bash
bash .ai/bin/init.sh --verify
```

Look for these checks in the output:
- `[PASS] Vendored engine has all required files for standalone CI`
- `[PASS] No symlinks found in CI-critical paths (cross-org compatible)`
- `[PASS] Cross-org CI ready: vendored engine + emissions directory present`

If you see warnings about symlinks, run `--refresh` to convert them to copies:

```bash
bash .ai/bin/init.sh --refresh
```

### 4. Commit Vendored Engine

The vendored engine at `.artifacts/engine/` must be committed to the repo. It is not gitignored by default. Ensure these files are tracked:

```
.artifacts/engine/policy-engine.py
.artifacts/engine/policy_engine.py     # (if present)
.artifacts/engine/VERSION
.artifacts/engine/policy/default.yaml
.artifacts/engine/schemas/panel-output.schema.json
```

### 5. Keep Vendored Engine Updated

After updating the `.ai/` submodule pointer, re-vendor:

```bash
git submodule update --remote .ai
bash .ai/bin/init.sh --refresh
git add .artifacts/engine/
git commit -m "chore: update vendored governance engine"
```

To check staleness without updating:

```bash
bash .ai/governance/bin/vendor-engine.sh --check
```

## How the Workflow Detects the Tier

The `dark-factory-governance.yml` workflow includes a **CI bootstrap** step that runs before policy evaluation:

1. Attempts to initialize the submodule (`git submodule update --init`)
2. Runs `ci-bootstrap.sh --check` to detect the available tier
3. If the submodule is available, uses Tier 1
4. If the vendored engine passes integrity checks (VERSION non-empty, `policy/default.yaml` exists), uses Tier 1.5
5. Otherwise, falls back to Tier 2 lightweight validation

The bootstrap step outputs `engine_tier` (1, 1.5, or 2) for downstream steps to consume.

## Troubleshooting

### "No governance engine detected"

The CI workflow could not find either the submodule or vendored engine.

**Fix:** Run `bash .ai/bin/init.sh --refresh` locally and commit `.artifacts/engine/`.

### "Vendored engine incomplete"

The vendored copy is missing required files.

**Fix:** Run `bash .ai/bin/init.sh --refresh` to re-vendor from the current submodule.

### "Vendored engine VERSION file is empty"

The VERSION file exists but has no content, indicating a corrupted vendor.

**Fix:** Run `bash .ai/governance/bin/vendor-engine.sh --force` to force re-vendor.

### Workflow still using Tier 2

Check that:
1. `.artifacts/engine/policy-engine.py` exists and is committed
2. `.artifacts/engine/VERSION` is non-empty
3. `.artifacts/engine/policy/default.yaml` exists
4. These files are not in `.gitignore`

### Panel emissions not found

Consuming repos store emissions in `.artifacts/panels/` (not `governance/emissions/`). Ensure your panels write output to the correct directory.

## Architecture Diagram

```
Consuming Repo (different org)
  ├── .ai/                          # Submodule (gitlink only in CI — content unavailable)
  ├── .artifacts/
  │   ├── engine/                   # Vendored policy engine (committed)
  │   │   ├── policy-engine.py
  │   │   ├── VERSION
  │   │   ├── policy/default.yaml
  │   │   └── schemas/panel-output.schema.json
  │   ├── panels/                   # Panel emissions (per-PR)
  │   ├── plans/                    # Implementation plans
  │   └── checkpoints/              # Session checkpoints
  ├── .github/
  │   └── workflows/
  │       └── dark-factory-governance.yml  # Governance workflow (copy, not symlink)
  ├── CLAUDE.md                     # AI instructions (copy, not symlink)
  └── project.yaml                  # Project configuration
```

## Related

- [Repository Setup](../configuration/repository-setup.md) -- initial setup guide
- [Governance Model](../architecture/governance-model.md) -- tiered evaluation architecture (section 15)
- `governance/bin/vendor-engine.sh` -- vendoring implementation
- `governance/bin/ci-bootstrap.sh` -- CI bootstrap implementation
