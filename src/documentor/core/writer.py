import os
from documentor.core.config import Config
import regex

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

        # check for any doc links and adjust path
        for doc_item in self.config.required_files:
            filename = os.path.basename(doc_item.filename)
            safe_docs_dir = regex.escape(config_docs_dir)
            replacement = f"{config_docs_dir}/{filename}".replace("\\", "/")
            pattern = rf"(?<!{safe_docs_dir}[/\\]){regex.escape(filename)}"
            content = regex.sub(pattern, lambda m: replacement, content, flags=regex.IGNORECASE)

        final_path = target_file
        if (
            not target_file.lower().endswith("readme.md")  # keep readmes at root
            and not target_dir.lower().startswith(config_docs_dir.lower())
        ):
            final_path = os.path.join(config_docs_dir, target_file)
            os.makedirs(os.path.dirname(final_path), exist_ok=True)

        with open(final_path, "w", encoding="utf-8") as f:
            f.write(content)
        return final_path
