from typing import List, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from documentor.core.config import Config
from documentor.llm.client import get_llm

def sync_doc(current_content: str, context: List[Dict[str, str]], config: Config, diff: Optional[str] = None) -> str:
    """Updates an existing document based on changes in the source code context."""
    llm = get_llm(config)

    prompt_messages = [
        ("system", "You are an expert technical writer. You are updating an existing markdown document because the underlying source code has changed."),
        ("system", "Your goal is to synchronize the document with the new source code state. Maintain the existing structure and style, but update any descriptions, examples, or references that are no longer accurate."),
        ("system", "Output ONLY the updated markdown content, without any extra conversation or markdown formatting ticks.")
    ]

    if diff:
        prompt_messages.append(("system", f"The following changes were detected in the source code:\n{diff}"))

    prompt_messages.append(("user", "Current Document Content:\n{current_content}\n\nNew Project Context:\n{context}\n\nPlease provide the updated document."))

    prompt = ChatPromptTemplate.from_messages(prompt_messages)

    chain = prompt | llm | StrOutputParser()

    context_str = "\n\n".join([f"--- File: {f['path']} ---\n{f['content']}" for f in context])

    return chain.invoke({
        "current_content": current_content,
        "context": context_str
    })
