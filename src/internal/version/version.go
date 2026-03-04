// Package version provides build-time version information for the dark-governance CLI.
// Values are injected via ldflags at build time (see Makefile).
package version

import (
	"encoding/json"
	"fmt"
	"runtime"
)

// Build-time variables injected via ldflags.
var (
	// Version is the semantic version (e.g., "0.1.0").
	Version = "dev"
	// Commit is the git commit SHA at build time.
	Commit = "unknown"
	// Date is the build timestamp in RFC 3339 format.
	Date = "unknown"
)

// Info holds structured version information.
type Info struct {
	Version   string `json:"version"`
	Commit    string `json:"commit"`
	Date      string `json:"date"`
	GoVersion string `json:"go_version"`
	Platform  string `json:"platform"`
}

// Get returns the current version info.
func Get() Info {
	return Info{
		Version:   Version,
		Commit:    Commit,
		Date:      Date,
		GoVersion: runtime.Version(),
		Platform:  fmt.Sprintf("%s/%s", runtime.GOOS, runtime.GOARCH),
	}
}

// String returns a human-readable version string.
func (i Info) String() string {
	return fmt.Sprintf("dark-governance %s (commit: %s, built: %s, %s, %s)",
		i.Version, i.Commit, i.Date, i.GoVersion, i.Platform)
}

// JSON returns the version info as a JSON string.
func (i Info) JSON() (string, error) {
	data, err := json.MarshalIndent(i, "", "  ")
	if err != nil {
		return "", fmt.Errorf("failed to marshal version info: %w", err)
	}
	return string(data), nil
}
