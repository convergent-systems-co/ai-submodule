package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	govembed "github.com/SET-Apps/ai-submodule/src/internal/embed"
	"github.com/SET-Apps/ai-submodule/src/internal/projectconfig"
	"github.com/spf13/cobra"
)

var (
	configureNonInteractive bool
	configureOutput         string
	configureList           bool
	configureGet            string
	configureSet            string
)

var configureCmd = &cobra.Command{
	Use:   "configure",
	Short: "Manage project.yaml configuration",
	Long: `Read, write, and manage project.yaml configuration values.

Modes:
  --list                     List all current settings (dotted paths)
  --get <key>                Get a specific value by dotted path
  --set <key>=<value>        Set a specific value by dotted path
  (no args)                  Interactive guided setup
  --non-interactive          Generate default project.yaml from template

Schema validation runs after every write operation.

Examples:
  dark-governance configure                                     # Interactive guided setup
  dark-governance configure --list                              # Show all settings
  dark-governance configure --get governance.parallel_coders    # Get a value
  dark-governance configure --set governance.parallel_coders=10 # Set a value
  dark-governance configure --non-interactive                   # Generate default config
  dark-governance configure --non-interactive --output out.yaml # Custom output path`,
	RunE: runConfigure,
}

func init() {
	configureCmd.Flags().BoolVar(&configureNonInteractive, "non-interactive", false, "Generate default config without prompts")
	configureCmd.Flags().StringVar(&configureOutput, "output", "project.yaml", "Output path for generated config")
	configureCmd.Flags().BoolVar(&configureList, "list", false, "List all current configuration settings")
	configureCmd.Flags().StringVar(&configureGet, "get", "", "Get a configuration value by dotted path")
	configureCmd.Flags().StringVar(&configureSet, "set", "", "Set a configuration value (key=value)")
}

func runConfigure(cmd *cobra.Command, args []string) error {
	// Dispatch by mode
	switch {
	case configureList:
		return runConfigureList()
	case configureGet != "":
		return runConfigureGet(configureGet)
	case configureSet != "":
		return runConfigureSet(configureSet)
	case configureNonInteractive:
		return runConfigureNonInteractive()
	default:
		return runConfigureInteractive()
	}
}

// resolveConfigPath returns the project.yaml path to use. If flagConfig is set
// (via --config), use that. Otherwise look in cwd.
func resolveConfigPath() (string, error) {
	if flagConfig != "" {
		return flagConfig, nil
	}
	cwd, err := os.Getwd()
	if err != nil {
		return "", fmt.Errorf("failed to get working directory: %w", err)
	}
	return filepath.Join(cwd, "project.yaml"), nil
}

// loadConfig loads project.yaml from the resolved path.
func loadConfig() (*projectconfig.Config, error) {
	path, err := resolveConfigPath()
	if err != nil {
		return nil, err
	}
	cfg, err := projectconfig.Load(path)
	if err != nil {
		return nil, fmt.Errorf("failed to load config at %s: %w", path, err)
	}
	return cfg, nil
}

// loadSchemaData returns the embedded project.schema.json, or nil if unavailable.
func loadSchemaData() []byte {
	if !govembed.HasContent() {
		return nil
	}
	data, err := govembed.GetSchema("project.schema.json")
	if err != nil {
		return nil
	}
	return data
}

// --- --list mode ---

func runConfigureList() error {
	cfg, err := loadConfig()
	if err != nil {
		return err
	}

	kvs := cfg.Flatten()

	if flagJSON {
		entries := make([]map[string]string, len(kvs))
		for i, kv := range kvs {
			entries[i] = map[string]string{"key": kv.Key, "value": kv.Value}
		}
		data, _ := json.MarshalIndent(entries, "", "  ")
		fmt.Fprintln(os.Stdout, string(data))
		return nil
	}

	// Find max key width for alignment
	maxW := 4
	for _, kv := range kvs {
		if len(kv.Key) > maxW {
			maxW = len(kv.Key)
		}
	}
	if maxW > 50 {
		maxW = 50
	}

	for _, kv := range kvs {
		displayKey := kv.Key
		if len(displayKey) > maxW {
			displayKey = displayKey[:maxW-1] + "…"
		}
		val := kv.Value
		if val == "" {
			val = "(empty)"
		}
		fmt.Fprintf(os.Stdout, "%-*s  %s\n", maxW, displayKey, val)
	}
	fmt.Fprintf(os.Stdout, "\n%d settings\n", len(kvs))
	return nil
}

// --- --get mode ---

func runConfigureGet(key string) error {
	cfg, err := loadConfig()
	if err != nil {
		return err
	}

	val, err := cfg.Get(key)
	if err != nil {
		return fmt.Errorf("key %q: %w", key, err)
	}

	if flagJSON {
		out := map[string]string{"key": key, "value": val}
		data, _ := json.MarshalIndent(out, "", "  ")
		fmt.Fprintln(os.Stdout, string(data))
	} else {
		fmt.Fprintln(os.Stdout, val)
	}
	return nil
}

// --- --set mode ---

func runConfigureSet(expr string) error {
	eqIdx := strings.Index(expr, "=")
	if eqIdx < 1 {
		return fmt.Errorf("invalid --set format: expected key=value, got %q", expr)
	}
	key := expr[:eqIdx]
	value := expr[eqIdx+1:]

	cfg, err := loadConfig()
	if err != nil {
		return err
	}

	if err := cfg.Set(key, value); err != nil {
		return fmt.Errorf("setting %q: %w", key, err)
	}

	if err := cfg.Save(); err != nil {
		return fmt.Errorf("saving config: %w", err)
	}

	// Validate after write
	yamlData, err := cfg.Bytes()
	if err != nil {
		return fmt.Errorf("encoding config for validation: %w", err)
	}

	schemaData := loadSchemaData()
	if verr := projectconfig.Validate(yamlData, schemaData); verr != nil {
		// Report as warning, don't rollback
		fmt.Fprintf(os.Stderr, "Warning: %v\n", verr)
	}

	if flagJSON {
		newVal, _ := cfg.Get(key)
		out := map[string]string{"key": key, "value": newVal, "status": "updated"}
		data, _ := json.MarshalIndent(out, "", "  ")
		fmt.Fprintln(os.Stdout, string(data))
	} else {
		fmt.Fprintf(os.Stdout, "%s = %s\n", key, value)
	}
	return nil
}

// --- interactive mode ---

// interactiveField defines a field to prompt for in interactive mode.
type interactiveField struct {
	Key     string
	Prompt  string
	Default string
}

func runConfigureInteractive() error {
	return runConfigureInteractiveWithReader(os.Stdin)
}

// runConfigureInteractiveWithReader runs the interactive wizard reading
// input from the provided reader, enabling testability.
func runConfigureInteractiveWithReader(in io.Reader) error {
	configPath, err := resolveConfigPath()
	if err != nil {
		return err
	}

	// Load existing config or create from defaults
	var cfg *projectconfig.Config
	if _, statErr := os.Stat(configPath); statErr == nil {
		cfg, err = projectconfig.Load(configPath)
		if err != nil {
			return fmt.Errorf("failed to load existing config: %w", err)
		}
		fmt.Fprintf(os.Stdout, "Editing existing configuration at %s\n\n", configPath)
	} else {
		cfg, err = projectconfig.LoadFromBytes(defaultProjectYAML(), configPath)
		if err != nil {
			return fmt.Errorf("failed to create default config: %w", err)
		}
		fmt.Fprintln(os.Stdout, "Creating new project.yaml configuration")
		fmt.Fprintln(os.Stdout, "")
	}

	fields := []interactiveField{
		{Key: "name", Prompt: "Project name", Default: getDefault(cfg, "name")},
		{Key: "governance.policy_profile", Prompt: "Policy profile (default, fin_pii_high, infrastructure_critical, reduced_touchpoint)", Default: getDefault(cfg, "governance.policy_profile")},
		{Key: "governance.parallel_coders", Prompt: "Max parallel coders (-1 to 10)", Default: getDefault(cfg, "governance.parallel_coders")},
		{Key: "governance.use_project_manager", Prompt: "Enable Project Manager mode (true/false)", Default: getDefault(cfg, "governance.use_project_manager")},
		{Key: "conventions.git.commit_style", Prompt: "Commit style (conventional, freeform)", Default: getDefault(cfg, "conventions.git.commit_style")},
	}

	scanner := bufio.NewScanner(in)

	for _, field := range fields {
		defStr := ""
		if field.Default != "" {
			defStr = " [" + field.Default + "]"
		}
		fmt.Fprintf(os.Stdout, "%s%s: ", field.Prompt, defStr)

		var input string
		if scanner.Scan() {
			input = strings.TrimSpace(scanner.Text())
		}

		if input == "" {
			continue // keep current/default value
		}

		if err := cfg.Set(field.Key, input); err != nil {
			fmt.Fprintf(os.Stderr, "Warning: could not set %s: %v\n", field.Key, err)
		}
	}

	if err := cfg.SaveTo(configPath); err != nil {
		return fmt.Errorf("saving config: %w", err)
	}

	// Validate after write
	yamlData, err := cfg.Bytes()
	if err != nil {
		return fmt.Errorf("encoding config for validation: %w", err)
	}

	schemaData := loadSchemaData()
	if verr := projectconfig.Validate(yamlData, schemaData); verr != nil {
		fmt.Fprintf(os.Stderr, "Warning: %v\n", verr)
	}

	fmt.Fprintf(os.Stdout, "\nConfiguration saved to %s\n", configPath)
	return nil
}

// getDefault retrieves the current value for a key, returning empty string if not found.
func getDefault(cfg *projectconfig.Config, key string) string {
	val, err := cfg.Get(key)
	if err != nil {
		return ""
	}
	return val
}

// --- non-interactive mode (existing functionality) ---

func runConfigureNonInteractive() error {
	outputPath := configureOutput

	// Check if output already exists
	if _, statErr := os.Stat(outputPath); statErr == nil {
		if flagJSON {
			fmt.Fprintf(os.Stdout, `{"status": "already_exists", "path": %q}`+"\n", outputPath)
		} else {
			fmt.Fprintf(os.Stdout, "Configuration file already exists at %s\n", outputPath)
			fmt.Fprintln(os.Stdout, "Remove it first or specify a different --output path.")
		}
		return nil
	}

	// Try to load from embedded content
	var content []byte
	if govembed.HasContent() {
		// Try language-specific template first if we can detect
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("failed to get current working directory: %w", err)
		}
		lang := detectLanguage(cwd)
		if lang != "" {
			templatePath := filepath.Join("templates", "languages", lang, "project.yaml")
			if data, err := govembed.ReadFile(templatePath); err == nil {
				content = data
			}
		}

		// Fall back to a generic default
		if content == nil {
			content = defaultProjectYAML()
		}
	} else {
		content = defaultProjectYAML()
	}

	// Ensure parent directory exists
	if dir := filepath.Dir(outputPath); dir != "." {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create output directory: %w", err)
		}
	}

	// Write the file
	if err := os.WriteFile(outputPath, content, 0644); err != nil {
		return fmt.Errorf("failed to write config: %w", err)
	}

	if flagJSON {
		output := map[string]interface{}{
			"status": "created",
			"path":   outputPath,
			"size":   len(content),
		}
		data, _ := json.MarshalIndent(output, "", "  ")
		fmt.Fprintln(os.Stdout, string(data))
	} else {
		fmt.Fprintf(os.Stdout, "Configuration created at %s\n", outputPath)
		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintln(os.Stdout, "Next steps:")
		fmt.Fprintln(os.Stdout, "  1. Edit project.yaml to match your project")
		fmt.Fprintln(os.Stdout, "  2. Run 'dark-governance init' to set up governance")
	}

	return nil
}

// defaultProjectYAML generates a minimal default project.yaml.
func defaultProjectYAML() []byte {
	return []byte(`# Project AI Configuration
# Generated by dark-governance configure

name: ""
languages: []
framework: null

# Governance configuration
governance:
  skip_panel_validation: false
  policy_profile: "default"
  parallel_coders: 5
  use_project_manager: false

# Required panels (from default policy)
panels:
  - code-review.md
  - security-review.md
  - threat-modeling.md
  - cost-analysis.md
  - documentation-review.md
  - data-governance-review.md

# Git conventions
conventions:
  git:
    branch_pattern: "{network_id}/{type}/{number}/{name}"
    commit_style: "conventional"
`)
}
