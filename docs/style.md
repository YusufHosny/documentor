# Style Guide
## Scope: Open Source Project Documentation
**Goal**: Create a readme file that describes the project and how its installed and used in a concise way. Then include a table of contents describing and linking to other documentation pages.

### 1. Document Structure
- **readme.md**: The top level readme file that describes installation, usage, and gives a top level overview over other docs.
- **usage.md**: Detailed descriptions of the CLI API including all commands and options, and extra usage examples
- **config.md**: A detailed reference for all the config options within the config file and their types, values, defaults, and important considerations.
- **tests.md**: Explains how to run the project's test suite, including details on test structure, what testing covers, and what tools are used (e.g. pytest, uv).

### 2. Content Requirements
- **Project Summary**: 2-3 sentences explaining what the project is and its core value.
- **Features**: A short bulleted list of the main capabilities.
- **Installation**: Minimal steps to get the project running locally.
- **Usage**: Clear, brief examples (code snippets or CLI commands) of how to use the project.
- **Config Format**: A detailed explanation of the structure of the config file and all options and effects.

### 3. Style and Tone
- **Conciseness is Key**: Avoid deep dives into architecture, design patterns, or internal logic.
- **Direct Language**: Use active voice and simple terminology.
- **Instructional**: Focus on the "Happy Path" – the quickest way for a user to see value.
- **No Over-Engineering**: If a feature is self-explanatory, don't write a paragraph for it.
