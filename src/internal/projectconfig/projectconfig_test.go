package projectconfig

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

const testYAML = `# Project configuration
name: "test-project"
languages:
  - python
  - go
framework: null

# Governance section
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

func TestLoadFromBytes(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}
	if cfg.Path() != "test.yaml" {
		t.Errorf("expected path 'test.yaml', got %q", cfg.Path())
	}
}

func TestLoadFromBytes_InvalidYAML(t *testing.T) {
	_, err := LoadFromBytes([]byte("a: {\n  b: [}"), "bad.yaml")
	if err == nil {
		t.Fatal("expected error for invalid YAML")
	}
}

func TestGet_ScalarString(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	val, err := cfg.Get("name")
	if err != nil {
		t.Fatalf("Get('name') failed: %v", err)
	}
	if val != "test-project" {
		t.Errorf("expected 'test-project', got %q", val)
	}
}

func TestGet_NestedScalar(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	val, err := cfg.Get("governance.parallel_coders")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if val != "5" {
		t.Errorf("expected '5', got %q", val)
	}
}

func TestGet_DeeplyNested(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	val, err := cfg.Get("conventions.git.commit_style")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if val != "conventional" {
		t.Errorf("expected 'conventional', got %q", val)
	}
}

func TestGet_BoolValue(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	val, err := cfg.Get("governance.use_project_manager")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if val != "false" {
		t.Errorf("expected 'false', got %q", val)
	}
}

func TestGet_NullValue(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	val, err := cfg.Get("framework")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if val != "null" {
		t.Errorf("expected 'null', got %q", val)
	}
}

func TestGet_NonExistentKey(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	_, err = cfg.Get("nonexistent.key")
	if err == nil {
		t.Fatal("expected error for non-existent key")
	}
	if !strings.Contains(err.Error(), "not found") {
		t.Errorf("expected 'not found' in error, got: %v", err)
	}
}

func TestGet_SequenceValue(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	val, err := cfg.Get("languages")
	if err != nil {
		t.Fatalf("Get('languages') failed: %v", err)
	}
	// Should return YAML representation
	if !strings.Contains(val, "python") || !strings.Contains(val, "go") {
		t.Errorf("expected sequence to contain 'python' and 'go', got %q", val)
	}
}

func TestSet_ExistingScalar(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	if err := cfg.Set("name", "updated-project"); err != nil {
		t.Fatalf("Set failed: %v", err)
	}

	val, err := cfg.Get("name")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if val != "updated-project" {
		t.Errorf("expected 'updated-project', got %q", val)
	}
}

func TestSet_NestedExisting(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	if err := cfg.Set("governance.parallel_coders", "10"); err != nil {
		t.Fatalf("Set failed: %v", err)
	}

	val, err := cfg.Get("governance.parallel_coders")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if val != "10" {
		t.Errorf("expected '10', got %q", val)
	}
}

func TestSet_NewKey(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	if err := cfg.Set("governance.evaluation_tier", "full"); err != nil {
		t.Fatalf("Set failed: %v", err)
	}

	val, err := cfg.Get("governance.evaluation_tier")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if val != "full" {
		t.Errorf("expected 'full', got %q", val)
	}
}

func TestSet_NewNestedPath(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	if err := cfg.Set("new_section.nested.key", "value"); err != nil {
		t.Fatalf("Set failed: %v", err)
	}

	val, err := cfg.Get("new_section.nested.key")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if val != "value" {
		t.Errorf("expected 'value', got %q", val)
	}
}

func TestSet_BoolCoercion(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	if err := cfg.Set("governance.use_project_manager", "true"); err != nil {
		t.Fatalf("Set failed: %v", err)
	}

	val, err := cfg.Get("governance.use_project_manager")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if val != "true" {
		t.Errorf("expected 'true', got %q", val)
	}
}

func TestSet_IntCoercion(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	if err := cfg.Set("governance.parallel_coders", "3"); err != nil {
		t.Fatalf("Set failed: %v", err)
	}

	val, err := cfg.Get("governance.parallel_coders")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if val != "3" {
		t.Errorf("expected '3', got %q", val)
	}
}

func TestSet_SequenceRefused(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	err = cfg.Set("languages", "python")
	if err == nil {
		t.Fatal("expected error when setting a sequence value")
	}
	if !strings.Contains(err.Error(), "sequence") {
		t.Errorf("expected error about sequence, got: %v", err)
	}
}

func TestSaveAndLoad_RoundTrip(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	tmpDir := t.TempDir()
	outPath := filepath.Join(tmpDir, "project.yaml")

	if err := cfg.Set("governance.parallel_coders", "8"); err != nil {
		t.Fatalf("Set failed: %v", err)
	}

	if err := cfg.SaveTo(outPath); err != nil {
		t.Fatalf("SaveTo failed: %v", err)
	}

	// Reload and verify
	cfg2, err := Load(outPath)
	if err != nil {
		t.Fatalf("Load failed: %v", err)
	}

	val, err := cfg2.Get("governance.parallel_coders")
	if err != nil {
		t.Fatalf("Get failed: %v", err)
	}
	if val != "8" {
		t.Errorf("expected '8' after round-trip, got %q", val)
	}

	// Verify original values survived
	name, err := cfg2.Get("name")
	if err != nil {
		t.Fatalf("Get name failed: %v", err)
	}
	if name != "test-project" {
		t.Errorf("expected 'test-project', got %q", name)
	}
}

func TestCommentPreservation(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	if err := cfg.Set("name", "changed"); err != nil {
		t.Fatalf("Set failed: %v", err)
	}

	data, err := cfg.Bytes()
	if err != nil {
		t.Fatalf("Bytes failed: %v", err)
	}

	output := string(data)
	if !strings.Contains(output, "# Project configuration") {
		t.Error("head comment lost after round-trip")
	}
	if !strings.Contains(output, "# Governance section") {
		t.Error("governance section comment lost after round-trip")
	}
}

func TestFlatten(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	kvs := cfg.Flatten()
	if len(kvs) == 0 {
		t.Fatal("expected non-empty flatten result")
	}

	// Build a map for easier lookup
	m := make(map[string]string)
	for _, kv := range kvs {
		m[kv.Key] = kv.Value
	}

	if m["name"] != "test-project" {
		t.Errorf("expected name='test-project', got %q", m["name"])
	}
	if m["governance.parallel_coders"] != "5" {
		t.Errorf("expected governance.parallel_coders='5', got %q", m["governance.parallel_coders"])
	}
	if m["conventions.git.commit_style"] != "conventional" {
		t.Errorf("expected conventions.git.commit_style='conventional', got %q", m["conventions.git.commit_style"])
	}

	// Verify sorted order
	for i := 1; i < len(kvs); i++ {
		if kvs[i].Key < kvs[i-1].Key {
			t.Errorf("flatten result not sorted: %q before %q", kvs[i-1].Key, kvs[i].Key)
			break
		}
	}
}

func TestFlatten_IncludesSequences(t *testing.T) {
	cfg, err := LoadFromBytes([]byte(testYAML), "test.yaml")
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	kvs := cfg.Flatten()
	m := make(map[string]string)
	for _, kv := range kvs {
		m[kv.Key] = kv.Value
	}

	langVal, ok := m["languages"]
	if !ok {
		t.Fatal("expected 'languages' key in flattened output")
	}
	if !strings.Contains(langVal, "python") || !strings.Contains(langVal, "go") {
		t.Errorf("expected languages to contain 'python, go', got %q", langVal)
	}
}

func TestValidate_ValidConfig(t *testing.T) {
	schemaJSON := `{
		"type": "object",
		"properties": {
			"name": {"type": "string"},
			"governance": {
				"type": "object",
				"properties": {
					"parallel_coders": {"type": "integer", "minimum": -1, "maximum": 10}
				}
			}
		}
	}`

	yamlData := []byte(`name: "test"
governance:
  parallel_coders: 5
`)

	err := Validate(yamlData, []byte(schemaJSON))
	if err != nil {
		t.Fatalf("expected valid config, got error: %v", err)
	}
}

func TestValidate_InvalidConfig(t *testing.T) {
	schemaJSON := `{
		"type": "object",
		"properties": {
			"name": {"type": "string"},
			"governance": {
				"type": "object",
				"properties": {
					"parallel_coders": {"type": "integer", "minimum": -1, "maximum": 10}
				}
			}
		}
	}`

	yamlData := []byte(`name: 123
governance:
  parallel_coders: 99
`)

	err := Validate(yamlData, []byte(schemaJSON))
	if err == nil {
		t.Fatal("expected validation error for out-of-range value")
	}
	if !strings.Contains(err.Error(), "validation") {
		t.Errorf("expected validation error, got: %v", err)
	}
}

func TestValidate_EmptySchema(t *testing.T) {
	err := Validate([]byte(`name: test`), nil)
	if err != nil {
		t.Fatalf("expected nil for empty schema, got: %v", err)
	}
}

func TestLoad_FileNotFound(t *testing.T) {
	_, err := Load("/nonexistent/path/project.yaml")
	if err == nil {
		t.Fatal("expected error for non-existent file")
	}
}

func TestSave_WritesFile(t *testing.T) {
	tmpDir := t.TempDir()
	outPath := filepath.Join(tmpDir, "project.yaml")

	cfg, err := LoadFromBytes([]byte(testYAML), outPath)
	if err != nil {
		t.Fatalf("LoadFromBytes failed: %v", err)
	}

	if err := cfg.Save(); err != nil {
		t.Fatalf("Save failed: %v", err)
	}

	data, err := os.ReadFile(outPath)
	if err != nil {
		t.Fatalf("ReadFile failed: %v", err)
	}
	if !strings.Contains(string(data), "test-project") {
		t.Error("saved file does not contain expected content")
	}
}

func TestCoerceScalar(t *testing.T) {
	tests := []struct {
		input    string
		wantTag  string
		wantVal  string
	}{
		{"true", "!!bool", "true"},
		{"false", "!!bool", "false"},
		{"True", "!!bool", "true"},
		{"FALSE", "!!bool", "false"},
		{"42", "!!int", "42"},
		{"-1", "!!int", "-1"},
		{"3.14", "!!float", "3.14"},
		{"null", "!!null", "null"},
		{"~", "!!null", "~"},
		{"", "!!null", ""},
		{"hello", "!!str", "hello"},
		{"hello world", "!!str", "hello world"},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			node := coerceScalar(tt.input)
			if node.Tag != tt.wantTag {
				t.Errorf("coerceScalar(%q): tag=%q, want %q", tt.input, node.Tag, tt.wantTag)
			}
			if node.Value != tt.wantVal {
				t.Errorf("coerceScalar(%q): value=%q, want %q", tt.input, node.Value, tt.wantVal)
			}
		})
	}
}
