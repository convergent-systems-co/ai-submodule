import { join, basename } from "node:path";
import { readdir } from "node:fs/promises";
import { z } from "zod";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import {
  readTextFile,
  parseMarkdownWithFrontmatter,
  scanMarkdownFiles,
  extractTitle,
  pathToSlug,
} from "./utils.js";

/**
 * Register all MCP prompts with the server.
 */
export function registerPrompts(
  server: McpServer,
  governanceRoot: string
): void {
  // Prompt: governance_review — generic panel runner with panel_name param
  server.prompt(
    "governance_review",
    "Run a governance review panel against code changes",
    {
      panel_name: z.string().describe(
        "Name of the review panel (e.g., code-review, security-review, threat-modeling)"
      ),
    },
    async ({ panel_name }) => {
      const reviewPath = join(
        governanceRoot,
        "governance",
        "prompts",
        "reviews",
        `${panel_name}.md`
      );

      try {
        const content = await readTextFile(reviewPath);
        return {
          messages: [
            {
              role: "user" as const,
              content: {
                type: "text" as const,
                text: content,
              },
            },
          ],
        };
      } catch {
        return {
          messages: [
            {
              role: "user" as const,
              content: {
                type: "text" as const,
                text: `Error: Review panel "${panel_name}" not found. Use list_panels tool to see available panels.`,
              },
            },
          ],
        };
      }
    }
  );

  // Prompt: plan_create
  server.prompt(
    "plan_create",
    "Create an implementation plan using the governance plan template",
    async () => {
      const templatePath = join(
        governanceRoot,
        "governance",
        "prompts",
        "templates",
        "plan-template.md"
      );

      try {
        const content = await readTextFile(templatePath);
        return {
          messages: [
            {
              role: "user" as const,
              content: {
                type: "text" as const,
                text: `Use this template to create an implementation plan:\n\n${content}`,
              },
            },
          ],
        };
      } catch {
        return {
          messages: [
            {
              role: "user" as const,
              content: {
                type: "text" as const,
                text: "Error: Plan template not found at governance/templates/prompts/plan-template.md",
              },
            },
          ],
        };
      }
    }
  );

  // Prompt: threat_model
  server.prompt(
    "threat_model",
    "Perform threat modeling analysis on code changes",
    async () => {
      const threatPath = join(
        governanceRoot,
        "governance",
        "prompts",
        "reviews",
        "threat-modeling.md"
      );

      try {
        const content = await readTextFile(threatPath);
        return {
          messages: [
            {
              role: "user" as const,
              content: {
                type: "text" as const,
                text: content,
              },
            },
          ],
        };
      } catch {
        return {
          messages: [
            {
              role: "user" as const,
              content: {
                type: "text" as const,
                text: "Error: Threat modeling prompt not found at governance/prompts/reviews/threat-modeling.md",
              },
            },
          ],
        };
      }
    }
  );

  // Prompt: assume_persona — activate a persona for the session
  server.prompt(
    "assume_persona",
    "Assume an agentic persona for the current session",
    {
      persona: z.string().describe(
        "Persona name (e.g., coder, tester, devops-engineer, tech-lead, iac-engineer, project-manager)"
      ),
    },
    async ({ persona }) => {
      const personaPath = join(
        governanceRoot,
        "governance",
        "personas",
        "agentic",
        `${persona}.md`
      );

      try {
        const content = await readTextFile(personaPath);
        return {
          messages: [
            {
              role: "user" as const,
              content: {
                type: "text" as const,
                text: `You are now operating as the following persona. Read and adopt these instructions:\n\n${content}`,
              },
            },
          ],
        };
      } catch {
        return {
          messages: [
            {
              role: "user" as const,
              content: {
                type: "text" as const,
                text: `Error: Persona "${persona}" not found. Available personas: coder, tester, devops-engineer, tech-lead, iac-engineer, project-manager`,
              },
            },
          ],
        };
      }
    }
  );
}

/**
 * Recursively scan a directory for *.prompt.md files.
 */
async function scanPromptFiles(dir: string): Promise<string[]> {
  const results: string[] = [];

  async function walk(d: string): Promise<void> {
    let entries;
    try {
      entries = await readdir(d, { withFileTypes: true });
    } catch {
      return;
    }

    for (const entry of entries) {
      const fullPath = join(d, entry.name);
      if (entry.isDirectory()) {
        await walk(fullPath);
      } else if (entry.isFile() && entry.name.endsWith(".prompt.md")) {
        results.push(fullPath);
      }
    }
  }

  await walk(dir);
  return results.sort();
}

/**
 * Discover and register all review panels as individual MCP prompts.
 * Each panel becomes a named prompt like "review_security_review", "review_code_review", etc.
 */
export async function discoverAndRegisterReviewPrompts(
  server: McpServer,
  governanceRoot: string
): Promise<number> {
  const reviewsDir = join(governanceRoot, "governance", "prompts", "reviews");
  const files = await scanMarkdownFiles(reviewsDir);
  let registered = 0;

  for (const filePath of files) {
    try {
      const slug = pathToSlug(basename(filePath));
      const content = await readTextFile(filePath);
      const title = extractTitle(content, basename(filePath));

      // Register as "review_{slug}" prompt (e.g., "review_security-review")
      const promptName = `review_${slug}`;

      server.prompt(
        promptName,
        `Run the ${title} panel`,
        async () => ({
          messages: [
            {
              role: "user" as const,
              content: {
                type: "text" as const,
                text: content,
              },
            },
          ],
        })
      );

      registered++;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error(
        `[dark-forge-mcp] Failed to register review prompt from ${filePath}: ${message}`
      );
    }
  }

  return registered;
}

/**
 * Discover and register persona definitions as MCP prompts.
 * Each persona becomes a named prompt like "persona_coder", "persona_tester", etc.
 */
export async function discoverAndRegisterPersonaPrompts(
  server: McpServer,
  governanceRoot: string
): Promise<number> {
  const personasDir = join(governanceRoot, "governance", "personas", "agentic");
  const files = await scanMarkdownFiles(personasDir);
  let registered = 0;

  for (const filePath of files) {
    try {
      const slug = pathToSlug(basename(filePath));
      const content = await readTextFile(filePath);
      const title = extractTitle(content, basename(filePath));

      const promptName = `persona_${slug}`;

      server.prompt(
        promptName,
        `Assume the ${title} persona`,
        async () => ({
          messages: [
            {
              role: "user" as const,
              content: {
                type: "text" as const,
                text: `You are now operating as the following persona. Read and adopt these instructions:\n\n${content}`,
              },
            },
          ],
        })
      );

      registered++;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error(
        `[dark-forge-mcp] Failed to register persona prompt from ${filePath}: ${message}`
      );
    }
  }

  return registered;
}

/**
 * Discover *.prompt.md files under prompts/ and register each as an MCP prompt.
 *
 * Each file must have YAML frontmatter with at least `name` and `description`.
 * The prompt handler returns the full markdown content (after frontmatter).
 */
export async function discoverAndRegisterPrompts(
  server: McpServer,
  governanceRoot: string
): Promise<number> {
  const promptsDir = join(governanceRoot, "prompts");
  const files = await scanPromptFiles(promptsDir);
  let registered = 0;

  for (const filePath of files) {
    try {
      const raw = await readTextFile(filePath);
      const { data, content } = parseMarkdownWithFrontmatter(raw);

      const name = data.name as string | undefined;
      const description = data.description as string | undefined;

      if (!name) {
        console.error(
          `[dark-forge-mcp] Skipping prompt file (missing 'name' in frontmatter): ${filePath}`
        );
        continue;
      }

      server.prompt(
        name,
        description ?? "",
        async () => ({
          messages: [
            {
              role: "user" as const,
              content: {
                type: "text" as const,
                text: content.trim(),
              },
            },
          ],
        })
      );

      registered++;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error(
        `[dark-forge-mcp] Failed to register prompt from ${filePath}: ${message}`
      );
    }
  }

  return registered;
}
