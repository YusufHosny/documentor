from typing import List, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from documentor.core.config import Config
from documentor.llm.client import get_llm
from documentor.llm.prompts import get_prompt_parts

def sync_doc(current_content: str, context: List[Dict[str, str]], config: Config, diff: Optional[str] = None) -> str:
    """Updates an existing document based on changes in the source code context."""
    llm = get_llm(config)

    prompts = get_prompt_parts("sync")

    prompt_messages = [
        ("system", prompts["system_prompt"]),
        ("user", prompts["user_prompt"])
    ]

    prompt = ChatPromptTemplate.from_messages(prompt_messages)

    chain = prompt | llm | StrOutputParser()

    context_str = "\n\n".join([f"--- File: {f['path']} ---\n{f['content']}" for f in context])

    inputs = {
        "context_instruction": "",
        "style_guide": config.get_style_guide(),
        "diff_content": f"The following changes were detected in the source code:\n{diff}" if diff else "",
        "current_content": current_content,
        "context_content": f"New Project Context:\n{context_str}",
        "agent_instruction": ""
    }

    return chain.invoke(inputs)
