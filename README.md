# Documentor CLI

A CLI tool for automatic documentation generation and management, powered by AI.

## Features

- **Init**: Scans your project and generates an initial documentation suite end-to-end.
- **Generate**: On-demand documentation generation based on your configuration.
- **Edit**: Iterates on an existing markdown document using AI based on your comments.
- **Expand**: Turns scrappy bullet points into a coherent, well-formatted document.

## Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.

```bash
# Clone the repository
git clone <repository_url>
cd documentor

# Install dependencies
poetry install

# Run the CLI
poetry run documentor --help
```

## Usage

### Initialize a project
```bash
documentor init
```

### Generate documentation
```bash
documentor generate
documentor generate --target docs/architecture.md
```

### Edit existing documentation
```bash
documentor edit docs/functional_spec.md --comments "Add a section about the new authentication flow."
```

### Expand scrappy notes
```bash
documentor expand notes.txt --type "decision"
```

## Configuration

`documentor init` creates a `documentor.yaml` file in your project root. You can configure:
- `provider`: AI provider (e.g., anthropic, openai, ollama)
- `model`: Specific model to use (e.g., claude-3-5-sonnet-20241022)
- `ignore_patterns`: Files and directories to ignore during project scanning
- `docs_dir`: Output directory for generated documentation
- `include_footer`: Boolean to append a footer to generated docs
