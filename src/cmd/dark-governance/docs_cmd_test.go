package main

import (
	"testing"

	"github.com/SET-Apps/ai-submodule/src/internal/docs"
)

func TestDocsCmdExists(t *testing.T) {
	// Verify the docs command is registered on the root command
	found := false
	for _, cmd := range rootCmd.Commands() {
		if cmd.Name() == "docs" {
			found = true
			break
		}
	}
	if !found {
		t.Error("expected 'docs' command to be registered on root")
	}
}

func TestDocsCmdHasOfflineFlag(t *testing.T) {
	flag := docsCmd.Flags().Lookup("offline")
	if flag == nil {
		t.Error("expected 'offline' flag on docs command")
	}
}

func TestDocsCmdAcceptsOneArg(t *testing.T) {
	// MaximumNArgs(1) means 0 or 1 args should be valid
	err := docsCmd.Args(docsCmd, []string{})
	if err != nil {
		t.Errorf("expected no error with 0 args, got: %v", err)
	}

	err = docsCmd.Args(docsCmd, []string{"guides/installation"})
	if err != nil {
		t.Errorf("expected no error with 1 arg, got: %v", err)
	}

	err = docsCmd.Args(docsCmd, []string{"a", "b"})
	if err == nil {
		t.Error("expected error with 2 args")
	}
}

func TestDocsURLConstant(t *testing.T) {
	expected := "https://set-apps.github.io/ai-submodule"
	if docs.DocsURL != expected {
		t.Errorf("expected DocsURL = %q, got %q", expected, docs.DocsURL)
	}
}

func TestDocsTopLevelFlagExists(t *testing.T) {
	// Verify the --docs persistent flag is registered on root
	flag := rootCmd.PersistentFlags().Lookup("docs")
	if flag == nil {
		t.Error("expected '--docs' persistent flag on root command")
	}
}
