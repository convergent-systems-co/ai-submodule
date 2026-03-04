// Package deliveryintent provides loading, validation, and verification of
// delivery intent manifests. A delivery intent declares what files were
// delivered by a governance change and what state is expected in a consumer
// repository after deployment.
package deliveryintent

// SchemaVersion is the current delivery intent schema version.
const SchemaVersion = "1.0.0"

// DeliveryIntent is the top-level manifest structure.
type DeliveryIntent struct {
	SchemaVersion string        `json:"schema_version"`
	IntentID      string        `json:"intent_id"`
	CreatedAt     string        `json:"created_at"`
	Source        Source        `json:"source"`
	Deliverables  []Deliverable `json:"deliverables"`
	ExpectedState ExpectedState `json:"expected_state"`
}

// Source holds metadata about the change that produced the intent.
type Source struct {
	PR     string `json:"pr,omitempty"`
	Branch string `json:"branch"`
	Commit string `json:"commit"`
}

// Deliverable represents a single file or directory in the intent.
type Deliverable struct {
	Type          string   `json:"type"`
	Path          string   `json:"path"`
	Action        string   `json:"action"`
	Checksum      string   `json:"checksum,omitempty"`
	Version       string   `json:"version,omitempty"`
	ExpectedState string   `json:"expected_state,omitempty"`
	RequiredKeys  []string `json:"required_keys,omitempty"`
}

// ExpectedState defines the governance configuration expectations.
type ExpectedState struct {
	GovernanceVersion   string   `json:"governance_version"`
	PolicyProfile       string   `json:"policy_profile"`
	RequiredPanels      []string `json:"required_panels,omitempty"`
	RequiredWorkflows   []string `json:"required_workflows,omitempty"`
	RequiredDirectories []string `json:"required_directories,omitempty"`
}

// CheckStatus represents the result of a single verification check.
type CheckStatus string

const (
	// StatusPass indicates the check passed.
	StatusPass CheckStatus = "pass"
	// StatusFail indicates the check failed.
	StatusFail CheckStatus = "fail"
	// StatusWarning indicates a non-critical issue.
	StatusWarning CheckStatus = "warning"
	// StatusSkipped indicates the check was skipped.
	StatusSkipped CheckStatus = "skipped"
)

// CheckResult holds the outcome of a single verification check.
type CheckResult struct {
	Name        string      `json:"name"`
	Status      CheckStatus `json:"status"`
	Message     string      `json:"message"`
	Remediation string      `json:"remediation,omitempty"`
}

// VerificationReport aggregates all check results.
type VerificationReport struct {
	IntentID    string        `json:"intent_id"`
	Passed      int           `json:"passed"`
	Failed      int           `json:"failed"`
	Warnings    int           `json:"warnings"`
	Skipped     int           `json:"skipped"`
	Results     []CheckResult `json:"results"`
	OverallPass bool          `json:"overall_pass"`
}
