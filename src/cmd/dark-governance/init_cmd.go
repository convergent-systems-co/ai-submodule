package main

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"

	govembed "github.com/SET-Apps/ai-submodule/src/internal/embed"
	"github.com/SET-Apps/ai-submodule/src/internal/home"
	"github.com/SET-Apps/ai-submodule/src/internal/lockfile"
	"github.com/SET-Apps/ai-submodule/src/internal/version"
	"github.com/spf13/cobra"
)

var (
	initDryRun   bool
	initForce    bool
	initLanguage string
)

var initCmd = &cobra.Command{
	Use:   "init",
	Short: "Initialize governance in a repository",
	Long: `Initialize the Dark Factory Governance framework in the current repository.

Extracts embedded governance content (CI workflows, slash commands, CLAUDE.md,
project.yaml template) and writes a .dark-governance.lock file for version pinning.

Files are extracted to the current working directory. Existing files are skipped
unless --force is specified.

Examples:
  dark-governance init                    # Initialize with defaults
  dark-governance init --dry-run          # Preview what would be extracted
  dark-governance init --force            # Overwrite existing files
  dark-governance init --language go      # Use Go project.yaml template`,
	RunE: runInit,
}

func init() {
	initCmd.Flags().BoolVar(&initDryRun, "dry-run", false, "Show what would be extracted without writing files")
	initCmd.Flags().BoolVar(&initForce, "force", false, "Overwrite existing files")
	initCmd.Flags().StringVar(&initLanguage, "language", "", "Language hint for project.yaml template (e.g., go, python, node)")
}

// extractionEntry describes a file to extract from embedded content.
type extractionEntry struct {
	// dst is the destination path relative to the repo root.
	dst string
	// src is the source path within the embedded _content/ directory.
	// Empty string means create the file/directory without source content.
	src string
	// skipIfExists controls whether to skip if the destination already exists.
	// When true, the file is only written if it doesn't exist (unless --force).
	skipIfExists bool
	// isDir means create a directory with a .gitkeep instead of extracting a file.
	isDir bool
}

func runInit(cmd *cobra.Command, args []string) error {
	if !govembed.HasContent() {
		return fmt.Errorf("binary does not contain governance content — was it built with 'make prepare-embed'?")
	}

	cwd, err := os.Getwd()
	if err != nil {
		return fmt.Errorf("failed to get working directory: %w", err)
	}

	// Build the extraction plan
	entries := buildExtractionPlan(cwd)

	if initDryRun {
		return printDryRun(cmd, entries, cwd)
	}

	// Execute the extraction
	extracted, skipped, err := executeExtraction(entries, cwd)
	if err != nil {
		return err
	}

	// Write lockfile
	binaryPath, _ := os.Executable()
	lockPath := filepath.Join(cwd, lockfile.DefaultPath)
	ver := version.Get().Version
	lockInfo := lockfile.LockInfo{
		Version:     ver,
		ContentHash: govembed.ContentHash(),
		BinaryPath:  binaryPath,
	}

	if initDryRun {
		// Already handled above, but for clarity
		return nil
	}

	if err := lockfile.Write(lockPath, lockInfo); err != nil {
		return fmt.Errorf("failed to write lockfile: %w", err)
	}

	// Determine content source for reporting
	contentSource := "embedded"
	homeDir, homeErr := home.DefaultHome()
	if homeErr == nil && home.IsInstalled(homeDir, ver) {
		contentSource = "home-cache (" + home.VersionDir(homeDir, ver) + ")"
	}

	// Print summary
	if flagJSON {
		fmt.Fprintf(os.Stdout, `{"status": "initialized", "extracted": %d, "skipped": %d, "lockfile": %q, "version": %q, "content_hash": %q, "content_source": %q}`+"\n",
			extracted, skipped, lockPath, lockInfo.Version, lockInfo.ContentHash, contentSource)
	} else {
		fmt.Fprintf(os.Stdout, "Governance initialized successfully.\n")
		fmt.Fprintf(os.Stdout, "  Extracted: %d files\n", extracted)
		fmt.Fprintf(os.Stdout, "  Skipped:   %d files (already exist)\n", skipped)
		fmt.Fprintf(os.Stdout, "  Lockfile:  %s\n", lockfile.DefaultPath)
		fmt.Fprintf(os.Stdout, "  Version:   %s\n", lockInfo.Version)
		fmt.Fprintf(os.Stdout, "  Content:   %s\n", lockInfo.ContentHash)
		fmt.Fprintf(os.Stdout, "  Source:    %s\n", contentSource)
	}

	return nil
}

// buildExtractionPlan creates the list of files to extract.
func buildExtractionPlan(cwd string) []extractionEntry {
	entries := []extractionEntry{
		// CI workflow
		{
			dst:          ".github/workflows/dark-factory-governance.yml",
			src:          "templates/workflows/pipeline.yml",
			skipIfExists: false, // Always update CI workflow
		},
		// CLAUDE.md (AI instructions)
		{
			dst:          "CLAUDE.md",
			src:          "instructions.md",
			skipIfExists: true, // Don't overwrite user's CLAUDE.md
		},
		// .artifacts directories
		{dst: ".artifacts/plans", isDir: true},
		{dst: ".artifacts/panels", isDir: true},
		{dst: ".artifacts/checkpoints", isDir: true},
		{dst: ".artifacts/emissions", isDir: true},
		{dst: ".artifacts/delivery-intents", isDir: true},
	}

	// Slash commands — always overwrite to stay in sync with binary
	commands, err := govembed.ListCommands()
	if err == nil {
		for _, cmd := range commands {
			entries = append(entries, extractionEntry{
				dst:          filepath.Join(".claude", "commands", cmd+".md"),
				src:          filepath.Join("commands", cmd+".md"),
				skipIfExists: false,
			})
		}
	}

	// project.yaml template — only if missing
	if initLanguage != "" {
		templatePath := filepath.Join("templates", "languages", initLanguage, "project.yaml")
		if _, err := govembed.ReadFile(templatePath); err == nil {
			entries = append(entries, extractionEntry{
				dst:          "project.yaml",
				src:          templatePath,
				skipIfExists: true,
			})
		}
	}

	return entries
}

// printDryRun displays what would be extracted without making changes.
func printDryRun(cmd *cobra.Command, entries []extractionEntry, cwd string) error {
	if flagJSON {
		fmt.Fprintln(os.Stdout, `{"mode": "dry_run", "files": [`)
		for i, e := range entries {
			status := "create"
			dst := filepath.Join(cwd, e.dst)
			if e.isDir {
				dst = filepath.Join(dst, ".gitkeep")
			}
			if _, err := os.Stat(dst); err == nil {
				if e.skipIfExists && !initForce {
					status = "skip"
				} else {
					status = "overwrite"
				}
			}
			comma := ","
			if i == len(entries)-1 {
				comma = ""
			}
			fmt.Fprintf(os.Stdout, `  {"path": %q, "action": %q}%s`+"\n", e.dst, status, comma)
		}
		fmt.Fprintln(os.Stdout, `]}`)
	} else {
		fmt.Fprintln(os.Stdout, "Dry run — the following actions would be taken:")
		fmt.Fprintln(os.Stdout, "")
		for _, e := range entries {
			action := "CREATE"
			dst := filepath.Join(cwd, e.dst)
			displayDst := e.dst
			if e.isDir {
				dst = filepath.Join(dst, ".gitkeep")
				displayDst = filepath.Join(e.dst, ".gitkeep")
			}
			if _, err := os.Stat(dst); err == nil {
				if e.skipIfExists && !initForce {
					action = "SKIP  "
				} else {
					action = "UPDATE"
				}
			}
			src := e.src
			if e.isDir {
				src = "(empty directory)"
			}
			fmt.Fprintf(os.Stdout, "  [%s] %s", action, displayDst)
			if src != "" {
				fmt.Fprintf(os.Stdout, "  <- %s", src)
			}
			fmt.Fprintln(os.Stdout)
		}
		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintf(os.Stdout, "  [CREATE] %s  <- (generated)\n", lockfile.DefaultPath)
		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintln(os.Stdout, "Run without --dry-run to apply.")
	}
	return nil
}

// executeExtraction writes the files to disk.
// It uses a three-tier resolution: embedded content -> home cache -> error.
func executeExtraction(entries []extractionEntry, cwd string) (extracted int, skipped int, err error) {
	// Determine home cache for fallback resolution
	ver := version.Get().Version
	homeDir, _ := home.DefaultHome()

	for _, e := range entries {
		dst := filepath.Join(cwd, e.dst)

		if e.isDir {
			// Create directory with .gitkeep
			gitkeep := filepath.Join(dst, ".gitkeep")
			if _, statErr := os.Stat(gitkeep); statErr == nil {
				skipped++
				continue
			}
			if mkErr := os.MkdirAll(dst, 0755); mkErr != nil {
				return extracted, skipped, fmt.Errorf("failed to create directory %s: %w", e.dst, mkErr)
			}
			if wErr := os.WriteFile(gitkeep, []byte(""), 0644); wErr != nil {
				return extracted, skipped, fmt.Errorf("failed to create %s/.gitkeep: %w", e.dst, wErr)
			}
			extracted++
			continue
		}

		// Check if destination exists
		if _, statErr := os.Stat(dst); statErr == nil {
			if e.skipIfExists && !initForce {
				skipped++
				continue
			}
		}

		// Read from embedded content first, then fall back to home cache
		data, readErr := govembed.ReadFile(e.src)
		if readErr != nil {
			// Try home cache as fallback
			if homeDir != "" && home.IsInstalled(homeDir, ver) {
				cachePath := filepath.Join(home.VersionDir(homeDir, ver), e.src)
				data, readErr = os.ReadFile(cachePath)
			}
			if readErr != nil {
				return extracted, skipped, fmt.Errorf("failed to read %s (embedded and home cache): %w", e.src, readErr)
			}
		}

		// Ensure parent directory exists
		if mkErr := os.MkdirAll(filepath.Dir(dst), 0755); mkErr != nil {
			return extracted, skipped, fmt.Errorf("failed to create directory for %s: %w", e.dst, mkErr)
		}

		// Write the file
		if wErr := os.WriteFile(dst, data, 0644); wErr != nil {
			return extracted, skipped, fmt.Errorf("failed to write %s: %w", e.dst, wErr)
		}
		extracted++
	}

	return extracted, skipped, nil
}

// detectLanguage attempts to detect the project language from common markers.
// Returns empty string if detection fails.
func detectLanguage(cwd string) string {
	markers := map[string]string{
		"go.mod":         "go",
		"package.json":   "node",
		"pyproject.toml": "python",
		"setup.py":       "python",
		"Cargo.toml":     "rust",
		"main.tf":        "terraform",
		"main.bicep":     "bicep",
	}

	for file, lang := range markers {
		if _, err := os.Stat(filepath.Join(cwd, file)); err == nil {
			return lang
		}
	}

	// Check for language-specific files in common patterns
	patterns := map[string]string{
		"*.csproj": "csharp",
		"*.sln":    "csharp",
	}

	for pattern, lang := range patterns {
		matches, err := filepath.Glob(filepath.Join(cwd, pattern))
		if err == nil && len(matches) > 0 {
			return lang
		}
	}

	return ""
}

// listExtractableContent returns a summary of all content that can be extracted.
// Used by engine status and other introspection commands.
func listExtractableContent() map[string][]string {
	result := make(map[string][]string)

	if policies, err := govembed.ListPolicies(); err == nil {
		result["policies"] = policies
	}
	if schemas, err := govembed.ListSchemas(); err == nil {
		result["schemas"] = schemas
	}
	if prompts, err := govembed.ListReviewPrompts(); err == nil {
		result["review_prompts"] = prompts
	}
	if personas, err := govembed.ListPersonas(); err == nil {
		result["personas"] = personas
	}
	if commands, err := govembed.ListCommands(); err == nil {
		result["commands"] = commands
	}
	if langs, err := govembed.ListLanguageTemplates(); err == nil {
		result["language_templates"] = langs
	}

	// Count workflow templates
	if entries, err := govembed.ReadDir("templates/workflows"); err == nil {
		var workflows []string
		for _, e := range entries {
			if !e.IsDir() {
				workflows = append(workflows, e.Name())
			}
		}
		result["workflows"] = workflows
	}

	// Check for instructions
	if _, err := govembed.ReadFile("instructions.md"); err == nil {
		result["instructions"] = []string{"instructions.md"}
	}
	if _, err := govembed.ReadFile("CLAUDE.md"); err == nil {
		result["instructions"] = append(result["instructions"], "CLAUDE.md")
	}

	return result
}

// walkEmbeddedDir recursively lists all files under a path in the embedded FS.
func walkEmbeddedDir(root string) ([]string, error) {
	var files []string
	embFS := govembed.GovernanceFS()

	err := fs.WalkDir(embFS, filepath.Join("_content", root), func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		// Strip the _content/ prefix
		rel := strings.TrimPrefix(path, "_content/")
		files = append(files, rel)
		return nil
	})

	return files, err
}
