# Documentor

Documentor is a command-line interface (CLI) tool that automatically generates and manages your project's documentation using Large Language Models (LLMs). By analyzing your codebase context, it creates tailored markdown files and keeps them synchronized as your source code evolves, eliminating the need for manual documentation updates.

### Features
* **Interactive Setup:** Configure documentation targets, file ignore patterns, and LLM providers via a quick CLI wizard.
* **Smart Generation:** Automatically write comprehensive markdown documentation based on your source code and custom style guides.
* **State Tracking & Sync:** Detect code changes via Git and selectively update only the documentation that has become stale.
* **AI Editing & Expansion:** Refine existing docs using natural language prompts or expand rough bullet points into formal documentation.
* **Multi-Provider Support:** Seamlessly integrate with Google Vertex AI (default), OpenAI, and local Ollama models.

### Installation

Documentor requires Python 3.10 or higher. 

```bash
# Clone the repository
git clone https://github.com/YusufHosny/documentor.git
cd documentor

# Install the CLI tool
pip install .
```

*Note: You will need to set up the appropriate API keys for your chosen LLM provider (e.g., `OPENAI_API_KEY` or Google Cloud credentials) in your environment before generating documentation.*

### Usage

Here is the quickest way to get Documentor running in your project:

```bash
# 1. Initialize Documentor (Walks you through creating a configuration and style guide)
documentor init

# 2. Generate your initial documentation suite
documentor generate

# 3. Sync your docs to keep them updated after making code changes
documentor sync
```

### Documentation Overview

For more detailed information on maximizing Documentor's capabilities, please refer to the following documentation pages:

* **[CLI Usage Guide](usage.md)**: Detailed descriptions of the CLI API, including all commands (`init`, `plan`, `generate`, `sync`, `edit`, `expand`), options, and extended workflow examples.
* **[Configuration Reference](config.md)**: A detailed reference for all the options within the `documentor.yaml` configuration file, including their types, default values, and effects on documentation generation.

> *Docs generated with [documentor](https://github.com/YusufHosny/documentor)*