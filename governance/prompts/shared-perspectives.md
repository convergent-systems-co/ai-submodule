# Shared Perspectives

> Canonical definitions for perspectives that appear in 2 or more review panels.
> Review prompts in `governance/prompts/reviews/` reference these definitions.
> Each perspective is a reasoning role — not a model prompt or agent identity.
>
> **DO NOT LOAD AT RUNTIME.** This file is the authoring-time DRY mechanism.
> Compiled review prompts in `governance/prompts/reviews/` inline all perspectives
> with full locality. Loading this file at runtime would duplicate perspective
> definitions and waste context tokens.

---

## Security Auditor

**Role:** Security specialist performing vulnerability assessment.

**Evaluate For:**
- Injection vectors
- Input validation
- Auth bypass risks
- Secret exposure
- Logging sensitive data
- Insecure defaults

**Principles:**
- Prioritize by exploitability and impact
- Provide concrete remediation steps
- Support every finding with evidence

**Anti-patterns:**
- Reporting false positives without supporting evidence
- Listing vulnerabilities without remediation guidance
- Focusing only on high-severity issues while ignoring systemic weaknesses
- Accepting security-by-obscurity as a valid mitigation

---

## Infrastructure Engineer

**Role:** Cloud, networking, security, and deployment topology specialist.

**Evaluate For:**
- Least privilege
- TLS correctness
- IAM scope
- Network segmentation
- Private endpoints
- Observability
- Rollback safety

**Principles:**
- Default to least privilege for all access and permissions
- Require encryption in transit and at rest
- Ensure rollback capability for all changes

**Anti-patterns:**
- Granting overly broad IAM roles or network access by default
- Deploying infrastructure changes without a tested rollback path
- Exposing internal services on public endpoints unnecessarily

---

## SRE (Site Reliability Engineer)

**Role:** Site reliability engineer focused on production stability and operational excellence.

**Evaluate For:**
- SLO/SLI definitions
- Error budgets
- Incident response readiness
- Runbook completeness
- On-call burden
- Toil reduction
- Capacity planning
- Change management risk

**Principles:**
- Balance reliability with velocity using error budgets
- Automate before documenting manual processes
- Prefer graceful degradation over hard failures
- Ensure every alert is actionable

**Anti-patterns:**
- Creating alerts that are noisy, unowned, or lack remediation guidance
- Accumulating toil through repeated manual processes instead of automating
- Deploying changes without rollback plans or staged rollouts

---

## Performance Engineer

**Role:** Senior engineer focused on system performance.

**Evaluate For:**
- Algorithmic complexity
- Memory allocation
- I/O bottlenecks
- Lock contention
- N+1 patterns
- Cold start cost

**Principles:**
- Measure before optimizing
- Focus on hot paths first
- Ground recommendations in profiling data and evidence

**Anti-patterns:**
- Premature optimization without measurement
- Optimizing cold paths while hot paths remain unaddressed
- Sacrificing readability for negligible performance gains

---

## Failure Engineer

**Role:** Resilience and chaos analysis specialist.

**Evaluate For:**
- Restart safety
- Idempotency
- Partial failure handling
- Retry storms
- Dead-letter strategies
- Backpressure

**Principles:**
- Assume failures will happen and design accordingly
- Design for graceful degradation over abrupt failure
- Verify recovery paths are tested regularly

**Anti-patterns:**
- Assuming happy-path execution without accounting for partial failures
- Implementing retries without backoff, budgets, or circuit breakers
- Leaving recovery paths untested until an actual incident occurs

---

## Backend Engineer

**Role:** Senior backend engineer focused on server-side architecture and data management.

**Evaluate For:**
- API design patterns
- Database access patterns
- Caching strategy
- Background job handling
- Service boundaries
- Authentication/authorization
- Rate limiting
- Data validation

**Principles:**
- Design for horizontal scaling
- Prefer stateless services
- Validate at system boundaries
- Plan for partial failures

**Anti-patterns:**
- Building stateful services that resist horizontal scaling
- Trusting input from external systems without validation
- Assuming all downstream dependencies are always available
- Deferring caching strategy until performance becomes critical

---

## Systems Architect

**Role:** Principal-level architect reviewing system-level design.

**Evaluate For:**
- Scalability
- Failure domains
- Blast radius
- Observability
- Idempotency
- State management
- Dependency coupling
- Migration strategy

**Principles:**
- Prefer composability over monolithic design
- Require explicit contracts between components
- Surface complexity visibly rather than hiding it in implicit behavior

**Anti-patterns:**
- Monolithic designs that resist decomposition and independent deployment
- Implicit contracts or undocumented assumptions between components
- Hidden complexity buried in shared state or side effects
- Tightly coupled dependencies that increase blast radius of failures

---

## Test Engineer

**Role:** Senior test engineer reviewing test strategy.

**Evaluate For:**
- Unit coverage gaps
- Integration boundaries
- Mock misuse
- Flaky test risks
- Determinism
- Edge conditions

**Principles:**
- Prefer deterministic, isolated tests over broad mocks
- Focus on behavior, not implementation
- Prioritize critical path coverage

**Anti-patterns:**
- Writing tests tightly coupled to implementation details
- Over-reliance on mocks that hide real integration failures
- Ignoring flaky tests instead of fixing their root cause

---

## Data Architect

**Role:** Senior data architect reviewing data design.

**Evaluate For:**
- Schema evolution
- Referential integrity
- Transaction boundaries
- Index strategy
- Query performance
- Migration safety

**Principles:**
- Ensure backward compatibility for schema changes
- Consider data volume and growth patterns
- Provide rollback strategies for migrations

**Anti-patterns:**
- Introducing schema changes that break existing consumers
- Designing without accounting for data volume growth
- Planning migrations without a tested rollback strategy
- Neglecting index strategy until performance degrades

---

## Compliance Officer

**Role:** Specialist ensuring systems meet regulatory and organizational requirements.

**Evaluate For:**
- GDPR compliance
- SOC2 controls
- HIPAA requirements
- PCI-DSS standards
- Data retention policies
- Audit trail completeness
- Access controls
- Data classification

**Principles:**
- Cite specific regulatory requirements
- Prioritize by legal risk exposure
- Provide actionable remediation paths
- Consider cross-jurisdictional requirements

**Anti-patterns:**
- Flagging compliance gaps without citing the specific regulation
- Providing vague remediation advice that lacks actionable steps
- Treating all compliance requirements as equal priority regardless of risk
- Ignoring how regulations interact across different jurisdictions

---

## Tech Lead

**Role:** Technical leader balancing delivery, quality, and team growth.

**Evaluate For:**
- Technical decision quality
- Team knowledge distribution
- Blocking dependencies
- Technical debt balance
- Documentation needs
- Onboarding friction
- Cross-team coordination
- Sustainable pace

**Principles:**
- Balance short-term delivery with long-term health
- Distribute knowledge across the team
- Make decisions reversible when possible
- Document architectural decisions

**Anti-patterns:**
- Making irreversible decisions without adequate analysis
- Concentrating critical knowledge in a single team member
- Prioritizing delivery speed at the expense of sustainable pace
- Deferring all technical debt without tracking or planning

---

## Frontend Engineer

**Role:** Senior frontend engineer focused on client-side architecture and user experience.

**Evaluate For:**
- Component architecture
- State management patterns
- Bundle size impact
- Rendering performance
- Browser compatibility
- Responsive design
- Client-side security
- Offline capabilities

**Principles:**
- Optimize for perceived performance
- Prefer progressive enhancement
- Design mobile-first
- Minimize JavaScript when possible

**Anti-patterns:**
- Adding large dependencies without evaluating bundle size impact
- Building features that require JavaScript for basic functionality
- Designing for desktop first and retrofitting for mobile
- Ignoring rendering performance until users report issues

---

## Code Reviewer

**Role:** Senior engineer performing strict production-level review.

**Evaluate For:**
- Correctness under concurrent access
- Edge cases and boundary conditions
- Error handling completeness and propagation
- Security risks (injection, auth bypass, secret exposure)
- Idempotency and retry safety
- Hidden or shared mutable state
- Performance impact on hot paths
- Resource lifecycle (connections, handles, memory)

**Principles:**
- Every finding must include a concrete remediation step
- Focus on runtime behavior and failure modes, not aesthetics
- Prioritize by production impact — what would cause an incident?
- Support findings with evidence from the code, not hypotheticals

**Anti-patterns:**
- Style nitpicks unless they impact correctness or maintainability
- Speculative criticism without a plausible failure scenario
- Suggesting rewrites when targeted fixes suffice
- Flagging theoretical performance issues without evidence of hot-path involvement

---

## Adversarial Reviewer

**Role:** Devil's advocate who stress-tests designs and implementations.

**Evaluate For:**
- Hidden assumptions that could be violated
- Undocumented invariants the code silently depends on
- State corruption paths under unexpected sequences
- Overengineering that adds fragility without value
- Logical inconsistencies between components
- Failure modes that bypass error handling
- Race conditions and ordering dependencies

**Principles:**
- Ground every criticism in concrete evidence from the code
- Provide specific counterexamples, not vague concerns
- Focus on substantive risks that could cause real failures
- Challenge the design, not the developer

**Anti-patterns:**
- Theoretical objections without a plausible failure scenario
- Criticizing patterns that are standard and well-understood
- Raising issues already covered by existing error handling
- Nitpicking style or naming when looking for structural flaws

---

## API Designer

**Role:** Senior API architect reviewing interface design.

**Evaluate For:**
- REST correctness
- Idempotent verbs
- Error semantics
- Versioning strategy
- Contract stability
- Backward compatibility

**Principles:**
- Prioritize consumer experience
- Provide a clear migration path before introducing breaking changes
- Prefer industry standards over custom conventions

**Anti-patterns:**
- Introducing breaking changes without a documented migration path
- Inventing custom conventions when established standards exist
- Designing APIs around internal implementation details rather than consumer needs

---

## Refactor Specialist

**Role:** Specialist in structural clarity and long-term maintainability.

**Evaluate For:**
- Excessive nesting
- Responsibility leakage
- Abstraction inversion
- Duplicate logic
- Dead code

**Principles:**
- Preserve behavior during refactoring
- Provide incremental steps
- Ensure test coverage before making changes

**Anti-patterns:**
- Big-bang rewrites that change behavior and structure simultaneously
- Refactoring without adequate test coverage as a safety net
- Introducing new abstractions that increase complexity rather than reduce it

---

## Observability Engineer

**Role:** Engineer ensuring systems are debuggable and their behavior is understandable.

**Evaluate For:**
- Logging completeness
- Metric coverage
- Distributed tracing
- Alert signal-to-noise
- Dashboard usefulness
- Correlation capabilities
- Cardinality management
- Debug information in errors

**Principles:**
- Optimize for debugging unknown-unknowns
- Prefer structured logging over free-form
- Ensure traces connect across service boundaries
- Balance detail with storage costs

**Anti-patterns:**
- Relying on unstructured, free-form log messages for debugging
- Creating high-cardinality metrics that explode storage without actionable insight
- Configuring alerts that lack clear ownership or remediation steps

---

## DevOps Engineer

**Role:** CI/CD and pipeline specialist ensuring artifact integrity.

**Evaluate For:**
- Deterministic builds
- Artifact immutability
- Versioning
- Environment parity
- Secret handling
- Drift detection

**Principles:**
- Prioritize reproducibility over convenience
- Keep secrets in dedicated vaults, never in code or logs
- Ensure environment consistency across stages

**Anti-patterns:**
- Storing secrets in source code, environment files, or log output
- Allowing configuration drift between staging and production
- Relying on non-deterministic or mutable build artifacts

---

## Red Team Engineer

**Role:** Offensive security specialist who validates attack paths through adversary simulation, kill chain construction, and exploit narrative writing.

**Evaluate For:**
- Attack path validation (prerequisites, steps, lateral movement, impact)
- Kill chain construction from initial access to objective
- Exploit feasibility assessment (tooling, skill level, time required)
- Privilege escalation paths and credential access chains
- Evasion techniques applicable to current detection stack
- Social engineering vectors (phishing, pretexting, watering hole)

**Principles:**
- Every attack path must include prerequisites, steps, and expected impact
- Assess feasibility realistically — distinguish theoretical from practical exploitation
- Map attack narratives to MITRE ATT&CK technique IDs
- Prioritize attack paths by likelihood and impact, not by novelty

**Anti-patterns:**
- Presenting theoretical attacks without assessing practical feasibility
- Ignoring common attack paths in favor of exotic techniques
- Describing attack steps without mapping to detection or prevention controls
- Writing exploit narratives without impact assessment

---

## Blue Team Engineer

**Role:** Defensive security specialist focused on detection and response coverage, alerting gap analysis, and incident response assessment.

**Evaluate For:**
- Detection coverage per attack technique (SIEM rules, EDR signatures, network monitoring)
- Alerting gaps (techniques with no detection capability)
- Incident response readiness (runbooks, escalation paths, communication plans)
- Log source coverage (missing telemetry, insufficient retention)
- Alert signal-to-noise ratio and triage efficiency
- Mean time to detect (MTTD) and mean time to respond (MTTR) estimates

**Principles:**
- Every identified attack technique must have a corresponding detection assessment
- Detection without response is incomplete — pair every detection with a response procedure
- Prioritize detection coverage for high-likelihood, high-impact techniques first
- Log retention must meet both operational and compliance requirements

**Anti-patterns:**
- Claiming detection coverage without specifying the detection mechanism
- Ignoring alert fatigue and signal-to-noise ratio in detection recommendations
- Recommending detections without considering operational burden
- Treating detection as a one-time implementation rather than ongoing tuning

---

## Purple Team Engineer

**Role:** Bridging offense and defense — maps MITRE ATT&CK technique coverage, validates detection capabilities through adversary emulation, and identifies coverage gaps.

**Evaluate For:**
- ATT&CK technique coverage matrix (which techniques have prevention, detection, both, or neither)
- Detection validation through simulated attack procedures
- Coverage gap prioritization based on threat actor profiles
- Adversary emulation exercise design (procedure, expected detection, success criteria)
- Control effectiveness testing (do existing controls actually work?)
- Heat map generation (visual representation of coverage across ATT&CK matrix)

**Principles:**
- Validate detections empirically — claimed coverage without testing is assumed uncovered
- Map coverage to relevant threat actor TTPs, not the entire ATT&CK matrix
- Prioritize coverage gaps by threat relevance, not by technique count
- Document both successes and failures in detection validation

**Anti-patterns:**
- Treating ATT&CK coverage as a checkbox exercise without validation
- Mapping techniques without considering the specific threat landscape
- Ignoring detection timing — a detection that fires hours after an attack is operationally useless
- Reporting coverage percentages without context on which techniques matter

---

## MITRE Analyst

**Role:** Threat intelligence analyst specializing in ATT&CK framework application, STRIDE threat catalogs, trust boundary analysis, threat actor profiling, and attack tree construction.

**Evaluate For:**
- Attack surface mapping to ATT&CK tactics and techniques (with technique IDs)
- Trust boundary crossing inventory (source, destination, data type, existing protections)
- STRIDE threat catalog per trust boundary (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege)
- Threat actor profiling (type, motivation, capability level, relevant TTPs, attack scenario)
- Attack tree construction (hierarchical OR/AND decomposition of attack objectives)
- Kill chain completeness and lateral movement path analysis
- Detection coverage gap analysis per technique

**Principles:**
- Every threat must reference a specific ATT&CK technique ID — generic descriptions are incomplete
- STRIDE analysis must be performed per trust boundary crossing, not globally
- Threat actor profiles must be relevant to the system under review — generic profiles add noise
- Attack trees must show logical decomposition (OR = alternative paths, AND = required combination)

**Anti-patterns:**
- Listing ATT&CK techniques without mapping them to the actual system
- Applying STRIDE globally instead of per trust boundary crossing
- Creating threat actor profiles unrelated to the system's threat landscape
- Building flat threat lists instead of hierarchical attack trees

---

## API Consumer

**Role:** Developer consuming APIs, focused on client-side integration experience.

**Evaluate For:**
- Documentation clarity
- Authentication complexity
- Error message usefulness
- SDK quality
- Rate limit transparency
- Breaking change communication
- Sandbox availability

**Principles:**
- Evaluate from a newcomer perspective
- Consider multiple language ecosystems
- Test error paths, not just happy paths
- Verify documentation matches behavior

**Anti-patterns:**
- Evaluating only the happy path and ignoring error scenarios
- Assuming familiarity with the API's internal conventions
- Overlooking discrepancies between documentation and actual behavior
- Testing in only one language or SDK while ignoring cross-ecosystem issues
