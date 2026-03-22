from typing import List, Optional
from langchain_core.tools import tool
from documentor.core.parser import Parser
from documentor.core.config import Config

def get_tools(config: Config):
    parser = Parser(config)

    @tool
    def list_files() -> List[str]:
        """Lists all available non-ignored files in the project."""
        return parser.list_files_for_agent()

    @tool
    def read_file(path: str) -> str:
        """Reads the content of a specific file."""
        content = parser.read_file(path)
        if content is None:
            return f"Error: Could not read file {path} (it might be binary or not found)."
        return content

    return [list_files, read_file]
