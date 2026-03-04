# Security Instructions

<!-- PHASE:security -->

Loaded for security-sensitive tasks and compliance-flagged changes.

## Secure Coding

- Validate all external input at system boundaries
- Use parameterized queries — never string concatenation for data access
- Apply least-privilege for all access controls
- Never log secrets, tokens, or PII
- Use established cryptographic libraries — never roll custom crypto

## Threat Awareness

- Consider OWASP Top 10 for web-facing changes
- Evaluate auth bypass and privilege escalation vectors
- Check for insecure defaults in configuration
- Ensure secrets are managed via vault or environment, never committed
