# Node.js / TypeScript Instructions

Extends the base AI instructions with Node.js/TypeScript-specific conventions.

## TypeScript

- Enable `strict: true` in tsconfig; also enable `noUncheckedIndexedAccess`
- Use `X | Y` union types, `X | null` over `Optional<X>`
- Avoid enums -- use `as const` objects with derived types
- Use discriminated unions for state modeling
- Use `satisfies` operator to validate values while preserving inferred types
- Use `import type` for type-only imports
- Avoid `any` -- use `unknown` for truly unknown types
- Prefer `interface` for object shapes (extensible), `type` for unions/intersections

## Code Style

- ESM by default: `"type": "module"` in `package.json`
- Use `node:` protocol prefix for built-in modules: `import fs from "node:fs"`
- ESLint 9 flat config (`eslint.config.mjs`) with `typescript-eslint`
- Prettier for formatting; disable ESLint formatting rules with `eslint-config-prettier`
- Import order: node built-ins, external packages, internal aliases, relative imports
- Use path aliases (`@/`) mapped in tsconfig to avoid deep relative imports

## Project Structure

- Feature-based folders: `src/features/{feature}/` with co-located controller, service, types, tests
- Barrel exports (`index.ts`) only at feature boundaries -- one per feature, not nested
- Shared code in `src/shared/` (utils, middleware, types)
- Separate `tsconfig.build.json` that excludes tests

## Error Handling

- Custom error classes with `statusCode`, `code`, and `isOperational` flag
- Centralized error handler middleware -- don't try/catch in every route
- Operational errors (bad input, not found) handled gracefully; programmer errors crash and restart
- Always handle `unhandledRejection` and `uncaughtException`
- Never swallow errors silently -- every `catch` must handle, rethrow, or log

## Async Patterns

- `async`/`await` everywhere -- no raw callbacks, minimal `.then()` chains
- `Promise.all` for independent parallel operations
- `Promise.allSettled` when partial failure is acceptable
- Use `p-limit` or similar for bounded concurrency against external services
- Never block the event loop -- offload CPU-intensive work to worker threads
- Use `AsyncLocalStorage` for request-scoped context (request IDs, user context)

## Validation & Security

- Zod for runtime validation + TypeScript type inference from a single schema
- Validate environment variables at startup (fail fast)
- `helmet` for security headers, explicit CORS configuration
- Never commit `.env` files; use `.env.example` as documentation
- Run `pnpm audit` in CI for dependency vulnerability scanning

## Testing

- Vitest with `describe`/`it` blocks; test names read as sentences
- Co-locate tests: `feature.test.ts` next to `feature.ts`
- Prefer dependency injection over `vi.mock()` / `jest.mock()`
- Use MSW (Mock Service Worker) for HTTP API mocking
- Use Testcontainers for integration tests with real databases
- Separate unit (`*.test.ts`) from integration (`*.integration.test.ts`) tests

## Common Pitfalls

- Event loop blocking: no sync file/crypto APIs in request handlers
- Memory leaks: unbounded caches, leaked event listeners, closures holding large objects
- Circular dependencies: use `import type`, `madge` for detection, extract shared logic
- Use `lru-cache` for bounded in-memory caching

## Package Management

- pnpm preferred; commit lockfile; use `--frozen-lockfile` in CI
- Separate `dependencies` from `devDependencies` correctly
- Use `depcheck` to find unused dependencies
- Automate updates with Renovate or Dependabot

---

*Extends .ai/instructions.md with Node.js/TypeScript-specific conventions.*
