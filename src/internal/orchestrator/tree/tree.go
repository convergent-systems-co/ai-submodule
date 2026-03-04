// Package tree provides workload tree visualization for the orchestrator.
// It builds a parent-child tree from dispatch and registry records and
// formats it as an indented text diagram.
//
// Ported from Python: governance/engine/orchestrator/tree.py
package tree

import (
	"fmt"
	"sort"
	"strings"
)

// ---------------------------------------------------------------------------
// Node
// ---------------------------------------------------------------------------

// Node represents one agent in the workload tree.
type Node struct {
	TaskID   string  `json:"task_id"`
	Persona  string  `json:"persona"`
	Status   string  `json:"status"`
	Children []*Node `json:"children,omitempty"`
}

// ---------------------------------------------------------------------------
// Build
// ---------------------------------------------------------------------------

// Build constructs the workload tree from dispatch records and registry data.
// Each map entry must have "task_id", "persona", "status", and optionally
// "parent_task_id" keys.
func Build(records map[string]map[string]interface{}, registry map[string]map[string]interface{}) []*Node {
	// Merge records and registry into a single lookup.
	all := make(map[string]map[string]interface{})
	for id, r := range records {
		all[id] = r
	}
	for id, r := range registry {
		if _, exists := all[id]; !exists {
			all[id] = r
		}
	}

	// Build nodes.
	nodes := make(map[string]*Node)
	for id, data := range all {
		nodes[id] = &Node{
			TaskID:  strVal(data, "task_id", id),
			Persona: strVal(data, "persona", "unknown"),
			Status:  strVal(data, "status", "unknown"),
		}
	}

	// Wire parent-child relationships.
	var roots []*Node
	for id, data := range all {
		parentID := strVal(data, "parent_task_id", "")
		if parentID == "" {
			roots = append(roots, nodes[id])
		} else if parent, ok := nodes[parentID]; ok {
			parent.Children = append(parent.Children, nodes[id])
		} else {
			// Orphan — treat as root.
			roots = append(roots, nodes[id])
		}
	}

	// Sort roots and children for deterministic output.
	sortNodes(roots)
	for _, n := range nodes {
		sortNodes(n.Children)
	}

	return roots
}

// ---------------------------------------------------------------------------
// Format
// ---------------------------------------------------------------------------

// Format renders the tree as an indented text diagram.
func Format(roots []*Node) string {
	if len(roots) == 0 {
		return "(no agents)"
	}

	var sb strings.Builder
	for i, root := range roots {
		formatNode(&sb, root, "", i == len(roots)-1)
	}
	return sb.String()
}

// formatNode recursively renders a single node and its children.
func formatNode(sb *strings.Builder, n *Node, prefix string, isLast bool) {
	connector := "\u251c\u2500\u2500" // "├──"
	if isLast {
		connector = "\u2514\u2500\u2500" // "└──"
	}

	icon := statusIcon(n.Status)
	if prefix == "" {
		// Root node — no connector.
		sb.WriteString(fmt.Sprintf("%s %s [%s]\n", icon, n.Persona, n.TaskID))
	} else {
		sb.WriteString(fmt.Sprintf("%s%s %s %s [%s]\n", prefix, connector, icon, n.Persona, n.TaskID))
	}

	childPrefix := prefix
	if prefix != "" {
		if isLast {
			childPrefix += "    "
		} else {
			childPrefix += "\u2502   " // "│   "
		}
	} else {
		childPrefix = ""
	}

	for i, child := range n.Children {
		formatNode(sb, child, childPrefix, i == len(n.Children)-1)
	}
}

// statusIcon returns a Unicode icon for the agent status.
func statusIcon(status string) string {
	switch status {
	case "registered":
		return "\u25cb" // ○
	case "running":
		return "\u25cf" // ●
	case "completed":
		return "\u2713" // ✓
	case "failed":
		return "\u2717" // ✗
	default:
		return "?"
	}
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

func strVal(m map[string]interface{}, key, fallback string) string {
	if v, ok := m[key].(string); ok && v != "" {
		return v
	}
	return fallback
}

func sortNodes(nodes []*Node) {
	sort.Slice(nodes, func(i, j int) bool {
		return nodes[i].TaskID < nodes[j].TaskID
	})
}
