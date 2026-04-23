# Testing Guide

The Documentor test suite ensures the reliability of the CLI, core configuration logic, and LLM integrations. We use `pytest` as our primary testing framework, along with `pytest-mock` and `pytest-asyncio` for advanced scenarios. Dependencies are managed using `uv` for fast, reproducible environments.

## Local Environment Setup

To run the tests locally, you need to install the project and its development dependencies. We recommend using `uv` for lightning-fast package installation.

1. **Install `uv`** (if you haven't already):
   ```bash
   pip install uv
   ```

2. **Install Development Dependencies**:
   From the project root, install the package in editable mode with the `dev` extras:
   ```bash
   uv pip install -e ".[dev]"
   ```
   *(Note: This installs `pytest`, `pytest-cov`, `pytest-asyncio`, and `pytest-mock` alongside standard dependencies.)*

## Running Tests

Execute the full test suite using `pytest` from the root directory:

```bash
pytest tests/
```

**Helpful `pytest` Flags:**
* `-v`: Verbose output.
* `-s`: Print standard output (useful for debugging).
* `--cov=src/documentor`: Run tests with coverage reporting.

## Test Structure

The `tests/` directory is organized to mirror the core components of the project:

* **`test_agent.py`**: Tests Agent Mode behavior, codebase exploration tools (e.g., list, read, grep), and dynamic document generation and syncing logic.
* **`test_cli.py`**: Validates Typer CLI commands, options, and user prompts.
* **`test_core.py`**: Covers internal business logic, including configuration management, state tracking, and file parsing.
* **`test_utils.py`**: Ensures helper functions and formatting utilities work correctly.

## CI/CD Pipeline

Documentor uses GitHub Actions to automate testing on every push and pull request to the `main` branch. 

Our workflow (`.github/workflows/test.yml`):
* Runs on `ubuntu-latest`.
* Uses a matrix strategy to test across Python versions `3.10`, `3.11`, and `3.12`.
* Leverages `astral-sh/setup-uv` to rapidly install the project and its development dependencies.
* Executes the `pytest tests/` suite to ensure cross-version compatibility.

Always review the CI status on your pull requests to ensure all checks pass before merging.

> *Docs generated with [documentor](https://github.com/YusufHosny/documentor)*
