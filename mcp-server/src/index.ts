#!/usr/bin/env node

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { resolveGovernanceRoot } from "./utils.js";
import { registerResources } from "./resources.js";
import { registerTools } from "./tools.js";
import {
  registerPrompts,
  discoverAndRegisterPrompts,
  discoverAndRegisterReviewPrompts,
  discoverAndRegisterPersonaPrompts,
} from "./prompts.js";
import { ENV } from "./fetch.js";

/**
 * Parsed CLI arguments for the MCP server.
 */
export interface CliArgs {
  governanceRoot?: string;
  noCache?: boolean;
  refresh?: boolean;
  validateHash?: boolean;
  offline?: boolean;
}

/**
 * Parse CLI arguments.
 */
export function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = {};

  for (let i = 2; i < argv.length; i++) {
    if (argv[i] === "--governance-root" && argv[i + 1]) {
      args.governanceRoot = argv[i + 1];
      i++;
    } else if (argv[i] === "--no-cache") {
      args.noCache = true;
    } else if (argv[i] === "--refresh") {
      args.refresh = true;
    } else if (argv[i] === "--validate-hash") {
      args.validateHash = true;
    } else if (argv[i] === "--offline") {
      args.offline = true;
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

  // Apply fetch-related CLI flags to environment
  if (args.offline) {
    process.env[ENV.OFFLINE] = "1";
  }
  if (args.noCache) {
    // Set TTL to 0 to effectively disable caching
    process.env[ENV.CACHE_TTL] = "0";
  }

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
  const skillCount = await registerTools(server, governanceRoot);
  registerPrompts(server, governanceRoot);
  const discoveredPrompts = await discoverAndRegisterPrompts(
    server,
    governanceRoot
  );
  const reviewPrompts = await discoverAndRegisterReviewPrompts(
    server,
    governanceRoot
  );
  const personaPrompts = await discoverAndRegisterPersonaPrompts(
    server,
    governanceRoot
  );

  // Log to stderr (stdout is reserved for MCP protocol)
  console.error(
    `[ai-submodule-mcp] Governance root: ${governanceRoot}`
  );
  console.error(
    `[ai-submodule-mcp] Serving ${discovered.length} resources, ${skillCount} skill(s)`
  );
  console.error(
    `[ai-submodule-mcp] Discovered ${discoveredPrompts} prompt(s) from prompts/`
  );
  console.error(
    `[ai-submodule-mcp] Registered ${reviewPrompts} review panel prompt(s), ${personaPrompts} persona prompt(s)`
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
