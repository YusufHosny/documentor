from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from documentor.core.config import Config, DocItem
from documentor.llm.client import get_llm
from documentor.core.writer import Writer
from documentor.llm.prompts import get_prompt_parts

def generate_docs(context: List[Dict[str, str]], config: Config, docs_to_generate: List[DocItem]) -> List[str]:
    """Generates documentation based on context and a specified list of documents."""
    llm = get_llm(config)
    writer = Writer(config)
    generated_files = []

    prompts = get_prompt_parts("generate")

    for doc in docs_to_generate:
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompts["system_prompt"]),
            ("user", prompts["user_prompt"])
        ])

        chain = prompt | llm | StrOutputParser()

        context_str = "\n\n".join([f"--- File: {f['path']} ---\n{f['content']}" for f in context])

        content = chain.invoke({
            "context_instruction": "Use the provided context as your source of truth.",
            "style_guide": config.get_style_guide(),
            "context_content": f"Here is the project context:\n{context_str}",
            "filename": doc.filename,
            "doc_type": doc.type,
            "description": doc.description,
            "agent_instruction": ""
        })

        final_path = writer.write(doc.filename, content)
        generated_files.append(final_path)

    return generated_files
