from typing import List, Dict

from openai import BaseModel
from pydantic import Field

class AnalysisResult(BaseModel):
    needs: List[str] = Field(default_factory=list, description="List of identified documentation needs based on project analysis") 

class Analyzer:
    def __init__(self, context: List[Dict[str, str]]):
        self.context = context

    def analyze_project(self) -> List[str]:
        """Analyzes the project context to determine documentation needs."""
        #TODO: more detailed analysis/rules
        needs = []

        has_python = any(f["path"].endswith(".py") for f in self.context)
        has_js = any(f["path"].endswith(".js") or f["path"].endswith(".ts") for f in self.context)

        if has_python:
            needs.append("Detected Python code. Generating Python-specific documentation.")

        if has_js:
            needs.append("Detected JavaScript/TypeScript code. Generating JS/TS-specific documentation.")

        return needs
