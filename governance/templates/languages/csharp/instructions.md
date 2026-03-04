# C# / .NET Instructions

Extends the base AI instructions with .NET-specific conventions.

## Naming

- PascalCase for all public members, namespaces, types, methods, properties, events, constants
- `_camelCase` for private fields (single underscore prefix)
- camelCase for parameters and local variables
- `I` prefix for interfaces (`IRepository`), `T` prefix for type parameters (`TEntity`)
- Two-letter acronyms are UPPERCASE (`IO`, `UI`); three+ are PascalCase (`Xml`, `Http`)
- Suffix async methods with `Async`; prefix booleans with `Is`, `Has`, `Can`, `Should`
- File names match the primary type name

## Code Style

- Enable nullable reference types everywhere; treat warnings as errors
- Use file-scoped namespaces
- Use primary constructors for DI and records for DTOs/value objects
- Use `sealed` on classes not designed for inheritance
- Prefer `using` declarations over `using` blocks
- Use pattern matching: `is null`, `is not null`, switch expressions
- Use collection expressions (C# 12): `int[] numbers = [1, 2, 3];`
- Use target-typed `new()` when the type is obvious

## Async/Await

- Always use `async`/`await` -- never `.Result`, `.Wait()`, or `.GetAwaiter().GetResult()`
- Accept `CancellationToken` in all async method signatures and propagate it
- Return `Task`/`Task<T>`, never `async void` (except event handlers)
- Use `ValueTask<T>` for hot paths that often complete synchronously
- Use `Task.WhenAll` for independent parallel operations
- Use `ConfigureAwait(false)` only in library code, not in ASP.NET Core app code

## Error Handling

- Prefer the Result pattern (`ErrorOr`, `FluentResults`) over exceptions for expected failures
- Use exceptions only for truly exceptional situations
- Return `ProblemDetails` (RFC 9457) from API error responses
- Create domain-specific exception hierarchies inheriting from `Exception`
- Handle exceptions at the boundary with `UseExceptionHandler` middleware
- Use exception filters: `catch (HttpRequestException ex) when (ex.StatusCode == ...)`

## Dependency Injection

- Register by interface: `services.AddScoped<IRepo, Repo>()`
- Use extension methods for clean service registration per layer
- Avoid Service Locator pattern (resolving directly from `IServiceProvider`)
- Watch for captive dependencies (scoped into singleton)
- More than 5 constructor parameters signals an SRP violation

## Testing

- xUnit with FluentAssertions and NSubstitute
- AAA pattern: Arrange, Act, Assert
- Name tests: `MethodName_Scenario_ExpectedBehavior`
- Use `WebApplicationFactory<Program>` for integration tests
- Use Testcontainers for database integration tests
- Use Bogus for test data generation

## LINQ & EF Core

- Materialize queries with `.ToListAsync()` before returning
- Never iterate an `IQueryable` multiple times
- Return `IReadOnlyList<T>` from repositories, not `IEnumerable<T>` or `IQueryable<T>`

## Tooling

- `dotnet format` for code formatting, enforced via `.editorconfig`
- `Directory.Build.props` with `TreatWarningsAsErrors`, `AnalysisLevel=latest-recommended`
- `Directory.Packages.props` for central package management
- `global.json` to pin SDK version

---

*Extends .ai/instructions.md with C#-specific conventions.*
