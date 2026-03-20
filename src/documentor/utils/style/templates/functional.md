# Style Template: Functional
## Scope: Large-Scale Open Source Projects (OSS)
**Goal**: Create a comprehensive, user-centric documentation suite that guides developers through using, understanding, and integrating with a large project.

### 1. Document Structure (Multi-File)
- **README.md**: The entry point. Overview, quick start, and a "Table of Contents" linking to other docs.
- **ARCHITECTURE.md**: Explains the high-level design, data flow, and core components.
- **USAGE_GUIDE.md**: Detailed tutorials and common patterns for using the software.
- **API_REFERENCE.md**: Exhaustive documentation of all exposed functions, classes, and endpoints. (Optionally split by module if the project is very large).

### 2. Content Requirements
- **Value Proposition**: Clearly state why this project exists and the problems it solves.
- **Architecture & Design**: Detailed explanation of *how* the system works together, using diagrams (Mermaid) where appropriate.
- **Exhaustive API Docs**: Every public interface must be documented with:
  - Signature / Type definitions.
  - Parameter descriptions.
  - Return value descriptions.
  - Example usage.
- **Error Handling**: Document common errors and how the user should handle them.

### 3. Style and Tone
- **User-Centric**: Write from the perspective of a developer who needs to use the tool, not the person who built it.
- **Professional & Formal**: Maintain a standard appropriate for a major OSS project.
- **Educational**: Explain the "Why" behind certain usage patterns to help users make better decisions.
- **Highly Structured**: Use headers, sub-headers, and lists to make the documentation easily skimmable.
