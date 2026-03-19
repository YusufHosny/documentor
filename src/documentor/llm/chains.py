import os
from typing import List, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from documentor.core.config import Config
from documentor.llm.client import get_llm
from documentor.core.writer import Writer

def generate_docs(context: List[Dict[str, str]], config: Config, target: Optional[str] = None):
    """Generates initial documentation from scratch based on context."""
    llm = get_llm(config)

    docs_to_generate = []
    if target is None:
        docs_to_generate = [
            {"filename": "README.md", "type": "Project Overview and Quickstart"},
            {"filename": f"{config.docs_dir}/functional_spec.md", "type": "Functional Specification"}
        ]
    else:
        docs_to_generate = [
            {"filename": target, "type": "Targeted Documentation based on user request"}
        ]

    writer = Writer(config)

    for doc in docs_to_generate:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert technical writer. Create a comprehensive, well-structured markdown document of type: {doc_type}. Use the provided context as your source of truth."),
            ("user", "Here is the project context:\n{context}\n\nPlease generate the {filename} file.")
        ])

        chain = prompt | llm | StrOutputParser()

        context_str = "\n\n".join([f"--- File: {f['path']} ---\n{f['content']}" for f in context])

        content = chain.invoke({
            "doc_type": doc["type"],
            "context": context_str,
            "filename": doc["filename"]
        })

        writer.write(doc["filename"], content)

def edit_doc(current_content: str, comments: str, config: Config) -> str:
    """Edits an existing document based on user comments."""
    llm = get_llm(config)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert technical writer. You are reviewing an existing markdown document. Update it based on the user's comments. Output ONLY the updated markdown content, without any extra conversation or markdown formatting ticks (unless they are part of the content itself)."),
        ("user", "Current Document:\n{current_content}\n\nUser Comments:\n{comments}\n\nPlease provide the updated document.")
    ])

    chain = prompt | llm | StrOutputParser()

    return chain.invoke({
        "current_content": current_content,
        "comments": comments
    })

def expand_doc(scrappy_notes: str, doc_type: str, config: Config) -> str:
    """Expands scrappy notes into a full document."""
    llm = get_llm(config)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert technical writer. Expand the following scrappy notes into a complete, well-formatted markdown document of type: {doc_type}. Maintain the original intent but improve flow, structure, and professional tone. Output ONLY the markdown content, without any extra conversation or markdown formatting ticks."),
        ("user", "Scrappy Notes:\n{notes}\n\nPlease expand into a full document.")
    ])

    chain = prompt | llm | StrOutputParser()

    return chain.invoke({
        "doc_type": doc_type,
        "notes": scrappy_notes
    })
