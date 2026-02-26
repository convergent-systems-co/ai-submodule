# Review: Threat Model — System-Level

## Purpose

Comprehensive system-level threat model producing a structured security assessment of the entire platform or application. This is an on-demand analysis — not a per-PR gate — that maps the full attack surface to MITRE ATT&CK, performs STRIDE analysis per trust boundary, constructs attack trees, validates detection coverage, and produces a prioritized mitigation roadmap with Sigma detection rules.

## Context

You are performing a **system-level threat model**. Analyze the entire system (or the scope specified by the user) from multiple security perspectives organized into 5 parallel review tracks. Each track has a sub-moderator coordinating its participants. The output must follow the standardized 15-section template exactly, including all appendices.

> **Panel name:** `threat-model-system`
> **Baseline emission:** Uses the same schema as [`threat-modeling.json`](../../emissions/threat-modeling.json) with `panel_name: "threat-model-system"`.

## Review Tracks and Participants

### Track 1: Infrastructure Security
**Sub-Moderator:** Infrastructure Security Engineer

| Participant | Focus |
|------------|-------|
| Systems Architect | Component inventory, data flow diagrams, trust boundaries, external dependencies |
| Infrastructure Engineer | Configuration assessment, IAM scope, network segmentation, encryption, rollback safety |

### Track 2: Supply Chain Security
**Sub-Moderator:** Supply Chain Security Specialist

| Participant | Focus |
|------------|-------|
| MITRE Analyst (ATT&CK) | Trust boundary crossings, threat actor profiles, ATT&CK technique mapping |
| Security Auditor | Dependency audit, third-party risk, SBOM analysis, vulnerability classification |

### Track 3: Application Security
**Sub-Moderator:** Application Security Engineer

| Participant | Focus |
|------------|-------|
| MITRE Analyst (STRIDE) | STRIDE threat catalog per trust boundary, attack tree construction |
| Red Team Engineer | Attack path validation, kill chain construction, exploit feasibility |

### Track 4: DevSecOps & AI Safety
**Sub-Moderator:** DevSecOps & AI Safety Engineer

| Participant | Focus |
|------------|-------|
| Purple Team Engineer | ATT&CK technique coverage matrix, detection validation, adversary emulation |
| Blue Team Engineer | Detection & response coverage, alerting gaps, incident response assessment |

### Track 5: Data Privacy & Compliance
**Sub-Moderator:** Data Privacy & Information Security

| Participant | Focus |
|------------|-------|
| Compliance Officer | SOC 2 Type II, GDPR/privacy, NIST 800-53 control families |
| Security Auditor | Data classification, access controls, audit trail completeness |

> **Shared perspectives:** Red Team Engineer, Blue Team Engineer, Purple Team Engineer, MITRE Analyst, Security Auditor, Infrastructure Engineer, Compliance Officer, and Systems Architect are defined in [`shared-perspectives.md`](../shared-perspectives.md).

---

## Process

### Phase 1: Parallel Analysis
All 5 tracks execute simultaneously. Each sub-moderator coordinates their participants to produce track-specific findings.

### Phase 2: Per-Track Aggregation
Each sub-moderator consolidates their track's findings, resolves contradictions, and produces a track summary.

### Phase 3: Overall Moderator Integration
The overall moderator (you) integrates all 5 track summaries into a unified threat model, cross-referencing findings and eliminating duplicates.

### Phase 4: Hardening Rounds
Iterate on findings where tracks disagree or where additional analysis is needed. Red Team challenges Blue Team detections. Purple Team validates coverage claims.

### Phase 5: Final Report Assembly
Assemble the 15-section output with all Mermaid diagrams, CVSS scores, and Sigma rules.

---

## Required Output Template

Your output **MUST** follow this exact 15-section template structure. Use `N/A — [reason]` for non-applicable sections rather than omitting them. Every section must be present in the final output.

````markdown
# System Threat Model — [System/Platform Name]

**Panel:** threat-model-system v1.0.0
**Date:** [ISO 8601 date, e.g., 2026-02-26T14:30:00Z]
**Policy Profile:** [active policy profile name, e.g., default, fin_pii_high]
**Repository:** [owner/repo]
**Scope:** [Full system | Subsystem name | Component name]
**Triggered by:** [manual | scheduled | incident_response]

---

## 1. Systems Architect: Architecture Presentation

### 1.1 Component Inventory

| Component | Type | Technology | Exposure | Data Sensitivity | Trust Zone |
|-----------|------|------------|----------|-----------------|------------|
| [Component name] | [Service/Database/Queue/Gateway/etc.] | [Tech stack] | [External/Internal/Restricted] | [Public/Internal/Confidential/Restricted] | [Zone name] |

### 1.2 Data Flow Diagram

```mermaid
graph TD
    subgraph "Trust Zone: External"
        A["Internet Users"]
    end
    subgraph "Trust Zone: DMZ"
        B["Load Balancer / WAF"]
        C["API Gateway"]
    end
    subgraph "Trust Zone: Application"
        D["Application Services"]
        E["Background Workers"]
    end
    subgraph "Trust Zone: Data"
        F["Primary Database"]
        G["Cache Layer"]
        H["Object Storage"]
    end
    subgraph "Trust Zone: Management"
        I["CI/CD Pipeline"]
        J["Monitoring Stack"]
    end

    A -->|"HTTPS (TLS 1.3)"| B
    B --> C
    C -->|"mTLS"| D
    D --> E
    D -->|"TLS"| F
    D -->|"TLS"| G
    D -->|"HTTPS"| H
    I -->|"SSH/HTTPS"| D
    D -->|"Metrics/Logs"| J
```

### 1.3 Trust Boundaries

| Boundary ID | Name | From Zone | To Zone | Protocol | Authentication | Authorization |
|-------------|------|-----------|---------|----------|----------------|---------------|
| TB-01 | [Boundary name] | [Source zone] | [Dest zone] | [Protocol] | [Auth method] | [Authz method] |

### 1.4 External Dependencies

| Dependency | Type | Data Shared | SLA | Fallback |
|-----------|------|-------------|-----|----------|
| [Dependency name] | [SaaS/API/Library/CDN] | [Data types] | [Availability target] | [Fallback mechanism] |

### 1.5 Agentic System Specifics

> Include this section if the system uses AI agents, LLMs, or autonomous workflows. Otherwise: `N/A — System does not include agentic components.`

#### OWASP LLM Top 10 Assessment

| ID | Threat | Applicability | Current Controls | Risk |
|----|--------|---------------|-----------------|------|
| LLM01 | Prompt Injection | [Yes/No/Partial] | [Controls] | [Low/Medium/High/Critical] |
| LLM02 | Insecure Output Handling | [Yes/No/Partial] | [Controls] | [Low/Medium/High/Critical] |
| LLM03 | Training Data Poisoning | [Yes/No/Partial] | [Controls] | [Low/Medium/High/Critical] |
| LLM04 | Model Denial of Service | [Yes/No/Partial] | [Controls] | [Low/Medium/High/Critical] |
| LLM05 | Supply Chain Vulnerabilities | [Yes/No/Partial] | [Controls] | [Low/Medium/High/Critical] |
| LLM06 | Sensitive Information Disclosure | [Yes/No/Partial] | [Controls] | [Low/Medium/High/Critical] |
| LLM07 | Insecure Plugin Design | [Yes/No/Partial] | [Controls] | [Low/Medium/High/Critical] |
| LLM08 | Excessive Agency | [Yes/No/Partial] | [Controls] | [Low/Medium/High/Critical] |
| LLM09 | Overreliance | [Yes/No/Partial] | [Controls] | [Low/Medium/High/Critical] |
| LLM10 | Model Theft | [Yes/No/Partial] | [Controls] | [Low/Medium/High/Critical] |

#### Agent-Specific Threat Surface

| Dimension | Current State | Risk Assessment |
|-----------|--------------|-----------------|
| Agent transport | [HTTP/WebSocket/Stdin/etc.] | [Assessment] |
| Agent authentication | [Method] | [Assessment] |
| Tool count | [N tools available] | [Assessment] |
| Tool authorization | [Per-tool/Blanket/None] | [Assessment] |
| Prompt source | [Hardcoded/User/Dynamic/Mixed] | [Assessment] |
| Context integrity | [Signed/Unsigned/Verified] | [Assessment] |
| Agent privilege level | [Least privilege/Elevated/Admin] | [Assessment] |
| Credential exposure | [In-context/Env/Vault/None] | [Assessment] |
| Audit logging | [Full/Partial/None] | [Assessment] |

#### Agent-Specific Threats

| Threat | Description | Likelihood | Impact | Current Mitigation |
|--------|-------------|------------|--------|-------------------|
| Scope escape | Agent performs actions outside intended boundaries | [L/M/H] | [L/M/H/C] | [Controls] |
| Hallucination exploitation | Attacker leverages model hallucination to trigger unintended actions | [L/M/H] | [L/M/H/C] | [Controls] |
| Context exhaustion | Adversarial input fills context window, displacing safety instructions | [L/M/H] | [L/M/H/C] | [Controls] |
| Multi-agent error amplification | Error in one agent cascades through agent chain | [L/M/H] | [L/M/H/C] | [Controls] |
| Decision deniability | Agent actions lack attribution or audit trail | [L/M/H] | [L/M/H/C] | [Controls] |
| Prompt injection via tools | Tool output contains adversarial instructions | [L/M/H] | [L/M/H/C] | [Controls] |
| Credential leakage via context | Secrets in agent context exposed through output | [L/M/H] | [L/M/H/C] | [Controls] |

---

## 2. MITRE Analyst: Trust Boundary Crossings

### Crossing Inventory

| Crossing ID | Boundary | Source | Destination | Data Types | Sensitivity | Existing Protections |
|-------------|----------|--------|-------------|------------|-------------|---------------------|
| TBC-01 | TB-01 | [Source component] | [Dest component] | [Data types] | [Classification] | [TLS, auth, validation, etc.] |

### Per-Crossing Analysis

#### TBC-01: [Crossing Name]

- **Boundary:** TB-01 ([boundary description])
- **Data in transit:** [What data crosses this boundary]
- **Current protections:** [Encryption, authentication, authorization, validation]
- **Gaps identified:** [Missing protections or weaknesses]
- **Applicable ATT&CK techniques:** [Txxxx — Name for each applicable technique]

---

## 3. MITRE Analyst: STRIDE Threat Catalog

### Per-Boundary STRIDE Analysis

#### TB-01: [Boundary Name]

| STRIDE Category | Threat Description | ATT&CK Technique | Likelihood | Impact | Risk | Existing Controls |
|----------------|-------------------|-------------------|------------|--------|------|-------------------|
| **S**poofing | [How identity could be forged at this boundary] | [Txxxx] | [L/M/H] | [L/M/H/C] | [L/M/H/C] | [Controls] |
| **T**ampering | [How data could be modified in transit/at rest] | [Txxxx] | [L/M/H] | [L/M/H/C] | [L/M/H/C] | [Controls] |
| **R**epudiation | [How actions could be denied without evidence] | [Txxxx] | [L/M/H] | [L/M/H/C] | [L/M/H/C] | [Controls] |
| **I**nformation Disclosure | [How data could leak across this boundary] | [Txxxx] | [L/M/H] | [L/M/H/C] | [L/M/H/C] | [Controls] |
| **D**enial of Service | [How availability could be disrupted] | [Txxxx] | [L/M/H] | [L/M/H/C] | [L/M/H/C] | [Controls] |
| **E**levation of Privilege | [How privileges could be escalated] | [Txxxx] | [L/M/H] | [L/M/H/C] | [L/M/H/C] | [Controls] |

[Repeat for each trust boundary: TB-02, TB-03, ...]

### STRIDE Summary

| STRIDE Category | Total Threats | Critical/High | Medium | Low |
|----------------|---------------|---------------|--------|-----|
| Spoofing | [n] | [n] | [n] | [n] |
| Tampering | [n] | [n] | [n] | [n] |
| Repudiation | [n] | [n] | [n] | [n] |
| Information Disclosure | [n] | [n] | [n] | [n] |
| Denial of Service | [n] | [n] | [n] | [n] |
| Elevation of Privilege | [n] | [n] | [n] | [n] |

---

## 4. Red Team Engineer: Attack Path Validation

### ATK-01: [Attack Path Name]

- **Objective:** [What the attacker aims to achieve]
- **Prerequisites:** [Required access, knowledge, or tooling]
- **ATT&CK Techniques:** [Txxxx → Tyyyy → Tzzzz (chain)]
- **Steps:**
  1. [Step description with technique mapping]
  2. [Step description with technique mapping]
  3. [Step description with technique mapping]
- **Lateral Movement:** [How attacker moves from initial foothold to objective]
- **Impact:** [Confidentiality/Integrity/Availability impact and scope]
- **Likelihood:** [Low/Medium/High with justification]
- **Feasibility:** [Tooling availability, skill level required, time estimate]
- **Current Detection:** [What would detect this attack path]
- **Detection Gaps:** [What would NOT be detected]

### ATK-02: [Attack Path Name]
[Same structure as above]

### ATK-03: [Attack Path Name]
[Same structure as above]

[Continue for all identified attack paths]

### Attack Path Summary

| ID | Name | Techniques | Likelihood | Impact | Feasibility | Detection Coverage |
|----|------|-----------|------------|--------|-------------|-------------------|
| ATK-01 | [Name] | [Technique chain] | [L/M/H] | [L/M/H/C] | [L/M/H] | [Full/Partial/None] |

---

## 5. Infrastructure Engineer: Configuration Assessment

### INFRA-01: [Configuration Finding]

- **Component:** [Affected component]
- **Current State:** [What is configured today]
- **Risk:** [What could go wrong]
- **Severity:** [Critical/High/Medium/Low/Info]
- **Recommendation:** [Specific remediation action]
- **Evidence:** [File path, configuration snippet, or reference]

### INFRA-02: [Configuration Finding]
[Same structure as above]

[Continue for all infrastructure findings]

### Infrastructure Assessment Summary

| ID | Component | Risk | Severity | Remediation Effort |
|----|-----------|------|----------|-------------------|
| INFRA-01 | [Component] | [Risk summary] | [Severity] | [Low/Medium/High] |

---

## 6. Blue Team Engineer: Detection & Response Coverage

### Detection Coverage Matrix

| ATT&CK Technique | Tactic | Detection Source | Detection Rule | Confidence | Alert Priority |
|-------------------|--------|-----------------|----------------|------------|----------------|
| [Txxxx — Name] | [Tactic] | [SIEM/EDR/Network/Application] | [Rule name or "None"] | [High/Medium/Low/None] | [P1/P2/P3/P4/None] |

### Alerting Gaps

| Gap ID | ATT&CK Technique | Gap Type | Impact | Remediation Priority |
|--------|-------------------|----------|--------|---------------------|
| GAP-01 | [Txxxx — Name] | [No detection / No response / Insufficient retention] | [Impact description] | [Immediate/Short-term/Medium-term] |

### Incident Response Assessment

| Dimension | Current State | Maturity | Gaps |
|-----------|--------------|----------|------|
| Runbooks | [Documented/Partial/None] | [1-5] | [Description] |
| Escalation paths | [Defined/Partial/None] | [1-5] | [Description] |
| Communication plan | [Tested/Documented/None] | [1-5] | [Description] |
| Evidence collection | [Automated/Manual/None] | [1-5] | [Description] |
| Recovery procedures | [Tested/Documented/None] | [1-5] | [Description] |
| Post-incident review | [Systematic/Ad-hoc/None] | [1-5] | [Description] |

### Detection Coverage Summary

| Metric | Value |
|--------|-------|
| Techniques with detection | [n] / [total] ([%]) |
| Techniques with prevention only | [n] |
| Techniques with no coverage | [n] |
| Mean detection confidence | [Low/Medium/High] |
| Alert-to-incident ratio | [Estimated ratio] |

---

## 7. Purple Team Engineer: MITRE ATT&CK Mapping

### Technique Coverage Matrix

| ATT&CK Technique | Tactic | Prevention | Detection | Validation Status | Priority |
|-------------------|--------|------------|-----------|-------------------|----------|
| [Txxxx — Name] | [Tactic] | [Control or None] | [Control or None] | [Validated/Untested/Failed] | [Critical/High/Medium/Low] |

### ATT&CK Heat Map

```mermaid
block-beta
    columns 11
    block:header:11
        title["MITRE ATT&CK Coverage Heat Map"]
    end
    IA["Initial\nAccess"] EX["Execution"] PE["Persistence"] PRV["Privilege\nEscalation"] DE["Defense\nEvasion"] CA["Credential\nAccess"] DI["Discovery"] LM["Lateral\nMovement"] CO["Collection"] EXF["Exfiltration"] IM["Impact"]

    style IA fill:#f44,color:#fff
    style EX fill:#f44,color:#fff
    style PE fill:#fa0,color:#fff
    style PRV fill:#fa0,color:#fff
    style DE fill:#f44,color:#fff
    style CA fill:#fa0,color:#fff
    style DI fill:#4a4,color:#fff
    style LM fill:#fa0,color:#fff
    style CO fill:#4a4,color:#fff
    style EXF fill:#4a4,color:#fff
    style IM fill:#f44,color:#fff
```

> Legend: 🟥 Red = <50% coverage, 🟧 Orange = 50-79% coverage, 🟩 Green = 80%+ coverage. Adjust colors per actual assessment.

### Coverage Summary

| Metric | Value |
|--------|-------|
| Total techniques assessed | [n] |
| Full coverage (prevention + detection) | [n] ([%]) |
| Prevention only | [n] ([%]) |
| Detection only | [n] ([%]) |
| No coverage | [n] ([%]) |
| Validated through emulation | [n] ([%]) |

---

## 8. Security Auditor: Vulnerability Classification

### VULN-01: [Vulnerability Title]

- **CVSS 3.1 Vector:** `CVSS:3.1/AV:[N/A/L/P]/AC:[L/H]/PR:[N/L/H]/UI:[N/R]/S:[U/C]/C:[N/L/H]/I:[N/L/H]/A:[N/L/H]`
- **CVSS Score:** [0.0-10.0] ([Critical/High/Medium/Low/None])
- **CWE:** CWE-[number] — [CWE Name]
- **OWASP Category:** [OWASP Top 10 category, e.g., A01:2021-Broken Access Control]
- **Component:** [Affected component and file/config reference]
- **Description:** [Detailed vulnerability description with evidence]
- **Exploitation Scenario:** [How this vulnerability could be exploited]
- **Remediation:** [Specific fix with code/config guidance]
- **Remediation Effort:** [Low/Medium/High]

### VULN-02: [Vulnerability Title]
[Same structure as above]

[Continue for all vulnerabilities]

### Vulnerability Summary

| Severity | Count | CVSS Range |
|----------|-------|------------|
| Critical (9.0-10.0) | [n] | [range] |
| High (7.0-8.9) | [n] | [range] |
| Medium (4.0-6.9) | [n] | [range] |
| Low (0.1-3.9) | [n] | [range] |
| Info (0.0) | [n] | N/A |

---

## 9. MITRE Analyst: Threat Actor Profiles

### Threat Actor 1: [Actor Name/Category]

- **Type:** [Nation-state / Organized crime / Hacktivist / Insider / Opportunistic / Automated]
- **Motivation:** [Financial / Espionage / Disruption / Ideology / Revenge / Curiosity]
- **Capability Level:** [Sophisticated / Moderate / Basic]
- **Relevant TTPs:**
  - [Txxxx — Technique Name]: [How this actor uses this technique]
  - [Tyyyy — Technique Name]: [How this actor uses this technique]
- **Target Assets:** [What this actor would target in this system]
- **Attack Scenario:** [Narrative describing a realistic attack by this actor]
- **Likelihood:** [Low/Medium/High — based on system exposure and actor motivation]

### Threat Actor 2: [Actor Name/Category]
[Same structure as above]

[Continue for all relevant threat actors]

---

## 10. MITRE Analyst: Attack Trees

### Attack Tree 1: [Objective — e.g., "Exfiltrate Customer Data"]

```mermaid
graph TD
    ROOT["Exfiltrate Customer Data<br/>(OR)"] --> PATH_A["Exploit Application Vulnerability<br/>(AND)"]
    ROOT --> PATH_B["Compromise Insider Account<br/>(AND)"]
    ROOT --> PATH_C["Supply Chain Attack<br/>(AND)"]

    PATH_A --> A1["Discover Injection Point<br/>T1190"]
    PATH_A --> A2["Escalate Privileges<br/>T1068"]
    PATH_A --> A3["Access Database<br/>T1213"]

    PATH_B --> B1["Phishing Campaign<br/>T1566"]
    PATH_B --> B2["Credential Harvesting<br/>T1078"]
    PATH_B --> B3["Lateral Movement<br/>T1021"]

    PATH_C --> C1["Compromise Dependency<br/>T1195"]
    PATH_C --> C2["Inject Malicious Code<br/>T1059"]
    PATH_C --> C3["Establish Persistence<br/>T1546"]

    style ROOT fill:#c00,color:#fff
    style PATH_A fill:#f60,color:#fff
    style PATH_B fill:#f60,color:#fff
    style PATH_C fill:#f60,color:#fff
```

> **OR** nodes: attacker needs to succeed on ANY child path.
> **AND** nodes: attacker must succeed on ALL child steps.

### Attack Tree 2: [Objective]
[Same structure — Mermaid graph with OR/AND decomposition]

[Continue for all major attack objectives]

---

## 11. Compliance Officer: Regulatory Impact

### SOC 2 Type II

| Trust Service Criteria | Control | Status | Gap | Remediation |
|-----------------------|---------|--------|-----|-------------|
| CC6.1 — Logical access security | [Control description] | [Met/Partial/Not Met] | [Gap description] | [Remediation] |
| CC6.2 — System credentials | [Control description] | [Met/Partial/Not Met] | [Gap description] | [Remediation] |
| CC6.3 — System boundaries | [Control description] | [Met/Partial/Not Met] | [Gap description] | [Remediation] |
| CC7.1 — Change detection | [Control description] | [Met/Partial/Not Met] | [Gap description] | [Remediation] |
| CC7.2 — Anomaly monitoring | [Control description] | [Met/Partial/Not Met] | [Gap description] | [Remediation] |

### GDPR / Privacy

| Requirement | Applicability | Status | Evidence | Gap |
|-------------|--------------|--------|----------|-----|
| Art. 5 — Data minimization | [Yes/No] | [Compliant/Partial/Non-compliant] | [Evidence] | [Gap] |
| Art. 25 — Privacy by design | [Yes/No] | [Compliant/Partial/Non-compliant] | [Evidence] | [Gap] |
| Art. 32 — Security of processing | [Yes/No] | [Compliant/Partial/Non-compliant] | [Evidence] | [Gap] |
| Art. 33 — Breach notification | [Yes/No] | [Compliant/Partial/Non-compliant] | [Evidence] | [Gap] |
| Art. 35 — DPIA requirement | [Yes/No] | [Compliant/Partial/Non-compliant] | [Evidence] | [Gap] |

### NIST 800-53 Control Families

| Family | Controls Assessed | Met | Partial | Not Met | Priority Gaps |
|--------|-------------------|-----|---------|---------|---------------|
| AC — Access Control | [n] | [n] | [n] | [n] | [Gap summary] |
| AU — Audit & Accountability | [n] | [n] | [n] | [n] | [Gap summary] |
| CA — Assessment & Authorization | [n] | [n] | [n] | [n] | [Gap summary] |
| CM — Configuration Management | [n] | [n] | [n] | [n] | [Gap summary] |
| IA — Identification & Authentication | [n] | [n] | [n] | [n] | [Gap summary] |
| IR — Incident Response | [n] | [n] | [n] | [n] | [Gap summary] |
| SC — System & Communications Protection | [n] | [n] | [n] | [n] | [Gap summary] |
| SI — System & Information Integrity | [n] | [n] | [n] | [n] | [Gap summary] |

---

## 12. Prioritized Threat Register

| Rank | ID | Title | CVSS | ATT&CK | STRIDE | Component | Status | Cross-Ref |
|------|----|-------|------|--------|--------|-----------|--------|-----------|
| 1 | VULN-XX | [Title] | [Score] | [Txxxx] | [S/T/R/I/D/E] | [Component] | [Open/Mitigated/Accepted] | ATK-XX, INFRA-XX |
| 2 | VULN-XX | [Title] | [Score] | [Txxxx] | [S/T/R/I/D/E] | [Component] | [Open/Mitigated/Accepted] | ATK-XX, GAP-XX |

[Continue for all findings, ranked by CVSS score descending]

---

## 13. Mitigation Roadmap

### Phased Remediation Plan

#### Immediate (0-7 days) — Critical/High Findings

| Priority | Finding | Remediation | Owner | Effort | Dependency |
|----------|---------|-------------|-------|--------|------------|
| P0 | [Finding ref] | [Action] | [Team/Role] | [Hours/Days] | [Dependencies] |

#### Short-term (1-4 weeks) — Medium Findings

| Priority | Finding | Remediation | Owner | Effort | Dependency |
|----------|---------|-------------|-------|--------|------------|
| P1 | [Finding ref] | [Action] | [Team/Role] | [Hours/Days] | [Dependencies] |

#### Medium-term (1-3 months) — Low Findings + Detection Improvements

| Priority | Finding | Remediation | Owner | Effort | Dependency |
|----------|---------|-------------|-------|--------|------------|
| P2 | [Finding ref] | [Action] | [Team/Role] | [Hours/Days] | [Dependencies] |

#### Long-term (3-6 months) — Architectural Improvements

| Priority | Finding | Remediation | Owner | Effort | Dependency |
|----------|---------|-------------|-------|--------|------------|
| P3 | [Finding ref] | [Action] | [Team/Role] | [Hours/Days] | [Dependencies] |

### Roadmap Timeline

```mermaid
gantt
    title Threat Mitigation Roadmap
    dateFormat  YYYY-MM-DD
    section Immediate (P0)
        Critical fix 1     :crit, p0_1, 2026-02-26, 3d
        Critical fix 2     :crit, p0_2, 2026-02-26, 5d
    section Short-term (P1)
        Medium fix 1       :p1_1, after p0_1, 7d
        Medium fix 2       :p1_2, after p0_2, 10d
    section Medium-term (P2)
        Detection improvement 1  :p2_1, after p1_1, 14d
        Detection improvement 2  :p2_2, after p1_2, 21d
    section Long-term (P3)
        Architecture change 1    :p3_1, after p2_1, 30d
```

---

## 14. Residual Risk Summary

### Risk Matrix — Before and After Mitigation

| Finding | Before (Likelihood x Impact) | After Immediate | After Short-term | After Medium-term | After Long-term |
|---------|------------------------------|-----------------|------------------|-------------------|-----------------|
| VULN-01 | [H x C = Critical] | [M x C = High] | [L x C = Medium] | [L x M = Low] | [L x L = Low] |
| VULN-02 | [M x H = High] | [M x H = High] | [L x H = Medium] | [L x M = Low] | [L x L = Low] |

### Accepted Risks

| Finding | Residual Risk | Justification | Review Date | Owner |
|---------|---------------|---------------|-------------|-------|
| [Finding ref] | [Risk level] | [Why this risk is acceptable] | [Next review date] | [Risk owner] |

### Risk Trend

| Phase | Critical | High | Medium | Low | Total Risk Score |
|-------|----------|------|--------|-----|-----------------|
| Current | [n] | [n] | [n] | [n] | [Weighted score] |
| After Immediate | [n] | [n] | [n] | [n] | [Weighted score] |
| After Short-term | [n] | [n] | [n] | [n] | [Weighted score] |
| After Medium-term | [n] | [n] | [n] | [n] | [Weighted score] |
| After Long-term | [n] | [n] | [n] | [n] | [Weighted score] |

---

## 15. Threat Posture Assessment

### Overall Verdict

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Confidence score | [0.XX] | >= 0.75 | [PASS/FAIL] |
| Critical findings | [n] | 0 | [PASS/FAIL] |
| High findings | [n] | 0 | [PASS/FAIL] |
| Aggregate verdict | [approve/request_changes] | approve | [PASS/FAIL] |
| Compliance score | [0.XX] | >= 0.85 | [PASS/FAIL] |
| ATT&CK coverage | [XX%] | >= 70% | [PASS/FAIL] |
| Detection coverage | [XX%] | >= 60% | [PASS/FAIL] |

### Executive Summary

[2-3 paragraph summary of the overall threat posture, key findings, most critical risks, and recommended priorities. Written for a non-technical audience.]

### Confidence Assessment

[Assessment of the threat model's completeness and confidence. What was well-analyzed? What areas need further investigation? What assumptions were made?]

### Next Review

- **Recommended review frequency:** [Quarterly / After major changes / After incidents]
- **Trigger conditions for re-assessment:** [New external-facing surface, architecture change, incident, regulatory change]
- **Areas requiring deeper analysis:** [List any areas that need specialized assessment]

---

## Appendix A: STRIDE Risk Heat Map

```mermaid
quadrantChart
    title STRIDE Risk Distribution
    x-axis Low Likelihood --> High Likelihood
    y-axis Low Impact --> High Impact
    quadrant-1 "Critical Risk"
    quadrant-2 "Monitor"
    quadrant-3 "Accept"
    quadrant-4 "Mitigate"
    "Spoofing": [0.5, 0.6]
    "Tampering": [0.4, 0.7]
    "Repudiation": [0.3, 0.4]
    "Info Disclosure": [0.6, 0.8]
    "Denial of Service": [0.5, 0.5]
    "Elevation of Privilege": [0.4, 0.9]
```

> Adjust coordinates based on actual assessment. Each point represents the aggregate risk for that STRIDE category.

---

## Appendix B: Sigma Detection Rules

### Rule 1: [Detection Name]

```yaml
title: [Detection name]
id: [UUID]
status: experimental
description: [What this rule detects]
author: threat-model-system
date: [YYYY-MM-DD]
references:
  - [ATT&CK technique URL]
logsource:
  category: [Category]
  product: [Product]
detection:
  selection:
    [field]: [value]
  condition: selection
falsepositives:
  - [Known false positive scenarios]
level: [critical/high/medium/low/informational]
tags:
  - attack.[tactic]
  - attack.t[xxxx]
```

### Rule 2: [Detection Name]
[Same structure as above]

[Continue for all recommended Sigma rules]

---

## Appendix C: Purple Team Validation Exercises

| Exercise | ATT&CK Technique | Procedure | Expected Detection | Success Criteria | Status |
|----------|-------------------|-----------|-------------------|------------------|--------|
| PTV-01 | [Txxxx — Name] | [Step-by-step procedure] | [Expected alert/log] | [What constitutes successful detection] | [Planned/Executed/Passed/Failed] |
| PTV-02 | [Txxxx — Name] | [Step-by-step procedure] | [Expected alert/log] | [What constitutes successful detection] | [Planned/Executed/Passed/Failed] |
````

---

## Scoring

Confidence score calculation:

| Parameter | Value |
|-----------|-------|
| Base confidence | 0.90 |
| Per critical finding | -0.30 |
| Per high finding | -0.20 |
| Per medium finding | -0.05 |
| Per low finding | -0.01 |
| Floor | 0.0 |

**Formula:** `confidence = max(0.0, 0.90 - (critical * 0.30) - (high * 0.20) - (medium * 0.05) - (low * 0.01))`

## Pass/Fail Criteria

| Criterion | Threshold |
|-----------|-----------|
| Confidence score | >= 0.75 |
| Critical findings | 0 |
| High findings | 0 |
| Aggregate verdict | `approve` |
| Compliance score | >= 0.85 |

If **any** criterion fails, the aggregate verdict must be `request_changes`. Critical or high findings indicate unresolved security concerns requiring remediation.

## Data Sensitivity and Redaction

When producing threat model findings, apply these redaction rules:

1. **Never include raw secrets** — API keys, tokens, passwords, or credentials discovered during analysis must be redacted. Use `[REDACTED]` placeholder and describe the type of secret (e.g., "AWS access key found in config.py:42")
2. **Redact PII** — Personal identifiable information (emails, names, addresses, SSNs) must be replaced with `[PII-REDACTED]`
3. **Sanitize file paths** — If file paths reveal infrastructure details (server names, internal network paths), generalize them
4. **Describe attack techniques generically** — Reference ATT&CK technique IDs and describe attack vectors at a conceptual level. Do not include working exploit code, payloads, or step-by-step exploitation instructions in the emission
5. **Threat scenarios over exploit recipes** — Threat models should describe *what* an attacker could achieve and *why* it matters, not provide a cookbook for reproducing the attack
6. **Set data_classification** — Include the `data_classification` block in your structured emission:
   - `"public"` — No sensitive content in findings
   - `"internal"` — Contains internal file paths, architecture details
   - `"confidential"` — Contains vulnerability evidence, security configurations, ATT&CK mappings with specific system details
   - `"restricted"` — Contains credential exposure evidence, PII findings, or detailed kill chain analysis of production systems

---

## Structured Emission

All output must include a JSON block between emission markers, validated against [`governance/schemas/panel-output.schema.json`](../../schemas/panel-output.schema.json).

Wrap the JSON in these markers:

```
<!-- STRUCTURED_EMISSION_START -->
{ ... }
<!-- STRUCTURED_EMISSION_END -->
```

### Example Emission

<!-- STRUCTURED_EMISSION_START -->
```json
{
  "panel_name": "threat-model-system",
  "panel_version": "1.0.0",
  "confidence_score": 0.80,
  "risk_level": "medium",
  "compliance_score": 0.85,
  "policy_flags": [],
  "requires_human_review": false,
  "timestamp": "2026-02-26T14:30:00Z",
  "findings": [
    {
      "persona": "architecture/systems-architect",
      "verdict": "approve",
      "confidence": 0.85,
      "rationale": "Architecture documented with 5 trust zones, 8 trust boundaries, 3 external dependencies. Data flow diagrams complete.",
      "findings_count": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 2}
    },
    {
      "persona": "compliance/mitre-analyst",
      "verdict": "approve",
      "confidence": 0.80,
      "rationale": "12 trust boundary crossings cataloged. STRIDE analysis complete for all boundaries. 3 threat actor profiles with relevant TTPs. Attack trees constructed for 2 primary objectives.",
      "findings_count": {"critical": 0, "high": 0, "medium": 2, "low": 3, "info": 0}
    },
    {
      "persona": "security/red-team-engineer",
      "verdict": "approve",
      "confidence": 0.80,
      "rationale": "5 attack paths validated. 2 paths rated high feasibility but existing controls reduce risk to medium. No unmitigated critical paths.",
      "findings_count": {"critical": 0, "high": 0, "medium": 2, "low": 1, "info": 0}
    },
    {
      "persona": "operations/infrastructure-engineer",
      "verdict": "approve",
      "confidence": 0.85,
      "rationale": "Infrastructure configuration assessed. IAM follows least privilege. Network segmentation adequate. 2 medium findings for encryption configuration.",
      "findings_count": {"critical": 0, "high": 0, "medium": 2, "low": 0, "info": 0}
    },
    {
      "persona": "security/blue-team-engineer",
      "verdict": "approve",
      "confidence": 0.75,
      "rationale": "Detection coverage at 72% of assessed techniques. 3 alerting gaps identified for lateral movement techniques. Incident response runbooks need update.",
      "findings_count": {"critical": 0, "high": 0, "medium": 3, "low": 1, "info": 0}
    },
    {
      "persona": "security/purple-team-engineer",
      "verdict": "approve",
      "confidence": 0.78,
      "rationale": "ATT&CK heat map generated. 68% full coverage, 15% prevention only, 12% detection only, 5% no coverage. 4 validation exercises designed.",
      "findings_count": {"critical": 0, "high": 0, "medium": 1, "low": 2, "info": 0}
    },
    {
      "persona": "compliance/security-auditor",
      "verdict": "approve",
      "confidence": 0.85,
      "rationale": "8 vulnerabilities classified with CVSS scoring. No critical or high severity. All medium findings have documented remediation paths.",
      "findings_count": {"critical": 0, "high": 0, "medium": 3, "low": 3, "info": 2}
    },
    {
      "persona": "compliance/compliance-officer",
      "verdict": "approve",
      "confidence": 0.82,
      "rationale": "SOC 2 Type II controls assessed — 2 partial gaps in CC6.3. GDPR Art. 32 controls adequate. NIST 800-53 control family assessment complete.",
      "findings_count": {"critical": 0, "high": 0, "medium": 2, "low": 0, "info": 1}
    }
  ],
  "aggregate_verdict": "approve",
  "data_classification": {
    "level": "confidential",
    "contains_sensitive_evidence": false,
    "redaction_applied": false
  }
}
```
<!-- STRUCTURED_EMISSION_END -->

## Constraints

- **Every threat must reference a specific ATT&CK technique** — Generic threat descriptions without ATT&CK mapping are incomplete. Use technique IDs (e.g., T1190, T1078) and full names.
- **STRIDE analysis is per trust boundary** — Do not perform a single global STRIDE analysis. Each trust boundary must have its own STRIDE table.
- **Attack trees use OR/AND decomposition** — OR = attacker needs any one child path; AND = attacker needs all child steps. Label nodes clearly.
- **CVSS vectors must be complete** — Use the full CVSS 3.1 vector string. Do not estimate scores without the vector.
- **Sigma rules must be syntactically valid** — Use correct Sigma YAML structure with logsource, detection, and tags.
- **Mermaid diagrams must render** — Test diagram syntax. Use quoted strings for labels with special characters.
- **Distinguish prevention vs detection controls** — A threat with prevention but no detection is a blind spot.
- **Use `N/A — [reason]` for non-applicable sections** — Never omit a section from the template.
- **Treat the threat model as a living document** — Note what should be re-evaluated when the system changes.
