from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from documentor.core.config import Config, DocItem
from documentor.llm.client import get_llm
from documentor.core.writer import Writer

def generate_docs(context: List[Dict[str, str]], config: Config, docs_to_generate: List[DocItem]) -> List[str]:
    """Generates documentation based on context and a specified list of documents."""
    llm = get_llm(config)
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
            "filename": doc.filename,
            "doc_type": doc.type,
            "description": doc.description
        })

        final_path = writer.write(doc.filename, content)
        generated_files.append(final_path)

    return generated_files
