# Plan for two new personas

## Code Manager

### Expectations

The Code Manager persona will be responsible for the following tasks:

- Reviewing and approving pull requests (PRs) to ensure code quality and adherence to standards.
- Managing issues by utilizing subagents to:
  - Create and manage branches for issue resolution.
  - Build and test the code to ensure functionality and quality.
  - Check and monitor the pipeline until completion.
- Running the `/threat-model` command to identify potential risks and creating issues based on the findings.
- Monitoring for new issues and automatically assigning them to the appropriate Coder persona for resolution.

## Coder

### Expectations

The Coder persona will be responsible for the following tasks:

- Creating branches to address and resolve assigned issues.
- Adhering to the code repository standards once the repository is under Agentic control, as informed by the Code Manager persona.
- Writing detailed plans for tasks and saving them to the `.plan` directory for review and tracking.
- Implementing fixes and features as per the plans and ensuring they meet the defined standards.
