# Plan: Support unlimited parallel_coders (-1) with context-monitored auto-clear

**Issue:** #388
**Status:** complete
**Branch:** `NETWORK_ID/feat/388/unlimited-parallel-coders`
**Risk:** Low — additive change, no breaking modifications

## Objective

Allow `governance.parallel_coders` to be set to `-1`, meaning "unlimited." When N=-1, the pipeline processes all actionable issues without an issue-count cap — context pressure (the four-tier capacity model) becomes the sole mechanism for session termination.

## Changes

1. **`governance/schemas/project.schema.json`** — Change minimum from 1 to -1; update description.
2. **`governance/prompts/startup.md`** — Update all references to session caps, N issues, and hard limits to handle N=-1.
3. **`governance/personas/agentic/devops-engineer.md`** — Update capacity thresholds, session cap, and anti-patterns for N=-1.
4. **`governance/personas/agentic/team-lead.md`** — Update parallel dispatch references for N=-1.
5. **`docs/architecture/context-management.md`** — Update capacity tier signal tables; add unlimited mode subsection; add auto-clear documentation.
6. **`CLAUDE.md`** — Update agentic startup sequence and parallel_coders references.
7. **`README.md`** — Update parallel_coders references.

## Acceptance Criteria

- [ ] `parallel_coders: -1` validates against the schema
- [ ] All documentation consistently describes -1 behavior
- [ ] No breaking changes to existing behavior (N > 0 unchanged)
- [ ] Auto-clear investigation findings documented
