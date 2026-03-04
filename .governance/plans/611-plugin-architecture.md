# Plan: Plugin Architecture for Prompt/Skill Extensibility (#611)

## Problem
Extending the orchestrator or policy engine requires modifying Python source code.
Consuming repos cannot easily add custom phases, panel types, or hooks without forking.

## Solution
Add a plugin system that allows consuming repos to register extensions via project.yaml.
Extensions are loaded at init time and run within the same containment/capacity constraints.

## Files
- `governance/engine/orchestrator/plugins.py` (NEW) - Plugin dataclasses, registry, validation, hook executor
- `governance/engine/orchestrator/config.py` (MODIFIED) - Parse governance.extensions from project.yaml
- `governance/engine/orchestrator/step_runner.py` (MODIFIED) - Load extensions at init, execute hooks and custom phases at transitions
- `governance/engine/orchestrator/__init__.py` (MODIFIED) - Export plugin types
- `governance/schemas/extensions.schema.json` (NEW) - Standalone JSON Schema for governance.extensions
- `governance/schemas/project.schema.json` (MODIFIED) - Extensions block added to project schema
- `governance/engine/tests/test_plugins.py` (NEW) - 71 tests for plugin module
- `governance/engine/tests/test_step_runner.py` (MODIFIED) - 11 new tests for step_runner plugin integration
- `docs/guides/plugin-architecture.md` (NEW) - Extension authoring guide with examples
