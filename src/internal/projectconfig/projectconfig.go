// Package projectconfig provides comment-preserving YAML configuration
// management for project.yaml files using the yaml.v3 Node API.
//
// It supports dotted-path traversal (e.g., "governance.parallel_coders"),
// type coercion for scalar values, and JSON Schema validation after writes.
package projectconfig

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strconv"
	"strings"

	"github.com/santhosh-tekuri/jsonschema/v6"
	"gopkg.in/yaml.v3"
)

// Config represents a loaded project.yaml file with its Node tree
// for comment-preserving round-trip editing.
type Config struct {
	path string
	root *yaml.Node // document node
}

// Load reads a project.yaml file and parses it into a yaml.Node tree.
func Load(path string) (*Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("reading config: %w", err)
	}

	return LoadFromBytes(data, path)
}

// LoadFromBytes parses YAML bytes into a Config. The path is stored
// for Save() but no file I/O occurs.
func LoadFromBytes(data []byte, path string) (*Config, error) {
	var doc yaml.Node
	if err := yaml.Unmarshal(data, &doc); err != nil {
		return nil, fmt.Errorf("parsing YAML: %w", err)
	}

	// yaml.Unmarshal wraps content in a DocumentNode
	if doc.Kind != yaml.DocumentNode || len(doc.Content) == 0 {
		return nil, fmt.Errorf("unexpected YAML structure: expected document node")
	}

	return &Config{
		path: path,
		root: &doc,
	}, nil
}

// Path returns the file path this config was loaded from.
func (c *Config) Path() string {
	return c.path
}

// Get retrieves the value at a dotted path (e.g., "governance.parallel_coders").
// Returns the string representation of the scalar value, or an error if the
// path does not exist or points to a non-scalar node.
func (c *Config) Get(dottedPath string) (string, error) {
	node, err := c.traverse(dottedPath)
	if err != nil {
		return "", err
	}

	if node.Kind != yaml.ScalarNode {
		// For sequences and mappings, encode to YAML string
		var buf bytes.Buffer
		enc := yaml.NewEncoder(&buf)
		enc.SetIndent(2)
		if err := enc.Encode(node); err != nil {
			return "", fmt.Errorf("encoding non-scalar value: %w", err)
		}
		enc.Close()
		return strings.TrimRight(buf.String(), "\n"), nil
	}

	return node.Value, nil
}

// Set updates or creates a value at a dotted path. The value string is
// coerced to the appropriate YAML scalar type (bool, int, float, null, or string).
// Intermediate mapping nodes are created as needed.
//
// Setting values on sequence (array) elements is not supported in this MVP.
func (c *Config) Set(dottedPath, value string) error {
	parts := strings.Split(dottedPath, ".")
	if len(parts) == 0 {
		return fmt.Errorf("empty path")
	}

	mapping := c.root.Content[0] // the top-level mapping
	if mapping.Kind != yaml.MappingNode {
		return fmt.Errorf("top-level node is not a mapping")
	}

	// Traverse/create intermediate nodes
	for i := 0; i < len(parts)-1; i++ {
		child := findMappingValue(mapping, parts[i])
		if child == nil {
			// Create intermediate mapping node
			keyNode := &yaml.Node{
				Kind:  yaml.ScalarNode,
				Tag:   "!!str",
				Value: parts[i],
			}
			valNode := &yaml.Node{
				Kind: yaml.MappingNode,
				Tag:  "!!map",
			}
			mapping.Content = append(mapping.Content, keyNode, valNode)
			mapping = valNode
		} else if child.Kind == yaml.MappingNode {
			mapping = child
		} else {
			return fmt.Errorf("path segment %q at %q is not a mapping (kind=%d)",
				parts[i], strings.Join(parts[:i+1], "."), child.Kind)
		}
	}

	lastKey := parts[len(parts)-1]
	existing := findMappingValue(mapping, lastKey)

	newNode := coerceScalar(value)

	if existing != nil {
		if existing.Kind == yaml.SequenceNode || existing.Kind == yaml.MappingNode {
			return fmt.Errorf("cannot set %q: target is a %s, not a scalar; edit project.yaml directly",
				dottedPath, kindName(existing.Kind))
		}
		existing.Kind = newNode.Kind
		existing.Tag = newNode.Tag
		existing.Value = newNode.Value
		existing.Style = 0 // reset to default style
	} else {
		keyNode := &yaml.Node{
			Kind:  yaml.ScalarNode,
			Tag:   "!!str",
			Value: lastKey,
		}
		mapping.Content = append(mapping.Content, keyNode, newNode)
	}

	return nil
}

// Save writes the Node tree back to the original file path, preserving
// comments and structure.
func (c *Config) Save() error {
	return c.SaveTo(c.path)
}

// SaveTo writes the Node tree to the specified file path.
func (c *Config) SaveTo(path string) error {
	data, err := c.Bytes()
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0644)
}

// Bytes encodes the Node tree to YAML bytes.
func (c *Config) Bytes() ([]byte, error) {
	var buf bytes.Buffer
	enc := yaml.NewEncoder(&buf)
	enc.SetIndent(2)
	if err := enc.Encode(c.root); err != nil {
		return nil, fmt.Errorf("encoding YAML: %w", err)
	}
	enc.Close()
	return buf.Bytes(), nil
}

// Flatten returns all leaf values as dotted-path key-value pairs,
// sorted alphabetically by path.
func (c *Config) Flatten() []KeyValue {
	mapping := c.root.Content[0]
	var kvs []KeyValue
	flattenNode(mapping, "", &kvs)
	sort.Slice(kvs, func(i, j int) bool {
		return kvs[i].Key < kvs[j].Key
	})
	return kvs
}

// KeyValue represents a flattened configuration entry.
type KeyValue struct {
	Key   string
	Value string
}

// Validate checks the current config against a JSON Schema.
// It converts the YAML to JSON first, then validates.
// Returns nil if valid or schemaData is empty.
func Validate(yamlData, schemaData []byte) error {
	if len(schemaData) == 0 {
		return nil
	}

	// YAML -> generic interface -> JSON
	var generic any
	if err := yaml.Unmarshal(yamlData, &generic); err != nil {
		return fmt.Errorf("parsing YAML for validation: %w", err)
	}

	jsonBytes, err := json.Marshal(generic)
	if err != nil {
		return fmt.Errorf("converting to JSON: %w", err)
	}

	c := jsonschema.NewCompiler()
	schema, err := jsonschema.UnmarshalJSON(bytes.NewReader(schemaData))
	if err != nil {
		return fmt.Errorf("parsing schema JSON: %w", err)
	}
	if err := c.AddResource("schema.json", schema); err != nil {
		return fmt.Errorf("adding schema resource: %w", err)
	}
	sch, err := c.Compile("schema.json")
	if err != nil {
		return fmt.Errorf("compiling schema: %w", err)
	}

	doc, err := jsonschema.UnmarshalJSON(bytes.NewReader(jsonBytes))
	if err != nil {
		return fmt.Errorf("parsing config JSON: %w", err)
	}

	verr := sch.Validate(doc)
	if verr == nil {
		return nil
	}

	ve, ok := verr.(*jsonschema.ValidationError)
	if !ok {
		return verr
	}

	errs := collectErrors(ve)
	return fmt.Errorf("schema validation failed:\n  %s", strings.Join(errs, "\n  "))
}

// --- internal helpers ---

// traverse follows a dotted path through the Node tree.
func (c *Config) traverse(dottedPath string) (*yaml.Node, error) {
	parts := strings.Split(dottedPath, ".")
	if len(parts) == 0 {
		return nil, fmt.Errorf("empty path")
	}

	current := c.root.Content[0] // top-level mapping
	for _, part := range parts {
		if current.Kind != yaml.MappingNode {
			return nil, fmt.Errorf("path segment %q: expected mapping, got %s", part, kindName(current.Kind))
		}
		child := findMappingValue(current, part)
		if child == nil {
			return nil, fmt.Errorf("key %q not found", dottedPath)
		}
		current = child
	}

	return current, nil
}

// findMappingValue finds the value node for a given key in a mapping node.
func findMappingValue(mapping *yaml.Node, key string) *yaml.Node {
	if mapping.Kind != yaml.MappingNode {
		return nil
	}
	for i := 0; i < len(mapping.Content)-1; i += 2 {
		if mapping.Content[i].Value == key {
			return mapping.Content[i+1]
		}
	}
	return nil
}

// coerceScalar converts a string value to an appropriately typed yaml.Node.
func coerceScalar(value string) *yaml.Node {
	// null
	if value == "null" || value == "~" || value == "" {
		return &yaml.Node{
			Kind:  yaml.ScalarNode,
			Tag:   "!!null",
			Value: value,
		}
	}

	// bool
	lower := strings.ToLower(value)
	if lower == "true" || lower == "false" {
		return &yaml.Node{
			Kind:  yaml.ScalarNode,
			Tag:   "!!bool",
			Value: lower,
		}
	}

	// integer
	if _, err := strconv.ParseInt(value, 10, 64); err == nil {
		return &yaml.Node{
			Kind:  yaml.ScalarNode,
			Tag:   "!!int",
			Value: value,
		}
	}

	// float
	if _, err := strconv.ParseFloat(value, 64); err == nil {
		return &yaml.Node{
			Kind:  yaml.ScalarNode,
			Tag:   "!!float",
			Value: value,
		}
	}

	// default: string
	return &yaml.Node{
		Kind:  yaml.ScalarNode,
		Tag:   "!!str",
		Value: value,
	}
}

// kindName returns a human-readable name for a yaml.Node Kind.
func kindName(k yaml.Kind) string {
	switch k {
	case yaml.DocumentNode:
		return "document"
	case yaml.SequenceNode:
		return "sequence"
	case yaml.MappingNode:
		return "mapping"
	case yaml.ScalarNode:
		return "scalar"
	case yaml.AliasNode:
		return "alias"
	default:
		return fmt.Sprintf("unknown(%d)", k)
	}
}

// flattenNode recursively collects leaf key-value pairs from a Node tree.
func flattenNode(node *yaml.Node, prefix string, kvs *[]KeyValue) {
	switch node.Kind {
	case yaml.MappingNode:
		for i := 0; i < len(node.Content)-1; i += 2 {
			key := node.Content[i].Value
			val := node.Content[i+1]
			path := key
			if prefix != "" {
				path = prefix + "." + key
			}
			if val.Kind == yaml.ScalarNode {
				*kvs = append(*kvs, KeyValue{Key: path, Value: val.Value})
			} else if val.Kind == yaml.MappingNode {
				flattenNode(val, path, kvs)
			} else if val.Kind == yaml.SequenceNode {
				// Represent sequences as comma-separated values
				var items []string
				for _, item := range val.Content {
					if item.Kind == yaml.ScalarNode {
						items = append(items, item.Value)
					} else {
						items = append(items, "<complex>")
					}
				}
				*kvs = append(*kvs, KeyValue{Key: path, Value: strings.Join(items, ", ")})
			}
		}
	case yaml.ScalarNode:
		if prefix != "" {
			*kvs = append(*kvs, KeyValue{Key: prefix, Value: node.Value})
		}
	}
}

// collectErrors recursively collects error messages from a
// jsonschema.ValidationError tree.
func collectErrors(ve *jsonschema.ValidationError) []string {
	var msgs []string
	if ve.ErrorKind != nil {
		loc := "/" + strings.Join(ve.InstanceLocation, "/")
		msg := fmt.Sprintf("%v", ve.ErrorKind)
		msgs = append(msgs, fmt.Sprintf("%s: %s", loc, msg))
	}
	for _, cause := range ve.Causes {
		msgs = append(msgs, collectErrors(cause)...)
	}
	return msgs
}
