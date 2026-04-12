import asyncio
from typing import List, Dict, Any, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from documentor.core.config import Config, DocItem
from documentor.llm.client import get_llm, retryable
from documentor.core.writer import Writer
from documentor.llm.prompts import get_prompt_parts


def _prepare_generate_chain_and_inputs(
    doc: DocItem, context_str: str, config: Config
) -> Tuple[Any, Dict[str, Any]]:
    """Helper to prepare the LangChain chain and inputs for doc generation."""
    llm = get_llm(config)
    prompts = get_prompt_parts("generate")
    prompt = ChatPromptTemplate.from_messages(
        [("system", prompts["system_prompt"]), ("user", prompts["user_prompt"])]
    )
    chain = retryable(prompt | llm | StrOutputParser())

    inputs = {
        "context_instruction": "Use the provided context as your source of truth.",
        "style_guide": config.get_style_guide(),
        "context_content": f"Here is the project context:\n{context_str}",
        "filename": doc.filename,
        "description": doc.description,
        "agent_instruction": "",
    }
    return chain, inputs


def generate_docs(
    context: List[Dict[str, str]], config: Config, docs_to_generate: List[DocItem]
) -> List[str]:
    """Generates documentation based on context and a specified list of documents."""
    writer = Writer(config)
    generated_files = []
    context_str = "\n\n".join(
        [f"--- File: {f['path']} ---\n{f['content']}" for f in context]
    )

    for doc in docs_to_generate:
        chain, inputs = _prepare_generate_chain_and_inputs(doc, context_str, config)
        content = chain.invoke(inputs)
        final_path = writer.write(doc.filename, content)
        generated_files.append(final_path)

    return generated_files


async def async_generate_docs(
    context: List[Dict[str, str]], config: Config, docs_to_generate: List[DocItem]
) -> List[str]:
    """Generates documentation based on context and a specified list of documents asynchronously."""
    writer = Writer(config)
    context_str = "\n\n".join(
        [f"--- File: {f['path']} ---\n{f['content']}" for f in context]
    )

    async def _generate_single(doc: DocItem) -> str:
        chain, inputs = _prepare_generate_chain_and_inputs(doc, context_str, config)
        content = await chain.ainvoke(inputs)
        return writer.write(doc.filename, content)

    tasks = [_generate_single(doc) for doc in docs_to_generate]
    return await asyncio.gather(*tasks)
