package manifest

// RunManifest is the top-level governance run manifest.
type RunManifest struct {
	ManifestVersion    string          `json:"manifest_version"`
	ManifestID         string          `json:"manifest_id"`
	Timestamp          string          `json:"timestamp"`
	PersonaSetCommit   string          `json:"persona_set_commit"`
	PanelGraphVersion  string          `json:"panel_graph_version"`
	PolicyProfileUsed  string          `json:"policy_profile_used"`
	ModelVersion       string          `json:"model_version"`
	AggregateConfidence float64        `json:"aggregate_confidence"`
	RiskLevel          string          `json:"risk_level"`
	HumanIntervention  HumanIntervention `json:"human_intervention"`
	Decision           Decision        `json:"decision"`
	PanelsExecuted     []PanelExecuted `json:"panels_executed"`
	Repository         *RepositoryInfo `json:"repository,omitempty"`
}

// HumanIntervention records whether human review was required or occurred.
type HumanIntervention struct {
	Required              bool   `json:"required"`
	Occurred              bool   `json:"occurred"`
	Reviewer              string `json:"reviewer"`
	Override              bool   `json:"override"`
	OverrideJustification string `json:"override_justification"`
}

// Decision records the governance decision and rationale.
type Decision struct {
	Action              string       `json:"action"`
	Rationale           string       `json:"rationale"`
	PolicyRulesEvaluated []RuleResult `json:"policy_rules_evaluated"`
}

// RuleResult records a single policy rule evaluation.
type RuleResult struct {
	RuleID string `json:"rule_id"`
	Result string `json:"result"`
	Detail string `json:"detail"`
}

// PanelExecuted records a single panel's execution result.
type PanelExecuted struct {
	PanelName       string  `json:"panel_name"`
	Verdict         string  `json:"verdict"`
	ConfidenceScore float64 `json:"confidence_score"`
	ArtifactPath    string  `json:"artifact_path"`
}

// RepositoryInfo holds repository metadata.
type RepositoryInfo struct {
	Name       string `json:"name"`
	Owner      string `json:"owner"`
	Branch     string `json:"branch"`
	BaseBranch string `json:"base_branch"`
	CommitSHA  string `json:"commit_sha"`
	PRNumber   int    `json:"pr_number"`
}
