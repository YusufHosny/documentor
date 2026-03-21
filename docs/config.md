# Documentor Configuration Reference

Documentor uses a `documentor.yaml` file located in the root of your project to control how documentation is generated, formatted, and tracked. You can generate this file interactively using the `documentor init` command, update it automatically using `documentor plan`, or create and modify it manually.

Below is a detailed reference of all available options in `documentor.yaml`.

---

## Configuration Options

### LLM Settings

Configure the AI provider and model used to analyze your code and generate documentation.

* **`provider`**
  * **Type:** String
  * **Default:** `"vertexai"`
  * **Allowed Values:** `"vertexai"`, `"openai"`, `"ollama"`
  * **Description:** The LLM provider used for documentation generation.
* **`model`**
  * **Type:** String
  * **Default:** `"gemini-3.1-pro-preview"`
  * **Description:** The specific model name to use (e.g., `gpt-4o`, `llama3`).

### Output Settings

Control where and how the generated markdown files are saved.

* **`docs_dir`**
  * **Type:** String
  * **Default:** `"docs"`
  * **Description:** The output directory where generated documentation is saved. *Note: Documentor always places `docs/readme.md` files in the project root, regardless of this setting.*
* **`include_footer`**
  * **Type:** Boolean
  * **Default:** `false`
  * **Description:** Appends a short attribution footer (`> *Docs generated with documentor*`) to the bottom of all generated markdown files.

### Styling and Formatting

Define the formatting rules and style instructions for your documentation.

* **`use_style_md`**
  * **Type:** Boolean
  * **Default:** `false`
  * **Description:** When enabled, Documentor reads a custom markdown file to understand your formatting instructions and style guidelines.
* **`style_md_path`**
  * **Type:** String
  * **Default:** `"docs/style.md"`
  * **Description:** The relative path to your style guide file. Only applies if `use_style_md` is set to `true`.

### Tracking and Parsing

Control how Documentor scans your project context and tracks code changes.

* **`use_git`**
  * **Type:** Boolean
  * **Default:** `true`
  * **Description:** Uses Git to track changes in your source code. This enables Documentor to perform smart, incremental updates on stale documentation via the `documentor sync` command.
* **`ignore_patterns`**
  * **Type:** List of Strings
  * **Default:** `[".git", "__pycache__", "venv", ".venv", "env", "node_modules", ".env", "*.pyc", "*.pyo"]`
  * **Description:** File paths or glob patterns to hide from the LLM context. *Important: Documentor automatically reads your existing `.gitignore` and merges its rules with this list.*
* **`ignore_above_size_kb`**
  * **Type:** Integer
  * **Default:** `100`
  * **Description:** Automatically excludes any files larger than this size (in kilobytes) from being analyzed by the LLM. 

### File Requirements

Define the exact documentation files Documentor should create and maintain.

* **`required_files`**
  * **Type:** List of Objects
  * **Default:** `[]`
  * **Description:** A list of specific documents that must be generated and managed. *Note: You can automatically populate this list based on your project context using the `documentor plan` command.*

Each object in the `required_files` list requires the following keys:
- **`filename`** *(String)*: The output filename (e.g., `API.md` or `docs/readme.md`).
- **`type`** *(String)*: The category of the document (e.g., `Overview`, `Technical`, `Usage`). This helps the LLM understand the intended audience and format.
- **`description`** *(String)*: A brief description defining exactly what the AI should cover in this specific file.

---

## Example `documentor.yaml`

Here is a standard configuration that uses OpenAI, enforces a style guide, ignores a custom `tests` directory, and strictly requires a `docs/readme.md` and an `architecture.md` file.

```yaml
provider: "openai"
model: "gpt-4o"
docs_dir: "docs"
include_footer: true
use_style_md: true
style_md_path: "docs/style.md"
use_git: true
ignore_above_size_kb: 150
ignore_patterns:
  - ".git"
  - "node_modules"
  - "tests/fixtures/**"
  - "*.tmp"
required_files:
  - filename: "docs/readme.md"
    type: "overview"
    description: "High-level project overview, installation steps, and quickstart usage examples."
  - filename: "architecture.md"
    type: "technical"
    description: "Detailed system design, data flow diagrams, and core architectural decisions."
```

> *Docs generated with [documentor](https://github.com/YusufHosny/documentor)*