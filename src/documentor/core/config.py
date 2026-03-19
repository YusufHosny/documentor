import os
from typing import Literal
import yaml
from pydantic import BaseModel, Field

class Config(BaseModel):
    provider: Literal['openai', 'vertexai', 'ollama'] = Field(default="vertexai", description="LLM provider", )
    model: str = Field(default="gemini-3.1-pro", description="Model name")
    docs_dir: str = Field(default="docs", description="Output directory for generated documentation")
    include_footer: bool = Field(default=False, description="Append footer to generated markdown")
    ignore_patterns: list[str] = Field(
        default=[".git", "__pycache__", "venv", ".venv", "env", "node_modules", ".env", "*.pyc", "*.pyo"],
        description="Patterns to ignore when scanning project"
    )
    #TODO: doc style/format options, ignore file extensions/above certain size, additional instructions, etc

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
        if not os.path.exists(self.config_file):
            return Config()

        with open(self.config_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return Config(**data)
