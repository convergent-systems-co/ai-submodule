// Package config loads and validates orchestrator configuration from
// project.yaml. It extracts the governance section, applies defaults,
// and validates invariants.
//
// Ported from Python: governance/engine/orchestrator/config.py
package config

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
)

// ---------------------------------------------------------------------------
// OrchestratorConfig
// ---------------------------------------------------------------------------

// OrchestratorConfig holds all orchestrator tunables.
type OrchestratorConfig struct {
	// Parallelism
	ParallelCoders    int `json:"parallel_coders" yaml:"parallel_coders"`
	ParallelTechLeads int `json:"parallel_tech_leads" yaml:"parallel_tech_leads"`
	UseProjectManager bool `json:"use_project_manager" yaml:"use_project_manager"`

	// Policy
	PolicyProfile string `json:"policy_profile" yaml:"policy_profile"`

	// Coder scaling
	CoderMin int `json:"coder_min" yaml:"coder_min"`
	CoderMax int `json:"coder_max" yaml:"coder_max"`

	// Worktree
	RequireWorktree bool `json:"require_worktree" yaml:"require_worktree"`

	// Directories
	CheckpointDir string `json:"checkpoint_dir" yaml:"checkpoint_dir"`
	AuditLogDir   string `json:"audit_log_dir" yaml:"audit_log_dir"`
	SessionDir    string `json:"session_dir" yaml:"session_dir"`
	PlansDir      string `json:"plans_dir" yaml:"plans_dir"`
	PanelsDir     string `json:"panels_dir" yaml:"panels_dir"`
	EmissionsDir  string `json:"emissions_dir" yaml:"emissions_dir"`

	// DevOps timing
	DevOpsHeartbeatIntervalSeconds int `json:"devops_heartbeat_interval_seconds" yaml:"devops_heartbeat_interval_seconds"`
	DevOpsIdleBackoffMaxSeconds    int `json:"devops_idle_backoff_max_seconds" yaml:"devops_idle_backoff_max_seconds"`

	// Feedback / eval limits
	MaxFeedbackCycles int `json:"max_feedback_cycles" yaml:"max_feedback_cycles"`
	MaxTotalEvalCycles int `json:"max_total_eval_cycles" yaml:"max_total_eval_cycles"`

	// Issue body limits
	MaxIssueBodyChars int `json:"max_issue_body_chars" yaml:"max_issue_body_chars"`
	MaxIssueComments  int `json:"max_issue_comments" yaml:"max_issue_comments"`

	// Quality
	MinCoverage float64 `json:"min_coverage" yaml:"min_coverage"`

	// Conventions
	BranchPattern string `json:"branch_pattern" yaml:"branch_pattern"`
	CommitStyle   string `json:"commit_style" yaml:"commit_style"`
}

// defaults returns a config with all defaults applied.
func defaults() *OrchestratorConfig {
	return &OrchestratorConfig{
		ParallelCoders:                 5,
		ParallelTechLeads:             3,
		PolicyProfile:                 "default",
		CoderMin:                      1,
		CoderMax:                      5,
		RequireWorktree:               true,
		CheckpointDir:                 ".artifacts/checkpoints",
		AuditLogDir:                   ".artifacts/audit",
		SessionDir:                    ".artifacts/state/sessions",
		PlansDir:                      ".artifacts/plans",
		PanelsDir:                     ".artifacts/panels",
		EmissionsDir:                  "governance/emissions",
		DevOpsHeartbeatIntervalSeconds: 60,
		DevOpsIdleBackoffMaxSeconds:   300,
		MaxFeedbackCycles:             2,
		MaxTotalEvalCycles:            5,
		MaxIssueBodyChars:             15000,
		MaxIssueComments:              50,
		MinCoverage:                   80.0,
		CommitStyle:                   "conventional",
	}
}

// ---------------------------------------------------------------------------
// LoadConfig
// ---------------------------------------------------------------------------

// LoadConfig reads a project.yaml file and extracts the orchestrator
// configuration from the governance section. Missing keys use defaults.
func LoadConfig(projectYAMLPath string) (*OrchestratorConfig, error) {
	cfg := defaults()

	data, err := os.ReadFile(projectYAMLPath)
	if err != nil {
		return nil, fmt.Errorf("config: read %s: %w", projectYAMLPath, err)
	}

	var raw map[string]interface{}
	if err := yaml.Unmarshal(data, &raw); err != nil {
		return nil, fmt.Errorf("config: parse %s: %w", projectYAMLPath, err)
	}

	// Extract governance section.
	if gov, ok := raw["governance"].(map[string]interface{}); ok {
		if v, ok := intVal(gov, "parallel_coders"); ok {
			cfg.ParallelCoders = v
		}
		if v, ok := intVal(gov, "parallel_tech_leads"); ok {
			cfg.ParallelTechLeads = v
		}
		if v, ok := gov["use_project_manager"].(bool); ok {
			cfg.UseProjectManager = v
		}
		if v, ok := gov["policy_profile"].(string); ok {
			cfg.PolicyProfile = v
		}
		if v, ok := intVal(gov, "coder_min"); ok {
			cfg.CoderMin = v
		}
		if v, ok := intVal(gov, "coder_max"); ok {
			cfg.CoderMax = v
		}
		if v, ok := gov["require_worktree"].(bool); ok {
			cfg.RequireWorktree = v
		}
		if v, ok := gov["checkpoint_dir"].(string); ok {
			cfg.CheckpointDir = v
		}
		if v, ok := gov["audit_log_dir"].(string); ok {
			cfg.AuditLogDir = v
		}
		if v, ok := gov["session_dir"].(string); ok {
			cfg.SessionDir = v
		}
		if v, ok := gov["plans_dir"].(string); ok {
			cfg.PlansDir = v
		}
		if v, ok := gov["panels_dir"].(string); ok {
			cfg.PanelsDir = v
		}
		if v, ok := gov["emissions_dir"].(string); ok {
			cfg.EmissionsDir = v
		}
		if v, ok := intVal(gov, "devops_heartbeat_interval_seconds"); ok {
			cfg.DevOpsHeartbeatIntervalSeconds = v
		}
		if v, ok := intVal(gov, "devops_idle_backoff_max_seconds"); ok {
			cfg.DevOpsIdleBackoffMaxSeconds = v
		}
		if v, ok := intVal(gov, "max_feedback_cycles"); ok {
			cfg.MaxFeedbackCycles = v
		}
		if v, ok := intVal(gov, "max_total_eval_cycles"); ok {
			cfg.MaxTotalEvalCycles = v
		}
		if v, ok := intVal(gov, "max_issue_body_chars"); ok {
			cfg.MaxIssueBodyChars = v
		}
		if v, ok := intVal(gov, "max_issue_comments"); ok {
			cfg.MaxIssueComments = v
		}
		if v, ok := floatVal(gov, "min_coverage"); ok {
			cfg.MinCoverage = v
		}
	}

	// Extract conventions section.
	if conv, ok := raw["conventions"].(map[string]interface{}); ok {
		if v, ok := conv["branch_pattern"].(string); ok {
			cfg.BranchPattern = v
		}
		if v, ok := conv["commit_style"].(string); ok {
			cfg.CommitStyle = v
		}
	}

	// Validate: coder_min <= coder_max (unless coder_max == -1 for unlimited).
	if cfg.CoderMax != -1 && cfg.CoderMin > cfg.CoderMax {
		return nil, fmt.Errorf(
			"config: coder_min (%d) must be <= coder_max (%d)",
			cfg.CoderMin, cfg.CoderMax,
		)
	}

	return cfg, nil
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

// intVal extracts an integer from a map[string]interface{}, handling
// both int and float64 (common after YAML/JSON round-tripping).
func intVal(m map[string]interface{}, key string) (int, bool) {
	v, ok := m[key]
	if !ok {
		return 0, false
	}
	switch n := v.(type) {
	case int:
		return n, true
	case float64:
		return int(n), true
	case int64:
		return int(n), true
	default:
		return 0, false
	}
}

// floatVal extracts a float64 from a map[string]interface{}.
func floatVal(m map[string]interface{}, key string) (float64, bool) {
	v, ok := m[key]
	if !ok {
		return 0, false
	}
	switch n := v.(type) {
	case float64:
		return n, true
	case int:
		return float64(n), true
	case int64:
		return float64(n), true
	default:
		return 0, false
	}
}
