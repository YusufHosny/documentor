from typing import Optional
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config
from documentor.llm.client import get_llm
from documentor.llm.prompts import get_prompt_parts
from .tools import get_tools

def agent_sync_doc(current_content: str, config: Config, diff: Optional[str] = None) -> str:
    """Synchronizes an existing document with the current codebase by exploring changes."""
    llm = get_llm(config)
    tools = get_tools(config)

    prompts = get_prompt_parts("sync")
    common_prompts = get_prompt_parts("common")

    system_message = prompts["system_prompt"].format(
        context_instruction="You can explore the codebase to see what changed using the provided tools.",
        style_guide=config.get_style_guide()
    )

    if diff:
        system_message += f"\n\nThe following changes were detected in the source code:\n{diff}"

    agent = create_agent(llm, tools, system_prompt=system_message)

    user_input = prompts["user_prompt"].format(
        diff_content="", # already in system message or not needed separately if integrated
        current_content=current_content,
        context_content="",
        agent_instruction="Explore the codebase as needed."
    )

    result = agent.invoke({"messages": [HumanMessage(content=user_input)]})

    content = result["messages"][-1].content

    refine_prompt = ChatPromptTemplate.from_messages([
        ("system", common_prompts["refine_prompt"]),
        ("user", "Updated Content:\n{content}")
    ])

    refine_chain = refine_prompt | llm | StrOutputParser()
    return refine_chain.invoke({"content": content})
