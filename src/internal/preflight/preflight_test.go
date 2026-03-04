package preflight

import (
	"os"
	"path/filepath"
	"testing"
)

func TestValidProjectYAML(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "project.yaml")
	os.WriteFile(path, []byte("project_name: test-project\nlanguage: go\n"), 0644)

	r := ValidateProjectYAML(path)
	if !r.Valid {
		t.Fatalf("expected valid, got: %s", r.Summary())
	}
	if len(r.Languages) != 1 || r.Languages[0] != "go" {
		t.Fatalf("expected [go], got %v", r.Languages)
	}
}

func TestFileNotFound(t *testing.T) {
	r := ValidateProjectYAML("/nonexistent/project.yaml")
	if r.Valid {
		t.Fatal("expected invalid for missing file")
	}
	errs := r.Errors()
	if len(errs) != 1 {
		t.Fatalf("expected 1 error, got %d", len(errs))
	}
}

func TestInvalidYAMLSyntax(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "project.yaml")
	os.WriteFile(path, []byte(":\n  :\n    - [invalid yaml{{{"), 0644)

	r := ValidateProjectYAML(path)
	if r.Valid {
		t.Fatal("expected invalid for bad YAML")
	}
}

func TestMissingProjectName(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "project.yaml")
	os.WriteFile(path, []byte("language: go\n"), 0644)

	r := ValidateProjectYAML(path)
	if r.Valid {
		t.Fatal("expected invalid when project_name missing")
	}
	errs := r.Errors()
	found := false
	for _, e := range errs {
		if e.Message == "missing required key: project_name" {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected 'missing required key: project_name' error, got %v", errs)
	}
}

func TestLanguageLanguagesConflict(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "project.yaml")
	content := "project_name: test\nlanguage: go\nlanguages:\n  - go\n  - python\n"
	os.WriteFile(path, []byte(content), 0644)

	r := ValidateProjectYAML(path)
	warnings := r.Warnings()
	if len(warnings) == 0 {
		t.Fatal("expected warning for language/languages conflict")
	}
	found := false
	for _, w := range warnings {
		if w.Message == "both 'language' and 'languages' are set; 'languages' takes precedence" {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected conflict warning, got %v", warnings)
	}
	// When both set, languages takes precedence.
	if len(r.Languages) != 2 {
		t.Fatalf("expected 2 languages, got %v", r.Languages)
	}
}

func TestUnknownPolicyProfile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "project.yaml")
	content := "project_name: test\ngovernance:\n  policy_profile: nonexistent_profile\n"
	os.WriteFile(path, []byte(content), 0644)

	r := ValidateProjectYAML(path)
	warnings := r.Warnings()
	found := false
	for _, w := range warnings {
		if w.Message == `unknown policy_profile "nonexistent_profile"` {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected unknown profile warning, got %v", warnings)
	}
}

func TestResultErrorsAndWarnings(t *testing.T) {
	r := &Result{
		Findings: []Finding{
			{Level: "error", Message: "err1"},
			{Level: "warning", Message: "warn1"},
			{Level: "error", Message: "err2"},
			{Level: "warning", Message: "warn2"},
		},
	}

	errs := r.Errors()
	if len(errs) != 2 {
		t.Fatalf("expected 2 errors, got %d", len(errs))
	}

	warns := r.Warnings()
	if len(warns) != 2 {
		t.Fatalf("expected 2 warnings, got %d", len(warns))
	}
}

func TestValidProfile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "project.yaml")
	content := "project_name: test\ngovernance:\n  policy_profile: fin_pii_high\n"
	os.WriteFile(path, []byte(content), 0644)

	r := ValidateProjectYAML(path)
	if !r.Valid {
		t.Fatalf("expected valid, got: %s", r.Summary())
	}
	warnings := r.Warnings()
	if len(warnings) != 0 {
		t.Fatalf("expected no warnings for valid profile, got %v", warnings)
	}
}
