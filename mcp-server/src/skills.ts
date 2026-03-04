import { readdir } from "node:fs/promises";
import { join, dirname, resolve } from "node:path";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { z } from "zod";
import { readTextFile, parseMarkdownWithFrontmatter } from "./utils.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Zod schema for skill YAML frontmatter.
 *
 * - name: kebab-case identifier, max 64 chars
 * - description: human-readable, max 1024 chars
 * - license: optional SPDX identifier
 * - allowed-tools: optional list of tools the skill may use
 * - metadata: optional arbitrary key-value pairs
 */
export const SkillMetadataSchema = z.object({
  name: z
    .string()
    .regex(/^[a-z][a-z0-9-]*$/, "Name must be lowercase kebab-case starting with a letter")
    .max(64),
  description: z.string().max(1024),
  license: z.string().optional(),
  "allowed-tools": z.array(z.string()).optional(),
  metadata: z.record(z.unknown()).optional(),
});

export type SkillMetadata = z.infer<typeof SkillMetadataSchema>;

export interface LoadedSkill {
  metadata: SkillMetadata;
  instructions: string;
  path: string;
  toolName: string;
}

/**
 * Zod schema for skill tool invocation input.
 */
export const SkillInputSchema = {
  task: z.string().describe("What to accomplish with this skill"),
  context: z.string().optional().describe("Additional context"),
  output_format: z
    .enum(["code", "explanation", "both"])
    .optional()
    .describe("Desired output format"),
};

/**
 * Load and validate a single .skill.md file.
 *
 * Parses YAML frontmatter via gray-matter, validates against SkillMetadataSchema,
 * and derives the MCP tool name from the skill name (hyphens -> underscores).
 */
export async function loadSkill(filePath: string): Promise<LoadedSkill> {
  const content = await readTextFile(filePath);
  const { data, content: instructions } = parseMarkdownWithFrontmatter(content);
  const metadata = SkillMetadataSchema.parse(data);
  const toolName = `skill_${metadata.name.replace(/-/g, "_")}`;
  return { metadata, instructions: instructions.trim(), path: filePath, toolName };
}

/**
 * Scan a directory for *.skill.md files and load each one.
 *
 * Files that fail validation are logged to stderr and skipped.
 * Returns an array of successfully loaded skills, sorted by name.
 */
export async function discoverSkills(skillsDir: string): Promise<LoadedSkill[]> {
  const skills: LoadedSkill[] = [];

  let entries;
  try {
    entries = await readdir(skillsDir, { withFileTypes: true });
  } catch {
    // Directory does not exist or is not readable — not an error
    return skills;
  }

  for (const entry of entries) {
    if (!entry.isFile() || !entry.name.endsWith(".skill.md")) {
      continue;
    }

    const filePath = join(skillsDir, entry.name);
    try {
      const skill = await loadSkill(filePath);
      skills.push(skill);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error(
        `[dark-forge-mcp] Warning: skipping invalid skill file ${entry.name}: ${message}`
      );
    }
  }

  return skills.sort((a, b) => a.metadata.name.localeCompare(b.metadata.name));
}

/**
 * Resolve the default skills directory.
 *
 * When running from dist/, looks for ../skills/ relative to the dist directory.
 * When running from src/, looks for ../../skills/ (the mcp-server/skills/ directory).
 * Falls back to the first path that exists.
 */
export function getDefaultSkillsDir(): string {
  // From dist/skills.js -> ../skills/
  const fromDist = resolve(__dirname, "..", "skills");
  if (existsSync(fromDist)) {
    return fromDist;
  }

  // From src/skills.ts -> ../../skills/ (mcp-server/skills/)
  const fromSrc = resolve(__dirname, "..", "..", "skills");
  if (existsSync(fromSrc)) {
    return fromSrc;
  }

  // Default to the dist-relative path even if it doesn't exist yet
  return fromDist;
}

/**
 * Generate an MCP tool definition object for a loaded skill.
 *
 * Returns the shape expected by McpServer.tool() registration:
 * { name, description, inputSchema, handler }.
 */
export function generateToolDefinition(skill: LoadedSkill): {
  name: string;
  description: string;
  inputSchema: typeof SkillInputSchema;
} {
  const allowedTools = skill.metadata["allowed-tools"];
  const toolsNote = allowedTools
    ? `\nAllowed tools: ${allowedTools.join(", ")}`
    : "";

  return {
    name: skill.toolName,
    description: `${skill.metadata.description}${toolsNote}`,
    inputSchema: SkillInputSchema,
  };
}

/**
 * Handle a skill tool invocation.
 *
 * Concatenates the skill's instructions with the user's task and optional context
 * to produce the output text that an AI agent would follow.
 */
export function handleSkillToolCall(
  skill: LoadedSkill,
  args: { task: string; context?: string; output_format?: string }
): string {
  const parts: string[] = [];

  parts.push("# Skill Instructions\n");
  parts.push(skill.instructions);
  parts.push("\n\n# Task\n");
  parts.push(args.task);

  if (args.context) {
    parts.push("\n\n# Additional Context\n");
    parts.push(args.context);
  }

  if (args.output_format) {
    parts.push(`\n\n# Output Format\nProvide output as: ${args.output_format}`);
  }

  return parts.join("");
}
