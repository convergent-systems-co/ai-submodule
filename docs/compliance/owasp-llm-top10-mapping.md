# OWASP LLM Top 10 Coverage Matrix

This document maps each risk in the [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) to the specific governance controls implemented by the Dark Factory Governance Platform. It identifies the panels, policy rules, schema fields, and persona guardrails that address each risk, along with coverage assessment and gap mitigation recommendations.

**Version:** 1.0.0
**Last Updated:** 2026-02-27
**Applicable OWASP LLM Top 10 Version:** 2025

---

## Coverage Summary

| Risk ID | Risk Name | Coverage Level | Primary Controls |
|---------|-----------|----------------|------------------|
| LLM01 | Prompt Injection | **Full** | Content Security Policy, APPROVE verification, untrusted content handling |
| LLM02 | Sensitive Information Disclosure | **Full** | data-governance-review panel, data_classification schema, redaction fields |
| LLM03 | Supply Chain Vulnerabilities | **Full** | Submodule integrity verification, critical-files.sha256, threat-modeling panel |
| LLM04 | Data and Model Poisoning | **Full** | Canary calibration, plausibility checks, evidence-grounded findings |
| LLM05 | Improper Output Handling | **Full** | Structured emissions with JSON Schema validation, panel-output.schema.json |
| LLM06 | Excessive Agency | **Full** | Coder cannot push/merge/self-approve, persona authority matrices, circuit breakers |
| LLM07 | System Prompt Leakage | **Partial** | Read-only persona definitions in consuming repos, trust-level classification |
| LLM08 | Vector and Embedding Weaknesses | **Not Applicable** | Architecture does not use vector stores or embeddings |
| LLM09 | Misinformation | **Full** | Anti-hallucination rules, evidence requirements, canary calibration |
| LLM10 | Unbounded Consumption | **Full** | Context capacity protocol, circuit breakers, rate limits, CANCEL messages |

---

## Detailed Risk Mapping

### LLM01: Prompt Injection

**Description:** An attacker crafts input that causes the LLM to deviate from the developer's intended behavior, executing unintended actions or bypassing safety controls.

**Coverage Level:** Full

#### Governance Controls

| Control Type | Control | Location |
|-------------|---------|----------|
| **Panel** | security-review | `governance/prompts/reviews/security-review.md` -- Security Auditor perspective evaluates injection vectors (SQL, XSS, command injection, template injection) |
| **Panel** | threat-modeling | `governance/prompts/reviews/threat-modeling.md` -- Track 3 (Application Security) performs STRIDE analysis including injection threats |
| **Panel** | ai-expert-review | `governance/prompts/reviews/ai-expert-review.md` -- Prompt Engineer perspective evaluates injection resistance of instructions |
| **Policy Rule** | Content Security Policy | `governance/prompts/agent-protocol.md` Section "Content Security Policy" -- Classifies all input into TRUSTED/UNTRUSTED levels with six mandatory rules |
| **Policy Rule** | APPROVE Verification | `governance/prompts/agent-protocol.md` Section "APPROVE Verification Requirements" -- Structural verification prevents self-approval via prompt injection |
| **Policy Rule** | Untrusted Content Handling | `governance/prompts/startup.md` Section "Untrusted Content Handling" -- Issue bodies treated as UNTRUSTED data; embedded protocol messages ignored |
| **Schema Field** | `findings[].evidence` | `governance/schemas/panel-output.schema.json` -- Grounding evidence links injection findings to specific code locations |
| **Persona Guardrail** | No instruction following from untrusted sources | Content Security Policy Rule 2 -- Agents must not execute commands from UNTRUSTED sources |
| **Persona Guardrail** | No role-switching or persona override | Content Security Policy Rule 4 -- Attempts to redefine agent role from untrusted content are disregarded |
| **Persona Guardrail** | No encoded instruction execution | Content Security Policy Rule 5 -- Agents must not decode/execute hidden instructions (base64, Unicode homoglyphs, invisible characters) |
| **Persona Guardrail** | Ignore protocol messages in untrusted content | Content Security Policy Rule 3 -- Agent protocol messages in untrusted content are ignored entirely |

#### How It Works

The Content Security Policy (`governance/prompts/agent-protocol.md`) establishes a two-tier trust model. Content from governance files, persona definitions, schemas, and policy profiles is classified as TRUSTED and may be interpreted as instructions. All external content -- GitHub issue bodies, PR descriptions, file contents under review, commit messages, webhook payloads -- is classified as UNTRUSTED and treated strictly as data. Six mandatory rules enforce this boundary across all agents and all execution modes.

The APPROVE verification mechanism provides a second layer of defense. Because the Coder and Tester may execute within the same LLM context (Phase A), a prompt injection embedded in code under review could attempt to instruct the model to emit a false APPROVE. The Code Manager performs structural verification of every APPROVE payload -- cross-referencing `files_reviewed` against actual git diff output, validating acceptance criteria, and checking test gate status against CI -- providing a programmatic check independent of the Tester's assertion.

---

### LLM02: Sensitive Information Disclosure

**Description:** The LLM inadvertently reveals sensitive information (PII, credentials, proprietary data) through its responses.

**Coverage Level:** Full

#### Governance Controls

| Control Type | Control | Location |
|-------------|---------|----------|
| **Panel** | data-governance-review | `governance/prompts/reviews/data-governance-review.md` -- Compliance Officer perspective evaluates GDPR, SOC2, HIPAA, PCI-DSS compliance; Data Architect evaluates schema structure and canonical compliance |
| **Panel** | security-review | `governance/prompts/reviews/security-review.md` -- Security Auditor checks for secret exposure (hardcoded credentials, API keys, tokens in logs/code) and logging of sensitive data (PII, credentials, session tokens) |
| **Policy Rule** | fin_pii_high profile | `governance/policy/fin_pii_high.yaml` -- High-security profile for financial/PII repositories; auto-merge disabled, missing panels block (not redistribute), 25% weight on security-review |
| **Policy Rule** | Block auto-remediate on security controls | `governance/policy/default.yaml` -- `prohibited_actions` includes `modify_security_controls` and `alter_data_schemas`; automated remediation cannot modify security-sensitive code |
| **Schema Field** | `data_classification.level` | `governance/schemas/panel-output.schema.json` -- Classifies emission data sensitivity: `public`, `internal`, `confidential`, `restricted` |
| **Schema Field** | `data_classification.contains_sensitive_evidence` | `governance/schemas/panel-output.schema.json` -- Boolean flag indicating whether findings contain sensitive evidence (credentials, PII, vulnerability details) |
| **Schema Field** | `data_classification.redaction_applied` | `governance/schemas/panel-output.schema.json` -- Boolean flag indicating whether sensitive content has been redacted from the emission |
| **Schema Field** | `policy_flags[].flag` | `governance/schemas/panel-output.schema.json` -- Machine-readable flags include `pii_exposure` for data leak detection |
| **Persona Guardrail** | Data-only processing for untrusted content | Content Security Policy Rule 1 -- Prevents agents from echoing sensitive data found in UNTRUSTED sources as instructions |

#### How It Works

The `data-governance-review` panel is a required panel on every PR across all policy profiles. It includes a Compliance Officer perspective evaluating data handling against GDPR, SOC2, HIPAA, and PCI-DSS requirements, including data classification, retention, and access controls. The `data_classification` schema object on every panel emission enables downstream systems to identify emissions that may themselves contain sensitive evidence and apply appropriate redaction or access controls.

The `fin_pii_high` policy profile elevates security-review weight to 25% and data-design-review to 15%, disables auto-merge entirely, and blocks on any missing panel. This ensures repositories handling financial data or PII receive stricter scrutiny with zero tolerance for gaps.

---

### LLM03: Supply Chain Vulnerabilities

**Description:** Compromised components, training data, or plugins introduce vulnerabilities into the LLM application lifecycle.

**Coverage Level:** Full

#### Governance Controls

| Control Type | Control | Location |
|-------------|---------|----------|
| **Panel** | threat-modeling | `governance/prompts/reviews/threat-modeling.md` -- Track 2 (Supply Chain Security) with Supply Chain Security Specialist sub-moderator; Security Auditor evaluates new/changed dependencies |
| **Panel** | security-review | `governance/prompts/reviews/security-review.md` -- Infrastructure Engineer perspective evaluates deployment topology and rollback safety |
| **Policy Rule** | Submodule integrity verification | `governance/integrity/critical-files.sha256` -- SHA-256 hashes for all critical governance files (policies, schemas, scripts); init.sh verifies integrity on bootstrap |
| **Policy Rule** | Submodule freshness check | `bin/init.sh` -- Checks `.ai` submodule freshness on every bootstrap; auto-updates if behind |
| **Policy Rule** | Required panel execution | `governance/policy/default.yaml` `required_panels` -- Merge blocked if any required panel did not execute (`required_panel_missing == true`) |
| **Schema Field** | `execution_context.commit_sha` | `governance/schemas/panel-output.schema.json` -- 40-character hex SHA linking the emission to the exact codebase state reviewed |
| **Schema Field** | `execution_context.repository` | `governance/schemas/panel-output.schema.json` -- Repository identifier for provenance tracking |
| **Persona Guardrail** | Coder dependency additions are limited | `governance/personas/agentic/coder.md` -- Decision authority: "Limited -- must justify in plan, subject to security review" |
| **Persona Guardrail** | Code Manager security review invocation | `governance/personas/agentic/code-manager.md` -- Invokes security-review panel after Tester approval; creates issues for findings |

#### How It Works

`governance/integrity/critical-files.sha256` contains SHA-256 hashes for 48+ critical governance files including all policy profiles, all schemas, all signal adapters, and the init script. This provides tamper detection for the governance framework itself -- if a supply chain attack modifies a policy file or schema, the hash mismatch is detectable.

The threat-modeling panel includes a dedicated Supply Chain Security track (Track 2) that evaluates new/changed dependencies and vulnerability classification for introduced code. The Coder persona has limited authority for dependency additions -- they must be justified in the plan and are subject to the security-review panel.

---

### LLM04: Data and Model Poisoning

**Description:** An attacker manipulates training data or fine-tuning processes to introduce biases, backdoors, or vulnerabilities into the model's behavior.

**Coverage Level:** Full

#### Governance Controls

| Control Type | Control | Location |
|-------------|---------|----------|
| **Panel** | All panels (canary injection) | `governance/policy/canary-calibration.yaml` -- Known-vulnerable code snippets injected during panel execution to verify genuine analysis |
| **Panel** | ai-expert-review | `governance/prompts/reviews/ai-expert-review.md` -- AI Safety Specialist evaluates behavioral predictability, guardrail integrity, and misuse resistance |
| **Policy Rule** | Canary calibration enforcement | `governance/policy/default.yaml` `canary_calibration` section -- Low pass rate (<70%) flags for human review; zero detections on security panel is anomalous; consistent severity mismatches suggest evaluation gaming |
| **Policy Rule** | Plausibility checks | `governance/policy/default.yaml` `plausibility_checks` section -- Detects anomalous emission patterns: PRs with >3 files but zero findings are suspicious; identical scores across 3+ panels is an anomaly; emissions without execution_trace get capped confidence |
| **Schema Field** | `canary_results[]` | `governance/schemas/panel-output.schema.json` -- Records canary test results: `canary_id`, `detected`, `expected_severity`, `actual_severity`, `severity_match`, `detection_latency_ms` |
| **Schema Field** | `execution_trace` | `governance/schemas/panel-output.schema.json` -- Records evidence of actual code evaluation: `files_read`, `diff_lines_analyzed`, `grounding_references` |
| **Schema Field** | `findings[].evidence` | `governance/schemas/panel-output.schema.json` -- Findings with severity medium or above that lack evidence may be treated as hallucinated and discarded |
| **Persona Guardrail** | Anti-hallucination rules | `governance/personas/agentic/coder.md` -- All claims must be grounded in actual tool output; test results require Test Coverage Gate execution; artifact lists verified against git diff |

#### How It Works

Canary calibration (`governance/policy/canary-calibration.yaml`) provides a direct defense against model poisoning. Known-vulnerable code snippets (SQL injection, XSS, unused variables, hardcoded secrets) are injected during panel execution. If a panel fails to detect these known issues -- potentially because its underlying model has been poisoned to overlook certain vulnerability classes -- the canary pass rate drops below the 70% threshold and the system flags for human review.

Plausibility checks (`governance/policy/default.yaml`) detect anomalous emission patterns that may indicate a compromised or gaming model: zero findings on non-trivial PRs, identical confidence scores across multiple panels, and emissions without execution traces. The `execution_trace` schema field provides evidence that the panel actually read and analyzed code files, making it harder for a poisoned model to fabricate convincing outputs.

---

### LLM05: Improper Output Handling

**Description:** Outputs from the LLM are consumed without validation, enabling downstream exploits such as injection attacks, code execution, or privilege escalation.

**Coverage Level:** Full

#### Governance Controls

| Control Type | Control | Location |
|-------------|---------|----------|
| **Panel** | All panels (structured emissions) | `governance/schemas/panel-output.schema.json` -- Every panel must produce JSON validated against this schema; missing or invalid JSON means panel execution failed |
| **Policy Rule** | Structured emission markers | CLAUDE.md "Structured Emissions" section -- All panel output must include JSON between `<!-- STRUCTURED_EMISSION_START -->` and `<!-- STRUCTURED_EMISSION_END -->` markers |
| **Policy Rule** | Schema validation | `governance/schemas/panel-output.schema.json` with `additionalProperties: false` -- No unexpected fields allowed; all verdicts constrained to enum values (`approve`, `request_changes`, `block`, `abstain`) |
| **Policy Rule** | Agent protocol message schema | `governance/prompts/agent-protocol.md` -- Every inter-agent message must conform to the defined schema with typed fields and valid transition maps |
| **Policy Rule** | APPROVE structural verification | `governance/prompts/agent-protocol.md` -- Code Manager verifies every APPROVE payload field against actual system state before accepting it |
| **Schema Field** | `panel_name` | `governance/schemas/panel-output.schema.json` -- Pattern-constrained: `^[a-z][a-z0-9-]+$` |
| **Schema Field** | `panel_version` | `governance/schemas/panel-output.schema.json` -- Pattern-constrained: `^\d+\.\d+\.\d+$` (semantic versioning) |
| **Schema Field** | `risk_level` | `governance/schemas/panel-output.schema.json` -- Enum-constrained: `critical`, `high`, `medium`, `low`, `negligible` |
| **Schema Field** | `findings[].verdict` | `governance/schemas/panel-output.schema.json` -- Enum-constrained: `approve`, `request_changes`, `block`, `abstain` |
| **Schema Field** | `policy_flags[].severity` | `governance/schemas/panel-output.schema.json` -- Enum-constrained: `critical`, `high`, `medium`, `low`, `info` |
| **Persona Guardrail** | Policy engine is deterministic | CLAUDE.md "Policy Engine" section -- AI models never interpret policy rules; policies are evaluated programmatically |

#### How It Works

The governance platform enforces strict output schema validation at every boundary. All panel emissions must include JSON between sentinel markers, validated against `panel-output.schema.json` with `additionalProperties: false`. This prevents panels from producing arbitrary output that could be misinterpreted by downstream consumers.

The policy engine evaluates panel emissions deterministically -- AI models never interpret policy rules. This separation ensures that even if a panel's LLM output contains unexpected content, the enforcement layer processes only the validated structured fields. Enum constraints on critical fields (`risk_level`, `verdict`, `severity`) prevent value injection through output manipulation.

Inter-agent messages follow the same principle: every message has a typed schema with required fields, valid sender/receiver constraints, and a transition map. The Code Manager's structural verification of APPROVE messages provides an additional output validation layer.

---

### LLM06: Excessive Agency

**Description:** The LLM-based system has excessive functionality, permissions, or autonomy, leading to unintended actions with significant impact.

**Coverage Level:** Full

#### Governance Controls

| Control Type | Control | Location |
|-------------|---------|----------|
| **Panel** | ai-expert-review | `governance/prompts/reviews/ai-expert-review.md` -- AI Safety Specialist evaluates scope containment and guardrail integrity; flags unauthorized authority expansion |
| **Policy Rule** | Auto-merge conditions | `governance/policy/default.yaml` `auto_merge` section -- Six conditions must ALL be true: confidence >= 0.85, risk low/negligible, no critical/high flags, all panels approve, no human review required, CI passed |
| **Policy Rule** | Auto-remediate restrictions | `governance/policy/default.yaml` `auto_remediate` section -- Prohibited actions: `modify_security_controls`, `change_api_contracts`, `alter_data_schemas`, `modify_infrastructure`; max 3 attempts with cooldown |
| **Policy Rule** | Override requirements | `governance/policy/default.yaml` `override` section -- Requires 2 approvals from senior_engineer + tech_lead with justified rationale (50+ chars); creates audit issue |
| **Policy Rule** | Circuit breaker | `governance/prompts/agent-protocol.md` -- MAX_TOTAL_EVALUATION_CYCLES = 5; prevents unbounded automated re-assignment loops |
| **Policy Rule** | Circuit breaker (remediation) | `governance/policy/circuit-breaker.yaml` -- failure_threshold: 3, cooldown periods, max_open_duration_hours: 24, open_action: human_escalation |
| **Policy Rule** | Autonomy thresholds | `governance/policy/autonomy-thresholds.yaml` -- Tracks human_intervention_rate, escalations_to_human, dirty_context_compactions; critical thresholds trigger alerts |
| **Persona Guardrail** | Coder cannot self-approve | `governance/personas/agentic/coder.md` -- Decision authority: "Self-approval: None"; "Push authorization: Conditional -- requires Tester APPROVE" |
| **Persona Guardrail** | Coder cannot merge | `governance/personas/agentic/coder.md` -- Decision authority: "Merge: None -- handled by Code Manager and policy engine" |
| **Persona Guardrail** | Coder cannot push without approval | `governance/personas/agentic/coder.md` -- Decision authority: "Push authorization: Conditional -- requires Tester APPROVE before push" |
| **Persona Guardrail** | Code Manager cannot override policy | `governance/personas/agentic/code-manager.md` -- Decision authority: "Override: None -- escalates to human reviewers" |
| **Persona Guardrail** | Code Manager cannot change governance | `governance/personas/agentic/code-manager.md` -- Decision authority: "Governance changes: None -- proposes changes for human approval" |
| **Persona Guardrail** | Valid transition map | `governance/prompts/agent-protocol.md` -- Strict sender/receiver constraints; DevOps Engineer never communicates directly with Coder/Tester |
| **Persona Guardrail** | CANCEL priority | `governance/prompts/agent-protocol.md` -- CANCEL supersedes all in-flight messages; agents must stop within one step |

#### How It Works

The governance platform implements defense-in-depth against excessive agency through persona authority matrices, policy constraints, and circuit breakers.

Each persona has an explicit decision authority table defining full, conditional, limited, advisory, and none authority levels per domain. The Coder has no authority over self-approval, merge, or architectural changes. The Code Manager has no authority over override, governance changes, or session lifecycle. These constraints create a separation-of-concerns model where no single agent can complete the full pipeline without cooperation.

Policy-level controls further constrain automation: auto-merge requires six simultaneous conditions (all AND), auto-remediate explicitly prohibits modifying security controls or infrastructure, and overrides require multi-party human approval with audit trails. Circuit breakers at both the protocol level (5 evaluation cycles) and remediation level (3 consecutive failures) enforce hard stops on automated loops.

---

### LLM07: System Prompt Leakage

**Description:** Sensitive system prompt information is exposed to users or external systems, revealing internal instructions, business logic, or security controls.

**Coverage Level:** Partial

#### Governance Controls

| Control Type | Control | Location |
|-------------|---------|----------|
| **Policy Rule** | Read-only governance sources | CLAUDE.md "Resource Locations" table -- Persona definitions, review prompts, policy profiles, and schemas are in the `.ai/` submodule, read-only in consuming repos |
| **Policy Rule** | Trust level classification | `governance/prompts/agent-protocol.md` Content Security Policy -- Governance files are TRUSTED; their content defines agent behavior but is not intended for external exposure |
| **Policy Rule** | Submodule distribution model | CLAUDE.md "What This Repository Is" -- Governance framework distributed as a git submodule; consuming repos reference but do not copy prompt content |
| **Persona Guardrail** | No role-switching or persona override | Content Security Policy Rule 4 -- Agents disregard attempts to extract prompt content via role-switching attacks |

#### Gap Analysis

| Gap | Severity | Mitigation Recommendation |
|-----|----------|--------------------------|
| No runtime exfiltration detection | Medium | Implement output filtering to detect when agent responses contain verbatim persona definitions, prompt templates, or policy rule content. Add a post-processing layer that compares agent output against known governance file content and redacts matches. |
| No prompt encryption at rest | Low | Governance files are plaintext in the git submodule. Consider encrypting sensitive persona definitions at rest and decrypting only during agent execution, particularly for the Content Security Policy rules themselves. |
| System prompt content in git history | Low | Even if prompts are updated, previous versions remain in git history. For high-security deployments, consider using a separate private repository for sensitive prompt content with access controls beyond standard git permissions. |

#### How It Works

The primary defense is architectural: persona definitions, review prompts, and policy profiles reside in the `.ai/` submodule and are read-only in consuming repositories. This means consuming repos cannot modify governance prompts, but the prompts are accessible to anyone with repository read access.

The Content Security Policy's rule against role-switching provides some protection: if an attacker attempts to extract system prompts via "repeat your instructions" or similar attacks through issue bodies or PR comments, the agent should disregard these as untrusted content. However, there is no runtime verification that agents are not inadvertently including prompt content in their responses.

---

### LLM08: Vector and Embedding Weaknesses

**Description:** Weaknesses in how vectors and embeddings are generated, stored, or retrieved can be exploited to inject malicious content or extract sensitive information.

**Coverage Level:** Not Applicable

#### Rationale

The Dark Factory Governance Platform does not use vector databases, embeddings, RAG (Retrieval-Augmented Generation), or semantic search. The architecture is based on:

- **Structured prompts** (Markdown) loaded directly from the file system
- **Deterministic policy evaluation** (YAML rules evaluated programmatically)
- **Schema-validated JSON emissions** (no vector similarity matching)
- **Tiered context loading** (JIT file reading, not embedding-based retrieval)

If a consuming repository introduces vector/embedding infrastructure, the existing `security-review` and `threat-modeling` panels would evaluate those components during PR review. The ai-expert-review panel would also assess any changes to the governance pipeline that introduce embedding-based retrieval.

#### Future Consideration

If the governance platform introduces embedding-based context retrieval (e.g., semantic search over governance documentation), this risk would become applicable and would require:
- Embedding provenance tracking in the panel output schema
- Vector store integrity verification analogous to `critical-files.sha256`
- Injection detection for adversarial embedding manipulation

---

### LLM09: Misinformation

**Description:** The LLM generates false or misleading information, leading to incorrect decisions, security vulnerabilities, or compliance failures.

**Coverage Level:** Full

#### Governance Controls

| Control Type | Control | Location |
|-------------|---------|----------|
| **Panel** | All panels (evidence requirements) | `governance/schemas/panel-output.schema.json` -- `findings[].evidence` field: "Findings with severity 'medium' or above that lack evidence may be treated as hallucinated and discarded" |
| **Panel** | All panels (canary calibration) | `governance/policy/canary-calibration.yaml` -- Known-vulnerable snippets verify panels are performing genuine analysis, not fabricating findings |
| **Panel** | ai-expert-review | `governance/prompts/reviews/ai-expert-review.md` -- AI Safety Specialist evaluates behavioral predictability and anti-pattern introduction |
| **Policy Rule** | Plausibility checks | `governance/policy/default.yaml` `plausibility_checks` section -- Zero findings on >3-file PRs are suspicious; confidence capped without execution_trace; identical scores across panels flagged |
| **Policy Rule** | Confidence cap without trace | `governance/policy/default.yaml` `plausibility_checks.confidence_cap_without_trace` -- Emissions without execution_trace get max_confidence capped at 0.70, preventing auto-merge |
| **Policy Rule** | Multi-panel consensus | `governance/policy/default.yaml` `escalation.panel_disagreement` -- Conflicting verdicts across panels require human review |
| **Schema Field** | `findings[].evidence.file` | `governance/schemas/panel-output.schema.json` -- Required field grounding findings to specific files |
| **Schema Field** | `findings[].evidence.snippet` | `governance/schemas/panel-output.schema.json` -- Code snippet (max 200 chars) providing concrete evidence |
| **Schema Field** | `execution_trace.files_read` | `governance/schemas/panel-output.schema.json` -- Required array of file paths the panel agent read during review |
| **Schema Field** | `execution_trace.grounding_references` | `governance/schemas/panel-output.schema.json` -- Links findings to specific code locations (file + line + finding_id) |
| **Persona Guardrail** | Anti-hallucination rules (Coder) | `governance/personas/agentic/coder.md` "Anti-Hallucination Rules" section -- Five explicit rules: test results must come from Test Coverage Gate output; plan references must come from Read tool; artifacts verified against git diff; file contents require reading the file; coverage claims require actual command output |
| **Persona Guardrail** | APPROVE grounding requirements | `governance/prompts/agent-protocol.md` -- Tester APPROVE must contain actual CI/test status, actual file diff list, and actual coverage percentage |

#### How It Works

The governance platform combats misinformation through a multi-layered evidence-grounding strategy.

At the panel level, every finding with severity medium or above must include an `evidence` object with at minimum a file path. Findings lacking evidence may be discarded as hallucinated. The `execution_trace` provides additional verification that the panel actually read the files it claims to have analyzed.

At the persona level, the Coder's anti-hallucination rules are explicit: do not assert test results without running the Test Coverage Gate, do not cite plan details without reading the plan file, do not describe file contents without reading the file. These rules prevent the most common LLM hallucination patterns in code generation contexts.

Canary calibration serves as a meta-defense: if a panel fabricates findings rather than performing genuine analysis, it will also fail to detect the known-vulnerable canary snippets, triggering human review. The plausibility checks provide statistical anomaly detection for emission patterns that suggest fabrication.

---

### LLM10: Unbounded Consumption

**Description:** The LLM application allows excessive resource consumption, leading to denial of service, cost escalation, or resource exhaustion.

**Coverage Level:** Full

#### Governance Controls

| Control Type | Control | Location |
|-------------|---------|----------|
| **Panel** | cost-analysis | `governance/prompts/reviews/cost-analysis.md` -- Required panel on every PR evaluating cost implications of changes |
| **Policy Rule** | Context capacity protocol | CLAUDE.md "Context Capacity Protocol" -- Hard stop at 80% context capacity; stop work, clean git state, write checkpoint, request reset |
| **Policy Rule** | Rate limits | `governance/policy/rate-limits.yaml` -- Per-DI: 5/hour, 20/day; per-component: 10/hour, 40/day; global: 50/hour, 200/day; overflow actions: queue, aggregate, triage by priority |
| **Policy Rule** | Circuit breaker (remediation) | `governance/policy/circuit-breaker.yaml` -- failure_threshold: 3, cooldown 30 minutes (exponential backoff to 240 min), max_open_duration_hours: 24, human_escalation on open |
| **Policy Rule** | Circuit breaker (evaluation) | `governance/prompts/agent-protocol.md` -- MAX_TOTAL_EVALUATION_CYCLES = 5; prevents unbounded feedback loops |
| **Policy Rule** | Panel execution circuit breaker | `governance/policy/circuit-breaker.yaml` `panel_execution` section -- 3 consecutive failures trip breaker; 15-minute cooldown; action: use_baseline_and_escalate |
| **Policy Rule** | Panel timeout configuration | `governance/policy/panel-timeout.yaml` (referenced by `governance/policy/default.yaml`) -- Configures timeout behavior per panel |
| **Policy Rule** | Cooldown by priority | `governance/policy/circuit-breaker.yaml` `cooldown_by_priority` -- P0: 5min, P1: 15min, P2: 60min, P3: 240min, P4: 1440min |
| **Policy Rule** | Session cap | `governance/prompts/startup.md` -- Max N issues per session (N = `governance.parallel_coders`, default 5) |
| **Policy Rule** | Auto-remediate limits | `governance/policy/default.yaml` `auto_remediate` section -- max_attempts: 3, cooldown_minutes: 5 |
| **Schema Field** | `duration_ms` | `governance/schemas/panel-output.schema.json` -- Panel execution duration in milliseconds; enables monitoring and anomaly detection |
| **Schema Field** | `execution_status` | `governance/schemas/panel-output.schema.json` -- Tracks `timeout` and `fallback` statuses; fallback emissions cannot trigger auto-merge |
| **Persona Guardrail** | Coder capacity tiers | `governance/personas/agentic/coder.md` -- Pre-task capacity check: Green (<60%), Yellow (60-70%), Orange (70-80%), Red (>=80%); stop signals at Orange and Red |
| **Persona Guardrail** | CANCEL messages | `governance/prompts/agent-protocol.md` -- Context capacity signals: tool calls >80 or chat turns >50 trigger CANCEL propagation; CANCEL supersedes all in-flight messages |
| **Persona Guardrail** | Error isolation | `governance/prompts/agent-protocol.md` "Error Isolation" section -- Failures in one work unit cannot cascade; retry cap of 2 per work unit; malformed inputs caught and isolated |
| **Persona Guardrail** | Autonomy thresholds | `governance/policy/autonomy-thresholds.yaml` -- Tracks avg_context_usage_percent (critical >75%), avg_issues_per_session, dirty_context_compactions (must be 0) |

#### How It Works

The governance platform implements resource consumption controls at every level of the pipeline.

**Context window management:** A hard stop at 80% context capacity prevents context exhaustion. The Coder persona has explicit capacity tiers (Green/Yellow/Orange/Red) with escalating stop signals. CANCEL messages propagate from DevOps Engineer through Code Manager to all workers when context signals exceed thresholds (tool calls >80, chat turns >50).

**Rate limiting:** `rate-limits.yaml` enforces per-DI, per-component, and global rate limits on panel executions with overflow strategies (queue, aggregate, triage by priority).

**Circuit breakers:** Two independent circuit breaker mechanisms prevent runaway loops. The evaluation circuit breaker (5 total cycles) prevents unbounded Tester feedback loops. The remediation circuit breaker (3 consecutive failures with exponential backoff) prevents runaway auto-remediation. Both escalate to human review when tripped.

**Error isolation:** Independent processing per work unit ensures a single malformed input cannot crash the pipeline, exhaust the context window, or block other work. Retry caps (2 per work unit) prevent infinite retry loops.

---

## Cross-Cutting Controls

Several governance controls address multiple OWASP LLM risks simultaneously:

| Control | Risks Addressed | Location |
|---------|----------------|----------|
| Content Security Policy | LLM01, LLM02, LLM07 | `governance/prompts/agent-protocol.md` |
| Canary calibration | LLM04, LLM09 | `governance/policy/canary-calibration.yaml` |
| Structured emission validation | LLM05, LLM09 | `governance/schemas/panel-output.schema.json` |
| Persona authority matrices | LLM01, LLM06 | `governance/personas/agentic/*.md` |
| Circuit breakers | LLM06, LLM10 | `governance/policy/circuit-breaker.yaml`, `governance/prompts/agent-protocol.md` |
| Evidence-grounded findings | LLM04, LLM09 | `governance/schemas/panel-output.schema.json` `findings[].evidence` |
| Plausibility checks | LLM04, LLM09 | `governance/policy/default.yaml` `plausibility_checks` |
| Policy engine determinism | LLM01, LLM05, LLM06 | `governance/policy/*.yaml` (all profiles) |
| Persistent audit logging | LLM01, LLM02, LLM06 | `governance/prompts/agent-protocol.md` "Persistent Logging" |

---

## Consolidated Gap Summary

| Risk | Gap | Severity | Recommended Mitigation |
|------|-----|----------|----------------------|
| LLM07 | No runtime exfiltration detection for system prompt content | Medium | Add output filtering that compares agent responses against governance file content and redacts matches |
| LLM07 | No prompt encryption at rest | Low | Encrypt sensitive persona definitions at rest for high-security deployments |
| LLM07 | System prompt history in git | Low | Use private repository with access controls for sensitive prompt content in high-security contexts |
| LLM08 | Not applicable to current architecture | None | Monitor for introduction of vector/embedding components in consuming repos; extend schema if needed |

---

## References

- [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Content Security Policy](../../governance/prompts/agent-protocol.md#content-security-policy)
- [Panel Output Schema](../../governance/schemas/panel-output.schema.json)
- [Default Policy Profile](../../governance/policy/default.yaml)
- [Circuit Breaker Configuration](../../governance/policy/circuit-breaker.yaml)
- [Rate Limits Configuration](../../governance/policy/rate-limits.yaml)
- [Canary Calibration Configuration](../../governance/policy/canary-calibration.yaml)
- [Critical Files Integrity](../../governance/integrity/critical-files.sha256)
- [Coder Persona](../../governance/personas/agentic/coder.md)
- [Code Manager Persona](../../governance/personas/agentic/code-manager.md)
- [Agent Protocol](../../governance/prompts/agent-protocol.md)
