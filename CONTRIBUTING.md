# Contributing to Bioicons MCP

Thank you for your interest in contributing to the Bioicons MCP Server! 🎉

This document outlines the process for contributing bug reports, feature requests, and code changes.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

---

## Getting Started

### Prerequisites

- Python ≥ 3.10
- [git](https://git-scm.com/)
- An MCP-compatible client for testing (optional but recommended)

### Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/bioicons-mcp/bioicons-mcp.git
cd bioicons-mcp

# 2. Create a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 3. Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

---

## Development Workflow

1. **Create a branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/issue-number
   ```

2. **Make your changes** following the [Code Standards](#code-standards) below.

3. **Run tests and linters** before committing:
   ```bash
   ruff check src/ tests/
   mypy src/
   pytest tests/ -v
   ```

4. **Commit** with a clear, descriptive message:
   ```bash
   git commit -m "Add support for XYZ license type"
   ```

5. **Push** and open a Pull Request.

---

## Code Standards

### Style

- We use [ruff](https://docs.astral.sh/ruff/) for linting and formatting.
- Line length: 120 characters.
- Target Python version: 3.10.

### Type Checking

- All code must pass [mypy](https://mypy-lang.org/) in strict mode.
- Use type hints for all function parameters and return values.

### Architecture

- `constants.py` — all static metadata (URLs, license info, category descriptions).
- `models.py` — typed data models.
- `client.py` — async HTTP client with caching.
- `server.py` — MCP server tools, prompts, and transport.

Keep these layers separated. Do not import `server.py` from `client.py` or `models.py`.

---

## Testing

All tests are in `tests/` and run without network access (they use in-memory mock data).

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=bioicons_mcp --cov-report=term-missing
```

### Test Guidelines

- Every new tool or feature must have corresponding tests.
- Test both success and failure paths.
- Use the `patched_client` fixture for tests that need icon data.
- Mock HTTP calls — never make real network requests in tests.

---

## Submitting Changes

### Pull Request Process

1. Ensure all tests pass: `pytest tests/ -v`
2. Ensure linters pass: `ruff check src/ tests/` and `mypy src/`
3. Update the README if you added a new feature.
4. Keep your PR focused — one feature or fix per PR.

### PR Template

When opening a PR, include:

- **Summary**: What does this PR do?
- **Motivation**: Why is this change needed?
- **Testing**: How was this tested?
- **Breaking changes**: Does this break existing functionality?

---

## Reporting Bugs

Use [GitHub Issues](https://github.com/bioicons-mcp/bioicons-mcp/issues) to report bugs.

Include:

1. **Description** of the bug
2. **Steps to reproduce**
3. **Expected vs actual behaviour**
4. **Environment**: Python version, OS, MCP client used
5. **Logs** (if applicable)

---

## Feature Requests

We welcome feature requests! Please open a GitHub Issue with:

1. **Use case**: What problem does this solve?
2. **Proposed solution**: How would you like it to work?
3. **Alternatives considered**

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

*This project is an independent community MCP adapter and is not officially affiliated with bioicons.com.*
