# Configuration Wizard — Step 2: Governance Level

You are guiding a user through project.yaml configuration. This is Step 2 of 5.

## Prerequisites

Read the wizard state from `.artifacts/state/configure-wizard.json` to get Step 1 results.

## Instructions

1. **Present three governance levels** with clear descriptions:

   ```
   What level of governance do you need?

   1. Light (fast-track)
      - Minimal review panels (code-review + security-review only)
      - Fast auto-merge with lower confidence thresholds
      - Best for: prototypes, internal tools, low-risk changes

   2. Standard (default)
      - Core review panels (code-review, security-review, threat-modeling,
        cost-analysis, documentation-review, data-governance-review)
      - Balanced auto-merge conditions
      - Best for: most production projects

   3. Strict (fin_pii_high / infrastructure_critical)
      - All review panels plus additional compliance panels
      - Strict confidence thresholds, human review for high-risk changes
      - Best for: financial systems, PII handling, critical infrastructure
   ```

2. **Map the selection** to configuration values:

   | Level | Policy Profile | Required Panels |
   |-------|---------------|-----------------|
   | Light | fast-track | code-review, security-review |
   | Standard | default | code-review, security-review, threat-modeling, cost-analysis, documentation-review, data-governance-review |
   | Strict | fin_pii_high | All standard + architecture-review, production-readiness-review, data-governance-review |

3. **Update wizard state** with the selection:
   ```json
   {
     "step": 2,
     "completed": true,
     "governance_level": "standard",
     "policy_profile": "default",
     "panels": ["code-review.md", "security-review.md", ...]
   }
   ```

## Output

After the user selects, tell them: "Step 2 complete. Moving to Step 3: Panel Configuration."

Then proceed to read and execute `governance/prompts/configuration/step-3-panels.md`.
