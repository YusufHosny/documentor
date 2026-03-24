# CLI Usage Guide

Documentor provides a command-line interface to initialize, generate, and maintain your project's documentation. 

## Global Options

* **`--version`**: Show the installed version and exit.
* **`--help`**: Show help messages and exit.

---

## Agent Mode

Documentor automatically switches to Agent Mode for large projects (default threshold: `1000 KB`). This prevents exceeding AI token limits by dynamically exploring the codebase instead of loading it all at once. You can force or configure this behavior in `documentor.yaml`.

---

## Commands

### `init`
Starts an interactive wizard to configure Documentor for your project.

```bash
documentor init
```
**Result:** Creates a `documentor.yaml` configuration file and an optional `style.md` formatting guide. It also offers to automatically plan your documentation suite.

### `plan`
Analyzes your project to suggest a list of needed documentation files. 

```bash
documentor plan
```
**Result:** Suggests new files and asks whether to merge them into or overwrite the existing `required_files` list in `documentor.yaml`.

### `generate`
Creates or updates your documentation files. By default, it skips files that are already up to date.

```bash
documentor generate
```
**Options:**
* `-f, --force`: Regenerate all files, ignoring current tracking state.

**Result:** Generates markdown files and updates `documentor-lock.yaml` with the current state.

### `sync`
Updates existing documentation files based on source code changes since the last generation.

```bash
documentor sync
```
*Note: Requires `use_git: true` in your configuration to utilize git diffs for incremental updates.*

### `edit`
Refines an existing markdown document based on your natural language instructions. The CLI prompts you for comments before applying the changes using AI.

```bash
documentor edit <target_file>
```
**Arguments:**
* `target_file`: Path to the markdown file to edit.

### `expand`
Transforms draft notes or scrappy bullet points into a coherent, well-formatted markdown document. Documentor infers the document's metadata (like type and description) and automatically adds it to your configuration if it's missing.

```bash
documentor expand <target_file>
```
**Arguments:**
* `target_file`: Path to the draft markdown file.

---

## Example Workflows

### Setup and Generate
The quickest way to get started.
```bash
documentor init
documentor generate
```

### Keep Docs Updated
Sync existing documentation after making code changes.
```bash
git commit -m "feat: add payment gateway"
documentor sync
```

### AI-Assisted Writing
```bash
# Expand rough notes into a formal document
documentor expand docs/draft-notes.md

# Provide specific feedback to refine a document
documentor edit docs/readme.md
```

---

## Tracing (Optional)

Documentor supports LangSmith for tracing AI requests. Enable it via environment variables:

```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_api_key
LANGSMITH_PROJECT=documentor
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

> *Docs generated with [documentor](https://github.com/YusufHosny/documentor)*