// Package storage provides pluggable key-value storage adapters for
// governance artifacts. Adapters store opaque byte blobs with optional
// metadata sidecars.
//
// Ported from Python: governance/engine/storage.py
package storage

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
)

// ---------------------------------------------------------------------------
// Interface
// ---------------------------------------------------------------------------

// Adapter is the storage interface for governance artifacts.
type Adapter interface {
	// Put stores data under key with optional metadata. Returns the resolved path/key.
	Put(key string, data []byte, metadata map[string]interface{}) (string, error)
	// Get retrieves data and metadata for key.
	Get(key string) ([]byte, map[string]interface{}, error)
	// List returns keys matching prefix.
	List(prefix string) ([]string, error)
	// Delete removes key. Returns true if the key existed.
	Delete(key string) (bool, error)
}

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------

// KeyNotFoundError is returned when a key does not exist.
type KeyNotFoundError struct {
	Key string
}

func (e *KeyNotFoundError) Error() string {
	return fmt.Sprintf("key not found: %s", e.Key)
}

// ---------------------------------------------------------------------------
// LocalAdapter
// ---------------------------------------------------------------------------

// LocalAdapter stores artifacts in a local directory (typically under
// XDG_STATE_HOME or the platform equivalent).
type LocalAdapter struct {
	baseDir string
}

// NewLocalAdapter creates a LocalAdapter rooted at baseDir.
// If baseDir is empty, xdgStateDir() is used. The directory is created if needed.
func NewLocalAdapter(baseDir string) (*LocalAdapter, error) {
	if baseDir == "" {
		baseDir = xdgStateDir()
	}
	if err := os.MkdirAll(baseDir, 0755); err != nil {
		return nil, fmt.Errorf("storage: create base dir: %w", err)
	}
	return &LocalAdapter{baseDir: baseDir}, nil
}

func (a *LocalAdapter) safePath(key string) (string, error) {
	if strings.Contains(key, "..") {
		return "", fmt.Errorf("storage: path traversal in key %q", key)
	}
	return filepath.Join(a.baseDir, key), nil
}

func (a *LocalAdapter) Put(key string, data []byte, metadata map[string]interface{}) (string, error) {
	p, err := a.safePath(key)
	if err != nil {
		return "", err
	}
	if err := os.MkdirAll(filepath.Dir(p), 0755); err != nil {
		return "", fmt.Errorf("storage: mkdir: %w", err)
	}
	if err := os.WriteFile(p, data, 0644); err != nil {
		return "", fmt.Errorf("storage: write %s: %w", p, err)
	}
	if metadata != nil {
		metaPath := p + ".meta.json"
		metaData, merr := json.MarshalIndent(metadata, "", "  ")
		if merr != nil {
			return p, fmt.Errorf("storage: marshal metadata: %w", merr)
		}
		if merr := os.WriteFile(metaPath, metaData, 0644); merr != nil {
			return p, fmt.Errorf("storage: write metadata: %w", merr)
		}
	}
	return p, nil
}

func (a *LocalAdapter) Get(key string) ([]byte, map[string]interface{}, error) {
	p, err := a.safePath(key)
	if err != nil {
		return nil, nil, err
	}
	data, err := os.ReadFile(p)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil, &KeyNotFoundError{Key: key}
		}
		return nil, nil, fmt.Errorf("storage: read %s: %w", p, err)
	}
	var metadata map[string]interface{}
	metaPath := p + ".meta.json"
	if metaData, merr := os.ReadFile(metaPath); merr == nil {
		_ = json.Unmarshal(metaData, &metadata)
	}
	return data, metadata, nil
}

func (a *LocalAdapter) List(prefix string) ([]string, error) {
	var keys []string
	prefixPath := filepath.Join(a.baseDir, prefix)
	dir := filepath.Dir(prefixPath)

	entries, err := os.ReadDir(dir)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, fmt.Errorf("storage: list dir: %w", err)
	}
	for _, e := range entries {
		if e.IsDir() || strings.HasSuffix(e.Name(), ".meta.json") {
			continue
		}
		rel, _ := filepath.Rel(a.baseDir, filepath.Join(dir, e.Name()))
		if strings.HasPrefix(rel, prefix) {
			keys = append(keys, rel)
		}
	}
	return keys, nil
}

func (a *LocalAdapter) Delete(key string) (bool, error) {
	p, err := a.safePath(key)
	if err != nil {
		return false, err
	}
	if _, err := os.Stat(p); os.IsNotExist(err) {
		return false, nil
	}
	if err := os.Remove(p); err != nil {
		return false, fmt.Errorf("storage: delete %s: %w", p, err)
	}
	// Best-effort removal of metadata sidecar.
	_ = os.Remove(p + ".meta.json")
	return true, nil
}

// ---------------------------------------------------------------------------
// RepoAdapter
// ---------------------------------------------------------------------------

// RepoAdapter stores artifacts under repoRoot/.artifacts/.
type RepoAdapter struct {
	baseDir string
}

// NewRepoAdapter creates a RepoAdapter rooted at repoRoot/.artifacts/.
func NewRepoAdapter(repoRoot string) (*RepoAdapter, error) {
	base := filepath.Join(repoRoot, ".artifacts")
	if err := os.MkdirAll(base, 0755); err != nil {
		return nil, fmt.Errorf("storage: create .artifacts dir: %w", err)
	}
	return &RepoAdapter{baseDir: base}, nil
}

func (a *RepoAdapter) safePath(key string) (string, error) {
	if strings.Contains(key, "..") {
		return "", fmt.Errorf("storage: path traversal in key %q", key)
	}
	return filepath.Join(a.baseDir, key), nil
}

func (a *RepoAdapter) Put(key string, data []byte, metadata map[string]interface{}) (string, error) {
	p, err := a.safePath(key)
	if err != nil {
		return "", err
	}
	if err := os.MkdirAll(filepath.Dir(p), 0755); err != nil {
		return "", fmt.Errorf("storage: mkdir: %w", err)
	}
	if err := os.WriteFile(p, data, 0644); err != nil {
		return "", fmt.Errorf("storage: write %s: %w", p, err)
	}
	if metadata != nil {
		metaPath := p + ".meta.json"
		metaData, merr := json.MarshalIndent(metadata, "", "  ")
		if merr != nil {
			return p, fmt.Errorf("storage: marshal metadata: %w", merr)
		}
		if merr := os.WriteFile(metaPath, metaData, 0644); merr != nil {
			return p, fmt.Errorf("storage: write metadata: %w", merr)
		}
	}
	return p, nil
}

func (a *RepoAdapter) Get(key string) ([]byte, map[string]interface{}, error) {
	p, err := a.safePath(key)
	if err != nil {
		return nil, nil, err
	}
	data, err := os.ReadFile(p)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil, &KeyNotFoundError{Key: key}
		}
		return nil, nil, fmt.Errorf("storage: read %s: %w", p, err)
	}
	var metadata map[string]interface{}
	metaPath := p + ".meta.json"
	if metaData, merr := os.ReadFile(metaPath); merr == nil {
		_ = json.Unmarshal(metaData, &metadata)
	}
	return data, metadata, nil
}

func (a *RepoAdapter) List(prefix string) ([]string, error) {
	var keys []string
	prefixPath := filepath.Join(a.baseDir, prefix)
	dir := filepath.Dir(prefixPath)

	entries, err := os.ReadDir(dir)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, fmt.Errorf("storage: list dir: %w", err)
	}
	for _, e := range entries {
		if e.IsDir() || strings.HasSuffix(e.Name(), ".meta.json") {
			continue
		}
		rel, _ := filepath.Rel(a.baseDir, filepath.Join(dir, e.Name()))
		if strings.HasPrefix(rel, prefix) {
			keys = append(keys, rel)
		}
	}
	return keys, nil
}

func (a *RepoAdapter) Delete(key string) (bool, error) {
	p, err := a.safePath(key)
	if err != nil {
		return false, err
	}
	if _, err := os.Stat(p); os.IsNotExist(err) {
		return false, nil
	}
	if err := os.Remove(p); err != nil {
		return false, fmt.Errorf("storage: delete %s: %w", p, err)
	}
	_ = os.Remove(p + ".meta.json")
	return true, nil
}

// ---------------------------------------------------------------------------
// Factory
// ---------------------------------------------------------------------------

// CreateAdapter builds an Adapter from a configuration map.
// Supported keys:
//
//	"type": "local" | "repo" (default: "local")
//	"base_dir": base directory for local adapter
//	"repo_root": repository root for repo adapter
func CreateAdapter(config map[string]interface{}) (Adapter, error) {
	adapterType, _ := config["type"].(string)
	switch adapterType {
	case "repo":
		root, _ := config["repo_root"].(string)
		if root == "" {
			root = "."
		}
		return NewRepoAdapter(root)
	case "local", "":
		baseDir, _ := config["base_dir"].(string)
		return NewLocalAdapter(baseDir)
	default:
		return nil, fmt.Errorf("storage: unknown adapter type %q", adapterType)
	}
}

// ---------------------------------------------------------------------------
// xdgStateDir
// ---------------------------------------------------------------------------

// xdgStateDir returns the platform-appropriate state directory.
func xdgStateDir() string {
	if dir := os.Getenv("DARK_GOVERNANCE_STATE_DIR"); dir != "" {
		return dir
	}
	switch runtime.GOOS {
	case "darwin":
		home, _ := os.UserHomeDir()
		return filepath.Join(home, "Library", "Application Support", "dark-governance")
	default:
		if xdg := os.Getenv("XDG_STATE_HOME"); xdg != "" {
			return filepath.Join(xdg, "dark-governance")
		}
		home, _ := os.UserHomeDir()
		return filepath.Join(home, ".local", "state", "dark-governance")
	}
}
