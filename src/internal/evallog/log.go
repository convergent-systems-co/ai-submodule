package evallog

import (
	"fmt"
	"io"
)

// Entry represents a single evaluation log entry.
type Entry struct {
	RuleID string
	Result string
	Detail string
}

// Log is an evaluation audit log that records rule evaluation results.
type Log struct {
	w       io.Writer
	entries []Entry
}

// New creates a new evaluation log that writes formatted output to w.
func New(w io.Writer) *Log {
	return &Log{w: w}
}

// Record logs a rule evaluation result. Result should be one of
// PASS, FAIL, WARN, or SKIP.
func (l *Log) Record(ruleID, result, detail string) {
	tag := "[" + result + "]"
	fmt.Fprintf(l.w, "%-6s %-40s %s\n", tag, ruleID, detail)
	l.entries = append(l.entries, Entry{
		RuleID: ruleID,
		Result: result,
		Detail: detail,
	})
}

// Entries returns a copy of all recorded log entries.
func (l *Log) Entries() []Entry {
	out := make([]Entry, len(l.entries))
	copy(out, l.entries)
	return out
}
