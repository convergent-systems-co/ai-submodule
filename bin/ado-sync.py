#!/usr/bin/env python3
"""ADO Sync CLI — manual operations, debugging, and setup for Azure DevOps integration.

Provides subcommands for connection testing, work item CRUD, WIQL queries,
sync ledger inspection, and custom field setup.

Usage:
    python bin/ado-sync.py test-connection
    python bin/ado-sync.py get 42
    python bin/ado-sync.py create --type "User Story" --title "My item"
    python bin/ado-sync.py sync-status
    python bin/ado-sync.py health

Exit codes:
    0  success
    1  error
    2  dry-run would change (no changes made)
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure the repo root is on sys.path so governance.integrations.ado is importable
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from governance.integrations.ado import (
    AdoClient,
    AdoConfig,
    AdoError,
    AdoAuthError,
    AdoConfigError,
    AdoNotFoundError,
    ClassificationNode,
    FieldDefinition,
    WorkItem,
    WorkItemType,
    add_field,
    create_auth_provider,
    load_config,
    replace_field,
    set_area_path,
    set_iteration_path,
)


# ── Exit codes ──────────────────────────────────────────────────────────────

EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_DRY_RUN_WOULD_CHANGE = 2


# ── Config loading ──────────────────────────────────────────────────────────


def _find_project_yaml(start: Path | None = None) -> Path | None:
    """Walk up from start (default: cwd) looking for project.yaml."""
    current = (start or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        candidate = directory / "project.yaml"
        if candidate.is_file():
            return candidate
    return None


def _load_yaml(path: Path) -> dict:
    """Load a YAML file, trying PyYAML first then falling back to basic parsing."""
    try:
        import yaml

        with open(path) as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        raise AdoConfigError(
            "PyYAML is required to parse project.yaml. "
            "Install it with: pip install pyyaml"
        )


def _build_config(args: argparse.Namespace) -> tuple[AdoConfig, dict]:
    """Build AdoConfig from CLI args + project.yaml.

    Returns (AdoConfig, raw_ado_section) where raw_ado_section is the
    original dict from project.yaml for use by subcommands that need it.
    """
    config_path = None
    if args.config:
        config_path = Path(args.config)
        if not config_path.is_file():
            raise AdoConfigError(f"Config file not found: {config_path}")
    else:
        config_path = _find_project_yaml()

    if config_path is None:
        # Allow --org and --project to work without project.yaml
        if args.org and args.project:
            raw: dict = {
                "organization": args.org,
                "default_project": args.project,
                "auth_method": "pat",
            }
            config = AdoConfig(
                organization=_extract_org_name(args.org),
                default_project=args.project,
            )
            return config, raw
        raise AdoConfigError(
            "No project.yaml found. Provide --config <path> or --org + --project."
        )

    data = _load_yaml(config_path)
    ado_section = data.get("ado_integration", {})
    if not ado_section:
        raise AdoConfigError(
            f"No ado_integration section in {config_path}. "
            "See docs for configuration format."
        )

    # Apply CLI overrides
    if args.org:
        ado_section["organization"] = args.org
    if args.project:
        ado_section["default_project"] = args.project
        ado_section["project"] = args.project

    # Normalize: schema uses 'project', load_config uses 'default_project'
    if "project" in ado_section and "default_project" not in ado_section:
        ado_section["default_project"] = ado_section["project"]

    # Extract org name from URL if needed
    org = ado_section.get("organization", "")
    if org.startswith("https://dev.azure.com/"):
        ado_section["organization"] = org.split("/")[-1]

    config = load_config(ado_section)
    return config, ado_section


def _extract_org_name(org: str) -> str:
    """Extract org name from URL or return as-is."""
    if org.startswith("https://dev.azure.com/"):
        return org.rstrip("/").split("/")[-1]
    return org


def _build_client(args: argparse.Namespace) -> tuple[AdoClient, dict]:
    """Build an AdoClient from CLI args, returning (client, raw_config)."""
    config, raw = _build_config(args)
    auth_method = raw.get("auth_method", "pat")
    auth = create_auth_provider(auth_method)
    return AdoClient(config, auth), raw


# ── Output helpers ──────────────────────────────────────────────────────────


def _print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, default=str))


def _print_table(headers: list[str], rows: list[list[str]], min_width: int = 4) -> None:
    """Print a simple aligned table without external dependencies."""
    if not rows:
        return

    col_widths = [max(len(h), min_width) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(str(cell)))

    fmt = "  ".join(f"{{:<{w}}}" for w in col_widths)
    print(fmt.format(*headers))
    print(fmt.format(*["-" * w for w in col_widths]))
    for row in rows:
        # Pad row to match header count
        padded = list(row) + [""] * (len(headers) - len(row))
        print(fmt.format(*[str(c) for c in padded]))


def _verbose(args: argparse.Namespace, msg: str) -> None:
    """Print a verbose message if --verbose is set."""
    if getattr(args, "verbose", False):
        print(f"[verbose] {msg}", file=sys.stderr)


# ── Work item display helpers ───────────────────────────────────────────────


def _format_work_item(wi: WorkItem) -> dict:
    """Format a WorkItem for display."""
    fields = wi.fields
    return {
        "id": wi.id,
        "rev": wi.rev,
        "type": fields.get("System.WorkItemType", ""),
        "title": fields.get("System.Title", ""),
        "state": fields.get("System.State", ""),
        "assigned_to": _extract_display_name(fields.get("System.AssignedTo", "")),
        "area_path": fields.get("System.AreaPath", ""),
        "iteration_path": fields.get("System.IterationPath", ""),
        "created_date": fields.get("System.CreatedDate", ""),
        "changed_date": fields.get("System.ChangedDate", ""),
        "url": wi.url,
        "fields": fields,
    }


def _extract_display_name(value: Any) -> str:
    """Extract display name from ADO identity field."""
    if isinstance(value, dict):
        return value.get("displayName", str(value))
    return str(value) if value else ""


def _print_work_item(wi: WorkItem, as_json: bool = False) -> None:
    """Print a work item in human-readable or JSON format."""
    data = _format_work_item(wi)
    if as_json:
        _print_json(data)
    else:
        print(f"Work Item #{data['id']} (rev {data['rev']})")
        print(f"  Type:           {data['type']}")
        print(f"  Title:          {data['title']}")
        print(f"  State:          {data['state']}")
        print(f"  Assigned To:    {data['assigned_to']}")
        print(f"  Area Path:      {data['area_path']}")
        print(f"  Iteration Path: {data['iteration_path']}")
        print(f"  Created:        {data['created_date']}")
        print(f"  Changed:        {data['changed_date']}")
        if wi.relations:
            print(f"  Relations:      {len(wi.relations)}")
            for rel in wi.relations:
                rel_type = rel.get("rel", "")
                url = rel.get("url", "")
                attrs = rel.get("attributes", {})
                name = attrs.get("name", rel_type)
                print(f"    - {name}: {url}")


def _print_classification_tree(
    node: ClassificationNode, prefix: str = "", is_last: bool = True
) -> None:
    """Print a classification node tree with indentation."""
    connector = "`-- " if is_last else "|-- "
    print(f"{prefix}{connector}{node.name}" if prefix else node.name)
    child_prefix = prefix + ("    " if is_last else "|   ")
    for i, child in enumerate(node.children):
        _print_classification_tree(child, child_prefix, i == len(node.children) - 1)


# ── Subcommand implementations ─────────────────────────────────────────────


def cmd_test_connection(args: argparse.Namespace) -> int:
    """Verify auth and print org/project/work item types."""
    _verbose(args, "Testing connection...")
    client, raw = _build_client(args)

    with client:
        # Test by fetching project properties
        _verbose(args, "Fetching project properties...")
        props = client.get_project_properties()

        project_name = props.get("name", "")
        project_state = props.get("state", "")
        description = props.get("description", "")

        if args.json:
            # Also fetch work item types for JSON output
            types = client.list_work_item_types()
            _print_json({
                "status": "connected",
                "organization": raw.get("organization", ""),
                "project": {
                    "name": project_name,
                    "state": project_state,
                    "description": description,
                },
                "work_item_types": [t.name for t in types],
            })
        else:
            print("Connection successful!")
            print(f"  Organization:   {raw.get('organization', '')}")
            print(f"  Project:        {project_name}")
            print(f"  Project State:  {project_state}")
            if description:
                print(f"  Description:    {description}")

            _verbose(args, "Fetching work item types...")
            types = client.list_work_item_types()
            print(f"\n  Work Item Types ({len(types)}):")
            for t in types:
                print(f"    - {t.name}")

    return EXIT_SUCCESS


def cmd_list_work_item_types(args: argparse.Namespace) -> int:
    """List work item types with their states."""
    client, _ = _build_client(args)

    with client:
        types = client.list_work_item_types()
        if args.json:
            result = []
            for t in types:
                states = client.get_work_item_type_states(t.name)
                result.append({
                    "name": t.name,
                    "description": t.description,
                    "states": [
                        {"name": s.get("name", ""), "category": s.get("category", "")}
                        for s in states
                    ],
                })
            _print_json(result)
        else:
            for t in types:
                states = client.get_work_item_type_states(t.name)
                state_names = [s.get("name", "") for s in states]
                print(f"{t.name}")
                if t.description:
                    print(f"  Description: {t.description}")
                print(f"  States: {', '.join(state_names)}")
                print()

    return EXIT_SUCCESS


def cmd_list_fields(args: argparse.Namespace) -> int:
    """List field definitions."""
    client, _ = _build_client(args)

    with client:
        fields = client.list_fields()

        if args.custom_only:
            fields = [f for f in fields if f.reference_name.startswith("Custom.")]

        if args.json:
            _print_json([
                {
                    "name": f.name,
                    "reference_name": f.reference_name,
                    "type": f.type,
                    "description": f.description,
                    "read_only": f.read_only,
                }
                for f in fields
            ])
        else:
            headers = ["Name", "Reference Name", "Type", "Read-Only"]
            rows = [
                [f.name, f.reference_name, f.type, str(f.read_only)]
                for f in fields
            ]
            _print_table(headers, rows)
            print(f"\nTotal: {len(fields)} fields")

    return EXIT_SUCCESS


def cmd_list_area_paths(args: argparse.Namespace) -> int:
    """List area paths as a tree."""
    client, _ = _build_client(args)

    with client:
        root = client.list_area_paths(depth=args.depth)
        if args.json:
            _print_json(_node_to_dict(root))
        else:
            _print_classification_tree(root)

    return EXIT_SUCCESS


def cmd_list_iteration_paths(args: argparse.Namespace) -> int:
    """List iteration paths as a tree."""
    client, _ = _build_client(args)

    with client:
        root = client.list_iteration_paths(depth=args.depth)
        if args.json:
            _print_json(_node_to_dict(root))
        else:
            _print_classification_tree(root)

    return EXIT_SUCCESS


def _node_to_dict(node: ClassificationNode) -> dict:
    """Recursively convert a ClassificationNode to a dict."""
    result: dict[str, Any] = {
        "id": node.id,
        "name": node.name,
        "path": node.path,
        "structure_type": node.structure_type,
        "has_children": node.has_children,
    }
    if node.children:
        result["children"] = [_node_to_dict(c) for c in node.children]
    return result


def cmd_get(args: argparse.Namespace) -> int:
    """Fetch and display a work item."""
    from governance.integrations.ado._types import WorkItemExpand

    client, _ = _build_client(args)

    with client:
        wi = client.get_work_item(args.id, expand=WorkItemExpand.ALL)
        _print_work_item(wi, as_json=args.json)

    return EXIT_SUCCESS


def cmd_create(args: argparse.Namespace) -> int:
    """Create a new work item."""
    if args.dry_run:
        ops_desc = [f"Type: {args.type}", f"Title: {args.title}"]
        if args.description:
            ops_desc.append(f"Description: {args.description[:50]}...")
        if args.area_path:
            ops_desc.append(f"Area Path: {args.area_path}")
        if args.iteration_path:
            ops_desc.append(f"Iteration Path: {args.iteration_path}")
        if args.assigned_to:
            ops_desc.append(f"Assigned To: {args.assigned_to}")
        print("[dry-run] Would create work item:")
        for d in ops_desc:
            print(f"  {d}")
        return EXIT_DRY_RUN_WOULD_CHANGE

    client, _ = _build_client(args)
    operations = [
        add_field("/fields/System.Title", args.title),
    ]
    if args.description:
        operations.append(add_field("/fields/System.Description", args.description))
    if args.area_path:
        operations.append(set_area_path(args.area_path))
    if args.iteration_path:
        operations.append(set_iteration_path(args.iteration_path))
    if args.assigned_to:
        operations.append(add_field("/fields/System.AssignedTo", args.assigned_to))

    with client:
        wi = client.create_work_item(args.type, operations)
        if args.json:
            _print_json(_format_work_item(wi))
        else:
            print(f"Created work item #{wi.id}")
            _print_work_item(wi)

    return EXIT_SUCCESS


def cmd_update(args: argparse.Namespace) -> int:
    """Update a work item with field=value pairs."""
    if not args.field:
        print("Error: at least one --field <field>=<value> is required.", file=sys.stderr)
        return EXIT_ERROR

    # Parse field=value pairs
    operations = []
    for field_spec in args.field:
        if "=" not in field_spec:
            print(
                f"Error: invalid field spec '{field_spec}'. "
                "Expected format: <field>=<value>",
                file=sys.stderr,
            )
            return EXIT_ERROR
        field_name, value = field_spec.split("=", 1)
        # Normalize field path
        if not field_name.startswith("/fields/"):
            field_name = f"/fields/{field_name}"
        operations.append(replace_field(field_name, value))

    if args.dry_run:
        print(f"[dry-run] Would update work item #{args.id}:")
        for op in operations:
            print(f"  {op.path} = {op.value}")
        return EXIT_DRY_RUN_WOULD_CHANGE

    client, _ = _build_client(args)

    with client:
        wi = client.update_work_item(args.id, operations)
        if args.json:
            _print_json(_format_work_item(wi))
        else:
            print(f"Updated work item #{wi.id}")
            _print_work_item(wi)

    return EXIT_SUCCESS


def cmd_query(args: argparse.Namespace) -> int:
    """Execute a WIQL query."""
    client, _ = _build_client(args)

    with client:
        items = client.query_wiql_with_details(args.wiql, top=200)
        if args.json:
            _print_json([_format_work_item(wi) for wi in items])
        else:
            if not items:
                print("No results.")
                return EXIT_SUCCESS
            headers = ["ID", "Type", "State", "Assigned To", "Title"]
            rows = []
            for wi in items:
                data = _format_work_item(wi)
                title = data["title"]
                if len(title) > 60:
                    title = title[:57] + "..."
                rows.append([
                    str(data["id"]),
                    data["type"],
                    data["state"],
                    data["assigned_to"],
                    title,
                ])
            _print_table(headers, rows)
            print(f"\n{len(items)} result(s)")

    return EXIT_SUCCESS


def cmd_sync_status(args: argparse.Namespace) -> int:
    """Display sync ledger summary."""
    ledger_path = _find_governance_file("state/ado-sync-ledger.json")
    if ledger_path is None:
        print("No sync ledger found at .governance/state/ado-sync-ledger.json")
        return EXIT_ERROR

    with open(ledger_path) as f:
        ledger = json.load(f)

    mappings = ledger.get("mappings", [])

    if args.json:
        _print_json({
            "ledger_path": str(ledger_path),
            "schema_version": ledger.get("schema_version", ""),
            "total_mappings": len(mappings),
            "by_status": _count_by(mappings, "sync_status"),
            "by_direction": _count_by(mappings, "sync_direction"),
            "mappings": mappings,
        })
    else:
        print(f"Sync Ledger: {ledger_path}")
        print(f"Schema Version: {ledger.get('schema_version', 'unknown')}")
        print(f"Total Mappings: {len(mappings)}")
        print()

        # Status breakdown
        by_status = _count_by(mappings, "sync_status")
        if by_status:
            print("By Status:")
            for status, count in sorted(by_status.items()):
                print(f"  {status}: {count}")

        # Direction breakdown
        by_direction = _count_by(mappings, "sync_direction")
        if by_direction:
            print("\nBy Direction:")
            for direction, count in sorted(by_direction.items()):
                print(f"  {direction}: {count}")

        if mappings:
            print()
            headers = ["GitHub Issue", "Repo", "ADO Work Item", "Status", "Last Synced"]
            rows = []
            for m in mappings:
                rows.append([
                    str(m.get("github_issue_number", "")),
                    m.get("github_repo", ""),
                    str(m.get("ado_work_item_id", "")),
                    m.get("sync_status", ""),
                    m.get("last_synced_at", "")[:19] if m.get("last_synced_at") else "",
                ])
            _print_table(headers, rows)

    return EXIT_SUCCESS


def cmd_sync_one(args: argparse.Namespace) -> int:
    """Force-sync a single GitHub issue to ADO."""
    if args.dry_run:
        print(f"[dry-run] Would sync GitHub issue #{args.github_issue_number} to ADO.")
        return EXIT_DRY_RUN_WOULD_CHANGE

    # Load ledger to check for existing mapping
    ledger_path = _find_governance_file("state/ado-sync-ledger.json")
    ledger: dict = {"schema_version": "1.0.0", "mappings": []}
    if ledger_path and ledger_path.is_file():
        with open(ledger_path) as f:
            ledger = json.load(f)

    mappings = ledger.get("mappings", [])
    existing = None
    for m in mappings:
        if m.get("github_issue_number") == args.github_issue_number:
            existing = m
            break

    # We need the GitHub CLI for issue data
    _verbose(args, f"Fetching GitHub issue #{args.github_issue_number}...")
    import subprocess

    result = subprocess.run(
        [
            "gh", "issue", "view", str(args.github_issue_number),
            "--json", "title,body,state,labels,assignees,number",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error: failed to fetch GitHub issue #{args.github_issue_number}: {result.stderr}", file=sys.stderr)
        return EXIT_ERROR

    issue = json.loads(result.stdout)
    title = issue.get("title", "")
    body = issue.get("body", "")
    state = issue.get("state", "OPEN")

    client, raw = _build_client(args)

    with client:
        if existing:
            # Update existing work item
            ado_id = existing["ado_work_item_id"]
            _verbose(args, f"Updating existing ADO work item #{ado_id}...")
            ops = [
                replace_field("/fields/System.Title", title),
            ]
            if body:
                ops.append(replace_field("/fields/System.Description", body))
            wi = client.update_work_item(ado_id, ops)
            existing["last_synced_at"] = datetime.now(timezone.utc).isoformat()
            existing["sync_status"] = "active"
            action = "Updated"
        else:
            # Determine work item type from config mappings
            type_mapping = raw.get("type_mapping", {"default": "User Story"})
            wi_type = type_mapping.get("default", "User Story")

            # Check issue labels against type mapping
            labels = [lb.get("name", "") for lb in issue.get("labels", [])]
            for label in labels:
                if label in type_mapping:
                    wi_type = type_mapping[label]
                    break

            _verbose(args, f"Creating ADO work item (type: {wi_type})...")
            ops = [add_field("/fields/System.Title", title)]
            if body:
                ops.append(add_field("/fields/System.Description", body))

            wi = client.create_work_item(wi_type, ops)

            # Add to ledger
            repo_result = subprocess.run(
                ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
                capture_output=True,
                text=True,
            )
            repo_name = repo_result.stdout.strip() if repo_result.returncode == 0 else ""

            new_mapping = {
                "github_issue_number": args.github_issue_number,
                "github_repo": repo_name,
                "ado_work_item_id": wi.id,
                "ado_project": raw.get("default_project", raw.get("project", "")),
                "ado_work_item_type": wi_type,
                "sync_direction": "github_to_ado",
                "last_synced_at": datetime.now(timezone.utc).isoformat(),
                "sync_status": "active",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            mappings.append(new_mapping)
            action = "Created"

        # Save ledger
        ledger["mappings"] = mappings
        save_path = ledger_path or Path(".governance/state/ado-sync-ledger.json")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(ledger, f, indent=2)

        if args.json:
            _print_json({"action": action.lower(), "work_item": _format_work_item(wi)})
        else:
            print(f"{action} ADO work item #{wi.id} for GitHub issue #{args.github_issue_number}")
            _print_work_item(wi)

    return EXIT_SUCCESS


def cmd_retry_failed(args: argparse.Namespace) -> int:
    """Process the error queue, retrying unresolved errors."""
    error_path = _find_governance_file("state/ado-sync-errors.json")
    if error_path is None:
        print("No error log found at .governance/state/ado-sync-errors.json")
        return EXIT_SUCCESS  # No errors is success

    with open(error_path) as f:
        error_log = json.load(f)

    errors = error_log.get("errors", [])
    unresolved = [e for e in errors if not e.get("resolved", False)]

    if not unresolved:
        if args.json:
            _print_json({"message": "No unresolved errors", "total_errors": len(errors)})
        else:
            print("No unresolved errors to retry.")
        return EXIT_SUCCESS

    if args.dry_run:
        if args.json:
            _print_json({
                "dry_run": True,
                "would_retry": len(unresolved),
                "errors": unresolved,
            })
        else:
            print(f"[dry-run] Would retry {len(unresolved)} failed operation(s):")
            for e in unresolved:
                issue = e.get("github_issue_number", "?")
                ado_id = e.get("ado_work_item_id", "?")
                print(
                    f"  - {e.get('operation', '?')} | "
                    f"GitHub #{issue} -> ADO #{ado_id} | "
                    f"{e.get('error_type', '?')}: {e.get('error_message', '')[:60]}"
                )
        return EXIT_DRY_RUN_WOULD_CHANGE

    client, raw = _build_client(args)
    retried = 0
    succeeded = 0

    with client:
        for error in unresolved:
            retried += 1
            error_id = error.get("error_id", "?")
            operation = error.get("operation", "")
            github_issue = error.get("github_issue_number")
            ado_id = error.get("ado_work_item_id")

            _verbose(args, f"Retrying error {error_id} ({operation})...")

            try:
                if operation == "create" and github_issue:
                    # Re-attempt sync for this issue
                    # Build a namespace-like object for sync_one
                    import subprocess

                    result = subprocess.run(
                        [
                            "gh", "issue", "view", str(github_issue),
                            "--json", "title,body,state,labels",
                        ],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode != 0:
                        _verbose(args, f"  Cannot fetch GitHub issue #{github_issue}, skipping")
                        error["retry_count"] = error.get("retry_count", 0) + 1
                        continue

                    issue_data = json.loads(result.stdout)
                    type_mapping = raw.get("type_mapping", {"default": "User Story"})
                    wi_type = type_mapping.get("default", "User Story")
                    ops = [add_field("/fields/System.Title", issue_data.get("title", ""))]
                    body = issue_data.get("body", "")
                    if body:
                        ops.append(add_field("/fields/System.Description", body))

                    wi = client.create_work_item(wi_type, ops)
                    print(f"  Retry succeeded: created ADO #{wi.id} for GitHub #{github_issue}")
                    error["resolved"] = True
                    succeeded += 1

                elif operation == "update" and ado_id:
                    # For update failures we just verify the work item exists
                    wi = client.get_work_item(ado_id)
                    print(f"  ADO #{ado_id} exists (state: {wi.fields.get('System.State', '?')}), marking resolved")
                    error["resolved"] = True
                    succeeded += 1

                else:
                    _verbose(args, f"  Unsupported retry for operation '{operation}', skipping")
                    error["retry_count"] = error.get("retry_count", 0) + 1

            except AdoError as exc:
                error["retry_count"] = error.get("retry_count", 0) + 1
                print(f"  Retry failed for {error_id}: {exc}", file=sys.stderr)

    # Save updated error log
    with open(error_path, "w") as f:
        json.dump(error_log, f, indent=2)

    if args.json:
        _print_json({
            "retried": retried,
            "succeeded": succeeded,
            "failed": retried - succeeded,
        })
    else:
        print(f"\nRetried {retried} error(s): {succeeded} succeeded, {retried - succeeded} failed")

    return EXIT_SUCCESS if succeeded == retried else EXIT_ERROR


def cmd_setup_custom_fields(args: argparse.Namespace) -> int:
    """Create Custom.GitHubIssueUrl and Custom.GitHubRepo fields (idempotent)."""
    custom_fields = [
        {
            "name": "GitHub Issue URL",
            "reference_name": "Custom.GitHubIssueUrl",
            "type": "string",
        },
        {
            "name": "GitHub Repo",
            "reference_name": "Custom.GitHubRepo",
            "type": "string",
        },
    ]

    if args.dry_run:
        if args.json:
            _print_json({"dry_run": True, "would_create": custom_fields})
        else:
            print("[dry-run] Would ensure these custom fields exist:")
            for f in custom_fields:
                print(f"  - {f['reference_name']} ({f['name']}, type: {f['type']})")
        return EXIT_DRY_RUN_WOULD_CHANGE

    client, _ = _build_client(args)

    with client:
        existing_fields = client.list_fields()
        existing_refs = {f.reference_name for f in existing_fields}

        results = []
        for field_def in custom_fields:
            ref = field_def["reference_name"]
            if ref in existing_refs:
                status = "already_exists"
                _verbose(args, f"Field {ref} already exists, skipping")
            else:
                _verbose(args, f"Creating field {ref}...")
                client.create_field(
                    name=field_def["name"],
                    reference_name=ref,
                    field_type=field_def["type"],
                )
                status = "created"

            results.append({"field": ref, "status": status})

        if args.json:
            _print_json(results)
        else:
            for r in results:
                icon = "+" if r["status"] == "created" else "="
                print(f"  [{icon}] {r['field']}: {r['status']}")

    return EXIT_SUCCESS


def cmd_setup_service_hooks(args: argparse.Namespace) -> int:
    """Create ADO Service Hook subscriptions for reverse sync.

    Creates ``workitem.created``, ``workitem.updated``, and
    ``workitem.deleted`` service hook subscriptions that target the
    GitHub ``repository_dispatch`` endpoint.  Idempotent — checks for
    existing subscriptions before creating new ones.
    """
    github_repo = getattr(args, "github_repo", None)
    if not github_repo:
        print("Error: --github-repo is required for setup-service-hooks", file=sys.stderr)
        return EXIT_ERROR

    github_pat = getattr(args, "github_pat", None)
    if not github_pat:
        import os
        github_pat = os.environ.get("GITHUB_TOKEN", "")
    if not github_pat:
        print("Error: --github-pat or GITHUB_TOKEN env var is required", file=sys.stderr)
        return EXIT_ERROR

    event_types = ["workitem.created", "workitem.updated", "workitem.deleted"]
    dispatch_url = f"https://api.github.com/repos/{github_repo}/dispatches"

    config, raw = _build_config(args)
    org = config.organization
    project = raw.get("project", config.default_project)

    # Build subscription definitions
    subscriptions = []
    for event_type in event_types:
        sub = {
            "publisherId": "tfs",
            "eventType": event_type,
            "resourceVersion": "1.0",
            "publisherInputs": {
                "projectId": project,
            },
            "consumerActionId": "httpRequest",
            "consumerId": "webHooks",
            "consumerInputs": {
                "url": dispatch_url,
                "httpHeaders": (
                    f"Authorization:Bearer {github_pat}\n"
                    "Accept:application/vnd.github+json\n"
                    "Content-Type:application/json"
                ),
                "resourceDetailsToSend": "All",
                "messagesToSend": "None",
                "detailedMessagesToSend": "None",
            },
        }
        subscriptions.append((event_type, sub))

    if args.dry_run:
        summary = [
            {
                "event_type": et,
                "target_url": dispatch_url,
                "project": project,
                "status": "would_create",
            }
            for et, _ in subscriptions
        ]
        if args.json:
            _print_json({"dry_run": True, "subscriptions": summary})
        else:
            print("[dry-run] Would create these service hook subscriptions:")
            for s in summary:
                print(f"  - {s['event_type']} -> {s['target_url']}")
        return EXIT_DRY_RUN_WOULD_CHANGE

    # Check for existing subscriptions and create missing ones
    import requests as req

    base_url = f"https://dev.azure.com/{org}"
    hooks_url = f"{base_url}/_apis/hooks/subscriptions"

    from governance.integrations.ado.auth import create_auth_provider
    auth_method = raw.get("auth_method", "pat")
    auth = create_auth_provider(auth_method)
    auth_header = auth.get_auth_header()

    headers = {
        "Authorization": auth_header,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    # List existing subscriptions
    _verbose(args, "Fetching existing service hook subscriptions...")
    resp = req.get(hooks_url, headers=headers, params={"api-version": "7.1"}, timeout=30)
    if resp.status_code >= 400:
        print(f"Error listing service hooks: {resp.status_code} {resp.text}", file=sys.stderr)
        return EXIT_ERROR

    existing_subs = resp.json().get("value", [])

    # Index existing by event type + URL
    existing_keys: set[str] = set()
    for sub in existing_subs:
        et = sub.get("eventType", "")
        consumer_inputs = sub.get("consumerInputs", {})
        url = consumer_inputs.get("url", "")
        existing_keys.add(f"{et}:{url}")

    results = []
    for event_type, sub_def in subscriptions:
        key = f"{event_type}:{dispatch_url}"
        if key in existing_keys:
            status = "already_exists"
            _verbose(args, f"Subscription for {event_type} already exists, skipping")
        else:
            _verbose(args, f"Creating subscription for {event_type}...")
            # The consumer inputs need to wrap the payload for repository_dispatch
            # Modify the webhook to post as a repository_dispatch event
            sub_def["consumerInputs"]["url"] = dispatch_url
            create_resp = req.post(
                hooks_url,
                headers=headers,
                json=sub_def,
                params={"api-version": "7.1"},
                timeout=30,
            )
            if create_resp.status_code >= 400:
                status = f"error: {create_resp.status_code}"
                _verbose(args, f"Failed to create {event_type}: {create_resp.text}")
            else:
                status = "created"

        results.append({"event_type": event_type, "status": status})

    if args.json:
        _print_json(results)
    else:
        for r in results:
            icon = "+" if r["status"] == "created" else ("=" if r["status"] == "already_exists" else "!")
            print(f"  [{icon}] {r['event_type']}: {r['status']}")

    # Check if any failed
    errors = [r for r in results if r["status"].startswith("error")]
    return EXIT_ERROR if errors else EXIT_SUCCESS


def cmd_health(args: argparse.Namespace) -> int:
    """Run health checks: connection, custom fields, ledger consistency."""
    checks: list[dict[str, Any]] = []

    # 1. Connection check
    _verbose(args, "Checking connection...")
    try:
        client, raw = _build_client(args)
        with client:
            props = client.get_project_properties()
            checks.append({
                "check": "connection",
                "status": "pass",
                "detail": f"Connected to {props.get('name', '?')}",
            })

            # 2. Custom fields check
            _verbose(args, "Checking custom fields...")
            fields = client.list_fields()
            field_refs = {f.reference_name for f in fields}
            required_fields = ["Custom.GitHubIssueUrl", "Custom.GitHubRepo"]
            missing = [f for f in required_fields if f not in field_refs]
            if missing:
                checks.append({
                    "check": "custom_fields",
                    "status": "warn",
                    "detail": f"Missing fields: {', '.join(missing)}. Run: ado-sync.py setup-custom-fields",
                })
            else:
                checks.append({
                    "check": "custom_fields",
                    "status": "pass",
                    "detail": "All custom fields present",
                })

    except AdoAuthError as exc:
        checks.append({
            "check": "connection",
            "status": "fail",
            "detail": f"Authentication failed: {exc}",
        })
    except AdoConfigError as exc:
        checks.append({
            "check": "connection",
            "status": "fail",
            "detail": f"Configuration error: {exc}",
        })
    except AdoError as exc:
        checks.append({
            "check": "connection",
            "status": "fail",
            "detail": f"Connection error: {exc}",
        })

    # 3. Ledger consistency check
    _verbose(args, "Checking ledger consistency...")
    ledger_path = _find_governance_file("state/ado-sync-ledger.json")
    if ledger_path is None:
        checks.append({
            "check": "ledger",
            "status": "info",
            "detail": "No ledger file found (no syncs performed yet)",
        })
    else:
        try:
            with open(ledger_path) as f:
                ledger = json.load(f)
            mappings = ledger.get("mappings", [])
            error_count = sum(1 for m in mappings if m.get("sync_status") == "error")
            checks.append({
                "check": "ledger",
                "status": "warn" if error_count > 0 else "pass",
                "detail": (
                    f"{len(mappings)} mapping(s), {error_count} in error state"
                    if error_count
                    else f"{len(mappings)} mapping(s), all healthy"
                ),
            })
        except (json.JSONDecodeError, OSError) as exc:
            checks.append({
                "check": "ledger",
                "status": "fail",
                "detail": f"Cannot read ledger: {exc}",
            })

    # 4. Error queue check
    _verbose(args, "Checking error queue...")
    error_path = _find_governance_file("state/ado-sync-errors.json")
    if error_path is None:
        checks.append({
            "check": "error_queue",
            "status": "pass",
            "detail": "No error log (clean)",
        })
    else:
        try:
            with open(error_path) as f:
                error_log = json.load(f)
            errors = error_log.get("errors", [])
            unresolved = [e for e in errors if not e.get("resolved", False)]
            if unresolved:
                checks.append({
                    "check": "error_queue",
                    "status": "warn",
                    "detail": (
                        f"{len(unresolved)} unresolved error(s) of {len(errors)} total. "
                        "Run: ado-sync.py retry-failed"
                    ),
                })
            else:
                checks.append({
                    "check": "error_queue",
                    "status": "pass",
                    "detail": f"{len(errors)} error(s), all resolved",
                })
        except (json.JSONDecodeError, OSError) as exc:
            checks.append({
                "check": "error_queue",
                "status": "fail",
                "detail": f"Cannot read error log: {exc}",
            })

    # Output
    if args.json:
        all_pass = all(c["status"] in ("pass", "info") for c in checks)
        _print_json({"healthy": all_pass, "checks": checks})
    else:
        status_icons = {"pass": "[OK]", "warn": "[!!]", "fail": "[FAIL]", "info": "[--]"}
        print("Health Checks:")
        for c in checks:
            icon = status_icons.get(c["status"], "[??]")
            print(f"  {icon} {c['check']}: {c['detail']}")

        all_pass = all(c["status"] in ("pass", "info") for c in checks)
        has_fail = any(c["status"] == "fail" for c in checks)
        print()
        if all_pass:
            print("All checks passed.")
        elif has_fail:
            print("Some checks failed. See details above.")
        else:
            print("Warnings detected. See details above.")

    has_fail = any(c["status"] == "fail" for c in checks)
    return EXIT_ERROR if has_fail else EXIT_SUCCESS


# ── Utility functions ───────────────────────────────────────────────────────


def _find_governance_file(relative: str) -> Path | None:
    """Find a file under .governance/ walking up from cwd."""
    current = Path.cwd().resolve()
    for directory in [current, *current.parents]:
        candidate = directory / ".governance" / relative
        if candidate.is_file():
            return candidate
    return None


def _count_by(items: list[dict], key: str) -> dict[str, int]:
    """Count items grouped by a key."""
    counts: dict[str, int] = {}
    for item in items:
        value = item.get(key, "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


# ── Argument parser ─────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ado-sync",
        description="ADO Sync CLI — manual operations, debugging, and setup for Azure DevOps integration.",
        epilog="Exit codes: 0=success, 1=error, 2=dry-run-would-change",
    )

    # Global flags
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to project.yaml (auto-detected if omitted).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON.",
    )
    parser.add_argument(
        "--org",
        metavar="URL",
        help="Azure DevOps organization URL (overrides project.yaml).",
    )
    parser.add_argument(
        "--project",
        metavar="NAME",
        help="Azure DevOps project name (overrides project.yaml).",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # ── Connection & Discovery ──────────────────────────────────────────

    subparsers.add_parser(
        "test-connection",
        help="Verify auth, print org/project/work item types.",
    )

    subparsers.add_parser(
        "list-work-item-types",
        help="List work item types with their states.",
    )

    p_fields = subparsers.add_parser(
        "list-fields",
        help="List all or custom-only field definitions.",
    )
    p_fields.add_argument(
        "--custom-only",
        action="store_true",
        help="Show only custom fields (Custom.* reference names).",
    )

    p_areas = subparsers.add_parser(
        "list-area-paths",
        help="List area paths as a tree.",
    )
    p_areas.add_argument(
        "--depth",
        type=int,
        default=3,
        help="Tree depth (default: 3).",
    )

    p_iters = subparsers.add_parser(
        "list-iteration-paths",
        help="List iteration paths as a tree.",
    )
    p_iters.add_argument(
        "--depth",
        type=int,
        default=3,
        help="Tree depth (default: 3).",
    )

    # ── Work Item Operations ────────────────────────────────────────────

    p_get = subparsers.add_parser(
        "get",
        help="Fetch and display a work item.",
    )
    p_get.add_argument("id", type=int, help="Work item ID.")

    p_create = subparsers.add_parser(
        "create",
        help="Create a new work item.",
    )
    p_create.add_argument("--type", required=True, help="Work item type (e.g., 'User Story', 'Bug').")
    p_create.add_argument("--title", required=True, help="Work item title.")
    p_create.add_argument("--description", help="Work item description (HTML or plain text).")
    p_create.add_argument("--area-path", help="Area path.")
    p_create.add_argument("--iteration-path", help="Iteration path.")
    p_create.add_argument("--assigned-to", help="Assigned to (email or display name).")

    p_update = subparsers.add_parser(
        "update",
        help="Update a work item's fields.",
    )
    p_update.add_argument("id", type=int, help="Work item ID.")
    p_update.add_argument(
        "--field",
        action="append",
        metavar="FIELD=VALUE",
        help="Field to update (repeatable). E.g., --field System.Title='New title'",
    )

    p_query = subparsers.add_parser(
        "query",
        help="Execute a WIQL query and display results.",
    )
    p_query.add_argument("wiql", help="WIQL query string.")

    # ── Sync Operations ─────────────────────────────────────────────────

    subparsers.add_parser(
        "sync-status",
        help="Display sync ledger summary.",
    )

    p_sync_one = subparsers.add_parser(
        "sync-one",
        help="Force-sync a single GitHub issue to ADO.",
    )
    p_sync_one.add_argument("github_issue_number", type=int, help="GitHub issue number.")

    subparsers.add_parser(
        "retry-failed",
        help="Process the error queue, retrying unresolved sync errors.",
    )

    # ── Setup ───────────────────────────────────────────────────────────

    subparsers.add_parser(
        "setup-custom-fields",
        help="Create Custom.GitHubIssueUrl and Custom.GitHubRepo fields (idempotent).",
    )

    p_hooks = subparsers.add_parser(
        "setup-service-hooks",
        help="Create ADO service hook subscriptions for reverse sync (idempotent).",
    )
    p_hooks.add_argument(
        "--github-repo",
        required=True,
        metavar="OWNER/REPO",
        help="GitHub repository (e.g., 'owner/repo') to receive dispatches.",
    )
    p_hooks.add_argument(
        "--github-pat",
        metavar="TOKEN",
        help="GitHub PAT for repository_dispatch (defaults to GITHUB_TOKEN env var).",
    )

    subparsers.add_parser(
        "health",
        help="Run health checks (connection, custom fields, ledger consistency).",
    )

    return parser


# ── Main entry point ────────────────────────────────────────────────────────

_COMMANDS = {
    "test-connection": cmd_test_connection,
    "list-work-item-types": cmd_list_work_item_types,
    "list-fields": cmd_list_fields,
    "list-area-paths": cmd_list_area_paths,
    "list-iteration-paths": cmd_list_iteration_paths,
    "get": cmd_get,
    "create": cmd_create,
    "update": cmd_update,
    "query": cmd_query,
    "sync-status": cmd_sync_status,
    "sync-one": cmd_sync_one,
    "retry-failed": cmd_retry_failed,
    "setup-custom-fields": cmd_setup_custom_fields,
    "setup-service-hooks": cmd_setup_service_hooks,
    "health": cmd_health,
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return EXIT_ERROR

    handler = _COMMANDS.get(args.command)
    if handler is None:
        print(f"Error: unknown command '{args.command}'", file=sys.stderr)
        return EXIT_ERROR

    try:
        return handler(args)
    except AdoAuthError as exc:
        if args.json:
            _print_json({"error": "auth_error", "message": str(exc)})
        else:
            print(f"Authentication error: {exc}", file=sys.stderr)
            if "401" in str(exc) or "403" in str(exc):
                print("  Hint: check ADO_PAT env var or auth configuration.", file=sys.stderr)
        return EXIT_ERROR
    except AdoConfigError as exc:
        if args.json:
            _print_json({"error": "config_error", "message": str(exc)})
        else:
            print(f"Configuration error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except AdoNotFoundError as exc:
        if args.json:
            _print_json({"error": "not_found", "message": str(exc)})
        else:
            print(f"Not found: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except AdoError as exc:
        if args.json:
            _print_json({"error": "ado_error", "message": str(exc), "status_code": exc.status_code})
        else:
            print(f"ADO error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
