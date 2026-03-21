import os
from typing import List, Dict

from documentor.core.config import Config

def get_style_templates() -> List[str]:
    """Returns a list of available style templates."""
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    template_files = [f for f in os.listdir(templates_dir) if f.endswith(".md")]
    return template_files

def load_style_template(template_name: str) -> str:
    """Loads the content of a style template."""
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    template_path = os.path.join(templates_dir, f"{template_name}.md")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()
    