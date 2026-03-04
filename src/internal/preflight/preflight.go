// Package preflight validates project.yaml before the orchestrator starts.
// It checks file existence, YAML syntax, required keys, language
// configuration, and governance section constraints.
//
// Ported from Python: governance/engine/preflight.py
package preflight

import (
	"fmt"
	"os"
	"strings"

	"gopkg.in/yaml.v3"
)

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

// Finding represents a single validation finding.
type Finding struct {
	Level   string `json:"level"` // "error" or "warning"
	Message string `json:"message"`
}

// Result captures the full outcome of a preflight validation.
type Result struct {
	Valid              bool      `json:"valid"`
	Findings           []Finding `json:"findings"`
	Languages          []string  `json:"languages"`
	TemplatesAvailable []string  `json:"templates_available"`
	TemplatesMissing   []string  `json:"templates_missing"`
}

// Errors returns only error-level findings.
func (r *Result) Errors() []Finding {
	var out []Finding
	for _, f := range r.Findings {
		if f.Level == "error" {
			out = append(out, f)
		}
	}
	return out
}

// Warnings returns only warning-level findings.
func (r *Result) Warnings() []Finding {
	var out []Finding
	for _, f := range r.Findings {
		if f.Level == "warning" {
			out = append(out, f)
		}
	}
	return out
}

// Summary returns a human-readable summary string.
func (r *Result) Summary() string {
	errs := r.Errors()
	warns := r.Warnings()
	var sb strings.Builder
	if r.Valid {
		sb.WriteString("project.yaml: VALID")
	} else {
		sb.WriteString("project.yaml: INVALID")
	}
	sb.WriteString(fmt.Sprintf(" (%d errors, %d warnings)", len(errs), len(warns)))
	for _, f := range r.Findings {
		sb.WriteString(fmt.Sprintf("\n  [%s] %s", f.Level, f.Message))
	}
	return sb.String()
}

// ---------------------------------------------------------------------------
// Valid policy profiles
// ---------------------------------------------------------------------------

var validProfiles = map[string]bool{
	"default":                 true,
	"fin_pii_high":            true,
	"infrastructure_critical": true,
	"fast-track":              true,
	"reduced_touchpoint":      true,
}

// ---------------------------------------------------------------------------
// ValidateProjectYAML
// ---------------------------------------------------------------------------

// ValidateProjectYAML performs six checks on a project.yaml file:
//  1. File exists
//  2. YAML syntax
//  3. Required keys (project_name)
//  4. language / languages conflict
//  5. Languages extraction
//  6. Governance section validation
func ValidateProjectYAML(path string) *Result {
	r := &Result{Valid: true}

	// 1. File exists.
	data, err := os.ReadFile(path)
	if err != nil {
		r.Valid = false
		r.Findings = append(r.Findings, Finding{
			Level:   "error",
			Message: fmt.Sprintf("cannot read project.yaml: %v", err),
		})
		return r
	}

	// 2. YAML syntax.
	var raw map[string]interface{}
	if err := yaml.Unmarshal(data, &raw); err != nil {
		r.Valid = false
		r.Findings = append(r.Findings, Finding{
			Level:   "error",
			Message: fmt.Sprintf("YAML syntax error: %v", err),
		})
		return r
	}

	// 3. Required keys.
	if _, ok := raw["project_name"]; !ok {
		r.Valid = false
		r.Findings = append(r.Findings, Finding{
			Level:   "error",
			Message: "missing required key: project_name",
		})
	}

	// 4. language / languages conflict.
	_, hasLang := raw["language"]
	_, hasLangs := raw["languages"]
	if hasLang && hasLangs {
		r.Findings = append(r.Findings, Finding{
			Level:   "warning",
			Message: "both 'language' and 'languages' are set; 'languages' takes precedence",
		})
	}

	// 5. Languages extraction.
	if hasLangs {
		switch v := raw["languages"].(type) {
		case []interface{}:
			for _, item := range v {
				if s, ok := item.(string); ok {
					r.Languages = append(r.Languages, s)
				}
			}
		}
	} else if hasLang {
		if s, ok := raw["language"].(string); ok {
			r.Languages = []string{s}
		}
	}

	// 6. Governance section.
	if gov, ok := raw["governance"].(map[string]interface{}); ok {
		// Profile validation.
		if profile, ok := gov["policy_profile"].(string); ok {
			if !validProfiles[profile] {
				r.Findings = append(r.Findings, Finding{
					Level:   "warning",
					Message: fmt.Sprintf("unknown policy_profile %q", profile),
				})
			}
		}

		// parallel_coders range.
		if pc, ok := numVal(gov, "parallel_coders"); ok {
			if pc < -1 || pc == 0 {
				r.Valid = false
				r.Findings = append(r.Findings, Finding{
					Level:   "error",
					Message: fmt.Sprintf("parallel_coders must be >= 1 or -1 (unlimited), got %d", pc),
				})
			}
		}
	}

	return r
}

// numVal extracts an integer from a map, handling int and float64.
func numVal(m map[string]interface{}, key string) (int, bool) {
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
