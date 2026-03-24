# Documentor

Documentor is an AI-powered CLI tool that automatically generates, manages, and synchronizes your project's documentation. By analyzing your codebase context, it plans a tailored documentation suite and ensures your markdown files stay up to date as your source code evolves.

## Features

* **Smart Planning**: AI analyzes your project to suggest required documentation files.
* **Automatic Generation**: Creates comprehensive markdown documentation directly from your codebase.
* **State Synchronization**: Keeps existing documentation up to date with code changes using Git diffs.
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

The quickest way to get value out of Documentor is to initialize it, let it plan your docs, and then generate them.

```bash
# 1. Initialize the configuration interactively
documentor init

# 2. Analyze the project and generate a documentation plan
documentor plan

# 3. Generate all missing or outdated documentation
documentor generate
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

## Documentation

For a deeper dive into Documentor's capabilities, check out the following guides:

* **[CLI Usage Guide](docs/usage.md)**: Detailed descriptions of all CLI commands, options, and advanced usage examples (like `edit` and `expand`).
* **[Configuration Reference](docs/config.md)**: A complete reference for the `documentor.yaml` file, including all available settings, tracking options, and LLM configuration.
* **[Style Customization](docs/style.md)**: Instructions on how to use `style.md` and built-in templates to control the formatting and tone of your generated documentation.

> *Docs generated with [documentor](https://github.com/YusufHosny/documentor)*