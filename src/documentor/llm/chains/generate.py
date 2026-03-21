from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from documentor.core.config import Config
from documentor.llm.client import get_llm
from documentor.core.writer import Writer

class DocItem(BaseModel):
    filename: str = Field(description="The desired markdown filename (e.g., 'API.md')")
    description: str = Field(description="A brief description of the document's purpose or focus")
    type: str = Field(description="The category of documentation (e.g., 'Functional', 'API Reference')")

class DocList(BaseModel):
    files: List[DocItem] = Field(description="List of documentation files to generate")

def _generate_doc_list(context: List[Dict[str, str]], config: Config) -> List[Dict[str, str]]:
    """Determines which documents to generate based on config and project context."""
    if config.required_only:
        return []

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert technical documentation architect."),
        ("system", "Analyze the project context and suggest a list of documentation files that should be generated to provide a complete understanding of the codebase."),
        ("system", "The current documentation style guide is:\n{style_guide}"),
        ("system", "The following files are already required and you should NOT duplicate them:\n{required_files}"),
        ("user", "Here is the project context:\n{context}")
    ])

    context_str = "\n\n".join([f"--- File: {f['path']} ---\n{f['content']}" for f in context])
    required_files_str = "\n".join([f"- {f['filename']} (Type: {f['type']})" for f in config.required_files])

    llm = get_llm(config)
    structured = llm.with_structured_output(DocList)
    chain = prompt | structured

    try:
        response: DocList = chain.invoke({
            "style_guide": config.get_style_guide(),
            "required_files": required_files_str,
            "context": context_str
        }) # type: ignore

        required_filenames = {f["filename"].lower() for f in config.required_files}
        pruned_files = [
            { "filename": f.filename, "type": f.type, "description": f.description } for f in response.files
            if f.filename.lower() not in required_filenames
        ]

        return pruned_files
    except Exception:
        return []


def generate_docs(context: List[Dict[str, str]], config: Config) -> List[str]:
    """Generates initial documentation from scratch based on context. Returns list of generated filenames."""
    llm = get_llm(config)

    docs_to_generate = [
        *config.required_files,
        *_generate_doc_list(context, config)
    ]

    writer = Writer(config)
    generated_files = []

    for doc in docs_to_generate:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert technical writer. Create a comprehensive, well-structured markdown document. Use the provided context as your source of truth."),
            ("system", "Here is the documentation style guide:\n{style_guide}"),
            ("user", "Here is the project context:\n{context}\n\nPlease generate the {filename} file with the following type {doc_type} and description: {description}")
        ])

        chain = prompt | llm | StrOutputParser()

        context_str = "\n\n".join([f"--- File: {f['path']} ---\n{f['content']}" for f in context])

        content = chain.invoke({
            "style_guide": config.get_style_guide(),
            "context": context_str,
            "filename": doc["filename"],
            "doc_type": doc["type"],
            "description": doc["description"]
        })

        final_path = writer.write(doc["filename"], content)
        generated_files.append(final_path)

    return generated_files
