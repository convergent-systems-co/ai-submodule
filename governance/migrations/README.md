# Schema Migrations

This directory contains migration rule files that define how to upgrade panel emissions from one schema version to another.

## Migration File Format

Each migration file is a JSON document named `v{FROM}_to_v{TO}.json` (e.g., `v1.0.0_to_v1.1.0.json`) containing:

```json
{
  "from_version": "1.0.0",
  "to_version": "1.1.0",
  "description": "Human-readable description of the migration",
  "transforms": [
    {
      "type": "add_field",
      "field": "new_field_name",
      "default_value": "default",
      "condition": "field_missing"
    }
  ]
}
```

## Supported Transform Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| `add_field` | Add a new field with a default value | `field`, `default_value` |
| `rename_field` | Rename an existing field | `old_field`, `new_field` |
| `set_default` | Set a default value if field is missing or null | `field`, `default_value` |
| `remove_field` | Remove a field from the emission | `field` |

## Conditions

Transforms support an optional `condition` field:

- `field_missing` — Apply only if the target field does not exist in the emission
- `field_exists` — Apply only if the target field exists in the emission
- (omitted) — Always apply the transform

## Migration Chaining

The migration CLI automatically chains migrations. For example, if you need to go from `1.0.0` to `1.2.0` and migration files exist for `1.0.0 -> 1.1.0` and `1.1.0 -> 1.2.0`, both will be applied in sequence.

## Usage

```bash
python governance/bin/migrate-emissions.py \
    --from-version 1.0.0 \
    --to-version 1.1.0 \
    --path .artifacts/emissions/

# Dry run (preview changes without modifying files)
python governance/bin/migrate-emissions.py \
    --from-version 1.0.0 \
    --to-version 1.1.0 \
    --dry-run
```

See `docs/guides/schema-migration.md` for full documentation.
