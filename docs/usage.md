# CLI Usage Guide

Documentor provides a straightforward command-line interface to initialize, generate, and maintain your project's documentation. 

## Global Options

* **`--version`**: Show the installed version of Documentor and exit.

---

## Commands

### `init`
Starts an interactive wizard to set up Documentor in your project. It walks you through selecting your LLM provider, setting output directories, defining file ignore patterns, and choosing a style template.

```bash
documentor init
```
**Result:** Creates a `documentor.yaml` configuration file and an optional `style.md` guide in your project root.

### `plan`
Analyzes your project's context and suggests a list of recommended documentation files. You can choose to merge these suggestions with your existing configuration or overwrite it entirely.

```bash
documentor plan
```
**Result:** Updates the `required_files` list in your `documentor.yaml`.

### `generate`
Reads your configuration, analyzes your project's source code, and creates your documentation files. By default, it skips files that are already up to date to save time and API costs.

```bash
documentor generate
```
**Options:**
* `-f, --force`: Force regeneration of all documentation files, ignoring the current tracking state.

**Result:** Generates markdown files in your configured output directory and creates a `documentor-lock.yaml` file to track the current state of your code.

### `sync`
Detects changes in your source code since the last generation and selectively updates only the documentation files that have become stale. 

```bash
documentor sync
```
*Note: Incremental updates rely on Git. Ensure `use_git: true` is set in your configuration.*

### `edit`
Refines an existing markdown document using natural language feedback. When run, the CLI prompts you to type your instructions for the AI to rewrite or adjust the file.

```bash
documentor edit <target_file>
```
**Arguments:**
* `target_file`: The path to the markdown file you want to edit (e.g., `docs/API.md`).

### `expand`
Transforms rough bullet points or scratchpad notes into a fully formatted, professional markdown document. Documentor automatically infers the intended document type, creates the file, and adds it to your `documentor.yaml` tracking list.

```bash
documentor expand <target_file>
```
**Arguments:**
* `target_file`: The path to the rough draft markdown file.

---

## Example Workflows

### The Happy Path: Setting Up a New Project
The fastest way to get value out of Documentor is to initialize it, plan your docs, generate them, and keep them synced as you write code.

```bash
# 1. Run the interactive setup and answer the prompts
documentor init

# 2. Let the AI suggest which docs your project needs
documentor plan

# 3. Generate the initial documentation suite
documentor generate

# 4. Write new code, commit changes
git commit -m "feat: add new payment gateway"

# 5. Bring your docs up to date with your new code
documentor sync
```

### Brainstorming to Formal Docs
If you prefer to write brief, messy notes during a meeting or coding session, you can use Documentor to instantly convert them into formal project documentation. 

```bash
# Expand your raw notes into a formal document
documentor expand docs/draft-notes.md
```

### Directing the AI
If a generated document isn't quite right, you don't need to rewrite it manually or regenerate the whole project. Use the `edit` command to give the AI specific feedback.

```bash
documentor edit README.md
# The CLI will prompt you:
# Please enter your comments for the AI: 
# > "Add a section explaining how to run the test suite."
```

> *Docs generated with [documentor](https://github.com/YusufHosny/documentor)*