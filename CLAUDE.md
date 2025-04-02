# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Run: `python main.py --user-id YOUR_PHONE_NUMBER [--transport {sse|stdio}]`
- Lint: `ruff check .`
- Type check: `mypy .`
- Format code: `ruff format .`

## Code Style Guidelines
- **Imports**: Standard library first, then third-party, then local. Group imports by type.
- **Formatting**: Use ruff formatter (Black-compatible).
- **Types**: Use strict type annotations. Define custom types for complex structures.
- **Naming**:
  - Functions/variables: snake_case
  - Classes: PascalCase
  - Constants: UPPER_CASE
- **Error Handling**: Use custom exception classes. Log errors before raising or returning.
- **Logging**: Use the established logger pattern with appropriate log levels.
- **Async**: Use asyncio for all I/O operations.
- **Security**: Always use shlex.quote for shell command arguments.