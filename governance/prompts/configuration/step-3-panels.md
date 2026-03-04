# Configuration Wizard — Step 3: Panel Configuration

You are guiding a user through project.yaml configuration. This is Step 3 of 5.

## Prerequisites

Read the wizard state from `.artifacts/state/configure-wizard.json` to get Steps 1-2 results.

## Instructions

1. **Show the panels** that will run based on the governance level selected in Step 2:

   ```
   Based on your governance level, these panels will run on every change:

   - code-review: Reviews code quality, patterns, and best practices
   - security-review: Identifies security vulnerabilities and risks
   - threat-modeling: Analyzes threat vectors and attack surfaces
   - cost-analysis: Estimates cost impact of changes
   - documentation-review: Checks documentation completeness
   - data-governance-review: Ensures data handling compliance
   ```

2. **Ask about model assignment**:

   ```
   Do you want to assign specific AI models to specific panels?

   This lets you use more powerful (expensive) models for critical reviews
   and faster (cheaper) models for routine reviews.

   1. No — use the default model for all panels (recommended for most users)
   2. Yes — configure per-panel model assignment
   ```

3. **If the user selects "Yes"**, walk through model assignment:

   ```
   For each panel, choose a model tier:

   - opus: Most capable, best for security and architecture review
   - sonnet: Balanced cost and quality (default)
   - haiku: Fastest, best for documentation and cost analysis

   security-review: [opus/sonnet/haiku]? (recommended: opus)
   threat-modeling: [opus/sonnet/haiku]? (recommended: opus)
   code-review: [opus/sonnet/haiku]? (recommended: sonnet)
   documentation-review: [opus/sonnet/haiku]? (recommended: haiku)
   cost-analysis: [opus/sonnet/haiku]? (recommended: haiku)
   data-governance-review: [opus/sonnet/haiku]? (recommended: sonnet)
   ```

4. **Update wizard state**:
   ```json
   {
     "step": 3,
     "completed": true,
     "use_custom_models": true,
     "panel_models": {
       "defaults": {"model": "sonnet"},
       "overrides": {
         "security-review": {"model": "opus"},
         "documentation-review": {"model": "haiku"}
       }
     }
   }
   ```

## Output

After the user confirms, tell them: "Step 3 complete. Moving to Step 4: Automation Level."

Then proceed to read and execute `governance/prompts/configuration/step-4-automation.md`.
