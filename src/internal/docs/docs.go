// Package docs provides documentation browsing support for the dark-governance CLI.
//
// It implements:
//   - Browser-open for online documentation
//   - Lightweight markdown-to-terminal rendering for offline mode
//   - Pager integration ($PAGER -> less -> more -> stdout)
package docs

import (
	"fmt"
	"io"
	"os"
	"os/exec"
	"runtime"
	"strings"
)

// DocsURL is the base URL for the online documentation site.
const DocsURL = "https://set-apps.github.io/ai-submodule"

// OpenBrowser opens the given URL in the user's default browser.
// It returns the exec.Cmd that was used (for testing) and any error.
func OpenBrowser(url string) (*exec.Cmd, error) {
	var cmd *exec.Cmd

	switch runtime.GOOS {
	case "darwin":
		cmd = exec.Command("open", url)
	case "linux":
		cmd = exec.Command("xdg-open", url)
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	default:
		return nil, fmt.Errorf("unsupported platform %q — open %s manually", runtime.GOOS, url)
	}

	if err := cmd.Start(); err != nil {
		return cmd, fmt.Errorf("failed to open browser: %w", err)
	}
	return cmd, nil
}

// BrowserCommand returns the command name and args that would be used to
// open a URL on the current platform, without executing it.
func BrowserCommand(url string) (string, []string) {
	switch runtime.GOOS {
	case "darwin":
		return "open", []string{url}
	case "linux":
		return "xdg-open", []string{url}
	case "windows":
		return "rundll32", []string{"url.dll,FileProtocolHandler", url}
	default:
		return "", nil
	}
}

// DetectPager returns the pager command to use.
// It follows the chain: $PAGER -> less -> more -> "" (stdout).
func DetectPager() string {
	if pager := os.Getenv("PAGER"); pager != "" {
		return pager
	}
	if _, err := exec.LookPath("less"); err == nil {
		return "less"
	}
	if _, err := exec.LookPath("more"); err == nil {
		return "more"
	}
	return ""
}

// RenderToPager writes content through a pager if available.
// If no pager is found, content is written directly to w.
func RenderToPager(content string, w io.Writer) error {
	pager := DetectPager()
	if pager == "" {
		_, err := fmt.Fprint(w, content)
		return err
	}

	// Split pager command in case it has args (e.g. "less -R")
	parts := strings.Fields(pager)
	cmd := exec.Command(parts[0], parts[1:]...)
	cmd.Stdin = strings.NewReader(content)
	cmd.Stdout = w
	cmd.Stderr = os.Stderr

	return cmd.Run()
}

// RenderMarkdown converts a markdown document to a terminal-friendly
// plain-text representation. This is a lightweight renderer that handles:
//   - Headings (# -> bold/uppercase)
//   - Code blocks (``` -> indented)
//   - Bullet lists (preserved)
//   - Bold/italic markers (stripped)
//   - Horizontal rules (--- -> dashes)
//
// It intentionally does not use ANSI escape codes to remain compatible
// with all terminals and pagers.
func RenderMarkdown(input string) string {
	lines := strings.Split(input, "\n")
	var out []string
	inCodeBlock := false

	for _, line := range lines {
		// Toggle code blocks
		if strings.HasPrefix(strings.TrimSpace(line), "```") {
			if inCodeBlock {
				inCodeBlock = false
				out = append(out, "    "+strings.Repeat("-", 40))
			} else {
				inCodeBlock = true
				lang := strings.TrimPrefix(strings.TrimSpace(line), "```")
				if lang != "" {
					out = append(out, "    ["+lang+"]")
				}
				out = append(out, "    "+strings.Repeat("-", 40))
			}
			continue
		}

		if inCodeBlock {
			out = append(out, "    "+line)
			continue
		}

		trimmed := strings.TrimSpace(line)

		// Horizontal rules
		if trimmed == "---" || trimmed == "***" || trimmed == "___" {
			out = append(out, strings.Repeat("-", 60))
			continue
		}

		// Headings
		if strings.HasPrefix(trimmed, "# ") {
			title := strings.TrimPrefix(trimmed, "# ")
			out = append(out, "")
			out = append(out, strings.ToUpper(title))
			out = append(out, strings.Repeat("=", len(title)))
			out = append(out, "")
			continue
		}
		if strings.HasPrefix(trimmed, "## ") {
			title := strings.TrimPrefix(trimmed, "## ")
			out = append(out, "")
			out = append(out, title)
			out = append(out, strings.Repeat("-", len(title)))
			out = append(out, "")
			continue
		}
		if strings.HasPrefix(trimmed, "### ") {
			title := strings.TrimPrefix(trimmed, "### ")
			out = append(out, "")
			out = append(out, "  "+title)
			out = append(out, "")
			continue
		}
		if strings.HasPrefix(trimmed, "#### ") {
			title := strings.TrimPrefix(trimmed, "#### ")
			out = append(out, "")
			out = append(out, "    "+title)
			out = append(out, "")
			continue
		}

		// Strip inline formatting markers
		rendered := stripInlineFormatting(line)
		out = append(out, rendered)
	}

	return strings.Join(out, "\n")
}

// stripInlineFormatting removes bold (**) and italic (*/_) markers from text.
func stripInlineFormatting(s string) string {
	// Remove bold markers first (**text** or __text__)
	s = removePairedMarkers(s, "**")
	s = removePairedMarkers(s, "__")
	// Remove italic markers (* or _) — only single ones remaining
	s = removePairedMarkers(s, "*")
	s = removePairedMarkers(s, "_")
	return s
}

// removePairedMarkers removes paired occurrences of a marker string.
// e.g. removePairedMarkers("**hello**", "**") -> "hello"
func removePairedMarkers(s, marker string) string {
	for {
		start := strings.Index(s, marker)
		if start == -1 {
			break
		}
		end := strings.Index(s[start+len(marker):], marker)
		if end == -1 {
			break
		}
		// Remove closing marker first, then opening
		closeIdx := start + len(marker) + end
		s = s[:closeIdx] + s[closeIdx+len(marker):]
		s = s[:start] + s[start+len(marker):]
	}
	return s
}

// FormatTopicList formats a list of topic names for terminal display.
func FormatTopicList(topics []string) string {
	if len(topics) == 0 {
		return "No documentation topics available.\n"
	}

	var b strings.Builder
	b.WriteString("Available documentation topics:\n\n")

	// Group by category (first path segment)
	categories := make(map[string][]string)
	var categoryOrder []string
	for _, t := range topics {
		parts := strings.SplitN(t, "/", 2)
		cat := parts[0]
		if _, seen := categories[cat]; !seen {
			categoryOrder = append(categoryOrder, cat)
		}
		categories[cat] = append(categories[cat], t)
	}

	for _, cat := range categoryOrder {
		b.WriteString("  " + cat + "/\n")
		for _, topic := range categories[cat] {
			b.WriteString("    " + topic + "\n")
		}
		b.WriteString("\n")
	}

	b.WriteString(fmt.Sprintf("%d topics available. Use 'dark-governance docs --offline <topic>' to read.\n", len(topics)))
	return b.String()
}
