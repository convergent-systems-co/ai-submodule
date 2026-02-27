---
name: ado
description: |
  Azure DevOps work item operations — query, create, update, comment,
  and link work items using the governance ADO client library.
allowed-tools:
  - Read
  - Bash
  - Grep
metadata:
  category: integrations
  version: "1.0.0"
---

# Azure DevOps Work Item Operations

You manage Azure DevOps work items using the `governance.integrations.ado` Python client library.

## Prerequisites

- Python 3.12+ with `requests` installed
- ADO PAT set in `ADO_PAT` environment variable (or Service Principal credentials)
- `ado_integration` section configured in `project.yaml`

## Client Library Location

The client library is at `governance/integrations/ado/`. Import from:

```python
from governance.integrations.ado import (
    AdoClient, AdoConfig, load_config, create_auth_provider,
    add_field, replace_field, add_tag, add_github_pr_link, add_hyperlink,
    to_json_patch,
)
```

## Instructions

### Reading Work Items

Use WIQL queries or direct ID lookup:

```python
# By ID
wi = client.get_work_item(12345)

# By WIQL
result = client.query_wiql(
    "SELECT [System.Id], [System.Title] FROM WorkItems "
    "WHERE [System.AssignedTo] = @Me AND [System.State] <> 'Closed'"
)

# WIQL with full details (two-step: query IDs then batch fetch)
items = client.query_wiql_with_details(
    "SELECT [System.Id] FROM WorkItems WHERE [System.IterationPath] = @CurrentIteration"
)
```

### Creating Work Items

```python
from governance.integrations.ado import add_field, to_json_patch

ops = [
    add_field("/fields/System.Title", "As a user, I want to..."),
    add_field("/fields/System.Description", "<p>User story description</p>"),
    add_field("/fields/Microsoft.VSTS.Common.AcceptanceCriteria", "<p>AC 1</p>"),
]
wi = client.create_work_item("User Story", ops)
```

### Updating State

Before updating state, inspect the project's available states — ADO processes are customizable:

```python
# Discover valid states for a work item type
states = client.get_work_item_type_states("Bug")
# Returns: [{"name": "New", "category": "Proposed"}, {"name": "Active", ...}, ...]

# Update state
from governance.integrations.ado import replace_field
ops = [replace_field("/fields/System.State", "Active")]
client.update_work_item(12345, ops)
```

### Comments (HTML Only)

ADO comments use HTML, not Markdown. Always format with HTML tags:

```python
# Post a comment
client.add_comment(12345, "<h3>Status Update</h3><ul><li>PR created</li><li>Tests passing</li></ul>")

# Read comments
comments = client.get_comments(12345)
for c in comments:
    print(f"{c.created_by}: {c.text}")
```

### Linking GitHub Resources

```python
from governance.integrations.ado import add_github_pr_link, add_hyperlink

# Link a PR (appears in Development section)
ops = [add_github_pr_link("connection-guid", 42)]
client.update_work_item(12345, ops)

# Link an issue or branch (appears in Links tab)
ops = [add_hyperlink("https://github.com/org/repo/issues/10", "Tracking issue #10")]
client.update_work_item(12345, ops)
```

### Project Inspection

Inspect project configuration before making assumptions about field names or states:

```python
# Get project process template and capabilities
props = client.get_project_properties()
process = props["capabilities"]["processTemplate"]["templateName"]  # e.g., "Agile"

# List work item types available in this project
types = client.list_work_item_types()

# List all fields (paginated)
fields = client.list_fields()
```

## HTML Formatting Reference

ADO uses HTML, not Markdown. Common patterns:

| Element | HTML |
|---------|------|
| Paragraph | `<p>text</p>` |
| Bold | `<strong>text</strong>` |
| List | `<ul><li>item</li></ul>` |
| Header | `<h3>title</h3>` |
| Code | `<code>inline</code>` or `<pre>block</pre>` |
| Link | `<a href="url">text</a>` |
| Table | `<table><tr><th>H</th></tr><tr><td>D</td></tr></table>` |

## Error Handling

The client raises typed exceptions:

| Exception | HTTP Status | Meaning |
|-----------|-------------|---------|
| `AdoAuthError` | 401/403 | Bad token or insufficient permissions |
| `AdoNotFoundError` | 404 | Work item or project doesn't exist |
| `AdoRateLimitError` | 429 | Throttled — check `retry_after_seconds` |
| `AdoValidationError` | 400 | Invalid field values or patch operations |
| `AdoServerError` | 5xx | ADO service issue (retried automatically) |
| `AdoConfigError` | — | Missing config or bad auth setup |

## Output Format

Return results as structured JSON with:
- `work_items`: array of `{id, title, state, url}`
- `action`: what was performed (created, updated, queried, commented)
- `error`: error message if the operation failed
