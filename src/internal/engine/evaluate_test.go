package engine

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"

	"github.com/SET-Apps/ai-submodule/src/internal/emission"
)

// minimalProfile returns YAML bytes for a minimal governance profile.
// autoMergeEnabled controls whether auto-merge is enabled.
func minimalProfile(autoMergeEnabled bool) []byte {
	return []byte(fmt.Sprintf(`
profile_name: test-profile
profile_version: "1.0"
required_panels: []
weighting:
  model: equal
  missing_panel_behavior: redistribute
auto_merge:
  enabled: %v
  operator: all
  conditions:
    - condition: 'all_panel_verdicts in ["approve"]'
      description: All panels must approve
    - condition: 'aggregate_confidence >= 0.80'
      description: High confidence required
    - condition: 'ci_checks_passed == true'
      description: CI must pass
    - condition: 'no_policy_flags_severity in ["critical", "high"]'
      description: No critical/high flags
block:
  conditions: []
escalation:
  rules: []
auto_remediate:
  enabled: false
  max_attempts: 3
`, autoMergeEnabled))
}

// writeEmission writes an emission JSON file to dir and returns the path.
func writeEmission(t *testing.T, dir string, em *emission.Emission) string {
	t.Helper()
	data, err := json.Marshal(em)
	if err != nil {
		t.Fatalf("marshal emission: %v", err)
	}
	name := em.PanelName
	if name == "" {
		name = "panel"
	}
	path := filepath.Join(dir, name+".json")
	if err := os.WriteFile(path, data, 0644); err != nil {
		t.Fatalf("write emission: %v", err)
	}
	return path
}

func TestAutoMerge(t *testing.T) {
	dir := t.TempDir()
	writeEmission(t, dir, &emission.Emission{
		PanelName:        "code-review",
		AggregateVerdict: "approve",
		ConfidenceScore:  0.95,
		RiskLevel:        "low",
	})
	writeEmission(t, dir, &emission.Emission{
		PanelName:        "security-review",
		AggregateVerdict: "approve",
		ConfidenceScore:  0.90,
		RiskLevel:        "low",
	})

	result, err := Evaluate(EvaluateParams{
		EmissionsDir: dir,
		ProfileData:  minimalProfile(true),
		CIPassed:     true,
		CommitSHA:    "abc1234",
		Repo:         "SET-Apps/ai-submodule",
		LogWriter:    os.Stderr,
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result.ExitCode != 0 {
		t.Errorf("expected exit code 0 (auto-merge), got %d", result.ExitCode)
	}
	if result.Manifest.Decision.Action != "auto_merge" {
		t.Errorf("expected action 'auto_merge', got %q", result.Manifest.Decision.Action)
	}
}

func TestBlock_CIFailed(t *testing.T) {
	dir := t.TempDir()
	writeEmission(t, dir, &emission.Emission{
		PanelName:        "code-review",
		AggregateVerdict: "approve",
		ConfidenceScore:  0.95,
		RiskLevel:        "low",
	})

	result, err := Evaluate(EvaluateParams{
		EmissionsDir: dir,
		ProfileData:  minimalProfile(true),
		CIPassed:     false, // CI failed
		LogWriter:    os.Stderr,
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result.ExitCode != 1 {
		t.Errorf("expected exit code 1 (block), got %d", result.ExitCode)
	}
}

func TestBlock_NoEmissions(t *testing.T) {
	dir := t.TempDir() // empty dir

	result, err := Evaluate(EvaluateParams{
		EmissionsDir: dir,
		ProfileData:  minimalProfile(true),
		CIPassed:     true,
		LogWriter:    os.Stderr,
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result.ExitCode != 1 {
		t.Errorf("expected exit code 1 (block for no emissions), got %d", result.ExitCode)
	}
}

func TestDryRun(t *testing.T) {
	dir := t.TempDir() // empty dir -> would block

	result, err := Evaluate(EvaluateParams{
		EmissionsDir: dir,
		ProfileData:  minimalProfile(true),
		CIPassed:     true,
		DryRun:       true,
		LogWriter:    os.Stderr,
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result.ExitCode != 0 {
		t.Errorf("expected exit code 0 (dry-run override), got %d", result.ExitCode)
	}
}

func TestHumanReviewRequired_LowConfidence(t *testing.T) {
	dir := t.TempDir()
	// Low confidence will not satisfy auto-merge condition "aggregate_confidence >= 0.80"
	writeEmission(t, dir, &emission.Emission{
		PanelName:        "code-review",
		AggregateVerdict: "approve",
		ConfidenceScore:  0.40,
		RiskLevel:        "low",
	})

	result, err := Evaluate(EvaluateParams{
		EmissionsDir: dir,
		ProfileData:  minimalProfile(true),
		CIPassed:     true,
		LogWriter:    os.Stderr,
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if result.ExitCode != 2 {
		t.Errorf("expected exit code 2 (human review required), got %d", result.ExitCode)
	}
}

func TestManifestStructure(t *testing.T) {
	dir := t.TempDir()
	writeEmission(t, dir, &emission.Emission{
		PanelName:        "code-review",
		AggregateVerdict: "approve",
		ConfidenceScore:  0.95,
		RiskLevel:        "low",
	})
	writeEmission(t, dir, &emission.Emission{
		PanelName:        "security-review",
		AggregateVerdict: "approve",
		ConfidenceScore:  0.90,
		RiskLevel:        "low",
	})

	result, err := Evaluate(EvaluateParams{
		EmissionsDir: dir,
		ProfileData:  minimalProfile(true),
		CIPassed:     true,
		CommitSHA:    "abc1234567890",
		PRNumber:     42,
		Repo:         "SET-Apps/ai-submodule",
		LogWriter:    os.Stderr,
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}

	m := result.Manifest
	if m.ManifestVersion != "1.0" {
		t.Errorf("expected manifest version '1.0', got %q", m.ManifestVersion)
	}
	if m.PolicyProfileUsed != "test-profile" {
		t.Errorf("expected profile 'test-profile', got %q", m.PolicyProfileUsed)
	}
	if m.Repository == nil {
		t.Fatal("expected repository info")
	}
	if m.Repository.Owner != "SET-Apps" {
		t.Errorf("expected owner 'SET-Apps', got %q", m.Repository.Owner)
	}
	if m.Repository.Name != "ai-submodule" {
		t.Errorf("expected name 'ai-submodule', got %q", m.Repository.Name)
	}
	if m.Repository.PRNumber != 42 {
		t.Errorf("expected PR number 42, got %d", m.Repository.PRNumber)
	}
	if len(m.PanelsExecuted) != 2 {
		t.Errorf("expected 2 panels, got %d", len(m.PanelsExecuted))
	}
	if len(m.Decision.PolicyRulesEvaluated) == 0 {
		t.Error("expected policy rules to be populated in manifest")
	}
}
