from typing import List, Dict

from openai import BaseModel
from pydantic import Field

class ProjectAnalysisResult(BaseModel):
    style_guide: str = Field(description="LLM-generated style guide for documentation formatting and tone")
    doc_plan: List[Dict[str, str]] = Field(description="LLM-generated plan for which documents to generate and what they should contain, based on project context analysis")

class Analyzer:
    def __init__(self, config):
        self.config = config

    def analyze_project(self, context: List[Dict[str, str]]) -> ProjectAnalysisResult:
        """Analyzes project context and generates a style guide and documentation plan."""
        style_guide = self.generate_style_guide(context)
        doc_plan = self.generate_file_plan(context)

        return ProjectAnalysisResult(style_guide=style_guide, doc_plan=doc_plan)


    def decide_docs_to_generate(self, context: List[Dict[str, str]]) -> List[Dict[str, str]]:
        pass

    def generate_style_guide(self, context: List[Dict[str, str]]) -> str:
        pass

    def generate_file_plan(self, context: List[Dict[str, str]]) -> str:
        pass
