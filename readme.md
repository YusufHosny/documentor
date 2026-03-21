# Documentor

Documentor is a CLI tool that automatically generates and manages your project's documentation using Large Language Models. It analyzes your codebase to create tailored markdown files and keeps them synchronized as your source code evolves, freeing you from manual documentation updates.

### Features
* **Interactive Setup:** Quickly configure documentation targets, required files (with custom descriptions), ignore patterns (automatically integrates with `.gitignore`), and LLM providers via a CLI wizard.
* **Smart Generation:** Automatically writes comprehensive markdown documentation based on your project's source code context and custom style guides.
* **State Tracking & Sync:** Detects code changes via Git (tracked locally via a `documentor-lock.yaml` file) and selectively updates only the documentation that has become stale, leveraging precise git diffs to ensure accurate and incremental AI updates.
* **AI Editing & Expansion:** Refine existing docs using natural language prompts or expand scrappy bullet points into formal documentation.
* **Multi-Provider Support:** Seamlessly works with Google Vertex AI (default: `gemini-3.1-pro-preview`), OpenAI, and local Ollama models.

### Installation

Documentor requires Python 3.10 or higher.

```bash
# Clone the repository
git clone https://github.com/YusufHosny/documentor.git
cd documentor

# Install the CLI tool
pip install .
```

*Note: You will also need to set up the appropriate API keys for your chosen LLM provider (e.g., `OPENAI_API_KEY` or Google Cloud credentials) in your environment before generating documentation.*

### Usage

Here is the quickest way to get Documentor running in your project:

```bash
# 1. Initialize Documentor (Walks you through creating a documentor.yaml config and style.md)
documentor init

# 2. Generate your initial documentation suite
documentor generate

# 3. After making changes to your code, sync the docs to keep them updated
documentor sync
```

**Additional Commands:**

You can also use Documentor to edit or expand specific files on the fly:

```bash
# Refine an existing document by providing feedback to the AI (prompts for comments)
documentor edit docs/API.md

# Expand rough notes into a fully formatted document (default type is "functional")
documentor expand docs/draft-notes.md --type "functional"
```

### Configuration Format

Documentor is configured via a `documentor.yaml` file located in the root of your project. This file defines how documentation is generated, which files are tracked, and the LLM settings used for generation. 

Here is a breakdown of the available configuration options, their types, and their effects:

* **`docs_dir`** *(string)*: The default directory where generated documentation will be saved (e.g., `docs/`). *Note: Documentor is smart enough to keep `README.md` files at the project root regardless of this setting.*
* **`provider`** *(string)*: The AI provider to use for documentation generation. Supported values are `vertexai`, `openai`, and `ollama`.
* **`model`** *(string)*: The specific model version to use (e.g., `gemini-3.1-pro-preview`, `gpt-4o`).
* **`ignore_patterns`** *(list of strings)*: A list of file paths or glob patterns to exclude from codebase analysis. This is automatically combined with your existing `.gitignore` rules.
* **`ignore_above_size_kb`** *(integer)*: Excludes files larger than this size (in kilobytes) from codebase analysis.
* **`use_git`** *(boolean)*: Whether to use Git tracking and diffs to detect code changes and perform incremental documentation updates.
* **`use_style_md`** *(boolean)*: Whether to use a style guide markdown file to shape the tone, formatting, and structure of the AI's output.
* **`style_md_path`** *(string)*: The path to the local style guide file (e.g., `style.md`), used if `use_style_md` is set to `true`.
* **`include_footer`** *(boolean)*: Whether to append a Documentor attribution footer to the generated markdown files.
* **`required_only`** *(boolean)*: If set to `true`, Documentor will only generate and manage the files explicitly defined in the `required_files` list.
* **`required_files`** *(list of objects)*: Defines specific documentation files that must be present and maintained by the tool. Each list item accepts the following keys:
  * **`filename`** *(string)*: The desired file name or path (e.g., `README.md` or `docs/API.md`).
  * **`type`** *(string)*: The category or format of the document (e.g., `overview`, `technical`, `functional`).
  * **`description`** *(string)*: Custom instructions or a specific prompt defining exactly what the generated file should cover.

**Example `documentor.yaml`:**

```yaml
docs_dir: "docs/"
provider: "vertexai"
model: "gemini-3.1-pro-preview"
ignore_patterns:
  - "tests/fixtures/**"
  - "*.tmp"
ignore_above_size_kb: 50
use_git: true
use_style_md: true
style_md_path: "style.md"
include_footer: true
required_only: false
required_files:
  - filename: "README.md"
    type: "overview"
    description: "High-level project overview, installation steps, and usage."
  - filename: "docs/architecture.md"
    type: "technical"
    description: "Detailed system design and architecture decisions."
```

> *Docs generated with [documentor](https://github.com/YusufHosny/documentor)*