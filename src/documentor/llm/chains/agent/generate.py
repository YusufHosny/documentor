import asyncio
from typing import List, Tuple, Any, Dict
from langchain_core.messages import HumanMessage
from documentor.llm.client import get_llm, create_retryable_agent, retryable
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config, DocItem
from documentor.llm.client import get_llm
from documentor.core.writer import Writer
from documentor.llm.prompts import get_prompt_parts
from .tools import get_tools


def _prepare_agent_generate_chain_and_inputs(
    doc: DocItem, config: Config
) -> Tuple[Any, Dict[str, Any], Any]:
    """Helper to prepare the agent and inputs for doc generation."""
    llm = get_llm(config)
    tools = get_tools(config)

    prompts = get_prompt_parts("generate")
    common_prompts = get_prompt_parts("common")

    system_message_base = prompts["system_prompt"].format(
        context_instruction="Your goal is to explore the codebase to find relevant information. You can use the provided tools to browse the files.",
        style_guide=config.get_style_guide(),
    )

    agent = create_retryable_agent(llm, tools, system_prompt=system_message_base)

    user_input = prompts["user_prompt"].format(
        context_content="",
        filename=doc.filename,
        description=doc.description,
        agent_instruction="Explore the codebase as needed.",
    )

    refine_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", common_prompts["refine_prompt"]),
            ("user", "Documentation Content:\n{content}"),
        ]
    )

    refine_chain = retryable(refine_prompt | llm | StrOutputParser())
    return agent, {"messages": [HumanMessage(content=user_input)]}, refine_chain


def agent_generate_docs(config: Config, docs_to_generate: List[DocItem]) -> List[str]:
    """Generates documentation by dynamically exploring the codebase for each document."""
    writer = Writer(config)
    generated_files = []

    for doc in docs_to_generate:
        agent, inputs, refine_chain = _prepare_agent_generate_chain_and_inputs(
            doc, config
        )
        result = agent.invoke(inputs)
        content = result["messages"][-1].content
        final_content = refine_chain.invoke({"content": content})

        final_path = writer.write(doc.filename, final_content)
        generated_files.append(final_path)

    return generated_files


async def async_agent_generate_docs(
    config: Config, docs_to_generate: List[DocItem]
) -> List[str]:
    """Generates documentation by dynamically exploring the codebase for each document asynchronously."""
    writer = Writer(config)

    async def _generate_single(doc: DocItem) -> str:
        agent, inputs, refine_chain = _prepare_agent_generate_chain_and_inputs(
            doc, config
        )
        result = await agent.ainvoke(inputs)
        content = result["messages"][-1].content
        final_content = await refine_chain.ainvoke({"content": content})
        return writer.write(doc.filename, final_content)

    tasks = [_generate_single(doc) for doc in docs_to_generate]
    return await asyncio.gather(*tasks)
