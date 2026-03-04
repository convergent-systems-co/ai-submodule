// Package containment enforces per-persona access restrictions.
// It parses a YAML policy that defines denied paths, denied operations,
// allowed operations, and resource limits for each persona.
//
// Ported from Python: governance/engine/containment.py
package containment

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"gopkg.in/yaml.v3"
)

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

// PersonaPolicy defines the containment rules for a single persona.
type PersonaPolicy struct {
	DeniedPaths       []string       `yaml:"denied_paths"`
	DeniedOperations  []string       `yaml:"denied_operations"`
	AllowedOperations []string       `yaml:"allowed_operations"`
	ResourceLimits    map[string]int `yaml:"resource_limits"`
}

// ContainmentConfig is the top-level containment policy.
type ContainmentConfig struct {
	Mode     string                    `yaml:"mode"` // "enforced" or "audit"
	Personas map[string]*PersonaPolicy `yaml:"personas"`
}

// CheckResult captures the outcome of a containment check.
type CheckResult struct {
	Allowed bool
	Blocked bool
	Reason  string
}

// ---------------------------------------------------------------------------
// Checker
// ---------------------------------------------------------------------------

// Checker evaluates containment rules.
type Checker struct {
	config           ContainmentConfig
	violationLogPath string
}

// NewChecker creates a Checker from raw YAML policy data.
// If violationLogPath is non-empty, violations are appended to that file.
func NewChecker(policyData []byte, violationLogPath string) (*Checker, error) {
	var cfg ContainmentConfig
	if err := yaml.Unmarshal(policyData, &cfg); err != nil {
		return nil, fmt.Errorf("containment: parse policy: %w", err)
	}
	if cfg.Mode == "" {
		cfg.Mode = "enforced"
	}
	if cfg.Personas == nil {
		cfg.Personas = make(map[string]*PersonaPolicy)
	}
	return &Checker{config: cfg, violationLogPath: violationLogPath}, nil
}

// Mode returns the containment mode ("enforced" or "audit").
func (c *Checker) Mode() string {
	return c.config.Mode
}

// CheckPath verifies that persona is allowed to access path.
func (c *Checker) CheckPath(persona, path string) CheckResult {
	pp := c.config.Personas[persona]
	if pp == nil {
		return CheckResult{Allowed: true}
	}

	cleanPath := filepath.Clean(path)
	for _, pattern := range pp.DeniedPaths {
		matched, err := filepath.Match(pattern, cleanPath)
		if err != nil {
			continue
		}
		if matched {
			r := CheckResult{
				Blocked: true,
				Reason:  fmt.Sprintf("persona %q denied access to path %q (pattern %q)", persona, path, pattern),
			}
			c.logViolation(r.Reason)
			return r
		}
		// Also check if the path starts with the pattern prefix (directory match).
		if strings.HasPrefix(cleanPath, strings.TrimRight(pattern, "*")) {
			matched2, _ := filepath.Match(pattern, filepath.Base(cleanPath))
			if matched2 {
				r := CheckResult{
					Blocked: true,
					Reason:  fmt.Sprintf("persona %q denied access to path %q (pattern %q)", persona, path, pattern),
				}
				c.logViolation(r.Reason)
				return r
			}
		}
	}

	return CheckResult{Allowed: true}
}

// CheckOperation verifies that persona may perform the named operation.
// If allowed_operations is set, only those operations are permitted (allowlist).
// Otherwise, denied_operations is checked (denylist).
func (c *Checker) CheckOperation(persona, op string) CheckResult {
	pp := c.config.Personas[persona]
	if pp == nil {
		return CheckResult{Allowed: true}
	}

	// Allowlist mode: if AllowedOperations is non-empty, only listed ops are OK.
	if len(pp.AllowedOperations) > 0 {
		for _, allowed := range pp.AllowedOperations {
			if allowed == op {
				return CheckResult{Allowed: true}
			}
		}
		r := CheckResult{
			Blocked: true,
			Reason:  fmt.Sprintf("persona %q operation %q not in allowed list", persona, op),
		}
		c.logViolation(r.Reason)
		return r
	}

	// Denylist mode.
	for _, denied := range pp.DeniedOperations {
		if denied == op {
			r := CheckResult{
				Blocked: true,
				Reason:  fmt.Sprintf("persona %q denied operation %q", persona, op),
			}
			c.logViolation(r.Reason)
			return r
		}
	}

	return CheckResult{Allowed: true}
}

// CheckResourceLimit verifies that value does not exceed the configured
// limit for resource under persona.
func (c *Checker) CheckResourceLimit(persona, resource string, value int) CheckResult {
	pp := c.config.Personas[persona]
	if pp == nil {
		return CheckResult{Allowed: true}
	}

	limit, ok := pp.ResourceLimits[resource]
	if !ok {
		return CheckResult{Allowed: true}
	}

	if value > limit {
		r := CheckResult{
			Blocked: true,
			Reason: fmt.Sprintf(
				"persona %q resource %q value %d exceeds limit %d",
				persona, resource, value, limit,
			),
		}
		c.logViolation(r.Reason)
		return r
	}

	return CheckResult{Allowed: true}
}

// logViolation appends the message to the violation log, if configured.
func (c *Checker) logViolation(msg string) {
	if c.violationLogPath == "" {
		return
	}
	f, err := os.OpenFile(c.violationLogPath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return
	}
	defer f.Close()
	_, _ = fmt.Fprintln(f, msg)
}
