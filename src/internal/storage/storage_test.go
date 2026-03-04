package storage

import (
	"path/filepath"
	"testing"
)

func TestLocalAdapter_PutGet(t *testing.T) {
	dir := t.TempDir()
	adapter, err := NewLocalAdapter(dir)
	if err != nil {
		t.Fatalf("new adapter: %v", err)
	}

	meta := map[string]interface{}{"author": "test"}
	path, err := adapter.Put("data/test.json", []byte(`{"hello":"world"}`), meta)
	if err != nil {
		t.Fatalf("put: %v", err)
	}
	if path == "" {
		t.Fatal("expected non-empty path from Put")
	}

	data, gotMeta, err := adapter.Get("data/test.json")
	if err != nil {
		t.Fatalf("get: %v", err)
	}
	if string(data) != `{"hello":"world"}` {
		t.Fatalf("data mismatch: %q", string(data))
	}
	if gotMeta["author"] != "test" {
		t.Fatalf("metadata mismatch: %v", gotMeta)
	}
}

func TestLocalAdapter_GetNotFound(t *testing.T) {
	dir := t.TempDir()
	adapter, _ := NewLocalAdapter(dir)

	_, _, err := adapter.Get("nonexistent.json")
	if err == nil {
		t.Fatal("expected error for missing key")
	}
	if _, ok := err.(*KeyNotFoundError); !ok {
		t.Fatalf("expected *KeyNotFoundError, got %T: %v", err, err)
	}
}

func TestLocalAdapter_ListWithPrefix(t *testing.T) {
	dir := t.TempDir()
	adapter, _ := NewLocalAdapter(dir)

	// Put files with a common prefix in the same directory.
	adapter.Put("plan-a.json", []byte("a"), nil)
	adapter.Put("plan-b.json", []byte("b"), nil)
	adapter.Put("other.json", []byte("x"), nil)

	keys, err := adapter.List("plan-")
	if err != nil {
		t.Fatalf("list: %v", err)
	}
	if len(keys) != 2 {
		t.Fatalf("expected 2 keys, got %d: %v", len(keys), keys)
	}
}

func TestLocalAdapter_Delete(t *testing.T) {
	dir := t.TempDir()
	adapter, _ := NewLocalAdapter(dir)

	adapter.Put("delete-me.json", []byte("gone"), nil)

	existed, err := adapter.Delete("delete-me.json")
	if err != nil {
		t.Fatalf("delete: %v", err)
	}
	if !existed {
		t.Fatal("expected existed=true")
	}

	existed, err = adapter.Delete("delete-me.json")
	if err != nil {
		t.Fatalf("second delete: %v", err)
	}
	if existed {
		t.Fatal("expected existed=false on second delete")
	}
}

func TestLocalAdapter_PathTraversal(t *testing.T) {
	dir := t.TempDir()
	adapter, _ := NewLocalAdapter(dir)

	_, err := adapter.Put("../escape.json", []byte("bad"), nil)
	if err == nil {
		t.Fatal("expected error for path traversal in Put")
	}

	_, _, err = adapter.Get("../escape.json")
	if err == nil {
		t.Fatal("expected error for path traversal in Get")
	}
}

func TestRepoAdapter_PutGet(t *testing.T) {
	dir := t.TempDir()
	adapter, err := NewRepoAdapter(dir)
	if err != nil {
		t.Fatalf("new repo adapter: %v", err)
	}

	_, err = adapter.Put("panels/review.json", []byte(`{"status":"pass"}`), nil)
	if err != nil {
		t.Fatalf("put: %v", err)
	}

	data, _, err := adapter.Get("panels/review.json")
	if err != nil {
		t.Fatalf("get: %v", err)
	}
	if string(data) != `{"status":"pass"}` {
		t.Fatalf("data mismatch: %q", string(data))
	}

	// Verify it's stored under .artifacts.
	expectedBase := filepath.Join(dir, ".artifacts")
	expectedPath := filepath.Join(expectedBase, "panels", "review.json")
	directData, _, err := adapter.Get("panels/review.json")
	if err != nil {
		t.Fatalf("get via path: %v", err)
	}
	if string(directData) != `{"status":"pass"}` {
		t.Fatalf("path mismatch; expected content at %s", expectedPath)
	}
}

func TestCreateAdapter_Local(t *testing.T) {
	dir := t.TempDir()
	adapter, err := CreateAdapter(map[string]interface{}{
		"type":     "local",
		"base_dir": dir,
	})
	if err != nil {
		t.Fatalf("create local: %v", err)
	}
	if adapter == nil {
		t.Fatal("expected non-nil adapter")
	}
}

func TestCreateAdapter_Repo(t *testing.T) {
	dir := t.TempDir()
	adapter, err := CreateAdapter(map[string]interface{}{
		"type":      "repo",
		"repo_root": dir,
	})
	if err != nil {
		t.Fatalf("create repo: %v", err)
	}
	if adapter == nil {
		t.Fatal("expected non-nil adapter")
	}
}

func TestCreateAdapter_Unknown(t *testing.T) {
	_, err := CreateAdapter(map[string]interface{}{
		"type": "s3",
	})
	if err == nil {
		t.Fatal("expected error for unknown adapter type")
	}
}
