# Schema Migration Guide

This guide explains how to use the emission migration CLI to upgrade panel emissions when the `panel-output.schema.json` schema evolves.

## Purpose

As the governance schema evolves (new fields, renamed fields, deprecated fields), existing panel emissions need to be updated to conform to the latest version. The migration CLI automates this process by applying versioned transform rules to emission JSON files.

## When to Use

- **After a schema version bump** — When `panel-output.schema.json` adds, renames, or removes fields
- **When onboarding a consuming repo** — To upgrade older emissions to the current schema version
- **During governance upgrades** — When updating the `.ai` submodule introduces schema changes

## CLI Usage

### Basic Migration

```bash
python governance/bin/migrate-emissions.py \
    --from-version 1.0.0 \
    --to-version 1.1.0
```

### Custom Emissions Path

```bash
python governance/bin/migrate-emissions.py \
    --from-version 1.0.0 \
    --to-version 1.1.0 \
    --path .artifacts/emissions/
```

### Dry Run (Preview Changes)

```bash
python governance/bin/migrate-emissions.py \
    --from-version 1.0.0 \
    --to-version 1.1.0 \
    --dry-run
```

Dry run output shows what would change without modifying any files:

```
Migration path: 1.0.0 -> 1.1.0
Mode: DRY RUN (no files will be modified)

code-review.json:
  + added 'schema_version' = "1.1.0"
  = schema_version -> 1.1.0
security-review.json:
  + added 'schema_version' = "1.1.0"
  = schema_version -> 1.1.0

[DRY RUN] Summary: 2 file(s) migrated, 4 field(s) changed
```

### Chained Migration

The CLI automatically chains migrations. If you need to go from `1.0.0` to `1.2.0` and migration rules exist for `1.0.0 -> 1.1.0` and `1.1.0 -> 1.2.0`, both are applied in sequence:

```bash
python governance/bin/migrate-emissions.py \
    --from-version 1.0.0 \
    --to-version 1.2.0
```

### CLI Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--from-version` | Yes | — | Source schema version (e.g., `1.0.0`) |
| `--to-version` | Yes | — | Target schema version (e.g., `1.1.0`) |
| `--path` | No | `.artifacts/emissions/` | Path to emissions directory |
| `--dry-run` | No | `false` | Preview changes without modifying files |
| `--migrations-dir` | No | `governance/migrations/` | Path to migration rules directory |

## Migration Rule Format

Migration rules are JSON files in `governance/migrations/` named `v{FROM}_to_v{TO}.json`:

```json
{
  "from_version": "1.0.0",
  "to_version": "1.1.0",
  "description": "Add schema_version field to emissions",
  "transforms": [
    {
      "type": "add_field",
      "field": "schema_version",
      "default_value": "1.1.0",
      "condition": "field_missing"
    }
  ]
}
```

### Supported Transform Types

#### `add_field`

Adds a new field with a default value.

```json
{
  "type": "add_field",
  "field": "new_field_name",
  "default_value": "default_value",
  "condition": "field_missing"
}
```

#### `rename_field`

Renames an existing field, preserving its value.

```json
{
  "type": "rename_field",
  "old_field": "old_name",
  "new_field": "new_name",
  "condition": "field_exists"
}
```

#### `set_default`

Sets a default value if the field is missing or null.

```json
{
  "type": "set_default",
  "field": "execution_status",
  "default_value": "success"
}
```

#### `remove_field`

Removes a field from the emission.

```json
{
  "type": "remove_field",
  "field": "deprecated_field",
  "condition": "field_exists"
}
```

### Transform Conditions

Transforms support an optional `condition` field:

| Condition | Behavior |
|-----------|----------|
| `field_missing` | Apply only if the target field does not exist |
| `field_exists` | Apply only if the target field exists |
| (omitted) | Always apply the transform |

## How to Create New Migration Rules

When you bump the schema version:

1. **Create the migration rule file** in `governance/migrations/`:

   ```bash
   # Example: migrating from 1.1.0 to 1.2.0
   cat > governance/migrations/v1.1.0_to_v1.2.0.json << 'EOF'
   {
     "from_version": "1.1.0",
     "to_version": "1.2.0",
     "description": "Add execution_trace field requirement",
     "transforms": [
       {
         "type": "set_default",
         "field": "execution_status",
         "default_value": "success"
       }
     ]
   }
   EOF
   ```

2. **Test with dry run** before applying:

   ```bash
   python governance/bin/migrate-emissions.py \
       --from-version 1.1.0 --to-version 1.2.0 --dry-run
   ```

3. **Apply the migration**:

   ```bash
   python governance/bin/migrate-emissions.py \
       --from-version 1.1.0 --to-version 1.2.0
   ```

4. **Update baseline emissions** in `governance/emissions/` to include the `schema_version` of the new version.

5. **Commit** the migration rule alongside the schema change.

## Troubleshooting

### "No migration found from version X"

The starting version has no corresponding migration rule. Check that a file named `vX_to_vY.json` exists in `governance/migrations/`.

### "Migration chain broken at X"

A migration exists from the starting version but does not reach the target version. You need to create intermediate migration rules to bridge the gap.

### "No migration rules found"

The migrations directory is empty or the `--migrations-dir` path is incorrect. Verify the directory contains `v*_to_v*.json` files.

### "Emissions path does not exist"

The `--path` directory does not exist. For consuming repos, ensure `.artifacts/emissions/` has been created (run `bash .ai/bin/init.sh` first). For the submodule itself, emissions are in `governance/emissions/`.

### Emission validation fails after migration

Run the schema validation tests to verify emissions conform to the updated schema:

```bash
python -m pytest governance/engine/tests/test_schema_validation.py -v
```
