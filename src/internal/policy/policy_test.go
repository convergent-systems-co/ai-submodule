package policy

import (
	"testing"
)

func TestLoadProfile_BasicFields(t *testing.T) {
	yaml := `
profile_name: fin_pii_high
profile_version: "2.0"
description: Financial PII high-risk profile
required_panels:
  - code-review
  - security-review
`
	p, err := LoadProfile([]byte(yaml))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if p.ProfileName != "fin_pii_high" {
		t.Errorf("expected profile name 'fin_pii_high', got %q", p.ProfileName)
	}
	if p.ProfileVersion != "2.0" {
		t.Errorf("expected version '2.0', got %q", p.ProfileVersion)
	}
	if p.Description != "Financial PII high-risk profile" {
		t.Errorf("unexpected description: %q", p.Description)
	}
	if len(p.RequiredPanels) != 2 {
		t.Fatalf("expected 2 required panels, got %d", len(p.RequiredPanels))
	}
	if p.RequiredPanels[0] != "code-review" || p.RequiredPanels[1] != "security-review" {
		t.Errorf("unexpected required panels: %v", p.RequiredPanels)
	}
}

func TestLoadProfile_Defaults(t *testing.T) {
	yaml := `
profile_name: minimal
`
	p, err := LoadProfile([]byte(yaml))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if p.Weighting.MissingPanelBehavior != "redistribute" {
		t.Errorf("expected MissingPanelBehavior 'redistribute', got %q", p.Weighting.MissingPanelBehavior)
	}
	if p.AutoMerge.Operator != "all" {
		t.Errorf("expected AutoMerge.Operator 'all', got %q", p.AutoMerge.Operator)
	}
	if p.AutoRemediate.MaxAttempts != 3 {
		t.Errorf("expected MaxAttempts 3, got %d", p.AutoRemediate.MaxAttempts)
	}
}

func TestLoadProfile_InvalidYAML(t *testing.T) {
	bad := `[invalid: yaml: {{`
	_, err := LoadProfile([]byte(bad))
	if err == nil {
		t.Fatal("expected error for invalid YAML")
	}
}

func TestLoadProfile_RawMapPopulated(t *testing.T) {
	yaml := `
profile_name: test
custom_field: custom_value
`
	p, err := LoadProfile([]byte(yaml))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if p.Raw == nil {
		t.Fatal("expected Raw map to be populated")
	}
	if v, ok := p.Raw["profile_name"]; !ok || v != "test" {
		t.Errorf("expected Raw[profile_name] = 'test', got %v", v)
	}
	if v, ok := p.Raw["custom_field"]; !ok || v != "custom_value" {
		t.Errorf("expected Raw[custom_field] = 'custom_value', got %v", v)
	}
}

// --- GetRequiredPanelsForChangeType ---

func TestGetRequiredPanelsForChangeType_Default(t *testing.T) {
	p := &Profile{
		RequiredPanels: []string{"code-review", "security-review", "documentation-review"},
	}
	panels := GetRequiredPanelsForChangeType(p, "feature")
	if len(panels) != 3 {
		t.Fatalf("expected 3 panels, got %d: %v", len(panels), panels)
	}
	// security-review should be present (it already is in defaults)
	found := false
	for _, pn := range panels {
		if pn == "security-review" {
			found = true
		}
	}
	if !found {
		t.Error("expected security-review to be present")
	}
}

func TestGetRequiredPanelsForChangeType_WithOverride(t *testing.T) {
	p := &Profile{
		RequiredPanels: []string{"code-review", "security-review"},
		PanelOverridesByChangeType: map[string]PanelOverride{
			"docs": {
				RequiredPanels: []string{"documentation-review"},
			},
		},
	}
	panels := GetRequiredPanelsForChangeType(p, "docs")
	// Override has "documentation-review" only, but security-review is always added
	if len(panels) != 2 {
		t.Fatalf("expected 2 panels (documentation-review + security-review), got %d: %v", len(panels), panels)
	}
	hasDoc := false
	hasSec := false
	for _, pn := range panels {
		if pn == "documentation-review" {
			hasDoc = true
		}
		if pn == "security-review" {
			hasSec = true
		}
	}
	if !hasDoc {
		t.Error("expected documentation-review in override panels")
	}
	if !hasSec {
		t.Error("expected security-review to always be included")
	}
}

func TestGetRequiredPanelsForChangeType_UnknownChangeType(t *testing.T) {
	p := &Profile{
		RequiredPanels: []string{"code-review"},
	}
	panels := GetRequiredPanelsForChangeType(p, "unknown-type")
	// Falls back to RequiredPanels + security-review
	if len(panels) != 2 {
		t.Fatalf("expected 2 panels, got %d: %v", len(panels), panels)
	}
}

// --- LoadPanelTimeoutConfig ---

func TestLoadPanelTimeoutConfig_WithValues(t *testing.T) {
	yaml := `
default_timeout_minutes: 10
max_retries: 3
fallback_strategy: "retry"
fallback_confidence_cap: 0.60
max_fallbacks_per_pr: 5
`
	cfg, err := LoadPanelTimeoutConfig([]byte(yaml))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if cfg.DefaultTimeoutMinutes != 10 {
		t.Errorf("expected 10, got %d", cfg.DefaultTimeoutMinutes)
	}
	if cfg.MaxRetries != 3 {
		t.Errorf("expected 3, got %d", cfg.MaxRetries)
	}
	if cfg.FallbackStrategy != "retry" {
		t.Errorf("expected 'retry', got %q", cfg.FallbackStrategy)
	}
	if cfg.FallbackConfidenceCap != 0.60 {
		t.Errorf("expected 0.60, got %f", cfg.FallbackConfidenceCap)
	}
	if cfg.MaxFallbacksPerPR != 5 {
		t.Errorf("expected 5, got %d", cfg.MaxFallbacksPerPR)
	}
}

func TestLoadPanelTimeoutConfig_Defaults(t *testing.T) {
	yaml := `{}`
	cfg, err := LoadPanelTimeoutConfig([]byte(yaml))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if cfg.DefaultTimeoutMinutes != 5 {
		t.Errorf("expected default 5, got %d", cfg.DefaultTimeoutMinutes)
	}
	if cfg.MaxRetries != 1 {
		t.Errorf("expected default 1, got %d", cfg.MaxRetries)
	}
	if cfg.FallbackStrategy != "baseline" {
		t.Errorf("expected default 'baseline', got %q", cfg.FallbackStrategy)
	}
	if cfg.FallbackConfidenceCap != 0.50 {
		t.Errorf("expected default 0.50, got %f", cfg.FallbackConfidenceCap)
	}
	if cfg.MaxFallbacksPerPR != 2 {
		t.Errorf("expected default 2, got %d", cfg.MaxFallbacksPerPR)
	}
}
