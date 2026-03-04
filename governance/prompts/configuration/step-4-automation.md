# Configuration Wizard — Step 4: Automation Level

You are guiding a user through project.yaml configuration. This is Step 4 of 5.

## Prerequisites

Read the wizard state from `.artifacts/state/configure-wizard.json` to get Steps 1-3 results.

## Instructions

1. **Suggest parallel_coders** based on repo size from Step 1:

   ```
   How many AI agents should work in parallel?

   Based on your repository size ([small/medium/large]), we recommend:
   - Small repos: 2 parallel agents
   - Medium repos: 5 parallel agents (default)
   - Large repos: 8 parallel agents

   Suggested: [N] parallel agents

   You can accept the suggestion or specify a custom number (1-10, or -1 for unlimited).
   ```

2. **Ask about Project Manager mode**:

   ```
   Enable Project Manager mode?

   - No (default): A single Tech Lead manages all Coder agents directly.
     Simpler, lower overhead. Best for most projects.

   - Yes: A Project Manager groups issues by theme and spawns multiple
     Tech Leads, each managing their own pool of Coders. Better for
     large issue batches (10+) with diverse themes.

   Enable PM mode? [yes/no] (recommended: no)
   ```

3. **If PM mode is enabled**, ask about team lead count:

   ```
   How many Tech Leads should run concurrently? (1-5, default: 3)
   ```

4. **Update wizard state**:
   ```json
   {
     "step": 4,
     "completed": true,
     "parallel_coders": 5,
     "use_project_manager": false,
     "parallel_tech_leads": 3
   }
   ```

## Output

After the user confirms, tell them: "Step 4 complete. Moving to Step 5: Review and Write."

Then proceed to read and execute `governance/prompts/configuration/step-5-review.md`.
