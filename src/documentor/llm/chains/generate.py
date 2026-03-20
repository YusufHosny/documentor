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
