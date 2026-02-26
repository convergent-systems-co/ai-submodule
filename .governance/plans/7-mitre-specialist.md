# MITRE Specialist and Threat Modeling Panel

**Author:** Code Manager (agentic)
**Date:** 2026-02-20
**Status:** approved
**Issue:** https://github.com/SET-Apps/ai-submodule/issues/7
**Branch:** itsfwcp/7-mitre-specialist

---

## 1. Objective

Add a MITRE Specialist persona and a Threat Modeling panel that coordinates threat analysis using MITRE ATT&CK, STRIDE, and attack tree methodologies.

## 2. Rationale

The existing Security Auditor focuses on code-level vulnerabilities (OWASP, injection, auth). The Adversarial Reviewer stress-tests designs for hidden assumptions. Neither systematically maps threats to MITRE ATT&CK techniques or produces structured threat models. A dedicated MITRE Specialist fills this gap.

The Threat Modeling panel is distinct from the existing Security Review panel — Security Review is a broad security assessment, while Threat Modeling specifically produces attack surface maps, threat matrices, and kill chain analysis.

## 3. Scope

### Files to Create

| File | Purpose |
|------|---------|
| `personas/compliance/mitre-specialist.md` | MITRE ATT&CK threat analysis persona |
| `personas/panels/threat-modeling.md` | Threat modeling review panel |

### Files to Modify

| File | Change Description |
|------|-------------------|
| `personas/index.md` | Add MITRE Specialist to Compliance, add Threat Modeling to Panels |

## 4. Approach

1. Create `compliance/mitre-specialist.md` — evaluates for ATT&CK technique coverage, kill chains, detection gaps
2. Create `panels/threat-modeling.md` — coordinates MITRE Specialist, Security Auditor, Infrastructure Engineer, Adversarial Reviewer, and Architect
3. Update index.md

## 5. Testing Strategy

Manual verification of format consistency.

## 6. Risk Assessment

None significant — additive change.

## 7. Dependencies

None.
