import { join, basename } from "node:path";
import { existsSync, statSync, mkdirSync, writeFileSync, readdirSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { z } from "zod";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { readTextFile, spawnPython, scanYamlFiles } from "./utils.js";
import { discoverResources } from "./resources.js";
import {
  discoverSkills,
  getDefaultSkillsDir,
  generateToolDefinition,
  handleSkillToolCall,
  SkillInputSchema,
  type LoadedSkill,
} from "./skills.js";

/**
 * Register all MCP tools with the server, including auto-discovered skills.
 */
export async function registerTools(
  server: McpServer,
  governanceRoot: string
): Promise<number> {
  // Tool: validate_emission
  server.tool(
    "validate_emission",
    "Validate a panel emission JSON against the panel-output schema",
    {
      emission_json: z.string().describe("The emission JSON string to validate"),
    },
    async ({ emission_json }) => {
      try {
        const emission = JSON.parse(emission_json);
        const schemaPath = join(
          governanceRoot,
          "governance",
          "schemas",
          "panel-output.schema.json"
        );
        const schemaText = await readTextFile(schemaPath);
        const schema = JSON.parse(schemaText);

        const errors = validateAgainstSchema(emission, schema);

        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(
                {
                  valid: errors.length === 0,
                  errors: errors.length > 0 ? errors : undefined,
                },
                null,
                2
              ),
            },
          ],
        };
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(
                { valid: false, errors: [`Parse error: ${message}`] },
                null,
                2
              ),
            },
          ],
          isError: true,
        };
      }
    }
  );

  // Tool: check_policy
  server.tool(
    "check_policy",
    "Run the policy engine against emissions to produce a merge decision",
    {
      emissions_dir: z.string().describe("Path to the directory containing panel emission files"),
      profile: z.string().default("default").describe("Policy profile name (default, fin_pii_high, infrastructure_critical, reduced_touchpoint)"),
    },
    async ({ emissions_dir, profile }) => {
      // Validate emissions_dir exists and is a directory before spawning subprocess
      if (!existsSync(emissions_dir)) {
        return {
          content: [{ type: "text" as const, text: JSON.stringify({ decision: "error", details: `Emissions directory does not exist: ${emissions_dir}` }, null, 2) }],
          isError: true,
        };
      }
      if (!statSync(emissions_dir).isDirectory()) {
        return {
          content: [{ type: "text" as const, text: JSON.stringify({ decision: "error", details: `Path is not a directory: ${emissions_dir}` }, null, 2) }],
          isError: true,
        };
      }

      const policyEnginePath = join(
        governanceRoot,
        "governance",
        "bin",
        "policy-engine.py"
      );

      const result = await spawnPython(
        [policyEnginePath, "--emissions-dir", emissions_dir, "--profile", profile],
        governanceRoot
      );

      if (!result.ok) {
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(
                {
                  decision: "error",
                  details: result.stderr || "Policy engine failed with no error message",
                  python_available: result.exitCode !== 1 || !result.stderr.includes("Failed to spawn"),
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        };
      }

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(
              { decision: "completed", details: result.stdout.trim() },
              null,
              2
            ),
          },
        ],
      };
    }
  );

  // Tool: generate_name
  server.tool(
    "generate_name",
    "Generate a compliant Azure resource name using the naming convention",
    {
      resource_type: z.string().describe("Azure resource type (e.g., Microsoft.KeyVault/vaults)"),
      lob: z.string().describe("Line of business code"),
      stage: z.string().describe("Deployment stage (dev, staging, prod)"),
      app_name: z.string().describe("Application name"),
      app_id: z.string().describe("Application identifier"),
    },
    async ({ resource_type, lob, stage, app_name, app_id }) => {
      const namingScript = join(governanceRoot, "bin", "generate-name.py");

      const result = await spawnPython(
        [
          namingScript,
          "--resource-type", resource_type,
          "--lob", lob,
          "--stage", stage,
          "--app-name", app_name,
          "--app-id", app_id,
        ],
        governanceRoot
      );

      if (!result.ok) {
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify(
                {
                  error: result.stderr || "Name generation failed",
                  python_available: result.exitCode !== 1 || !result.stderr.includes("Failed to spawn"),
                },
                null,
                2
              ),
            },
          ],
          isError: true,
        };
      }

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(
              { name: result.stdout.trim() },
              null,
              2
            ),
          },
        ],
      };
    }
  );

  // Tool: list_panels
  server.tool(
    "list_panels",
    "List all available governance review panels with their descriptions and URIs",
    {},
    async () => {
      const resources = await discoverResources(governanceRoot);
      const panels = resources
        .filter((r) => r.uri.startsWith("governance://reviews/"))
        .map((r) => ({
          name: r.uri.replace("governance://reviews/", ""),
          description: r.description,
          uri: r.uri,
        }));

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(panels, null, 2),
          },
        ],
      };
    }
  );

  // Tool: list_policy_profiles
  server.tool(
    "list_policy_profiles",
    "List available policy profiles with their key settings",
    {},
    async () => {
      const profiles = [
        {
          name: "default",
          description: "Standard risk tolerance, auto-merge enabled with conditions",
          risk_tolerance: "standard",
          auto_merge: true,
        },
        {
          name: "fin_pii_high",
          description: "SOC2/PCI-DSS/HIPAA/GDPR compliance, auto-merge disabled",
          risk_tolerance: "low",
          auto_merge: false,
        },
        {
          name: "infrastructure_critical",
          description: "Mandatory architecture and SRE review for infrastructure changes",
          risk_tolerance: "low",
          auto_merge: false,
        },
        {
          name: "reduced_touchpoint",
          description: "Near-full autonomy, human approval only for policy overrides",
          risk_tolerance: "high",
          auto_merge: true,
        },
      ];

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(profiles, null, 2),
          },
        ],
      };
    }
  );

  // Tool: list_personas
  server.tool(
    "list_personas",
    "List all available agentic personas with their descriptions",
    {},
    async () => {
      const resources = await discoverResources(governanceRoot);
      const personas = resources
        .filter((r) => r.uri.startsWith("governance://personas/"))
        .map((r) => ({
          name: r.uri.replace("governance://personas/", ""),
          description: r.description,
          uri: r.uri,
          prompt: `persona_${r.uri.replace("governance://personas/", "")}`,
        }));

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify(personas, null, 2),
          },
        ],
      };
    }
  );

  // Tool: search_catalog
  server.tool(
    "search_catalog",
    "Search the governance prompt and resource catalog by keyword. Returns matching reviews, personas, policies, and developer prompts.",
    {
      query: z.string().describe("Search keyword(s) to match against names and descriptions"),
      category: z.string().optional().describe("Filter by category: reviews, personas, policies, workflows, prompts (optional)"),
    },
    async ({ query, category }) => {
      const resources = await discoverResources(governanceRoot);
      const queryLower = query.toLowerCase();

      let filtered = resources.filter((r) => {
        const searchable = `${r.name} ${r.description}`.toLowerCase();
        return searchable.includes(queryLower);
      });

      if (category) {
        const categoryMap: Record<string, string> = {
          reviews: "governance://reviews/",
          personas: "governance://personas/",
          policies: "governance://policy/",
          workflows: "governance://workflows/",
          schemas: "governance://schemas/",
        };
        const prefix = categoryMap[category];
        if (prefix) {
          filtered = filtered.filter((r) => r.uri.startsWith(prefix));
        }
      }

      const results = filtered.map((r) => ({
        name: r.name,
        description: r.description,
        uri: r.uri,
        category: r.uri.split("/")[2] || "other",
      }));

      return {
        content: [
          {
            type: "text" as const,
            text: JSON.stringify({
              query,
              count: results.length,
              results,
            }, null, 2),
          },
        ],
      };
    }
  );


  // Tool: create_plan — write a plan to .governance/plans/
  server.tool(
    "create_plan",
    "Create an implementation plan in .governance/plans/. The plan file is written with the given content.",
    {
      plan_name: z.string().describe("Plan filename without extension (e.g., '42-fix-auth-flow')"),
      content: z.string().describe("Markdown content for the plan"),
    },
    async ({ plan_name, content }) => {
      try {
        const plansDir = join(governanceRoot, "..", ".governance", "plans");
        if (!existsSync(plansDir)) {
          mkdirSync(plansDir, { recursive: true });
        }
        const filePath = join(plansDir, `${plan_name}.md`);
        writeFileSync(filePath, content, "utf-8");
        return {
          content: [
            {
              type: "text" as const,
              text: JSON.stringify({ success: true, path: filePath }, null, 2),
            },
          ],
        };
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return {
          content: [
            { type: "text" as const, text: JSON.stringify({ success: false, error: message }, null, 2) },
          ],
          isError: true,
        };
      }
    }
  );

  // Tool: write_emission — write a validated emission to .governance/panels/
  server.tool(
    "write_emission",
    "Write a panel emission JSON to .governance/panels/. Validates against the schema before writing.",
    {
      panel_name: z.string().describe("Panel name (e.g., 'code-review', 'security-review')"),
      emission_json: z.string().describe("The emission JSON string to validate and write"),
    },
    async ({ panel_name, emission_json }) => {
      try {
        const emission = JSON.parse(emission_json);

        // Validate against schema
        const schemaPath = join(governanceRoot, "governance", "schemas", "panel-output.schema.json");
        const schemaText = await readTextFile(schemaPath);
        const schema = JSON.parse(schemaText);
        const errors = validateAgainstSchema(emission, schema);

        if (errors.length > 0) {
          return {
            content: [
              { type: "text" as const, text: JSON.stringify({ success: false, errors }, null, 2) },
            ],
            isError: true,
          };
        }

        // Write to .governance/panels/
        const panelsDir = join(governanceRoot, "..", ".governance", "panels");
        if (!existsSync(panelsDir)) {
          mkdirSync(panelsDir, { recursive: true });
        }
        const filePath = join(panelsDir, `${panel_name}.json`);
        writeFileSync(filePath, JSON.stringify(emission, null, 2), "utf-8");

        return {
          content: [
            { type: "text" as const, text: JSON.stringify({ success: true, path: filePath, valid: true }, null, 2) },
          ],
        };
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return {
          content: [
            { type: "text" as const, text: JSON.stringify({ success: false, error: message }, null, 2) },
          ],
          isError: true,
        };
      }
    }
  );

  // Tool: read_checkpoint — read the latest checkpoint
  server.tool(
    "read_checkpoint",
    "Read the latest governance checkpoint from .governance/checkpoints/",
    {},
    async () => {
      try {
        const checkpointDir = join(governanceRoot, "..", ".governance", "checkpoints");
        if (!existsSync(checkpointDir)) {
          return {
            content: [
              { type: "text" as const, text: JSON.stringify({ found: false, message: "No checkpoints directory" }, null, 2) },
            ],
          };
        }

        const files = readdirSync(checkpointDir)
          .filter((f: string) => f.endsWith(".json"))
          .sort()
          .reverse();

        if (files.length === 0) {
          return {
            content: [
              { type: "text" as const, text: JSON.stringify({ found: false, message: "No checkpoints found" }, null, 2) },
            ],
          };
        }

        const latestPath = join(checkpointDir, files[0]);
        const content = await readFile(latestPath, "utf-8");
        const checkpoint = JSON.parse(content);

        return {
          content: [
            { type: "text" as const, text: JSON.stringify({ found: true, file: files[0], checkpoint }, null, 2) },
          ],
        };
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return {
          content: [
            { type: "text" as const, text: JSON.stringify({ found: false, error: message }, null, 2) },
          ],
          isError: true,
        };
      }
    }
  );

  // Tool: get_governance_status — aggregate project governance posture
  server.tool(
    "get_governance_status",
    "Get an aggregate view of the project's governance posture: emissions, plans, checkpoints, and policy profile",
    {},
    async () => {
      try {
        const status: Record<string, unknown> = {
          governance_root: governanceRoot,
        };

        // Count emissions
        const panelsDir = join(governanceRoot, "..", ".governance", "panels");
        if (existsSync(panelsDir) && statSync(panelsDir).isDirectory()) {
          const emissions = readdirSync(panelsDir).filter((f: string) => f.endsWith(".json"));
          status.emissions_count = emissions.length;
          status.emissions = emissions;
        } else {
          status.emissions_count = 0;
        }

        // Count plans
        const plansDir = join(governanceRoot, "..", ".governance", "plans");
        if (existsSync(plansDir) && statSync(plansDir).isDirectory()) {
          const plans = readdirSync(plansDir).filter((f: string) => f.endsWith(".md"));
          status.plans_count = plans.length;
        } else {
          status.plans_count = 0;
        }

        // Count checkpoints
        const checkpointDir = join(governanceRoot, "..", ".governance", "checkpoints");
        if (existsSync(checkpointDir) && statSync(checkpointDir).isDirectory()) {
          const checkpoints = readdirSync(checkpointDir).filter((f: string) => f.endsWith(".json"));
          status.checkpoints_count = checkpoints.length;
        } else {
          status.checkpoints_count = 0;
        }

        // Check for project.yaml
        const projectYamlPaths = [
          join(governanceRoot, "..", "project.yaml"),
          join(governanceRoot, "project.yaml"),
        ];
        status.project_yaml_found = projectYamlPaths.some((p) => existsSync(p));

        // List available policy profiles
        const policyDir = join(governanceRoot, "governance", "policy");
        if (existsSync(policyDir) && statSync(policyDir).isDirectory()) {
          const profiles = readdirSync(policyDir)
            .filter((f: string) => f.endsWith(".yaml"))
            .map((f: string) => f.replace(".yaml", ""));
          status.available_profiles = profiles;
        }

        return {
          content: [
            { type: "text" as const, text: JSON.stringify(status, null, 2) },
          ],
        };
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return {
          content: [
            { type: "text" as const, text: JSON.stringify({ error: message }, null, 2) },
          ],
          isError: true,
        };
      }
    }
  );

  // Tool: validate_project_yaml — schema validation for project.yaml
  server.tool(
    "validate_project_yaml",
    "Validate project.yaml against the project schema",
    {
      yaml_path: z.string().optional().describe("Path to project.yaml (defaults to project root)"),
    },
    async ({ yaml_path }) => {
      try {
        const projectYaml = yaml_path || join(governanceRoot, "..", "project.yaml");
        if (!existsSync(projectYaml)) {
          return {
            content: [
              { type: "text" as const, text: JSON.stringify({ valid: false, error: `File not found: ${projectYaml}` }, null, 2) },
            ],
          };
        }

        const schemaPath = join(governanceRoot, "governance", "schemas", "project.schema.json");
        if (!existsSync(schemaPath)) {
          return {
            content: [
              { type: "text" as const, text: JSON.stringify({ valid: false, error: "Project schema not found" }, null, 2) },
            ],
          };
        }

        // Use Python for YAML parsing + validation
        const result = await spawnPython(
          ["-c", `
import json, yaml, sys
from pathlib import Path

yaml_path = sys.argv[1]
schema_path = sys.argv[2]

with open(yaml_path) as f:
    data = yaml.safe_load(f) or {}

with open(schema_path) as f:
    schema = json.load(f)

try:
    from jsonschema import validate, ValidationError
    validate(data, schema)
    print(json.dumps({"valid": True}))
except ValidationError as e:
    print(json.dumps({"valid": False, "error": e.message, "path": list(e.path)}))
except ImportError:
    print(json.dumps({"valid": None, "error": "jsonschema not installed"}))
`, projectYaml, schemaPath],
          governanceRoot
        );

        if (result.ok) {
          return {
            content: [
              { type: "text" as const, text: result.stdout.trim() },
            ],
          };
        }

        return {
          content: [
            { type: "text" as const, text: JSON.stringify({ valid: false, error: result.stderr || "Validation failed" }, null, 2) },
          ],
          isError: true,
        };
      } catch (err) {
        const message = err instanceof Error ? err.message : String(err);
        return {
          content: [
            { type: "text" as const, text: JSON.stringify({ valid: false, error: message }, null, 2) },
          ],
          isError: true,
        };
      }
    }
  );

  // Tool: health_check — verify server, governance root, Python availability
  server.tool(
    "health_check",
    "Check the health of the MCP server: governance root, Python, schemas, and policy engine availability",
    {},
    async () => {
      const health: Record<string, unknown> = {
        server: "running",
        governance_root: governanceRoot,
        governance_root_exists: existsSync(governanceRoot),
      };

      // Check governance subdirectories
      const requiredDirs = [
        "governance/prompts/reviews",
        "governance/policy",
        "governance/schemas",
        "governance/personas/agentic",
      ];
      const dirChecks: Record<string, boolean> = {};
      for (const dir of requiredDirs) {
        const fullPath = join(governanceRoot, dir);
        dirChecks[dir] = existsSync(fullPath);
      }
      health.directories = dirChecks;

      // Check Python
      const pythonResult = await spawnPython(["--version"], governanceRoot);
      health.python_available = pythonResult.ok;
      health.python_version = pythonResult.ok ? pythonResult.stdout.trim() : null;

      // Check policy engine
      const policyEnginePath = join(governanceRoot, "governance", "bin", "policy-engine.py");
      health.policy_engine_available = existsSync(policyEnginePath);

      // Check schema
      const schemaPath = join(governanceRoot, "governance", "schemas", "panel-output.schema.json");
      health.panel_schema_available = existsSync(schemaPath);

      return {
        content: [
          { type: "text" as const, text: JSON.stringify(health, null, 2) },
        ],
      };
    }
  );


  // --- Skill auto-discovery and registration ---
  const skillsDir = getDefaultSkillsDir();
  const skills = await discoverSkills(skillsDir);

  for (const skill of skills) {
    const def = generateToolDefinition(skill);
    server.tool(
      def.name,
      def.description,
      def.inputSchema,
      async (args) => {
        const output = handleSkillToolCall(skill, args);
        return {
          content: [
            {
              type: "text" as const,
              text: output,
            },
          ],
        };
      }
    );
  }

  if (skills.length > 0) {
    console.error(
      `[dark-forge-mcp] Registered ${skills.length} skill(s): ${skills.map((s) => s.toolName).join(", ")}`
    );
  }

  return skills.length;
}

/**
 * Basic JSON Schema validation (subset of draft 2020-12).
 * Validates required fields, types, enums, min/max, pattern, and arrays.
 *
 * Supported features: type, required, properties, additionalProperties,
 * pattern, enum, minimum, maximum, minItems, items, union types (["string", "null"]).
 *
 * NOT supported: $ref, anyOf, oneOf, allOf, if/then/else, dependentRequired,
 * patternProperties, unevaluatedProperties, format, const, prefixItems.
 *
 * This intentional subset avoids a full JSON Schema library dependency (e.g., ajv)
 * while covering the fields actually used in panel-output.schema.json. If the schema
 * evolves to use unsupported features, upgrade to ajv or a comparable library.
 */
function validateAgainstSchema(
  data: unknown,
  schema: Record<string, unknown>,
  path = ""
): string[] {
  const errors: string[] = [];

  if (schema.type === "object" && typeof data === "object" && data !== null) {
    const obj = data as Record<string, unknown>;
    const properties = (schema.properties || {}) as Record<
      string,
      Record<string, unknown>
    >;
    const required = (schema.required || []) as string[];

    // Check required fields
    for (const field of required) {
      if (!(field in obj)) {
        errors.push(`${path ? path + "." : ""}${field}: required field missing`);
      }
    }

    // Validate each property
    for (const [key, value] of Object.entries(obj)) {
      if (properties[key]) {
        errors.push(
          ...validateAgainstSchema(
            value,
            properties[key],
            path ? `${path}.${key}` : key
          )
        );
      } else if (schema.additionalProperties === false) {
        errors.push(
          `${path ? path + "." : ""}${key}: additional property not allowed`
        );
      }
    }
  } else if (schema.type === "string") {
    if (typeof data !== "string") {
      errors.push(`${path}: expected string, got ${typeof data}`);
    } else {
      if (schema.pattern) {
        const re = new RegExp(schema.pattern as string);
        if (!re.test(data)) {
          errors.push(`${path}: does not match pattern ${schema.pattern}`);
        }
      }
      if (schema.enum && !(schema.enum as string[]).includes(data)) {
        errors.push(
          `${path}: value "${data}" not in enum [${(schema.enum as string[]).join(", ")}]`
        );
      }
    }
  } else if (schema.type === "number" || schema.type === "integer") {
    if (typeof data !== "number") {
      errors.push(`${path}: expected number, got ${typeof data}`);
    } else {
      if (schema.minimum !== undefined && data < (schema.minimum as number)) {
        errors.push(`${path}: ${data} is less than minimum ${schema.minimum}`);
      }
      if (schema.maximum !== undefined && data > (schema.maximum as number)) {
        errors.push(`${path}: ${data} is greater than maximum ${schema.maximum}`);
      }
    }
  } else if (schema.type === "boolean") {
    if (typeof data !== "boolean") {
      errors.push(`${path}: expected boolean, got ${typeof data}`);
    }
  } else if (schema.type === "array") {
    if (!Array.isArray(data)) {
      errors.push(`${path}: expected array, got ${typeof data}`);
    } else {
      if (
        schema.minItems !== undefined &&
        data.length < (schema.minItems as number)
      ) {
        errors.push(
          `${path}: array has ${data.length} items, minimum is ${schema.minItems}`
        );
      }
      if (schema.items) {
        for (let i = 0; i < data.length; i++) {
          errors.push(
            ...validateAgainstSchema(
              data[i],
              schema.items as Record<string, unknown>,
              `${path}[${i}]`
            )
          );
        }
      }
    }
  } else if (schema.type && typeof data !== schema.type) {
    // Handle union types like ["string", "null"]
    if (Array.isArray(schema.type)) {
      const types = schema.type as string[];
      const actualType = data === null ? "null" : typeof data;
      if (!types.includes(actualType)) {
        errors.push(
          `${path}: expected one of [${types.join(", ")}], got ${actualType}`
        );
      }
    } else {
      errors.push(`${path}: expected ${schema.type}, got ${typeof data}`);
    }
  }

  return errors;
}
