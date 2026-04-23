from typing import List, Optional
from langchain_core.tools import tool
import re
from pathlib import Path
from documentor.core.parser import Parser
from documentor.core.config import Config


def get_tools(config: Config):
    parser = Parser(config)

    @tool
    def grep_files(expression: str) -> List[str]:
        """Lists all files and a snippet with content that matches an expression"""
        matches = []
        try:
            pattern = re.compile(expression)
        except re.error:
            return ["Error: Invalid regular expression."]

        files_to_search = parser.list_files_for_agent()

        for path_str in files_to_search:
            path = Path(path_str)
            if path.is_file():
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            if pattern.search(line):
                                snippet = line.strip()
                                matches.append(f"{path} (line {line_num}): {snippet}")
                except (PermissionError, OSError):
                    continue

        return matches if matches else ["No matches found."]

    @tool
    def list_files() -> List[str]:
        """Lists all available non-ignored files in the project."""
        return parser.list_files_for_agent()

    @tool
    def read_file(path: str) -> str:
        """Reads the content of a specific file."""
        content = parser.read_file(path)
        if content is None:
            return (
                f"Error: Could not read file {path} (it might be binary or not found)."
            )
        return content

    return [grep_files, list_files, read_file]
