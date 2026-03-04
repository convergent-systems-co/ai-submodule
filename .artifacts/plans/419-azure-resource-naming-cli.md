# Azure Resource Naming CLI Tool

**Author:** Team Lead (agentic)
**Date:** 2026-02-26
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/419
**Branch:** NETWORK_ID/feat/419/azure-naming-cli

---

## 1. Objective

Build a standalone CLI tool (`bin/generate-name`) that produces predictable, Azure-compliant resource names following JM naming conventions. The tool enforces length limits, character restrictions, and deterministic shortening — enabling local testing without Azure deployment.

## 2. Rationale

The existing `getResourceNames()` Bicep utility module runs only within Bicep deployments. DevOps users need an independent CLI to preview, validate, and script resource names outside the deployment pipeline.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Bash script | Yes | Complex shortening logic, poor cross-platform support |
| Go binary | Yes | Adds build complexity; Python already in repo's toolchain |
| Python CLI (chosen) | Yes | Matches repo language, easy testing, cross-platform |
| Node.js | Yes | Not part of existing repo toolchain |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `bin/generate-name.py` | CLI entry point — argparse, validation, output |
| `governance/engine/naming.py` | Core naming logic — patterns, length rules, shortening |
| `governance/engine/naming_data.py` | Azure resource type data — prefixes, max lengths, char constraints |
| `governance/engine/tests/test_naming.py` | Unit tests for naming module |
| `docs/guides/naming-cli-usage.md` | User guide with examples |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/templates/bicep/project.yaml` | Add `naming.cli_path` reference |
| `CLAUDE.md` | Add generate-name to Repository Commands section |

### Files to Delete

| File | Reason |
|------|--------|
| None | N/A — additive change |

## 4. Approach

1. **Create `governance/engine/naming_data.py`** — Define Azure resource type registry:
   - Resource type → prefix mapping (from Azure CAF abbreviations)
   - Resource type → max name length
   - Resource type → character restrictions (allow hyphens, alphanumeric-only, etc.)
   - Resource type → naming pattern (standard, mini, small)
   - Valid LOBs: jma, jmf, jmfe, set, setf, to, ocio, octo, lexus
   - Valid stages: dev, stg, uat, prod, nonprod

2. **Create `governance/engine/naming.py`** — Core naming engine:
   - `generate_name(resource_type, lob, stage, app_name, app_id, role, location=None)` → str
   - Three patterns:
     - **Standard:** `{prefix}-{lob}-{stage}-{appName}-{role}-{appId}` (with optional `-si` suffix)
     - **Mini:** `{prefix}{lob}{stage}{shortName}` (no hyphens, 24-char max)
     - **Small:** `{prefix}-{lob}-{stage}-{shortName}` (60-char max, omits appId)
   - Deterministic shortening: truncate `appName` from right, then `role` from right; prefix/lob/stage/appId are never reduced
   - Optional location insertion: `{prefix}-{lob}-{stage}-{appName}-{role}-{location}-{appId}`
   - Validation: reject inputs that cannot fit even after shortening

3. **Create `bin/generate-name.py`** — CLI wrapper:
   - Arguments: `--resource-type`, `--lob`, `--stage`, `--app-name`, `--app-id`, `--role`, `--location` (optional)
   - Output: generated name, pattern used, original vs shortened components
   - `--json` flag for structured output
   - `--validate-only` flag to check if a given name is valid
   - `--list-types` to show all supported resource types and their constraints

4. **Create tests** — pytest suite covering:
   - All three naming patterns
   - Length limit enforcement per resource type
   - Deterministic shortening (same inputs = same output)
   - Character restriction enforcement
   - Location insertion
   - Edge cases (minimum-length names, SI suffix, long app names)

5. **Create documentation** — Usage guide with examples

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | naming.py, naming_data.py | Pattern generation, shortening, validation for all resource types |
| Integration | bin/generate-name.py | CLI argument parsing, output format, error handling |
| Property | naming.py | Generated names always meet Azure constraints (length, chars) |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Azure naming rules change | Low | Medium | Data file is isolated; easy to update |
| Shortening produces collisions | Low | High | Shortening is deterministic; same inputs always produce same output |
| Missing resource types | Medium | Low | CLI warns on unknown types; data file is extensible |

## 7. Dependencies

- [ ] Python 3.12+ (already required by repo) — non-blocking
- [ ] Azure CAF abbreviations reference — non-blocking (public documentation)

## 8. Backward Compatibility

Fully additive. No existing files modified in breaking ways. New CLI tool and module.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New Python module with business logic |
| security-review | Yes | Required by policy |
| threat-modeling | Yes | Required by policy |
| cost-analysis | Yes | Required by policy |
| documentation-review | Yes | New docs created |
| data-governance-review | Yes | Required by policy |
| testing-review | Yes | New test suite |

**Policy Profile:** default
**Expected Risk Level:** low

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-26 | Python over Go/Bash | Matches repo toolchain, easy testing, cross-platform |
| 2026-02-26 | Separate data file for Azure types | Isolates frequently-changing data from logic |
| 2026-02-26 | Deterministic shortening (right-truncate) | Ensures predictability — same inputs always produce same short name |
