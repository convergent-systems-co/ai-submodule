# Configuration Wizard — Step 1: Project Basics

You are guiding a user through project.yaml configuration. This is Step 1 of 5.

## Instructions

1. **Auto-detect the project** by scanning the repository for language and framework markers:
   - Look for: `package.json`, `tsconfig.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `pom.xml`, `build.gradle`, `*.csproj`, `Cargo.toml`, `*.bicep`, `*.tf`, `Dockerfile`
   - If `governance/engine/orchestrator/auto_detect.py` is available, use it:
     ```python
     from governance.engine.orchestrator.auto_detect import detect_project
     result = detect_project(".")
     ```
   - Otherwise, scan manually using the file markers above

2. **Present the detection results** to the user:
   ```
   Detected project characteristics:
   - Languages: [list]
   - Framework: [name or "none detected"]
   - Has IaC: [yes/no]
   - Has tests: [yes/no]
   - Repository size: [small/medium/large]
   ```

3. **Ask the user to confirm or modify**:
   - "Does this look correct? You can modify any of these values."
   - Accept corrections to language, framework, or project name

4. **Write wizard state** to `.artifacts/state/configure-wizard.json`:
   ```json
   {
     "step": 1,
     "completed": true,
     "project_name": "<name>",
     "languages": ["<detected>"],
     "framework": "<detected or null>",
     "has_iac": false,
     "has_tests": true,
     "repo_size": "medium"
   }
   ```

## Output

After the user confirms, tell them: "Step 1 complete. Moving to Step 2: Governance Level."

Then proceed to read and execute `governance/prompts/configuration/step-2-governance-level.md`.
