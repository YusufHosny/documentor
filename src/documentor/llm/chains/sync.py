import asyncio
from typing import List, Dict, Optional, Tuple, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from documentor.core.config import Config
from documentor.llm.client import get_llm, retryable
from documentor.llm.prompts.sync import get_system_prompt, get_user_prompt


def _prepare_sync_chain_and_inputs(
    current_content: str, context_str: str, config: Config, diff: Optional[str] = None
) -> Tuple[Any, Dict[str, Any]]:
    """Helper to prepare the LangChain chain and inputs for sync."""
    llm = get_llm(config)

    system_msg = get_system_prompt(
        context_instruction="",
        style_guide=config.get_style_guide()
    )
    user_msg = get_user_prompt(
        diff_content=f"The following changes were detected in the source code:\n{diff}" if diff else "",
        current_content=current_content,
        context_content=f"New Project Context:\n{context_str}",
        agent_instruction=""
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_msg}"),
        ("user", "{user_msg}")
    ])
    chain = retryable(prompt | llm | StrOutputParser())

    return chain, {"system_msg": system_msg, "user_msg": user_msg}


def sync_doc(
    current_content: str,
    context: List[Dict[str, str]],
    config: Config,
    diff: Optional[str] = None,
) -> str:
    """Updates an existing document based on changes in the source code context."""
    context_str = "\n\n".join(
        [f"--- File: {f['path']} ---\n{f['content']}" for f in context]
    )
    chain, inputs = _prepare_sync_chain_and_inputs(
        current_content, context_str, config, diff
    )
    return chain.invoke(inputs)


async def async_sync_doc(
    current_content: str, context_str: str, config: Config, diff: Optional[str] = None
) -> str:
    """Updates an existing document based on changes in the source code context asynchronously."""
    chain, inputs = _prepare_sync_chain_and_inputs(
        current_content, context_str, config, diff
    )
    return await chain.ainvoke(inputs)


async def async_sync_docs(
    context: List[Dict[str, str]], config: Config, docs_to_sync: List[Dict[str, Any]]
) -> List[str]:
    """Updates multiple documents in parallel based on changes in the source code context."""
    from documentor.core.writer import Writer

    writer = Writer(config)
    context_str = "\n\n".join(
        [f"--- File: {f['path']} ---\n{f['content']}" for f in context]
    )

    async def _sync_single(doc_data: Dict[str, Any]) -> str:
        filepath = doc_data["filepath"]
        current_content = doc_data["current_content"]
        diff = doc_data.get("diff")

        chain, inputs = _prepare_sync_chain_and_inputs(
            current_content, context_str, config, diff
        )
        new_content = await chain.ainvoke(inputs)
        return writer.write(str(filepath), new_content)

    tasks = [_sync_single(d) for d in docs_to_sync]
    return await asyncio.gather(*tasks)
