# Configuration Wizard — Runner

This prompt orchestrates the five-step configuration wizard for project.yaml.

## Overview

The wizard guides users through project.yaml setup without requiring documentation. Each step builds on previous answers using progressive disclosure.

## Instructions

Run the following steps in sequence. Between steps, persist state to `.artifacts/state/configure-wizard.json` so each step has full context of prior choices.

### Pre-flight

1. Check if `.artifacts/state/configure-wizard.json` exists with partial progress.
   If yes, offer to resume from the last completed step.
2. Create the state directory if needed: `mkdir -p .artifacts/state`

### Steps

Execute each step by reading and following the corresponding prompt:

1. **Step 1 — Basics**: Read `governance/prompts/configuration/step-1-basics.md`
   - Auto-detect language, framework, repo characteristics
   - User confirms or modifies

2. **Step 2 — Governance Level**: Read `governance/prompts/configuration/step-2-governance-level.md`
   - Choose Light / Standard / Strict
   - Maps to policy profile and panel set

3. **Step 3 — Panel Configuration**: Read `governance/prompts/configuration/step-3-panels.md`
   - Review which panels will run
   - Optionally configure per-panel model assignment

4. **Step 4 — Automation Level**: Read `governance/prompts/configuration/step-4-automation.md`
   - Set parallel agent count
   - Optionally enable Project Manager mode

5. **Step 5 — Review and Write**: Read `governance/prompts/configuration/step-5-review.md`
   - Generate complete project.yaml
   - User reviews and confirms
   - Write to disk and validate

### Error Handling

- If the user wants to go back to a previous step, re-read that step's prompt
- If auto-detection fails, fall back to asking the user directly
- If schema validation fails, show the errors and offer to fix

## State File Schema

The wizard state file `.artifacts/state/configure-wizard.json` conforms to:
`governance/schemas/configure-wizard-state.schema.json`
