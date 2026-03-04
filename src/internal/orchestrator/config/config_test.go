package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadConfig_Defaults(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "project.yaml")
	os.WriteFile(path, []byte("project_name: test\n"), 0644)

	cfg, err := LoadConfig(path)
	if err != nil {
		t.Fatalf("load: %v", err)
	}

	if cfg.ParallelCoders != 5 {
		t.Fatalf("expected ParallelCoders=5, got %d", cfg.ParallelCoders)
	}
	if cfg.ParallelTechLeads != 3 {
		t.Fatalf("expected ParallelTechLeads=3, got %d", cfg.ParallelTechLeads)
	}
	if cfg.PolicyProfile != "default" {
		t.Fatalf("expected default profile, got %q", cfg.PolicyProfile)
	}
	if cfg.CoderMin != 1 {
		t.Fatalf("expected CoderMin=1, got %d", cfg.CoderMin)
	}
	if cfg.CoderMax != 5 {
		t.Fatalf("expected CoderMax=5, got %d", cfg.CoderMax)
	}
	if cfg.CommitStyle != "conventional" {
		t.Fatalf("expected conventional, got %q", cfg.CommitStyle)
	}
}

func TestLoadConfig_GovernanceOverrides(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "project.yaml")
	content := `project_name: test
governance:
  parallel_coders: 10
  policy_profile: fin_pii_high
  max_feedback_cycles: 5
  use_project_manager: true
`
	os.WriteFile(path, []byte(content), 0644)

	cfg, err := LoadConfig(path)
	if err != nil {
		t.Fatalf("load: %v", err)
	}

	if cfg.ParallelCoders != 10 {
		t.Fatalf("expected ParallelCoders=10, got %d", cfg.ParallelCoders)
	}
	if cfg.PolicyProfile != "fin_pii_high" {
		t.Fatalf("expected fin_pii_high, got %q", cfg.PolicyProfile)
	}
	if cfg.MaxFeedbackCycles != 5 {
		t.Fatalf("expected MaxFeedbackCycles=5, got %d", cfg.MaxFeedbackCycles)
	}
	if !cfg.UseProjectManager {
		t.Fatal("expected UseProjectManager=true")
	}
}

func TestLoadConfig_Conventions(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "project.yaml")
	content := `project_name: test
conventions:
  branch_pattern: 'NETWORK_ID/{type}/{number}/{name}'
  commit_style: 'angular'
`
	os.WriteFile(path, []byte(content), 0644)

	cfg, err := LoadConfig(path)
	if err != nil {
		t.Fatalf("load: %v", err)
	}

	if cfg.BranchPattern != "NETWORK_ID/{type}/{number}/{name}" {
		t.Fatalf("expected branch pattern, got %q", cfg.BranchPattern)
	}
	if cfg.CommitStyle != "angular" {
		t.Fatalf("expected angular, got %q", cfg.CommitStyle)
	}
}

func TestLoadConfig_InvalidCoderRange(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "project.yaml")
	content := `project_name: test
governance:
  coder_min: 10
  coder_max: 3
`
	os.WriteFile(path, []byte(content), 0644)

	_, err := LoadConfig(path)
	if err == nil {
		t.Fatal("expected error for coder_min > coder_max")
	}
}

func TestLoadConfig_FileNotFound(t *testing.T) {
	_, err := LoadConfig("/nonexistent/project.yaml")
	if err == nil {
		t.Fatal("expected error for missing file")
	}
}

func TestLoadConfig_InvalidYAML(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "project.yaml")
	os.WriteFile(path, []byte(":\n  :\n    - [bad{{{"), 0644)

	_, err := LoadConfig(path)
	if err == nil {
		t.Fatal("expected error for invalid YAML")
	}
}
