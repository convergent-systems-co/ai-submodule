# Plan: Extend Orchestrator with Deployment Phases (#609)

## Problem
The orchestrator covers phases 0-5 (triage through merge) but has no deployment phases.

## Solution
Add optional Phase 6 (Build & Package) and Phase 7 (Deploy & Verify) to the orchestrator.
Phases are gated by `governance.deployment.enabled` in project.yaml.

## Files Changed
- `governance/engine/orchestrator/deployment.py` (NEW) - Deployment config, targets, results
- `governance/engine/orchestrator/capacity.py` (MODIFIED) - Gate actions for phases 6-7
- `governance/engine/orchestrator/state_machine.py` (MODIFIED) - Valid transitions for 6-7
- `governance/engine/orchestrator/step_runner.py` (MODIFIED) - Phase routing and descriptions
- `governance/engine/orchestrator/config.py` (MODIFIED) - DeploymentConfig loading
- `governance/engine/orchestrator/session.py` (MODIFIED) - Deployment state fields
- `governance/schemas/project.schema.json` (MODIFIED) - Deployment schema
- `governance/engine/tests/test_deployment_phases.py` (NEW) - 30+ tests
- `docs/guides/deployment-phases.md` (NEW) - Usage guide
