import { join } from "node:path";
import { existsSync, statSync } from "node:fs";
import { z } from "zod";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { readTextFile, spawnPython } from "./utils.js";
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
      `[ai-submodule-mcp] Registered ${skills.length} skill(s): ${skills.map((s) => s.toolName).join(", ")}`
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
