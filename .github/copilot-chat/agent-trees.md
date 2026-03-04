Show the full agent topology as a hierarchical ASCII tree with live status for all dispatched agents.

## Steps

1. **Get orchestrator tree data** — run:

   ```bash
   python3 -m governance.engine.orchestrator tree
   ```

   This returns JSON with: `session_id`, `phase`, `phase_name`, `loop_count`, `config` (including `use_project_manager`), `agents` (list of `{persona, issue_ref, branch, status, task_id}`), `issues`, `prs`, and `summary`.

   If the command fails or returns `{"error": ...}`, report the error and stop.

2. **Enrich running agents with live activity** — for each agent where `status` is `"pending"` (i.e., still running) and `task_id` is non-empty:

   - Look for the task output file at `/private/tmp/claude-501/*/tasks/{task_id}.output`
   - Read the last 80 lines of the output file
   - Extract the most recent meaningful assistant action — look for tool calls (Edit, Write, Read, Bash, Grep, Glob) or text describing what the agent is doing
   - Summarize this into a short activity phrase like: `implementing agent_registry.py`, `reading codebase`, `running tests`, `creating PR`, `writing plan`

3. **Determine topology from config** and render:

   ### Standard mode (`use_project_manager: false`)

   ```
   Session: {session_id} | Phase: {phase} ({phase_name}) | Loop: {loop_count}

   DevOps Engineer ── PR operations loop ── [background]
   │
   Team Lead (this session) ── orchestrating {N} agents ── [active]
   ├── Coder [{issue_ref}] ── {issue title or ref} ── [{activity or status}]
   ├── Coder [{issue_ref}] ── {issue title or ref} ── [{activity}]
   └── Coder [{issue_ref}] ── {issue title or ref} ── [completed ✓]

   Issues: {selected} selected, {done} done | PRs: {created} created, {resolved} resolved
   ```

   ### PM mode (`use_project_manager: true`)

   ```
   Session: {session_id} | Phase: {phase} ({phase_name}) | Loop: {loop_count}

   Project Manager ── Phase {phase}: {phase_name} ── [active]
   ├── DevOps Engineer ── PR operations loop ── [background]
   ├── Team Lead [batch-1] ── issues {refs} ── [running]
   │   ├── Coder [{issue_ref}] ── {description} ── [{activity}]
   │   └── Coder [{issue_ref}] ── {description} ── [{activity}]
   └── Team Lead [batch-2] ── issues {refs} ── [running]
       ├── Coder [{issue_ref}] ── {description} ── [completed ✓]
       └── Coder [{issue_ref}] ── {description} ── [{activity}]

   Issues: {selected} selected, {done} done | PRs: {created} created, {resolved} resolved
   ```

4. **Status indicators**:
   - `[completed ✓]` — agent finished successfully
   - `[failed ✗]` — agent encountered an error
   - `[{activity phrase}]` — agent is running; show what it's doing (from step 2)
   - `[pending]` — agent is running but no output file found yet
   - `[background]` — long-running background agent (DevOps Engineer)
   - `[active]` — the current session's own agent (Team Lead / Project Manager)

5. **Use box-drawing characters** for the tree: `├──`, `└──`, `│`, and proper indentation for nested levels. Use `──` (em-dash pairs) as connectors between columns.

## Important

- Do NOT create any files or modify any code. This is a read-only status command.
- If there are no active sessions, say so clearly.
- In PM mode, group Coders under their parent Team Lead. If batch assignment info is not available in the JSON, show all Coders as direct children of a single Team Lead node.
- Keep the output compact — this is meant for quick glances, not detailed reporting.
