import os
from pathlib import Path
from typing import Dict

PROMPTS_DIR = Path(__file__).parent

def load_prompt(name: str) -> str:
    """Loads a prompt from a markdown file in the prompts directory."""
    path = PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        return ""
    return path.read_text().strip()

def get_prompt_parts(name: str) -> Dict[str, str]:
    """Parses a markdown prompt file into sections (e.g., System Prompt, User Prompt)."""
    content = load_prompt(name)
    parts = {}
    current_part = None
    current_content = []

    for line in content.splitlines():
        if line.startswith("# "):
            if current_part:
                parts[current_part] = "\n".join(current_content).strip()
            current_part = line[2:].strip().lower().replace(" ", "_")
            current_content = []
        else:
            current_content.append(line)

    if current_part:
        parts[current_part] = "\n".join(current_content).strip()

    return parts
