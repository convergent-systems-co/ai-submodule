package main

import (
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/SET-Apps/ai-submodule/src/internal/docs"
	govembed "github.com/SET-Apps/ai-submodule/src/internal/embed"
	"github.com/spf13/cobra"
)

var (
	docsOffline bool
)

var docsCmd = &cobra.Command{
	Use:   "docs [topic]",
	Short: "Browse governance documentation",
	Long: `Open the governance documentation site or browse embedded docs offline.

Without flags, opens the documentation website in your default browser.

With --offline, lists available documentation topics or renders a specific
topic in the terminal using a pager.

Examples:
  dark-governance docs                              # Open docs site in browser
  dark-governance docs --offline                    # List available topics
  dark-governance docs --offline guides/installation  # Read a topic offline
  dark-governance --docs                            # Alias: open docs site`,
	Args: cobra.MaximumNArgs(1),
	RunE: runDocs,
}

func init() {
	docsCmd.Flags().BoolVar(&docsOffline, "offline", false, "Browse embedded docs in the terminal (no network required)")
}

func runDocs(cmd *cobra.Command, args []string) error {
	// Offline mode: list topics or render a specific topic
	if docsOffline {
		return runDocsOffline(args)
	}

	// Online mode: open browser
	return runDocsOnline(args)
}

// runDocsOnline opens the documentation site in the user's default browser.
// If a topic argument is provided, it opens the specific page URL.
func runDocsOnline(args []string) error {
	url := docs.DocsURL

	if len(args) == 1 {
		// Construct topic URL: e.g. guides/installation -> /guides/installation/
		topic := strings.TrimSuffix(args[0], "/")
		url = docs.DocsURL + "/" + topic + "/"
	}

	if flagJSON {
		data := map[string]string{
			"action": "open_browser",
			"url":    url,
		}
		out, _ := json.MarshalIndent(data, "", "  ")
		fmt.Fprintln(os.Stdout, string(out))
	} else {
		fmt.Fprintf(os.Stdout, "Opening documentation: %s\n", url)
	}

	_, err := docs.OpenBrowser(url)
	if err != nil {
		return fmt.Errorf("could not open browser: %w\n\nOpen manually: %s", err, url)
	}
	return nil
}

// runDocsOffline lists available topics or renders a specific topic.
func runDocsOffline(args []string) error {
	if !govembed.HasContent() {
		return fmt.Errorf("binary does not contain governance content — was it built with 'make prepare-embed'?")
	}

	// No topic specified: list all available topics
	if len(args) == 0 {
		return runDocsOfflineList()
	}

	// Topic specified: render it
	return runDocsOfflineRender(args[0])
}

// runDocsOfflineList displays all available embedded documentation topics.
func runDocsOfflineList() error {
	topics, err := govembed.ListDocs()
	if err != nil {
		return fmt.Errorf("failed to list docs: %w", err)
	}

	if flagJSON {
		data := map[string]interface{}{
			"topics": topics,
			"count":  len(topics),
		}
		out, _ := json.MarshalIndent(data, "", "  ")
		fmt.Fprintln(os.Stdout, string(out))
		return nil
	}

	fmt.Fprint(os.Stdout, docs.FormatTopicList(topics))
	return nil
}

// runDocsOfflineRender reads and renders a specific topic in the pager.
func runDocsOfflineRender(topic string) error {
	data, err := govembed.GetDoc(topic)
	if err != nil {
		// Provide helpful suggestion
		topics, listErr := govembed.ListDocs()
		if listErr == nil {
			// Find close matches
			var suggestions []string
			for _, t := range topics {
				if strings.Contains(t, topic) || strings.Contains(topic, t) {
					suggestions = append(suggestions, t)
				}
			}
			if len(suggestions) > 0 {
				return fmt.Errorf("topic %q not found. Did you mean:\n  %s", topic, strings.Join(suggestions, "\n  "))
			}
		}
		return fmt.Errorf("topic %q not found. Run 'dark-governance docs --offline' to list available topics", topic)
	}

	if flagJSON {
		resp := map[string]string{
			"topic":   topic,
			"content": string(data),
		}
		out, _ := json.MarshalIndent(resp, "", "  ")
		fmt.Fprintln(os.Stdout, string(out))
		return nil
	}

	rendered := docs.RenderMarkdown(string(data))
	return docs.RenderToPager(rendered, os.Stdout)
}
