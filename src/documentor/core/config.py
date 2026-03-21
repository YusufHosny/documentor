import os
from typing import Literal, List, Dict, Optional
import yaml
from pydantic import BaseModel, Field

class DocItem(BaseModel):
    filename: str = Field(description="The desired markdown filename (e.g., 'API.md')")
    description: str = Field(description="A brief description of the document's purpose or focus")
    type: str = Field(description="The category of documentation (e.g., 'Functional', 'API Reference')")

class DocList(BaseModel):
    files: List[DocItem] = Field(description="List of documentation files to generate")

class Config(BaseModel):
    provider: Literal['openai', 'vertexai', 'ollama'] = Field(default="vertexai", description="LLM provider")
    model: str = Field(default="gemini-3.1-pro-preview", description="Model name")

    docs_dir: str = Field(default="docs", description="Output directory for generated documentation")
    include_footer: bool = Field(default=False, description="Append footer to generated markdown")

    use_style_md: bool = Field(default=False, description="Whether to use the style.md file for formatting instructions when generating docs")
    style_md_path: str = Field(default="docs/style.md", description="Path to style.md file for formatting instructions")
    use_git: bool = Field(default=True, description="Whether to use git-based tracking for incremental updates")
    required_files: List[DocItem] = Field(
        default=[],
        description="Files that must be included in the documentation suite"
    )

    ignore_above_size_kb: int = Field(default=100, description="Ignore files above this size (in KB) when extracting context")
    ignore_patterns: List[str] = Field(
        default=[".git", "__pycache__", "venv", ".venv", "env", "node_modules", ".env", "*.pyc", "*.pyo"],
        description="Patterns to ignore when scanning project"
    )
    #TODO: semantically ignore files with llm/vectorsearch

    # -------------------------- config helpers --------------------------
    def get_style_guide(self) -> str:
        """Loads the user's style guide if it exists, otherwise returns an empty string."""
        style_path = self.style_md_path or os.path.join(self.docs_dir or "docs", "style.md")
        if os.path.exists(style_path):
            with open(style_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            return ""

class ConfigManager:
    def __init__(self, config_file: str = "documentor.yaml"):
        self.config_file = config_file

    def create_default_config(self):
        """Creates a default configuration file."""
        default_config = Config()
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(default_config.model_dump(), f, default_flow_style=False, sort_keys=False)

    def load_config(self) -> Config:
        """Loads configuration from file, falling back to defaults if not found."""
        if not self.config_exists():
            return Config()

        with open(self.config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return Config(**data)
    
    def config_exists(self) -> bool:
        """Checks if the configuration file already exists."""
        return os.path.exists(self.config_file)
    
    def clear_config(self):
        """Deletes the existing configuration file."""
        if self.config_exists():
            os.remove(self.config_file)

    def save_config(self, config: Config):
        """Saves the given configuration to file."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)
