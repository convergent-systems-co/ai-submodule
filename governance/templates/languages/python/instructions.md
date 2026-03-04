# Python Instructions

Extends the base AI instructions with Python-specific conventions.

## Type Hints

- Use modern syntax: `list[int]`, `dict[str, Any]`, `X | None` (not `Optional[X]`)
- Use `from __future__ import annotations` on Python 3.9 for forward references
- Use `TypedDict` for structured dictionaries, `Protocol` for structural subtyping
- Python 3.12+: use type parameter syntax `def f[T](x: T) -> T:` and `type` aliases
- Use `@override` decorator for methods overriding a parent
- Enable mypy `strict` mode; avoid `Any` as an escape hatch

## Code Style

- `ruff` for all linting and formatting (replaces flake8, isort, black)
- Google or NumPy style docstrings -- be consistent project-wide
- Define `__all__` in `__init__.py` to control the public API
- Keep `__init__.py` minimal -- use explicit re-exports with redundant alias (`from .core import Thing as Thing`)
- Use `pre-commit` hooks for ruff and mypy

## Project Structure

- `src/` layout: `src/my_package/` with `pyproject.toml` at root
- `pyproject.toml` as single source of truth for metadata, dependencies, and tool config
- Include `py.typed` marker file for PEP 561 typed packages
- No `requirements.txt` as primary -- use lock files (`uv.lock`, `poetry.lock`)
- Use dependency groups in `pyproject.toml` for dev, test, docs

## Data Modeling

- `dataclass(frozen=True, slots=True)` for immutable value objects
- Pydantic `BaseModel` for external data validation (API input, config files)
- Pydantic `BaseSettings` with `SecretStr` for environment configuration
- Prefer dataclasses or Pydantic models over raw dicts for structured data

## Error Handling

- Custom exception hierarchy: `AppError -> (ValidationError, NotFoundError, ...)`
- Use exception chaining: `raise NewError("msg") from original_error`
- Use `add_note()` (Python 3.11+) to add context without wrapping
- EAFP (try/except) by default; LBYL (if-check) when failure is common and check is cheap
- Never catch bare `Exception` without re-raising
- Use `ExceptionGroup` and `except*` for concurrent error handling (Python 3.11+)

## Async

- `asyncio.run()` as the entry point; never nest event loops
- `asyncio.TaskGroup` (Python 3.11+) over `gather()` for structured concurrency
- `asyncio.timeout()` (Python 3.11+) for network operation timeouts
- Use `asyncio.to_thread()` for blocking I/O in async code
- Handle `asyncio.CancelledError` properly (it's a `BaseException` subclass)

## Testing

- pytest with plain `assert` statements (pytest rewrites for clear output)
- `@pytest.mark.parametrize` for data-driven tests with IDs
- Fixtures in `conftest.py`; scope appropriately (`session`, `module`, `function`)
- `pytest-asyncio` with `asyncio_mode = "auto"` for async tests
- `pytest-cov` with `--cov=src/my_package --cov-report=term-missing`
- Register custom markers in `pyproject.toml` (`slow`, `integration`)

## Common Pitfalls

- Never use mutable default arguments: `def f(items=None):` not `def f(items=[]):`
- Late binding closures in loops: use default argument `lambda x, i=i: ...`
- Break import cycles with local imports, `TYPE_CHECKING` guard, or restructuring
- `is` only for `None`, `True`, `False`, and singletons -- use `==` for value equality
- Use `"".join()` for string concatenation in loops, not `+=`
- Never use `pickle` with untrusted data -- prefer JSON/msgpack
- Use `secrets` module for security-sensitive randomness, not `random`

## Dependency Management

- `uv` for fast dependency resolution and virtual environment management
- Always use virtual environments
- Commit lock files for applications; use loose bounds for libraries
- `pip-audit` for vulnerability scanning in CI

---

*Extends .ai/instructions.md with Python-specific conventions.*
