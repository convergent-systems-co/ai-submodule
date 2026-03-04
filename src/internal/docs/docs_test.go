package docs

import (
	"bytes"
	"runtime"
	"strings"
	"testing"
)

func TestDocsURL(t *testing.T) {
	if DocsURL == "" {
		t.Fatal("DocsURL is empty")
	}
	if !strings.HasPrefix(DocsURL, "https://") {
		t.Errorf("DocsURL should start with https://, got: %s", DocsURL)
	}
}

func TestBrowserCommand(t *testing.T) {
	url := "https://example.com"
	cmd, args := BrowserCommand(url)

	switch runtime.GOOS {
	case "darwin":
		if cmd != "open" {
			t.Errorf("expected 'open' on darwin, got %q", cmd)
		}
		if len(args) != 1 || args[0] != url {
			t.Errorf("expected [%s], got %v", url, args)
		}
	case "linux":
		if cmd != "xdg-open" {
			t.Errorf("expected 'xdg-open' on linux, got %q", cmd)
		}
	case "windows":
		if cmd != "rundll32" {
			t.Errorf("expected 'rundll32' on windows, got %q", cmd)
		}
	}
}

func TestBrowserCommandUnsupportedPlatform(t *testing.T) {
	// This test just verifies the function doesn't panic on the current platform
	cmd, _ := BrowserCommand("https://example.com")
	if cmd == "" && runtime.GOOS != "plan9" && runtime.GOOS != "js" {
		t.Errorf("expected non-empty command for %s", runtime.GOOS)
	}
}

func TestDetectPager(t *testing.T) {
	// DetectPager should return something on most systems
	pager := DetectPager()
	// We just verify it doesn't panic — the actual value depends on the environment
	_ = pager
}

func TestDetectPagerRespectsEnv(t *testing.T) {
	t.Setenv("PAGER", "cat")
	pager := DetectPager()
	if pager != "cat" {
		t.Errorf("expected 'cat' from $PAGER, got %q", pager)
	}
}

func TestRenderToPagerFallback(t *testing.T) {
	var buf bytes.Buffer
	content := "hello world"

	// Use PAGER=cat which just passes through
	t.Setenv("PAGER", "cat")
	err := RenderToPager(content, &buf)
	if err != nil {
		t.Fatalf("RenderToPager failed: %v", err)
	}
	if buf.String() != content {
		t.Errorf("expected %q, got %q", content, buf.String())
	}
}

func TestRenderMarkdownHeadings(t *testing.T) {
	input := "# Main Title\n## Sub Title\n### Section\n#### Detail\n"
	result := RenderMarkdown(input)

	if !strings.Contains(result, "MAIN TITLE") {
		t.Error("expected H1 to be uppercased")
	}
	if !strings.Contains(result, "Sub Title") {
		t.Error("expected H2 text")
	}
	if !strings.Contains(result, "  Section") {
		t.Error("expected H3 to be indented")
	}
	if !strings.Contains(result, "    Detail") {
		t.Error("expected H4 to be double-indented")
	}
}

func TestRenderMarkdownCodeBlocks(t *testing.T) {
	input := "before\n```bash\necho hello\n```\nafter\n"
	result := RenderMarkdown(input)

	if !strings.Contains(result, "    echo hello") {
		t.Error("expected code block content to be indented")
	}
	if !strings.Contains(result, "[bash]") {
		t.Error("expected language annotation")
	}
	if !strings.Contains(result, "before") {
		t.Error("expected text before code block")
	}
	if !strings.Contains(result, "after") {
		t.Error("expected text after code block")
	}
}

func TestRenderMarkdownHorizontalRule(t *testing.T) {
	input := "above\n---\nbelow\n"
	result := RenderMarkdown(input)

	if !strings.Contains(result, strings.Repeat("-", 60)) {
		t.Error("expected horizontal rule to render as dashes")
	}
}

func TestRenderMarkdownBoldStripping(t *testing.T) {
	input := "This is **bold** text and __also bold__ text.\n"
	result := RenderMarkdown(input)

	if strings.Contains(result, "**") {
		t.Error("expected ** markers to be stripped")
	}
	if strings.Contains(result, "__") {
		t.Error("expected __ markers to be stripped")
	}
	if !strings.Contains(result, "bold") {
		t.Error("expected bold text content to remain")
	}
}

func TestRenderMarkdownItalicStripping(t *testing.T) {
	input := "This is *italic* text.\n"
	result := RenderMarkdown(input)

	if !strings.Contains(result, "italic") {
		t.Error("expected italic text content to remain")
	}
}

func TestRenderMarkdownBulletLists(t *testing.T) {
	input := "- item one\n- item two\n  - nested\n"
	result := RenderMarkdown(input)

	if !strings.Contains(result, "- item one") {
		t.Error("expected bullet list to be preserved")
	}
	if !strings.Contains(result, "- item two") {
		t.Error("expected second bullet to be preserved")
	}
}

func TestRemovePairedMarkers(t *testing.T) {
	tests := []struct {
		input, marker, want string
	}{
		{"**hello**", "**", "hello"},
		{"a **b** c **d** e", "**", "a b c d e"},
		{"no markers here", "**", "no markers here"},
		{"*one* and *two*", "*", "one and two"},
		{"unmatched *marker", "*", "unmatched *marker"},
	}

	for _, tt := range tests {
		got := removePairedMarkers(tt.input, tt.marker)
		if got != tt.want {
			t.Errorf("removePairedMarkers(%q, %q) = %q, want %q", tt.input, tt.marker, got, tt.want)
		}
	}
}

func TestFormatTopicList(t *testing.T) {
	topics := []string{
		"guides/installation",
		"guides/quickstart",
		"architecture/governance-model",
		"onboarding/developer-guide",
	}

	result := FormatTopicList(topics)

	if !strings.Contains(result, "guides/") {
		t.Error("expected guides category header")
	}
	if !strings.Contains(result, "architecture/") {
		t.Error("expected architecture category header")
	}
	if !strings.Contains(result, "guides/installation") {
		t.Error("expected installation topic")
	}
	if !strings.Contains(result, "4 topics available") {
		t.Error("expected topic count")
	}
}

func TestFormatTopicListEmpty(t *testing.T) {
	result := FormatTopicList(nil)
	if !strings.Contains(result, "No documentation topics") {
		t.Error("expected empty message for nil topics")
	}
}

func TestStripInlineFormatting(t *testing.T) {
	tests := []struct {
		input, want string
	}{
		{"**bold**", "bold"},
		{"__bold__", "bold"},
		{"*italic*", "italic"},
		{"plain text", "plain text"},
		{"**a** and *b*", "a and b"},
	}

	for _, tt := range tests {
		got := stripInlineFormatting(tt.input)
		if got != tt.want {
			t.Errorf("stripInlineFormatting(%q) = %q, want %q", tt.input, got, tt.want)
		}
	}
}
