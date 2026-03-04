// Package embed provides go:embed declarations for governance content.
//
// At build time, the Makefile `prepare-embed` target copies governance/
// content into _content/ so it can be embedded into the binary.
// This ensures the binary is self-contained and does not require
// the governance directory at runtime.
package embed

import (
	"crypto/sha256"
	"embed"
	"fmt"
	"io/fs"
	"path/filepath"
	"sort"
	"strings"
	"sync"
)

// Content holds the embedded governance content from _content/.
// The _content/ directory is populated by `make prepare-embed` before build.
// During development/testing, it contains only a .gitkeep placeholder.
//
// The all: prefix ensures dotfiles and directories starting with _ are included.
//
//go:embed all:_content
var Content embed.FS

// contentRoot is the prefix for all embedded paths.
const contentRoot = "_content"

// cachedHash stores the computed content hash for reuse.
var (
	cachedHash     string
	cachedHashOnce sync.Once
)

// GovernanceFS returns the embedded filesystem containing governance content.
func GovernanceFS() embed.FS {
	return Content
}

// SubFS returns a sub-filesystem rooted at the given path within _content/.
// For example, SubFS("policy") returns an fs.FS rooted at _content/policy/.
func SubFS(path string) (fs.FS, error) {
	return fs.Sub(Content, filepath.Join(contentRoot, path))
}

// ReadFile reads a single file from the embedded content.
// The path is relative to _content/, e.g. "policy/default.yaml".
func ReadFile(path string) ([]byte, error) {
	return Content.ReadFile(filepath.Join(contentRoot, path))
}

// ReadDir lists entries in a directory within the embedded content.
// The path is relative to _content/, e.g. "policy".
func ReadDir(path string) ([]fs.DirEntry, error) {
	return Content.ReadDir(filepath.Join(contentRoot, path))
}

// ListPolicies returns the names of available policy profiles (without extension).
func ListPolicies() ([]string, error) {
	entries, err := Content.ReadDir(filepath.Join(contentRoot, "policy"))
	if err != nil {
		return nil, fmt.Errorf("failed to list policies: %w", err)
	}
	var policies []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		if strings.HasSuffix(name, ".yaml") || strings.HasSuffix(name, ".yml") {
			policies = append(policies, strings.TrimSuffix(strings.TrimSuffix(name, ".yaml"), ".yml"))
		}
	}
	return policies, nil
}

// ListSchemas returns the names of available JSON schemas.
func ListSchemas() ([]string, error) {
	entries, err := Content.ReadDir(filepath.Join(contentRoot, "schemas"))
	if err != nil {
		return nil, fmt.Errorf("failed to list schemas: %w", err)
	}
	var schemas []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		if strings.HasSuffix(name, ".json") {
			schemas = append(schemas, name)
		}
	}
	return schemas, nil
}

// ListReviewPrompts returns the names of available review prompts.
func ListReviewPrompts() ([]string, error) {
	entries, err := Content.ReadDir(filepath.Join(contentRoot, "prompts", "reviews"))
	if err != nil {
		return nil, fmt.Errorf("failed to list review prompts: %w", err)
	}
	var prompts []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		if strings.HasSuffix(name, ".md") {
			prompts = append(prompts, strings.TrimSuffix(name, ".md"))
		}
	}
	return prompts, nil
}

// ListPersonas returns the names of available agentic personas.
func ListPersonas() ([]string, error) {
	entries, err := Content.ReadDir(filepath.Join(contentRoot, "personas", "agentic"))
	if err != nil {
		return nil, fmt.Errorf("failed to list personas: %w", err)
	}
	var personas []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		if strings.HasSuffix(name, ".md") {
			personas = append(personas, strings.TrimSuffix(name, ".md"))
		}
	}
	return personas, nil
}

// ListCommands returns the names of available slash commands.
func ListCommands() ([]string, error) {
	entries, err := Content.ReadDir(filepath.Join(contentRoot, "commands"))
	if err != nil {
		return nil, fmt.Errorf("failed to list commands: %w", err)
	}
	var commands []string
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		if strings.HasSuffix(name, ".md") {
			commands = append(commands, strings.TrimSuffix(name, ".md"))
		}
	}
	return commands, nil
}

// GetPolicy reads a policy profile by name (without extension).
func GetPolicy(name string) ([]byte, error) {
	data, err := ReadFile(filepath.Join("policy", name+".yaml"))
	if err != nil {
		return nil, fmt.Errorf("policy %q not found: %w", name, err)
	}
	return data, nil
}

// GetSchema reads a JSON schema by filename.
func GetSchema(name string) ([]byte, error) {
	data, err := ReadFile(filepath.Join("schemas", name))
	if err != nil {
		return nil, fmt.Errorf("schema %q not found: %w", name, err)
	}
	return data, nil
}

// ContentHash returns a deterministic SHA-256 hash of all embedded content.
// The hash is computed once and cached for subsequent calls.
// Files are sorted by path before hashing to ensure determinism.
func ContentHash() string {
	cachedHashOnce.Do(func() {
		cachedHash = computeContentHash()
	})
	return cachedHash
}

// computeContentHash walks all embedded files and computes a combined SHA-256.
func computeContentHash() string {
	h := sha256.New()

	// Collect all file paths for deterministic ordering
	var paths []string
	_ = fs.WalkDir(Content, contentRoot, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if d.IsDir() {
			return nil
		}
		// Skip .gitkeep files — they're placeholders, not content
		if d.Name() == ".gitkeep" {
			return nil
		}
		paths = append(paths, path)
		return nil
	})

	sort.Strings(paths)

	for _, path := range paths {
		data, err := Content.ReadFile(path)
		if err != nil {
			continue
		}
		// Hash the path and content together for path-sensitivity
		h.Write([]byte(path))
		h.Write([]byte{0}) // null separator
		h.Write(data)
		h.Write([]byte{0})
	}

	return fmt.Sprintf("sha256:%x", h.Sum(nil))
}

// HasContent returns true if the embedded filesystem contains governance content
// beyond just the .gitkeep placeholder.
func HasContent() bool {
	entries, err := Content.ReadDir(contentRoot)
	if err != nil {
		return false
	}
	for _, e := range entries {
		if e.Name() != ".gitkeep" {
			return true
		}
	}
	return false
}

// ListDocs returns the names of available embedded documentation topics.
// Topics are returned as forward-slash paths relative to the docs/ root,
// e.g. "guides/installation", "architecture/governance-model".
func ListDocs() ([]string, error) {
	var docs []string
	docsRoot := filepath.Join(contentRoot, "docs")
	err := fs.WalkDir(Content, docsRoot, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if d.IsDir() {
			return nil
		}
		name := d.Name()
		if !strings.HasSuffix(name, ".md") {
			return nil
		}
		// Convert _content/docs/guides/installation.md -> guides/installation
		rel := strings.TrimPrefix(path, docsRoot+"/")
		rel = strings.TrimSuffix(rel, ".md")
		docs = append(docs, rel)
		return nil
	})
	if err != nil {
		return nil, fmt.Errorf("failed to list docs: %w", err)
	}
	sort.Strings(docs)
	return docs, nil
}

// GetDoc reads an embedded documentation topic by its topic path.
// The path uses forward slashes without the .md extension,
// e.g. "guides/installation" reads _content/docs/guides/installation.md.
func GetDoc(topic string) ([]byte, error) {
	data, err := ReadFile(filepath.Join("docs", topic+".md"))
	if err != nil {
		return nil, fmt.Errorf("doc topic %q not found: %w", topic, err)
	}
	return data, nil
}

// ListLanguageTemplates returns the names of available language templates.
func ListLanguageTemplates() ([]string, error) {
	entries, err := Content.ReadDir(filepath.Join(contentRoot, "templates", "languages"))
	if err != nil {
		return nil, fmt.Errorf("failed to list language templates: %w", err)
	}
	var langs []string
	for _, e := range entries {
		if e.IsDir() {
			langs = append(langs, e.Name())
		}
	}
	return langs, nil
}
