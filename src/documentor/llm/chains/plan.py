from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config, DocList, DocItem
from documentor.llm.client import get_llm

def generate_plan(context: List[Dict[str, str]], config: Config) -> List[DocItem]:
    """Determines which documents to generate based on project context."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert technical documentation architect."),
        ("system", "Analyze the project context and suggest a list of documentation files that should be generated to provide a complete understanding of the codebase."),
        ("system", "The current documentation style guide is:\n{style_guide}"),
        ("system", "The following files are already required and you should NOT duplicate them:\n{required_files}"),
        ("user", "Here is the project context:\n{context}")
    ])

    context_str = "\n\n".join([f"--- File: {f['path']} ---\n{f['content']}" for f in context])
    required_files_str = "\n".join([f"- {f.filename} (Type: {f.type})" for f in config.required_files])

    llm = get_llm(config)
    structured = llm.with_structured_output(DocList)
    chain = prompt | structured

    try:
        response: DocList = chain.invoke({
            "style_guide": config.get_style_guide(),
            "required_files": required_files_str,
            "context": context_str
        }) # type: ignore

        required_filenames = {f.filename.lower() for f in config.required_files}
        pruned_files = [
            f for f in response.files
            if f.filename.lower() not in required_filenames
        ]

        return pruned_files
    except Exception:
        return []

def infer_doc_info(filename: str, context: List[Dict[str, str]], config: Config) -> DocItem:
    """Infers type and description for a specific file based on context."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert technical documentation architect."),
        ("system", "Based on the project context, infer the most appropriate documentation type and a brief description for the file: {filename}"),
        ("user", "Here is the project context:\n{context}")
    ])

    context_str = "\n\n".join([f"--- File: {f['path']} ---\n{f['content']}" for f in context])

    llm = get_llm(config)
    structured = llm.with_structured_output(DocItem)
    chain = prompt | structured

    try:
        response: DocItem = chain.invoke({
            "filename": filename,
            "context": context_str
        }) # type: ignore
        return response
    except Exception:
        return DocItem(filename=filename, type="General", description="Auto-inferred documentation")
