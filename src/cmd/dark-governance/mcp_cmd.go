package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"

	"github.com/spf13/cobra"
)

var (
	mcpTarget         string
	mcpGovernanceRoot string
)

var mcpCmd = &cobra.Command{
	Use:   "mcp",
	Short: "Manage MCP server integration",
	Long: `Install and manage the MCP (Model Context Protocol) server for IDE integration.

The MCP server provides governance tools to AI coding assistants like Claude
and Cursor through a standardized protocol.`,
}

var mcpInstallCmd = &cobra.Command{
	Use:   "install",
	Short: "Install MCP server configuration for an IDE",
	Long: `Write MCP server configuration to the appropriate IDE config location.

Supported targets:
  claude  — Write to the platform-specific Claude Desktop config
            (macOS: ~/Library/Application Support/Claude/claude_desktop_config.json)
  cursor  — Write to ~/.cursor/mcp.json
  all     — Write to all supported IDE configs

Examples:
  dark-governance mcp install                              # Install for all IDEs
  dark-governance mcp install --target claude               # Claude only
  dark-governance mcp install --governance-root /path/to    # Custom governance root`,
	RunE: runMCPInstall,
}

var mcpStatusCmd = &cobra.Command{
	Use:   "status",
	Short: "Show MCP server installation status",
	Long:  `Check whether MCP server configuration is present for supported IDEs.`,
	RunE:  runMCPStatus,
}

func init() {
	mcpInstallCmd.Flags().StringVar(&mcpTarget, "target", "all", "Target IDE (claude, cursor, all)")
	mcpInstallCmd.Flags().StringVar(&mcpGovernanceRoot, "governance-root", "", "Path to governance root (default: auto-detect)")

	mcpCmd.AddCommand(mcpInstallCmd)
	mcpCmd.AddCommand(mcpStatusCmd)
}

// mcpConfigPath returns the MCP config path for a given target IDE.
func mcpConfigPath(target string) (string, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return "", fmt.Errorf("failed to determine home directory: %w", err)
	}

	switch target {
	case "claude":
		// Claude Desktop stores config under the platform app support directory
		switch runtime.GOOS {
		case "darwin":
			return filepath.Join(homeDir, "Library", "Application Support", "Claude", "claude_desktop_config.json"), nil
		case "windows":
			appData := os.Getenv("APPDATA")
			if appData == "" {
				appData = filepath.Join(homeDir, "AppData", "Roaming")
			}
			return filepath.Join(appData, "Claude", "claude_desktop_config.json"), nil
		default:
			// Linux / other: use ~/.config/Claude/
			return filepath.Join(homeDir, ".config", "Claude", "claude_desktop_config.json"), nil
		}
	case "cursor":
		return filepath.Join(homeDir, ".cursor", "mcp.json"), nil
	default:
		return "", fmt.Errorf("unknown target: %s (supported: claude, cursor)", target)
	}
}

// mcpServerEntry builds the MCP server config entry.
func mcpServerEntry(governanceRoot string) map[string]interface{} {
	serverPath := filepath.Join(governanceRoot, "mcp-server", "index.js")

	// Use node as the command
	command := "node"
	if runtime.GOOS == "windows" {
		command = "node.exe"
	}

	return map[string]interface{}{
		"command": command,
		"args":    []string{serverPath},
		"env": map[string]string{
			"GOVERNANCE_ROOT": governanceRoot,
		},
	}
}

// writeMCPConfig writes the MCP server entry to an IDE's config file.
// It merges with existing config rather than overwriting.
func writeMCPConfig(configPath string, serverEntry map[string]interface{}) error {
	// Read existing config if present
	config := make(map[string]interface{})
	if data, err := os.ReadFile(configPath); err == nil {
		if jsonErr := json.Unmarshal(data, &config); jsonErr != nil {
			return fmt.Errorf("existing config at %s contains invalid JSON: %w", configPath, jsonErr)
		}
	} else if !os.IsNotExist(err) {
		return fmt.Errorf("failed to read existing config from %s: %w", configPath, err)
	}

	// Get or create mcpServers section
	servers, ok := config["mcpServers"].(map[string]interface{})
	if !ok {
		servers = make(map[string]interface{})
	}

	// Add/update the dark-factory-governance entry
	servers["dark-factory-governance"] = serverEntry
	config["mcpServers"] = servers

	// Ensure parent directory exists
	if err := os.MkdirAll(filepath.Dir(configPath), 0755); err != nil {
		return fmt.Errorf("failed to create config directory: %w", err)
	}

	// Write the config
	data, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal config: %w", err)
	}

	if err := os.WriteFile(configPath, append(data, '\n'), 0644); err != nil {
		return fmt.Errorf("failed to write config: %w", err)
	}

	return nil
}

func runMCPInstall(cmd *cobra.Command, args []string) error {
	// Determine governance root
	govRoot := mcpGovernanceRoot
	if govRoot == "" {
		// Try to auto-detect from CWD
		cwd, err := os.Getwd()
		if err != nil {
			return fmt.Errorf("failed to get working directory: %w", err)
		}
		// Check for .ai directory or governance directory
		if _, err := os.Stat(filepath.Join(cwd, "mcp-server")); err == nil {
			govRoot = cwd
		} else if _, err := os.Stat(filepath.Join(cwd, ".ai", "mcp-server")); err == nil {
			govRoot = filepath.Join(cwd, ".ai")
		} else {
			return fmt.Errorf("cannot auto-detect governance root; use --governance-root to specify")
		}
	}

	// Verify mcp-server directory exists
	mcpDir := filepath.Join(govRoot, "mcp-server")
	if _, err := os.Stat(mcpDir); os.IsNotExist(err) {
		return fmt.Errorf("MCP server directory not found at %s", mcpDir)
	}

	serverEntry := mcpServerEntry(govRoot)

	targets := []string{mcpTarget}
	if mcpTarget == "all" {
		targets = []string{"claude", "cursor"}
	}

	var results []map[string]string
	for _, target := range targets {
		configPath, err := mcpConfigPath(target)
		if err != nil {
			return err
		}

		if err := writeMCPConfig(configPath, serverEntry); err != nil {
			return fmt.Errorf("failed to install for %s: %w", target, err)
		}

		results = append(results, map[string]string{
			"target": target,
			"config": configPath,
		})

		if !flagJSON {
			fmt.Fprintf(os.Stdout, "  [OK] %s: %s\n", target, configPath)
		}
	}

	if flagJSON {
		output := map[string]interface{}{
			"status":          "installed",
			"governance_root": govRoot,
			"targets":         results,
		}
		data, _ := json.MarshalIndent(output, "", "  ")
		fmt.Fprintln(os.Stdout, string(data))
	} else {
		fmt.Fprintln(os.Stdout, "")
		fmt.Fprintf(os.Stdout, "MCP server configured with governance root: %s\n", govRoot)
	}

	return nil
}

func runMCPStatus(cmd *cobra.Command, args []string) error {
	targets := []string{"claude", "cursor"}

	type targetStatus struct {
		Target    string `json:"target"`
		Config    string `json:"config"`
		Installed bool   `json:"installed"`
	}

	var statuses []targetStatus
	for _, target := range targets {
		configPath, err := mcpConfigPath(target)
		if err != nil {
			continue
		}

		installed := false
		if data, readErr := os.ReadFile(configPath); readErr == nil {
			var config map[string]interface{}
			if jsonErr := json.Unmarshal(data, &config); jsonErr == nil {
				if servers, ok := config["mcpServers"].(map[string]interface{}); ok {
					if _, ok := servers["dark-factory-governance"]; ok {
						installed = true
					}
				}
			}
		}

		statuses = append(statuses, targetStatus{
			Target:    target,
			Config:    configPath,
			Installed: installed,
		})
	}

	if flagJSON {
		data, _ := json.MarshalIndent(statuses, "", "  ")
		fmt.Fprintln(os.Stdout, string(data))
		return nil
	}

	fmt.Fprintln(os.Stdout, "MCP server status")
	fmt.Fprintln(os.Stdout, "")
	for _, s := range statuses {
		status := "not installed"
		if s.Installed {
			status = "installed"
		}
		fmt.Fprintf(os.Stdout, "  %-10s %s (%s)\n", s.Target+":", status, s.Config)
	}

	return nil
}
