#!/usr/bin/env python3
"""Azure Resource Naming CLI — generate predictable, Azure-compliant names.

Produces resource names following JM naming conventions with deterministic
shortening for length-constrained Azure resource types.

Usage:
    python bin/generate-name.py \\
        --resource-type Microsoft.KeyVault/vaults \\
        --lob set --stage dev \\
        --app-name myapp --app-id a

    python bin/generate-name.py --list-types

    python bin/generate-name.py \\
        --validate-only "kv-set-dev-myapp" \\
        --resource-type Microsoft.KeyVault/vaults
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure the repo root is on sys.path so governance.engine is importable
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from governance.engine.naming import (
    NamingError,
    NamingInput,
    generate_name,
    list_resource_types,
    validate_name,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="generate-name",
        description="Generate Azure-compliant resource names following JM conventions.",
    )

    # --- Mutually-exclusive modes ---
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--list-types",
        action="store_true",
        help="List all supported Azure resource types and exit.",
    )
    mode.add_argument(
        "--validate-only",
        metavar="NAME",
        help="Validate an existing name against resource type rules.",
    )

    # --- Generation arguments ---
    parser.add_argument(
        "--resource-type",
        help="Azure resource type (e.g., Microsoft.KeyVault/vaults).",
    )
    parser.add_argument(
        "--lob",
        help="Line of business (e.g., set, jma, ocio).",
    )
    parser.add_argument(
        "--stage",
        help="Deployment stage (dev, stg, uat, prod, nonprod).",
    )
    parser.add_argument(
        "--app-name",
        help="Application name.",
    )
    parser.add_argument(
        "--app-id",
        help="Application ID — single letter (a-z), optionally with '-si'.",
    )
    parser.add_argument(
        "--role",
        default="",
        help="Component role (web, db, api, etc.) — required for standard pattern.",
    )
    parser.add_argument(
        "--location",
        default="",
        help="Azure region short name (e.g., eastus). Optional, inserted before appId.",
    )

    # --- Output options ---
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output result as structured JSON.",
    )

    return parser


def _cmd_list_types(args: argparse.Namespace) -> int:
    """Handle --list-types."""
    types = list_resource_types()
    if args.json_output:
        print(json.dumps(types, indent=2))
    else:
        header = f"{'Resource Type':<55} {'Prefix':<8} {'Max':<5} {'Pattern':<10} {'Hyphens'}"
        print(header)
        print("-" * len(header))
        for t in types:
            hyphens = "yes" if t["allows_hyphens"] else "no"
            print(
                f"{t['resource_type']:<55} {t['prefix']:<8} "
                f"{t['max_length']:<5} {t['pattern']:<10} {hyphens}"
            )
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    """Handle --validate-only."""
    if not args.resource_type:
        print("Error: --resource-type is required with --validate-only.", file=sys.stderr)
        return 1

    result = validate_name(args.validate_only, args.resource_type)
    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        if result["valid"]:
            print(f"VALID: '{args.validate_only}' passes all checks for {args.resource_type}.")
        else:
            print(f"INVALID: '{args.validate_only}' for {args.resource_type}:")
            for err in result["errors"]:
                print(f"  - {err}")
        print(f"  Length: {result['actual_length']}/{result['max_length']}")
    return 0 if result["valid"] else 1


def _cmd_generate(args: argparse.Namespace) -> int:
    """Handle name generation (default mode)."""
    missing = []
    for field in ("resource_type", "lob", "stage", "app_name", "app_id"):
        if not getattr(args, field, None):
            missing.append(f"--{field.replace('_', '-')}")

    if missing:
        print(
            f"Error: the following arguments are required for name generation: "
            f"{', '.join(missing)}",
            file=sys.stderr,
        )
        return 1

    try:
        inp = NamingInput(
            resource_type=args.resource_type,
            lob=args.lob,
            stage=args.stage,
            app_name=args.app_name,
            app_id=args.app_id,
            role=args.role,
            location=args.location,
        )
        name = generate_name(inp)
    except NamingError as exc:
        if args.json_output:
            print(json.dumps({"error": str(exc)}, indent=2))
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.json_output:
        print(
            json.dumps(
                {
                    "name": name,
                    "resource_type": args.resource_type,
                    "length": len(name),
                    "max_length": _get_max_length(args.resource_type),
                    "pattern": _get_pattern(args.resource_type),
                    "inputs": {
                        "lob": args.lob,
                        "stage": args.stage,
                        "app_name": args.app_name,
                        "app_id": args.app_id,
                        "role": args.role,
                        "location": args.location or None,
                    },
                },
                indent=2,
            )
        )
    else:
        print(name)

    return 0


def _get_max_length(resource_type: str) -> int:
    from governance.engine.naming_data import RESOURCE_TYPES

    info = RESOURCE_TYPES.get(resource_type)
    return info.max_length if info else 0


def _get_pattern(resource_type: str) -> str:
    from governance.engine.naming_data import RESOURCE_TYPES

    info = RESOURCE_TYPES.get(resource_type)
    return info.pattern if info else ""


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.list_types:
        return _cmd_list_types(args)

    if args.validate_only is not None:
        return _cmd_validate(args)

    return _cmd_generate(args)


if __name__ == "__main__":
    sys.exit(main())
