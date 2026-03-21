import os
from documentor.core.config import Config

class Writer:
    def __init__(self, config: Config):
        self.config = config

    def write(self, target_file: str, content: str):
        """Writes markdown content to disk, optionally adding a footer."""

        if self.config.include_footer:
            footer = "\n\n> *Docs generated with [documentor](https://github.com/YusufHosny/documentor)*"
            if footer not in content:
                content += footer

        target_dir = os.path.dirname(target_file) or ""
        config_docs_dir = self.config.docs_dir or "docs"
        if (
            not target_file.lower().endswith("readme.md")  # keep README.md at root
            and not target_dir.lower().startswith(config_docs_dir) 
        ):
            target_dir = os.path.join(config_docs_dir, target_dir)
            os.makedirs(target_dir, exist_ok=True)

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
