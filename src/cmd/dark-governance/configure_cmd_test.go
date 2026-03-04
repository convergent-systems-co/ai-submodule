package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/SET-Apps/ai-submodule/src/internal/projectconfig"
)

const testConfigYAML = `# Test config
name: "my-project"
languages:
  - go
framework: null

governance:
  policy_profile: "default"
  parallel_coders: 5
  use_project_manager: false
  skip_panel_validation: false

conventions:
  git:
    branch_pattern: "{network_id}/{type}/{number}/{name}"
    commit_style: "conventional"
`

// setupTestConfig writes a project.yaml to a temp directory and returns the path.
func setupTestConfig(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	path := filepath.Join(dir, "project.yaml")
	if err := os.WriteFile(path, []byte(testConfigYAML), 0644); err != nil {
		t.Fatalf("failed to write test config: %v", err)
	}
	return path
}

func TestRunConfigureList(t *testing.T) {
	path := setupTestConfig(t)

	// Override flagConfig to point to our test file
	origFlagConfig := flagConfig
	flagConfig = path
	defer func() { flagConfig = origFlagConfig }()

	// Capture stdout
	origStdout := os.Stdout
	r, w, _ := os.Pipe()
	os.Stdout = w

	err := runConfigureList()

	w.Close()
	os.Stdout = origStdout

	if err != nil {
		t.Fatalf("runConfigureList failed: %v", err)
	}

	buf := make([]byte, 4096)
	n, _ := r.Read(buf)
	output := string(buf[:n])

	// Should contain flattened keys
	if !strings.Contains(output, "name") {
		t.Error("expected 'name' in output")
	}
	if !strings.Contains(output, "governance.parallel_coders") {
		t.Error("expected 'governance.parallel_coders' in output")
	}
	if !strings.Contains(output, "settings") {
		t.Error("expected settings count in output")
	}
}

func TestRunConfigureList_JSON(t *testing.T) {
	path := setupTestConfig(t)

	origFlagConfig := flagConfig
	origFlagJSON := flagJSON
	flagConfig = path
	flagJSON = true
	defer func() {
		flagConfig = origFlagConfig
		flagJSON = origFlagJSON
	}()

	origStdout := os.Stdout
	r, w, _ := os.Pipe()
	os.Stdout = w

	err := runConfigureList()

	w.Close()
	os.Stdout = origStdout

	if err != nil {
		t.Fatalf("runConfigureList JSON failed: %v", err)
	}

	buf := make([]byte, 8192)
	n, _ := r.Read(buf)
	output := string(buf[:n])

	if !strings.Contains(output, `"key"`) {
		t.Error("expected JSON key field in output")
	}
	if !strings.Contains(output, `"value"`) {
		t.Error("expected JSON value field in output")
	}
}

func TestRunConfigureGet(t *testing.T) {
	path := setupTestConfig(t)

	origFlagConfig := flagConfig
	flagConfig = path
	defer func() { flagConfig = origFlagConfig }()

	origStdout := os.Stdout
	r, w, _ := os.Pipe()
	os.Stdout = w

	err := runConfigureGet("governance.parallel_coders")

	w.Close()
	os.Stdout = origStdout

	if err != nil {
		t.Fatalf("runConfigureGet failed: %v", err)
	}

	buf := make([]byte, 1024)
	n, _ := r.Read(buf)
	output := strings.TrimSpace(string(buf[:n]))

	if output != "5" {
		t.Errorf("expected '5', got %q", output)
	}
}

func TestRunConfigureGet_NestedKey(t *testing.T) {
	path := setupTestConfig(t)

	origFlagConfig := flagConfig
	flagConfig = path
	defer func() { flagConfig = origFlagConfig }()

	origStdout := os.Stdout
	r, w, _ := os.Pipe()
	os.Stdout = w

	err := runConfigureGet("conventions.git.commit_style")

	w.Close()
	os.Stdout = origStdout

	if err != nil {
		t.Fatalf("runConfigureGet failed: %v", err)
	}

	buf := make([]byte, 1024)
	n, _ := r.Read(buf)
	output := strings.TrimSpace(string(buf[:n]))

	if output != "conventional" {
		t.Errorf("expected 'conventional', got %q", output)
	}
}

func TestRunConfigureGet_NonExistent(t *testing.T) {
	path := setupTestConfig(t)

	origFlagConfig := flagConfig
	flagConfig = path
	defer func() { flagConfig = origFlagConfig }()

	err := runConfigureGet("nonexistent.key")
	if err == nil {
		t.Fatal("expected error for non-existent key")
	}
}

func TestRunConfigureGet_JSON(t *testing.T) {
	path := setupTestConfig(t)

	origFlagConfig := flagConfig
	origFlagJSON := flagJSON
	flagConfig = path
	flagJSON = true
	defer func() {
		flagConfig = origFlagConfig
		flagJSON = origFlagJSON
	}()

	origStdout := os.Stdout
	r, w, _ := os.Pipe()
	os.Stdout = w

	err := runConfigureGet("name")

	w.Close()
	os.Stdout = origStdout

	if err != nil {
		t.Fatalf("runConfigureGet JSON failed: %v", err)
	}

	buf := make([]byte, 1024)
	n, _ := r.Read(buf)
	output := string(buf[:n])

	if !strings.Contains(output, "my-project") {
		t.Errorf("expected 'my-project' in JSON output, got: %s", output)
	}
}

func TestRunConfigureSet(t *testing.T) {
	path := setupTestConfig(t)

	origFlagConfig := flagConfig
	flagConfig = path
	defer func() { flagConfig = origFlagConfig }()

	origStdout := os.Stdout
	_, w, _ := os.Pipe()
	os.Stdout = w

	err := runConfigureSet("governance.parallel_coders=10")

	w.Close()
	os.Stdout = origStdout

	if err != nil {
		t.Fatalf("runConfigureSet failed: %v", err)
	}

	// Reload and verify
	cfg, err := projectconfig.Load(path)
	if err != nil {
		t.Fatalf("failed to reload config: %v", err)
	}

	val, err := cfg.Get("governance.parallel_coders")
	if err != nil {
		t.Fatalf("failed to get value: %v", err)
	}
	if val != "10" {
		t.Errorf("expected '10', got %q", val)
	}
}

func TestRunConfigureSet_BoolValue(t *testing.T) {
	path := setupTestConfig(t)

	origFlagConfig := flagConfig
	flagConfig = path
	defer func() { flagConfig = origFlagConfig }()

	origStdout := os.Stdout
	_, w, _ := os.Pipe()
	os.Stdout = w

	err := runConfigureSet("governance.use_project_manager=true")

	w.Close()
	os.Stdout = origStdout

	if err != nil {
		t.Fatalf("runConfigureSet failed: %v", err)
	}

	cfg, err := projectconfig.Load(path)
	if err != nil {
		t.Fatalf("failed to reload config: %v", err)
	}

	val, err := cfg.Get("governance.use_project_manager")
	if err != nil {
		t.Fatalf("failed to get value: %v", err)
	}
	if val != "true" {
		t.Errorf("expected 'true', got %q", val)
	}
}

func TestRunConfigureSet_NewKey(t *testing.T) {
	path := setupTestConfig(t)

	origFlagConfig := flagConfig
	flagConfig = path
	defer func() { flagConfig = origFlagConfig }()

	origStdout := os.Stdout
	_, w, _ := os.Pipe()
	os.Stdout = w

	err := runConfigureSet("governance.evaluation_tier=full")

	w.Close()
	os.Stdout = origStdout

	if err != nil {
		t.Fatalf("runConfigureSet failed: %v", err)
	}

	cfg, err := projectconfig.Load(path)
	if err != nil {
		t.Fatalf("failed to reload config: %v", err)
	}

	val, err := cfg.Get("governance.evaluation_tier")
	if err != nil {
		t.Fatalf("failed to get value: %v", err)
	}
	if val != "full" {
		t.Errorf("expected 'full', got %q", val)
	}
}

func TestRunConfigureSet_InvalidFormat(t *testing.T) {
	path := setupTestConfig(t)

	origFlagConfig := flagConfig
	flagConfig = path
	defer func() { flagConfig = origFlagConfig }()

	err := runConfigureSet("no-equals-sign")
	if err == nil {
		t.Fatal("expected error for invalid format")
	}
	if !strings.Contains(err.Error(), "key=value") {
		t.Errorf("expected key=value error message, got: %v", err)
	}
}

func TestRunConfigureSet_JSON(t *testing.T) {
	path := setupTestConfig(t)

	origFlagConfig := flagConfig
	origFlagJSON := flagJSON
	flagConfig = path
	flagJSON = true
	defer func() {
		flagConfig = origFlagConfig
		flagJSON = origFlagJSON
	}()

	origStdout := os.Stdout
	r, w, _ := os.Pipe()
	os.Stdout = w

	err := runConfigureSet("name=updated")

	w.Close()
	os.Stdout = origStdout

	if err != nil {
		t.Fatalf("runConfigureSet JSON failed: %v", err)
	}

	buf := make([]byte, 1024)
	n, _ := r.Read(buf)
	output := string(buf[:n])

	if !strings.Contains(output, `"status"`) {
		t.Error("expected 'status' in JSON output")
	}
	if !strings.Contains(output, "updated") {
		t.Error("expected 'updated' in JSON output")
	}
}

func TestRunConfigureInteractiveWithReader(t *testing.T) {
	dir := t.TempDir()
	configPath := filepath.Join(dir, "project.yaml")

	// Write initial config
	if err := os.WriteFile(configPath, defaultProjectYAML(), 0644); err != nil {
		t.Fatalf("failed to write config: %v", err)
	}

	origFlagConfig := flagConfig
	flagConfig = configPath
	defer func() { flagConfig = origFlagConfig }()

	// Simulate user input: set name, skip policy, set parallel_coders, skip rest
	input := "my-new-project\n\n3\n\n\n"
	reader := strings.NewReader(input)

	origStdout := os.Stdout
	_, w, _ := os.Pipe()
	os.Stdout = w

	err := runConfigureInteractiveWithReader(reader)

	w.Close()
	os.Stdout = origStdout

	if err != nil {
		t.Fatalf("interactive mode failed: %v", err)
	}

	// Verify saved values
	cfg, err := projectconfig.Load(configPath)
	if err != nil {
		t.Fatalf("failed to reload config: %v", err)
	}

	name, err := cfg.Get("name")
	if err != nil {
		t.Fatalf("failed to get name: %v", err)
	}
	if name != "my-new-project" {
		t.Errorf("expected 'my-new-project', got %q", name)
	}

	pc, err := cfg.Get("governance.parallel_coders")
	if err != nil {
		t.Fatalf("failed to get parallel_coders: %v", err)
	}
	if pc != "3" {
		t.Errorf("expected '3', got %q", pc)
	}
}

func TestRunConfigureInteractiveWithReader_AllDefaults(t *testing.T) {
	dir := t.TempDir()
	configPath := filepath.Join(dir, "project.yaml")

	if err := os.WriteFile(configPath, defaultProjectYAML(), 0644); err != nil {
		t.Fatalf("failed to write config: %v", err)
	}

	origFlagConfig := flagConfig
	flagConfig = configPath
	defer func() { flagConfig = origFlagConfig }()

	// All empty inputs = keep defaults
	input := "\n\n\n\n\n"
	reader := strings.NewReader(input)

	origStdout := os.Stdout
	_, w, _ := os.Pipe()
	os.Stdout = w

	err := runConfigureInteractiveWithReader(reader)

	w.Close()
	os.Stdout = origStdout

	if err != nil {
		t.Fatalf("interactive mode failed: %v", err)
	}

	cfg, err := projectconfig.Load(configPath)
	if err != nil {
		t.Fatalf("failed to reload config: %v", err)
	}

	// Default values should be preserved
	pp, err := cfg.Get("governance.policy_profile")
	if err != nil {
		t.Fatalf("failed to get policy_profile: %v", err)
	}
	if pp != "default" {
		t.Errorf("expected 'default', got %q", pp)
	}
}

func TestRunConfigureInteractiveWithReader_NewFile(t *testing.T) {
	dir := t.TempDir()
	configPath := filepath.Join(dir, "project.yaml")
	// Do not create the file - interactive mode should create from defaults

	origFlagConfig := flagConfig
	flagConfig = configPath
	defer func() { flagConfig = origFlagConfig }()

	input := "brand-new\n\n\n\n\n"
	reader := strings.NewReader(input)

	origStdout := os.Stdout
	_, w, _ := os.Pipe()
	os.Stdout = w

	err := runConfigureInteractiveWithReader(reader)

	w.Close()
	os.Stdout = origStdout

	if err != nil {
		t.Fatalf("interactive mode (new file) failed: %v", err)
	}

	// File should exist now
	if _, statErr := os.Stat(configPath); statErr != nil {
		t.Fatal("config file was not created")
	}

	cfg, err := projectconfig.Load(configPath)
	if err != nil {
		t.Fatalf("failed to load created config: %v", err)
	}

	name, err := cfg.Get("name")
	if err != nil {
		t.Fatalf("failed to get name: %v", err)
	}
	if name != "brand-new" {
		t.Errorf("expected 'brand-new', got %q", name)
	}
}

func TestResolveConfigPath_DefaultCwd(t *testing.T) {
	origFlagConfig := flagConfig
	flagConfig = ""
	defer func() { flagConfig = origFlagConfig }()

	path, err := resolveConfigPath()
	if err != nil {
		t.Fatalf("resolveConfigPath failed: %v", err)
	}

	cwd, _ := os.Getwd()
	expected := filepath.Join(cwd, "project.yaml")
	if path != expected {
		t.Errorf("expected %q, got %q", expected, path)
	}
}

func TestResolveConfigPath_CustomPath(t *testing.T) {
	origFlagConfig := flagConfig
	flagConfig = "/custom/path/config.yaml"
	defer func() { flagConfig = origFlagConfig }()

	path, err := resolveConfigPath()
	if err != nil {
		t.Fatalf("resolveConfigPath failed: %v", err)
	}

	if path != "/custom/path/config.yaml" {
		t.Errorf("expected '/custom/path/config.yaml', got %q", path)
	}
}
