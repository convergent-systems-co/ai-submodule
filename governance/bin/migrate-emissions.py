#!/usr/bin/env python3
"""Emission Migration CLI — upgrade panel emissions across schema versions.

Reads migration rules from governance/migrations/ and applies transforms to
emission JSON files, supporting chained migrations (e.g., 1.0.0 -> 1.1.0 -> 1.2.0).

Usage:
    python governance/bin/migrate-emissions.py \\
        --from-version 1.0.0 --to-version 1.1.0

    python governance/bin/migrate-emissions.py \\
        --from-version 1.0.0 --to-version 1.1.0 \\
        --path .artifacts/emissions/ --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Repo root is three levels up: bin/ -> governance/ -> repo root
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_MIGRATIONS_DIR = _REPO_ROOT / "governance" / "migrations"
_DEFAULT_EMISSIONS_PATH = _REPO_ROOT / ".governance" / "emissions"


def load_migration(path: Path) -> dict[str, Any]:
    """Load a single migration rule file."""
    with open(path) as f:
        return json.load(f)


def discover_migrations(migrations_dir: Path) -> dict[str, dict[str, Any]]:
    """Discover all migration rules, keyed by from_version.

    Returns a dict mapping from_version -> migration rule dict.
    """
    migrations: dict[str, dict[str, Any]] = {}
    for fpath in sorted(migrations_dir.glob("v*_to_v*.json")):
        rule = load_migration(fpath)
        from_ver = rule.get("from_version")
        if from_ver:
            migrations[from_ver] = rule
    return migrations


def build_migration_chain(
    migrations: dict[str, dict[str, Any]],
    from_version: str,
    to_version: str,
) -> list[dict[str, Any]]:
    """Build an ordered chain of migrations from from_version to to_version.

    Raises ValueError if no path exists.
    """
    chain: list[dict[str, Any]] = []
    current = from_version
    visited: set[str] = set()

    while current != to_version:
        if current in visited:
            raise ValueError(
                f"Cycle detected in migration chain at version {current}"
            )
        visited.add(current)

        rule = migrations.get(current)
        if rule is None:
            if not chain:
                raise ValueError(
                    f"No migration found from version {current}. "
                    f"Available migrations: {sorted(migrations.keys())}"
                )
            raise ValueError(
                f"Migration chain broken at {current} — no rule to reach {to_version}. "
                f"Chain so far: {' -> '.join(r['from_version'] for r in chain)} -> {current}"
            )

        chain.append(rule)
        current = rule["to_version"]

    return chain


def check_condition(emission: dict[str, Any], transform: dict[str, Any]) -> bool:
    """Check whether a transform's condition is satisfied."""
    condition = transform.get("condition")
    if condition is None:
        return True

    field = transform.get("field", transform.get("old_field", ""))

    if condition == "field_missing":
        return field not in emission
    elif condition == "field_exists":
        return field in emission
    else:
        # Unknown condition — skip transform
        return False


def apply_transform(
    emission: dict[str, Any],
    transform: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Apply a single transform to an emission.

    Returns (updated_emission, list_of_change_descriptions).
    """
    changes: list[str] = []
    transform_type = transform["type"]

    if not check_condition(emission, transform):
        return emission, changes

    if transform_type == "add_field":
        field = transform["field"]
        default_value = transform["default_value"]
        emission[field] = default_value
        changes.append(f"  + added '{field}' = {json.dumps(default_value)}")

    elif transform_type == "rename_field":
        old_field = transform["old_field"]
        new_field = transform["new_field"]
        if old_field in emission:
            emission[new_field] = emission.pop(old_field)
            changes.append(f"  ~ renamed '{old_field}' -> '{new_field}'")

    elif transform_type == "set_default":
        field = transform["field"]
        default_value = transform["default_value"]
        if field not in emission or emission[field] is None:
            emission[field] = default_value
            changes.append(f"  = set default '{field}' = {json.dumps(default_value)}")

    elif transform_type == "remove_field":
        field = transform["field"]
        if field in emission:
            del emission[field]
            changes.append(f"  - removed '{field}'")

    else:
        changes.append(f"  ? unknown transform type: {transform_type}")

    return emission, changes


def apply_migration(
    emission: dict[str, Any],
    rule: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Apply all transforms from a migration rule to an emission.

    Returns (updated_emission, list_of_all_change_descriptions).
    """
    all_changes: list[str] = []
    for transform in rule.get("transforms", []):
        emission, changes = apply_transform(emission, transform)
        all_changes.extend(changes)
    return emission, all_changes


def detect_schema_version(emission: dict[str, Any]) -> str:
    """Detect the schema version of an emission.

    Returns the schema_version field value, or '1.0.0' if not present.
    """
    return emission.get("schema_version", "1.0.0")


def migrate_file(
    fpath: Path,
    chain: list[dict[str, Any]],
    dry_run: bool = False,
) -> tuple[int, list[str]]:
    """Migrate a single emission file through the migration chain.

    Returns (number_of_fields_changed, list_of_change_descriptions).
    """
    with open(fpath) as f:
        emission = json.load(f)

    all_changes: list[str] = []
    for rule in chain:
        emission, changes = apply_migration(emission, rule)
        all_changes.extend(changes)

    # Update schema_version to the final version
    final_version = chain[-1]["to_version"]
    if emission.get("schema_version") != final_version:
        emission["schema_version"] = final_version
        all_changes.append(f"  = schema_version -> {final_version}")

    if not dry_run and all_changes:
        with open(fpath, "w") as f:
            json.dump(emission, f, indent=2)
            f.write("\n")

    return len(all_changes), all_changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Migrate panel emissions between schema versions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --from-version 1.0.0 --to-version 1.1.0\n"
            "  %(prog)s --from-version 1.0.0 --to-version 1.1.0 --dry-run\n"
            "  %(prog)s --from-version 1.0.0 --to-version 1.2.0 --path ./emissions/\n"
        ),
    )
    parser.add_argument(
        "--from-version",
        required=True,
        help="Source schema version (e.g., 1.0.0)",
    )
    parser.add_argument(
        "--to-version",
        required=True,
        help="Target schema version (e.g., 1.1.0)",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=_DEFAULT_EMISSIONS_PATH,
        help=f"Path to emissions directory (default: {_DEFAULT_EMISSIONS_PATH})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    parser.add_argument(
        "--migrations-dir",
        type=Path,
        default=_MIGRATIONS_DIR,
        help=f"Path to migrations directory (default: {_MIGRATIONS_DIR})",
    )

    args = parser.parse_args(argv)

    # Discover and chain migrations
    migrations = discover_migrations(args.migrations_dir)
    if not migrations:
        print(f"Error: No migration rules found in {args.migrations_dir}", file=sys.stderr)
        return 1

    try:
        chain = build_migration_chain(migrations, args.from_version, args.to_version)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Display migration plan
    version_path = " -> ".join(
        [chain[0]["from_version"]] + [r["to_version"] for r in chain]
    )
    print(f"Migration path: {version_path}")
    if args.dry_run:
        print("Mode: DRY RUN (no files will be modified)\n")
    else:
        print()

    # Find emission files
    emissions_path = args.path
    if not emissions_path.is_dir():
        print(f"Error: Emissions path does not exist: {emissions_path}", file=sys.stderr)
        return 1

    json_files = sorted(emissions_path.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {emissions_path}")
        return 0

    # Apply migrations
    total_files = 0
    total_fields = 0
    for fpath in json_files:
        fields_changed, changes = migrate_file(fpath, chain, dry_run=args.dry_run)
        if changes:
            total_files += 1
            total_fields += fields_changed
            print(f"{fpath.name}:")
            for change in changes:
                print(change)

    # Summary
    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Summary: "
          f"{total_files} file(s) migrated, {total_fields} field(s) changed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
