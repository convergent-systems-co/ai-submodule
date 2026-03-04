# Plan: Configurable model selection per panel and persona

**Issue:** #597
**Type:** Feature
**Priority:** Medium

## Problem

All panels and personas run on the same model. No way to route security review to Opus and documentation review to Haiku for cost optimization.

## Solution

1. Add `governance.models` section to project.yaml schema
2. Create `model_router.py` in orchestrator with tier-based auto-routing
3. Update `OrchestratorConfig` to load model config
4. Update `StepResult`/`DispatchInstruction` with model field
5. Update `ClaudeCodeDispatcher` to include model in dispatch instructions
6. Update policy engine to record model in manifest

## Deliverables

1. `governance/engine/orchestrator/model_router.py` — model routing module
2. Updated `config.py` — loads models config
3. Updated `step_result.py` — model field in DispatchInstruction
4. Updated `claude_code_dispatcher.py` — model in dispatch
5. Updated `project.schema.json` — models section
6. Tests for model routing
