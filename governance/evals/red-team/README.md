# Red-Team Adversarial Test Datasets

This directory contains adversarial test cases designed to validate that governance panels resist manipulation, deception, and social engineering techniques embedded in code under review.

## Purpose

Standard canary calibration (see `governance/policy/canary-calibration.yaml`) verifies that panels detect *known* vulnerabilities. Red-team datasets go further: they verify that panels are **not fooled** by adversarial techniques that attempt to suppress, bypass, or misdirect panel findings.

## Dataset Structure

Each YAML file follows a consistent schema:

```yaml
dataset: "<unique-dataset-name>"
version: "1.0.0"
target_panels: ["<panel-type>", ...]
test_cases:
  - id: "<dataset-prefix>-NNN"
    description: "Human-readable description of the adversarial scenario"
    adversarial_technique: "<technique-category>"
    code_snippet: |
      # The adversarial code to evaluate
    expected_behavior:
      should_detect_vulnerability: true|false
      should_ignore_fake_approval: true|false  # when applicable
      expected_finding_category: "<category>"
      min_severity: "low|medium|high|critical"
```

## Datasets

| File | Technique | Tests |
|------|-----------|-------|
| `fake-approval-comments.yaml` | Social engineering via code comments that mimic security approvals | 3 |
| `misleading-docs.yaml` | Deceptive docstrings and documentation that contradict code behavior | 3 |
| `obfuscated-vulns.yaml` | Obfuscated vulnerabilities using encoding, indirection, and naming tricks | 3 |
| `protocol-injection.yaml` | Agent protocol keywords embedded in code to confuse panel agents | 3 |

## Adversarial Technique Categories

- **social_engineering_comments** -- Fake approval stamps, fabricated audit trails in comments
- **misleading_documentation** -- Docstrings that claim safety properties the code does not have
- **obfuscation** -- Base64 encoding, dynamic construction, variable name misdirection
- **protocol_injection** -- Agent protocol keywords (`APPROVE`, `AGENT_MSG_START`) in code artifacts

## Adding New Test Cases

1. Choose the appropriate dataset file (or create a new one for a new technique category)
2. Assign the next sequential ID using the dataset prefix (e.g., `rt-fac-004`)
3. Include a realistic but safe code snippet -- no actual working exploits
4. Define expected behavior: what the panel should detect and what it should ignore
5. Update `canary-calibration.yaml` if adding a new dataset file

## Integration with Canary Calibration

Red-team datasets are referenced from `governance/policy/canary-calibration.yaml` under the `red_team` section. The canary calibration system evaluates red-team pass rates alongside standard canary detection rates. See `docs/guides/red-team-validation.md` for interpretation guidance.
