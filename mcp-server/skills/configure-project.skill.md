---
name: configure-project
description: Run the guided configuration wizard to generate project.yaml step by step
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Bash
---

# Configure Project Skill

You are a configuration wizard for the Dark Forge. Guide the user through project.yaml setup in 5 steps using progressive disclosure.

## Instructions

1. Read and execute the wizard runner prompt at `governance/prompts/configuration/wizard-runner.md`
2. Follow each step sequentially, persisting state between steps
3. The wizard state is stored in `.governance/state/configure-wizard.json`

## Steps

1. **Basics** — Auto-detect language, framework, project characteristics
2. **Governance Level** — Choose Light / Standard / Strict
3. **Panel Configuration** — Review panels, optionally assign models
4. **Automation Level** — Set parallel agents, PM mode
5. **Review and Write** — Generate, review, and write project.yaml

## Resumption

If the wizard state file exists with partial progress, offer to resume from the last completed step rather than starting over.

## Validation

After writing project.yaml in Step 5, validate against `governance/schemas/project.schema.json` if the jsonschema library is available. Report any validation errors.
