package emission

// Risk level constants.
const (
	RiskCritical   = "critical"
	RiskHigh       = "high"
	RiskMedium     = "medium"
	RiskLow        = "low"
	RiskNegligible = "negligible"
)

// RiskIndex returns a numeric index for a risk level string.
// critical=4, high=3, medium=2, low=1, negligible=0, unknown=-1.
func RiskIndex(level string) int {
	switch level {
	case RiskCritical:
		return 4
	case RiskHigh:
		return 3
	case RiskMedium:
		return 2
	case RiskLow:
		return 1
	case RiskNegligible:
		return 0
	default:
		return -1
	}
}

// Verdict constants.
const (
	VerdictApprove        = "approve"
	VerdictRequestChanges = "request_changes"
	VerdictBlock          = "block"
	VerdictAbstain        = "abstain"
)

// Execution status constants.
const (
	ExecStatusSuccess  = "success"
	ExecStatusTimeout  = "timeout"
	ExecStatusError    = "error"
	ExecStatusFallback = "fallback"
)

// Emission represents a single panel output (emission).
type Emission struct {
	PanelName             string            `json:"panel_name"`
	ModelID               string            `json:"model_id"`
	PanelVersion          string            `json:"panel_version"`
	ConfidenceScore       float64           `json:"confidence_score"`
	RiskLevel             string            `json:"risk_level"`
	ComplianceScore       string            `json:"compliance_score"`
	PolicyFlags           []PolicyFlag      `json:"policy_flags"`
	RequiresHumanReview   bool              `json:"requires_human_review"`
	Timestamp             string            `json:"timestamp"`
	Findings              []Finding         `json:"findings"`
	AggregateVerdict      string            `json:"aggregate_verdict"`
	DataClassification    *DataClassification `json:"data_classification"`
	AIActRiskTier         string            `json:"ai_act_risk_tier"`
	DestructionRecommended bool             `json:"destruction_recommended"`
	RequiresHumanApproval bool              `json:"requires_human_approval"`
	ExecutionStatus       string            `json:"execution_status"`
	ExecutionContext      *ExecutionContext  `json:"execution_context"`
	SchemaVersion         string            `json:"schema_version"`
	DurationMs            int               `json:"duration_ms"`
	CanaryResults         []CanaryResult    `json:"canary_results"`
	ExecutionTrace        *ExecutionTrace   `json:"execution_trace"`
	SourcePath            string            `json:"-"`
}

// EffectiveExecutionStatus returns the execution status, defaulting to "success"
// if empty.
func (e *Emission) EffectiveExecutionStatus() string {
	if e.ExecutionStatus == "" {
		return ExecStatusSuccess
	}
	return e.ExecutionStatus
}

// PolicyFlag represents a policy flag raised by a panel.
type PolicyFlag struct {
	Flag            string `json:"flag"`
	Severity        string `json:"severity"`
	Description     string `json:"description"`
	Remediation     string `json:"remediation"`
	AutoRemediable  bool   `json:"auto_remediable"`
}

// Finding represents a single finding from a panel.
type Finding struct {
	Persona                string         `json:"persona"`
	Verdict                string         `json:"verdict"`
	Confidence             float64        `json:"confidence"`
	Rationale              string         `json:"rationale"`
	FindingsCount          *FindingsCount `json:"findings_count"`
	Evidence               *Evidence      `json:"evidence"`
	GroundednessScore      *float64       `json:"groundedness_score"`
	HallucinationIndicators []string      `json:"hallucination_indicators"`
}

// FindingsCount holds categorized finding counts.
type FindingsCount struct {
	Critical int `json:"critical"`
	High     int `json:"high"`
	Medium   int `json:"medium"`
	Low      int `json:"low"`
	Info     int `json:"info"`
}

// Evidence points to source code backing a finding.
type Evidence struct {
	File      string `json:"file"`
	LineStart int    `json:"line_start"`
	LineEnd   int    `json:"line_end"`
	Snippet   string `json:"snippet"`
}

// CanaryResult records a canary injection detection result.
type CanaryResult struct {
	CanaryID         string  `json:"canary_id"`
	Detected         bool    `json:"detected"`
	ExpectedSeverity string  `json:"expected_severity"`
	ActualSeverity   *string `json:"actual_severity"`
	SeverityMatch    bool    `json:"severity_match"`
	DetectionLatencyMs *int  `json:"detection_latency_ms"`
}

// ExecutionContext holds metadata about the execution environment.
type ExecutionContext struct {
	Repository       string           `json:"repository"`
	Branch           string           `json:"branch"`
	CommitSHA        string           `json:"commit_sha"`
	PRNumber         int              `json:"pr_number"`
	PolicyProfile    string           `json:"policy_profile"`
	ModelID          string           `json:"model_id"`
	ModelVersion     string           `json:"model_version"`
	ModelHash        string           `json:"model_hash"`
	Provider         string           `json:"provider"`
	VersionDate      string           `json:"version_date"`
	SystemPromptHash string           `json:"system_prompt_hash"`
	InferenceConfig  *InferenceConfig `json:"inference_config"`
	TriggeredBy      string           `json:"triggered_by"`
	TokenCount       *TokenCount      `json:"token_count"`
	EstimatedCostUSD float64          `json:"estimated_cost_usd"`
}

// InferenceConfig holds model inference parameters.
type InferenceConfig struct {
	Temperature float64 `json:"temperature"`
	MaxTokens   int     `json:"max_tokens"`
	TopP        float64 `json:"top_p"`
}

// TokenCount holds input/output token counts.
type TokenCount struct {
	Input  int `json:"input"`
	Output int `json:"output"`
}

// ExecutionTrace records files and analysis metrics.
type ExecutionTrace struct {
	FilesRead           []string             `json:"files_read"`
	DiffLinesAnalyzed   int                  `json:"diff_lines_analyzed"`
	AnalysisDurationMs  int                  `json:"analysis_duration_ms"`
	GroundingReferences []GroundingReference `json:"grounding_references"`
}

// GroundingReference maps a finding back to source code.
type GroundingReference struct {
	File      string `json:"file"`
	Line      int    `json:"line"`
	FindingID string `json:"finding_id"`
}

// DataClassification holds data sensitivity metadata.
type DataClassification struct {
	Level                     string `json:"level"`
	ContainsSensitiveEvidence bool   `json:"contains_sensitive_evidence"`
	RedactionApplied          bool   `json:"redaction_applied"`
	SensitiveCategories       string `json:"sensitive_categories"`
	RedactionRulesApplied     string `json:"redaction_rules_applied"`
}
