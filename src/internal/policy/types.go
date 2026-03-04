package policy

// Profile represents a governance policy profile.
type Profile struct {
	ProfileVersion            string                       `yaml:"profile_version" json:"profile_version"`
	ProfileName               string                       `yaml:"profile_name" json:"profile_name"`
	Description               string                       `yaml:"description" json:"description"`
	Weighting                 Weighting                    `yaml:"weighting" json:"weighting"`
	RiskAggregation           RiskAggregation              `yaml:"risk_aggregation" json:"risk_aggregation"`
	Escalation                Escalation                   `yaml:"escalation" json:"escalation"`
	AutoMerge                 AutoMerge                    `yaml:"auto_merge" json:"auto_merge"`
	AutoRemediate             AutoRemediate                `yaml:"auto_remediate" json:"auto_remediate"`
	Block                     BlockConfig                  `yaml:"block" json:"block"`
	Override                  Override                     `yaml:"override" json:"override"`
	PanelExecution            PanelExecution               `yaml:"panel_execution" json:"panel_execution"`
	RequiredPanels            []string                     `yaml:"required_panels" json:"required_panels"`
	OptionalPanels            []OptionalPanel              `yaml:"optional_panels" json:"optional_panels"`
	PanelOverridesByChangeType map[string]PanelOverride    `yaml:"panel_overrides_by_change_type" json:"panel_overrides_by_change_type"`
	CanaryCalibration         CanaryCalibrationConfig      `yaml:"canary_calibration" json:"canary_calibration"`
	MultiModel                MultiModelConfig             `yaml:"multi_model" json:"multi_model"`
	Raw                       map[string]interface{}       `yaml:"-" json:"-"`
}

// Weighting defines how panel confidence scores are combined.
type Weighting struct {
	Model               string             `yaml:"model" json:"model"`
	Weights             map[string]float64 `yaml:"weights" json:"weights"`
	MissingPanelBehavior string            `yaml:"missing_panel_behavior" json:"missing_panel_behavior"`
}

// RiskAggregation defines how risk levels are combined.
type RiskAggregation struct {
	Model string     `yaml:"model" json:"model"`
	Rules []RiskRule `yaml:"rules" json:"rules"`
}

// RiskRule is a single risk aggregation rule.
type RiskRule struct {
	Condition   string `yaml:"condition" json:"condition"`
	Result      string `yaml:"result" json:"result"`
	Description string `yaml:"description" json:"description"`
}

// Escalation defines when human review is triggered.
type Escalation struct {
	Rules []EscalationRule `yaml:"rules" json:"rules"`
}

// EscalationRule is a single escalation rule.
type EscalationRule struct {
	Name        string   `yaml:"name" json:"name"`
	Condition   string   `yaml:"condition" json:"condition"`
	Action      string   `yaml:"action" json:"action"`
	Reviewers   []string `yaml:"reviewers" json:"reviewers"`
	Description string   `yaml:"description" json:"description"`
}

// AutoMerge defines when PRs can be automatically merged.
type AutoMerge struct {
	Enabled    bool                 `yaml:"enabled" json:"enabled"`
	Conditions []AutoMergeCondition `yaml:"conditions" json:"conditions"`
	Operator   string               `yaml:"operator" json:"operator"`
}

// AutoMergeCondition is a single auto-merge condition.
type AutoMergeCondition struct {
	Condition   string `yaml:"condition" json:"condition"`
	Description string `yaml:"description" json:"description"`
}

// AutoRemediate defines when automatic remediation is allowed.
type AutoRemediate struct {
	Enabled    bool                      `yaml:"enabled" json:"enabled"`
	MaxAttempts int                      `yaml:"max_attempts" json:"max_attempts"`
	Cooldown    string                   `yaml:"cooldown" json:"cooldown"`
	Conditions  []AutoRemediateCondition `yaml:"conditions" json:"conditions"`
	AllowedActions string               `yaml:"allowed_actions" json:"allowed_actions"`
	Prohibited     string               `yaml:"prohibited_actions" json:"prohibited_actions"`
}

// AutoRemediateCondition is a single auto-remediate condition.
type AutoRemediateCondition struct {
	Condition   string `yaml:"condition" json:"condition"`
	Description string `yaml:"description" json:"description"`
}

// BlockConfig defines when PRs are blocked.
type BlockConfig struct {
	Conditions []BlockCondition `yaml:"conditions" json:"conditions"`
}

// BlockCondition is a single block condition.
type BlockCondition struct {
	Condition   string `yaml:"condition" json:"condition"`
	Description string `yaml:"description" json:"description"`
}

// Override defines manual override configuration.
type Override struct {
	MinApprovals              int    `yaml:"min_approvals" json:"min_approvals"`
	RequiredRoles             string `yaml:"required_roles" json:"required_roles"`
	JustificationMinLength    int    `yaml:"justification_min_length" json:"justification_min_length"`
	Cooldown                  string `yaml:"cooldown" json:"cooldown"`
	PostOverrideAuditRequired bool   `yaml:"post_override_audit_required" json:"post_override_audit_required"`
}

// PanelExecution defines panel execution rules and timeout configuration.
type PanelExecution struct {
	TimeoutConfig PanelTimeoutConfig  `yaml:"timeout_config" json:"timeout_config"`
	Rules         []PanelExecutionRule `yaml:"rules" json:"rules"`
}

// PanelExecutionRule is a single panel execution rule.
type PanelExecutionRule struct {
	Condition   string `yaml:"condition" json:"condition"`
	Action      string `yaml:"action" json:"action"`
	Description string `yaml:"description" json:"description"`
}

// OptionalPanel defines a conditionally-required panel.
type OptionalPanel struct {
	Name      string `yaml:"name" json:"name"`
	Condition string `yaml:"trigger_condition" json:"trigger_condition"`
}

// PanelOverride defines per-change-type panel requirements.
type PanelOverride struct {
	RequiredPanels []string `yaml:"required_panels" json:"required_panels"`
	OptionalPanels []string `yaml:"optional_panels" json:"optional_panels"`
}

// CanaryCalibrationConfig holds canary calibration settings.
type CanaryCalibrationConfig struct {
	Config string `yaml:"config" json:"config"`
}

// MultiModelConfig holds multi-model evaluation settings.
type MultiModelConfig struct {
	Enabled   string `yaml:"enabled" json:"enabled"`
	Models    string `yaml:"models" json:"models"`
	Consensus string `yaml:"consensus" json:"consensus"`
	MinModels string `yaml:"min_models" json:"min_models"`
	Panels    string `yaml:"panels" json:"panels"`
}

// PanelTimeoutConfig holds timeout settings for panel execution.
type PanelTimeoutConfig struct {
	DefaultTimeoutMinutes int                      `yaml:"default_timeout_minutes" json:"default_timeout_minutes"`
	MaxRetries            int                      `yaml:"max_retries" json:"max_retries"`
	FallbackStrategy      string                   `yaml:"fallback_strategy" json:"fallback_strategy"`
	FallbackConfidenceCap float64                  `yaml:"fallback_confidence_cap" json:"fallback_confidence_cap"`
	MaxFallbacksPerPR     int                      `yaml:"max_fallbacks_per_pr" json:"max_fallbacks_per_pr"`
	PerPanelOverrides     map[string]PanelTimeout  `yaml:"per_panel_overrides" json:"per_panel_overrides"`
}

// PanelTimeout holds timeout settings for a specific panel.
type PanelTimeout struct {
	TimeoutMinutes int `yaml:"timeout_minutes" json:"timeout_minutes"`
}
