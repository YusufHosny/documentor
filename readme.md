# Documentor

Documentor is a CLI tool that automatically generates and manages your project's documentation using Large Language Models. It analyzes your codebase to create tailored markdown files and keeps them synchronized as your source code evolves, freeing you from manual documentation updates.

### Features
* **Interactive Setup:** Quickly configure documentation targets, required files, ignore patterns (automatically integrates with `.gitignore`), and LLM providers via a CLI wizard.
* **Smart Generation:** Automatically writes comprehensive markdown documentation based on your project's source code context and custom style guides.
* **State Tracking & Sync:** Detects code changes via Git (tracked locally via a `documentor-lock.yaml` file) and selectively updates only the documentation that has become stale.
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

### Results
Once generated, Documentor will populate your target directory (default: `docs/`) with cleanly formatted Markdown files that accurately reflect the current state of your codebase. It will also generate a `documentor-lock.yaml` file in your project root to keep track of synchronization state. The generation follows your `documentor.yaml` configuration and any built-in style templates (such as Basic, Functional, Handoff, or Research) you chose to initialize during setup.

> *Docs generated with [documentor](https://github.com/YusufHosny/documentor)*