package embed

import (
	"strings"
	"testing"
)

func TestEmbeddedContentPresent(t *testing.T) {
	fs := GovernanceFS()

	// The _content directory should exist and contain at least the .gitkeep
	entries, err := fs.ReadDir("_content")
	if err != nil {
		t.Fatalf("failed to read embedded _content directory: %v", err)
	}
	if len(entries) == 0 {
		t.Error("expected at least one entry in embedded _content directory")
	}
}

func TestGovernanceFSReturnsFS(t *testing.T) {
	fs := GovernanceFS()
	// Verify the returned FS is functional
	_, err := fs.ReadDir("_content")
	if err != nil {
		t.Fatalf("GovernanceFS() returned non-functional FS: %v", err)
	}
}

func TestHasContent(t *testing.T) {
	// HasContent should return true when governance content is present,
	// false when only .gitkeep exists. In test builds after prepare-embed,
	// this should be true.
	result := HasContent()
	// We just verify it doesn't panic — the actual value depends on
	// whether prepare-embed was run before tests.
	_ = result
}

func TestReadFile(t *testing.T) {
	if !HasContent() {
		t.Skip("no governance content embedded — run make prepare-embed first")
	}

	// Read a known file
	data, err := ReadFile("instructions.md")
	if err != nil {
		t.Fatalf("failed to read instructions.md: %v", err)
	}
	if len(data) == 0 {
		t.Error("instructions.md is empty")
	}
	if !strings.Contains(string(data), "AI Instructions") {
		t.Error("instructions.md does not contain expected header")
	}
}

func TestReadDir(t *testing.T) {
	if !HasContent() {
		t.Skip("no governance content embedded — run make prepare-embed first")
	}

	entries, err := ReadDir("policy")
	if err != nil {
		t.Fatalf("failed to read policy directory: %v", err)
	}
	if len(entries) == 0 {
		t.Error("expected at least one policy file")
	}

	// Verify we find default.yaml
	found := false
	for _, e := range entries {
		if e.Name() == "default.yaml" {
			found = true
			break
		}
	}
	if !found {
		t.Error("expected default.yaml in policy directory")
	}
}

func TestListPolicies(t *testing.T) {
	if !HasContent() {
		t.Skip("no governance content embedded — run make prepare-embed first")
	}

	policies, err := ListPolicies()
	if err != nil {
		t.Fatalf("ListPolicies failed: %v", err)
	}
	if len(policies) == 0 {
		t.Fatal("expected at least one policy")
	}

	// Should contain "default"
	found := false
	for _, p := range policies {
		if p == "default" {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("expected 'default' in policies, got: %v", policies)
	}
}

func TestListSchemas(t *testing.T) {
	if !HasContent() {
		t.Skip("no governance content embedded — run make prepare-embed first")
	}

	schemas, err := ListSchemas()
	if err != nil {
		t.Fatalf("ListSchemas failed: %v", err)
	}
	if len(schemas) == 0 {
		t.Fatal("expected at least one schema")
	}

	// Should contain panel-output.schema.json
	found := false
	for _, s := range schemas {
		if s == "panel-output.schema.json" {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("expected 'panel-output.schema.json' in schemas, got: %v", schemas)
	}
}

func TestListReviewPrompts(t *testing.T) {
	if !HasContent() {
		t.Skip("no governance content embedded — run make prepare-embed first")
	}

	prompts, err := ListReviewPrompts()
	if err != nil {
		t.Fatalf("ListReviewPrompts failed: %v", err)
	}
	if len(prompts) == 0 {
		t.Fatal("expected at least one review prompt")
	}

	// Should contain code-review
	found := false
	for _, p := range prompts {
		if p == "code-review" {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("expected 'code-review' in prompts, got: %v", prompts)
	}
}

func TestListPersonas(t *testing.T) {
	if !HasContent() {
		t.Skip("no governance content embedded — run make prepare-embed first")
	}

	personas, err := ListPersonas()
	if err != nil {
		t.Fatalf("ListPersonas failed: %v", err)
	}
	if len(personas) == 0 {
		t.Fatal("expected at least one persona")
	}

	// Should contain coder
	found := false
	for _, p := range personas {
		if p == "coder" {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("expected 'coder' in personas, got: %v", personas)
	}
}

func TestListCommands(t *testing.T) {
	if !HasContent() {
		t.Skip("no governance content embedded — run make prepare-embed first")
	}

	commands, err := ListCommands()
	if err != nil {
		t.Fatalf("ListCommands failed: %v", err)
	}
	if len(commands) == 0 {
		t.Fatal("expected at least one command")
	}
}

func TestGetPolicy(t *testing.T) {
	if !HasContent() {
		t.Skip("no governance content embedded — run make prepare-embed first")
	}

	data, err := GetPolicy("default")
	if err != nil {
		t.Fatalf("GetPolicy(default) failed: %v", err)
	}
	if len(data) == 0 {
		t.Error("default policy is empty")
	}
	if !strings.Contains(string(data), "profile_name: default") {
		t.Error("default policy does not contain expected profile_name")
	}
}

func TestGetPolicyNotFound(t *testing.T) {
	_, err := GetPolicy("nonexistent-policy-that-does-not-exist")
	if err == nil {
		t.Error("expected error for nonexistent policy")
	}
}

func TestGetSchema(t *testing.T) {
	if !HasContent() {
		t.Skip("no governance content embedded — run make prepare-embed first")
	}

	data, err := GetSchema("panel-output.schema.json")
	if err != nil {
		t.Fatalf("GetSchema(panel-output.schema.json) failed: %v", err)
	}
	if len(data) == 0 {
		t.Error("panel-output.schema.json is empty")
	}
}

func TestContentHash(t *testing.T) {
	hash := ContentHash()
	if hash == "" {
		t.Fatal("ContentHash returned empty string")
	}
	if !strings.HasPrefix(hash, "sha256:") {
		t.Errorf("expected sha256: prefix, got: %s", hash)
	}

	// Hash should be deterministic
	hash2 := ContentHash()
	if hash != hash2 {
		t.Errorf("ContentHash not deterministic: %s != %s", hash, hash2)
	}
}

func TestSubFS(t *testing.T) {
	if !HasContent() {
		t.Skip("no governance content embedded — run make prepare-embed first")
	}

	policyFS, err := SubFS("policy")
	if err != nil {
		t.Fatalf("SubFS(policy) failed: %v", err)
	}

	// Should be able to read default.yaml directly (no _content prefix)
	data, err := policyFS.Open("default.yaml")
	if err != nil {
		t.Fatalf("failed to open default.yaml from SubFS: %v", err)
	}
	data.Close()
}

// hasDocs checks whether the embedded content includes the docs subdirectory.
func hasDocs() bool {
	docs, err := ListDocs()
	return err == nil && len(docs) > 0
}

func TestListDocs(t *testing.T) {
	if !hasDocs() {
		t.Skip("no docs content embedded — run make prepare-embed first")
	}

	docs, err := ListDocs()
	if err != nil {
		t.Fatalf("ListDocs failed: %v", err)
	}
	if len(docs) == 0 {
		t.Fatal("expected at least one doc topic")
	}

	// Should contain a known topic
	found := false
	for _, d := range docs {
		if d == "guides/installation" {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("expected 'guides/installation' in docs, got: %v", docs)
	}
}

func TestGetDoc(t *testing.T) {
	if !hasDocs() {
		t.Skip("no docs content embedded — run make prepare-embed first")
	}

	data, err := GetDoc("guides/installation")
	if err != nil {
		t.Fatalf("GetDoc(guides/installation) failed: %v", err)
	}
	if len(data) == 0 {
		t.Error("guides/installation doc is empty")
	}
}

func TestGetDocNotFound(t *testing.T) {
	_, err := GetDoc("nonexistent-topic-that-does-not-exist")
	if err == nil {
		t.Error("expected error for nonexistent doc topic")
	}
}

func TestListLanguageTemplates(t *testing.T) {
	if !HasContent() {
		t.Skip("no governance content embedded — run make prepare-embed first")
	}

	langs, err := ListLanguageTemplates()
	if err != nil {
		t.Fatalf("ListLanguageTemplates failed: %v", err)
	}
	if len(langs) == 0 {
		t.Fatal("expected at least one language template")
	}

	// Should contain "go"
	found := false
	for _, l := range langs {
		if l == "go" {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("expected 'go' in language templates, got: %v", langs)
	}
}
