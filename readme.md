# Documentor

Documentor is an AI-powered CLI tool that automatically generates, manages, and synchronizes your project's documentation. By analyzing your codebase context, it plans a tailored documentation suite and ensures your markdown files stay up to date as your source code evolves.

## Features

* **Smart Planning**: AI analyzes your project to suggest documentation files.
* **Parallel Execution**: Generates and synchronizes multiple documentation files concurrently for significantly faster performance.
* **Automatic Generation**: Creates comprehensive markdown documentation directly from your codebase.
* **State Synchronization**: Keeps existing documentation up to date with code changes using Git diffs and a lockfile.
* **AI-Assisted Editing**: Expand quick bullet points into well-formatted documents or edit existing files via natural language prompts.
* **Scalable Context**: Uses an intelligent Agent Mode to handle large codebases without hitting context limits.
* **Multiple LLM Providers**: Works out-of-the-box with Google Vertex AI, OpenAI, and local models via Ollama.

## Installation

Documentor requires Python 3.10 or higher. You can install it locally using `pip`:

```bash
git clone https://github.com/YusufHosny/documentor.git
cd documentor
pip install .
```

Ensure your chosen LLM provider's API keys are set in your environment variables (e.g., `OPENAI_API_KEY`, or your GCP credentials for Vertex AI). You can also use a `.env` file to manage these along with optional LangSmith tracing configurations.

## Usage

To quickly generate a README for your project without keeping any configuration files:

```bash
documentor add-readme --once
```

To set up Documentor for long-term documentation management:

```bash
# 1. Initialize the configuration interactively and plan your docs
documentor init

# 2. Generate all missing or outdated documentation
documentor generate
```

To automatically analyze your project and suggest documentation outside of initialization:

```bash
documentor plan
```

To add or remove a documentation file from Documentor's tracking:

```bash
documentor add docs/existing.md
documentor remove docs/existing.md
```

To update your documentation after changing your code, simply run:

```bash
documentor sync
```

To edit or expand a specific document using AI:

```bash
documentor edit docs/readme.md
documentor expand docs/draft-notes.md
```

To completely remove Documentor's configuration from your project:

```bash
documentor destroy
```

## Documentation

For a deeper dive into Documentor's capabilities, check out the following guides:

* **[CLI Usage Guide](docs/usage.md)**: Detailed descriptions of all CLI commands, options, and advanced usage examples (like `add`, `remove`, `edit`, and `expand`).
* **[Configuration Reference](docs/confdg.md)**: A complete reference for the `documentor.yaml` file, including all available settings, tracking options, and LLM configuration.
* **[Style Customization](docs/style.md)**: Instructions on how to use `style.md` and built-in templates to control the formatting and tone of your generated documentation.
* **[Testing Guide](docs/tests.md)**: Explains how to run the project's test suite, including details on test structure, what testing covers, and what tools are used (e.g., pytest, uv).

> *Docs generated with [documentor](https://github.com/YusufHosny/documentor)*
