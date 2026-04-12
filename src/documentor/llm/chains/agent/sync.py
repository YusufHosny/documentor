import asyncio
from typing import Optional, List, Dict, Any, Tuple
from langchain_core.messages import HumanMessage
from documentor.llm.client import get_llm, create_retryable_agent, retryable
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config
from documentor.llm.client import get_llm
from documentor.llm.prompts.sync import get_system_prompt, get_user_prompt
from documentor.llm.prompts.common import get_refine_prompt
from .tools import get_tools


def _prepare_agent_sync_chain_and_inputs(
    current_content: str, config: Config, diff: Optional[str] = None
) -> Tuple[Any, Dict[str, Any], Any]:
    """Helper to prepare the agent and inputs for doc sync."""
    llm = get_llm(config)
    tools = get_tools(config)

    system_message = get_system_prompt(
        context_instruction="You can explore the codebase to see what changed using the provided tools.",
        style_guide=config.get_style_guide(),
    )

    if diff:
        system_message += (
            f"\n\nThe following changes were detected in the source code:\n{diff}"
        )

    agent = create_retryable_agent(llm, tools, system_prompt=system_message)

    user_input = get_user_prompt(
        diff_content="",  # already in system message or not needed separately if integrated
        current_content=current_content,
        context_content="",
        agent_instruction="Explore the codebase as needed.",
    )

    refine_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_msg}"),
            ("user", "Updated Content:\n{content}"),
        ]
    )

    refine_chain = retryable(refine_prompt | llm | StrOutputParser())
    return agent, {"messages": [HumanMessage(content=user_input)]}, refine_chain


def agent_sync_doc(
    current_content: str, config: Config, diff: Optional[str] = None
) -> str:
    """Synchronizes an existing document with the current codebase by exploring changes."""
    agent, inputs, refine_chain = _prepare_agent_sync_chain_and_inputs(
        current_content, config, diff
    )
    result = agent.invoke(inputs)
    content = result["messages"][-1].content
    return refine_chain.invoke({"system_msg": get_refine_prompt(), "content": content})


async def async_agent_sync_doc(
    current_content: str, config: Config, diff: Optional[str] = None
) -> str:
    """Synchronizes an existing document with the current codebase by exploring changes asynchronously."""
    agent, inputs, refine_chain = _prepare_agent_sync_chain_and_inputs(
        current_content, config, diff
    )
    result = await agent.ainvoke(inputs)
    content = result["messages"][-1].content
    return await refine_chain.ainvoke({"system_msg": get_refine_prompt(), "content": content})


async def async_agent_sync_docs(
    config: Config, docs_to_sync: List[Dict[str, Any]]
) -> List[str]:
    """Synchronizes multiple documents with the current codebase in parallel."""
    from documentor.core.writer import Writer

    writer = Writer(config)

    async def _sync_single(doc_data: Dict[str, Any]) -> str:
        filepath = doc_data["filepath"]
        current_content = doc_data["current_content"]
        diff = doc_data.get("diff")

        new_content = await async_agent_sync_doc(current_content, config, diff)
        return writer.write(str(filepath), new_content)

    tasks = [_sync_single(d) for d in docs_to_sync]
    return await asyncio.gather(*tasks)
