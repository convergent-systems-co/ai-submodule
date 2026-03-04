# Add Schema Evolution Tooling and Emission Migration CLI

**Author:** Team Lead (agent)
**Date:** 2026-02-27
**Status:** approved
**Issue:** https://github.com/convergent-systems-co/dark-forge/issues/435
**Branch:** NETWORK_ID/feat/435/schema-evolution-tooling

---

## 1. Objective

Add schema versioning to governance schemas and provide a CLI tool (`governance/bin/migrate-emissions.py`) that upgrades existing panel emissions when schema versions bump.

## 2. Rationale

The platform mandates backward compatibility but has no automated migration path. When panel-output.schema.json adds new required fields, consuming repos' existing emissions become invalid.

| Alternative | Considered | Rejected Because |
|-------------|-----------|------------------|
| Always make new fields optional | Yes | Accumulates technical debt |
| Manual migration guide | Yes | Does not scale |
| Automated CI migration | Yes | Too invasive for initial rollout |

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `governance/bin/migrate-emissions.py` | CLI tool to upgrade emissions between schema versions |
| `governance/migrations/` | Directory for per-version migration rules |
| `governance/migrations/v1.0.0_to_v1.1.0.json` | Example migration rule |
| `governance/engine/tests/test_migration.py` | Tests for migration CLI |
| `docs/guides/schema-migration.md` | Usage documentation |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `governance/schemas/panel-output.schema.json` | Add `schema_version` field |
| `governance/emissions/*.json` | Add `schema_version` to all baseline emissions |
| `GOALS.md` | Mark schema evolution tooling as completed |

### Files to Delete

None.

## 4. Approach

1. Add `schema_version` field (optional, default "1.0.0") to `panel-output.schema.json`
2. Update all baseline emissions to include `schema_version: "1.0.0"`
3. Create `governance/migrations/` directory with migration rule format
4. Create `governance/bin/migrate-emissions.py` with `--from-version`, `--to-version`, `--dry-run`, `--path` flags
5. Create initial migration rule `v1.0.0_to_v1.1.0.json` as example
6. Write tests covering: version detection, migration application, dry-run mode
7. Create `docs/guides/schema-migration.md`
8. Update GOALS.md

## 5. Testing Strategy

| Test Type | Coverage | Description |
|-----------|----------|-------------|
| Unit | `test_migration.py` | Version detection, rule application, dry-run, error handling |
| Schema | `test_schema_validation.py` | Updated schema accepts versioned and unversioned emissions |
| Integration | Migration rules | End-to-end migration of sample emissions |

## 6. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking existing emissions | Low | High | schema_version is optional |
| Migration data loss | Low | High | --dry-run flag; additive-only migrations |

## 7. Dependencies

- [ ] Python 3.12+ (already required)

## 8. Backward Compatibility

Fully backward compatible. `schema_version` is optional. Emissions without it treated as v1.0.0.

## 9. Governance

| Panel | Required | Rationale |
|-------|----------|-----------|
| code-review | Yes | New Python CLI tool |
| security-review | Yes | File system operations |
| documentation-review | Yes | New documentation |

**Policy Profile:** default
**Expected Risk Level:** medium

## 10. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-27 | Optional schema_version field | Backward compatibility |
| 2026-02-27 | JSON migration rules | Machine-readable, versionable, testable |
