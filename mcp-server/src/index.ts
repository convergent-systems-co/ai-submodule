#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { resolveGovernanceRoot } from "./utils.js";
import { registerResources } from "./resources.js";
import { registerTools } from "./tools.js";
import { registerPrompts } from "./prompts.js";

/**
 * Parse CLI arguments.
 */
function parseArgs(argv: string[]): { governanceRoot?: string } {
  const args: { governanceRoot?: string } = {};

  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === "--governance-root" && argv[i + 1]) {
      args.governanceRoot = argv[i + 1];
      i++;
    }
  }

  return args;
}

/**
 * Route CLI subcommands before starting the MCP server.
 * Returns true if a subcommand was handled (caller should exit).
 */
async function routeSubcommand(argv: string[]): Promise<boolean> {
  const subcommand = argv[2];

  if (subcommand === "install") {
    const { runInstaller } = await import("./install.js");
    await runInstaller(argv);
    return true;
  }

  return false;
}

/**
 * Main entry point for the MCP server.
 */
async function main(): Promise<void> {
  // Check for subcommands before starting the server
  const handled = await routeSubcommand(process.argv);
  if (handled) return;

  const args = parseArgs(process.argv);

  let governanceRoot: string;
  try {
    governanceRoot = resolveGovernanceRoot(args.governanceRoot);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error(`Error: ${message}`);
    process.exit(1);
  }

  const server = new McpServer(
    {
      name: "ai-submodule-mcp",
      version: "0.1.0",
    },
    {
      capabilities: {
        resources: {},
        tools: {},
        prompts: {},
      },
    }
  );

  // Register all components
  const discovered = await registerResources(server, governanceRoot);
  registerTools(server, governanceRoot);
  registerPrompts(server, governanceRoot);

  // Log to stderr (stdout is reserved for MCP protocol)
  console.error(
    `[ai-submodule-mcp] Governance root: ${governanceRoot}`
  );
  console.error(
    `[ai-submodule-mcp] Serving ${discovered.length} resources`
  );

  // Connect via STDIO transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error("[ai-submodule-mcp] Server started on stdio");

  // Graceful shutdown
  const shutdown = async () => {
    console.error("[ai-submodule-mcp] Shutting down...");
    await server.close();
    process.exit(0);
  };

  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
