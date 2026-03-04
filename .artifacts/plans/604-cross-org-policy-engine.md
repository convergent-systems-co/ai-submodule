# Plan: Enable cross-org consuming repos to run the full Python policy engine in CI

**Issue:** #604
**Type:** Feature
**Priority:** High

## Problem

Consuming repos in different GitHub orgs cannot clone the `convergent-systems-co/dark-forge` private submodule in CI. This means the full Python policy engine is unavailable, forcing a fallback to lightweight Tier 2 validation with reduced confidence (0.70 vs 0.85).

## Solution: Option A — Vendor the policy engine

During `init.sh --refresh` (and initial `init.sh` in submodule context), copy the policy engine, schemas, and policy profiles into the consuming repo at `.governance/engine/`. The governance workflow detects the vendored engine and uses it instead of requiring the submodule.

## Deliverables

1. **`governance/bin/vendor-engine.sh`** — Script that copies engine files to `.governance/engine/` in the consuming repo
2. **Update `governance/bin/setup-workflows.sh`** — Call vendor-engine during submodule setup
3. **Update `init.sh`** — Integrate vendoring into the init flow
4. **Update `dark-factory-governance.yml`** — Detect vendored engine path and use it for consuming repos
5. **Update `verify-installation.sh`** — Add vendored engine check
6. **Version tracking** — Write a `.governance/engine/VERSION` file with the submodule commit SHA for staleness detection
7. **Documentation** — Update relevant docs

## Implementation Steps

1. Create `governance/bin/vendor-engine.sh` that copies:
   - `governance/engine/policy_engine.py` -> `.governance/engine/policy_engine.py`
   - `governance/bin/policy-engine.py` -> `.governance/engine/policy-engine.py`
   - `governance/policy/` -> `.governance/engine/policy/`
   - `governance/schemas/panel-output.schema.json` -> `.governance/engine/schemas/panel-output.schema.json`
   - `governance/bin/requirements.txt` -> `.governance/engine/requirements.txt`
   - Write VERSION file with current submodule SHA

2. Integrate vendoring into `setup-workflows.sh` (called during init for submodule contexts)

3. Update governance workflow to detect vendored engine at `.governance/engine/policy-engine.py`

4. Update verify-installation.sh to check vendored engine presence and staleness

5. Run tests to ensure nothing breaks

## Testing

- Existing policy engine tests must still pass
- Verify vendoring script copies correct files
- Verify workflow detects vendored engine path
