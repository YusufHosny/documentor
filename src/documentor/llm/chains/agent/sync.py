from typing import Optional
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config
from documentor.llm.client import get_llm
from .tools import get_tools

def agent_sync_doc(current_content: str, config: Config, diff: Optional[str] = None) -> str:
    """Synchronizes an existing document with the current codebase by exploring changes."""
    llm = get_llm(config)
    tools = get_tools(config)

    system_message = f"""You are an expert technical writer. Your goal is to synchronize an existing markdown document with the current source code state.
You can explore the codebase to see what changed using the provided tools.
Follow this style guide:
{config.get_style_guide()}"""

    if diff:
        system_message += f"\n\nThe following changes were detected in the source code:\n{diff}"

    agent = create_agent(llm, tools, system_prompt=system_message)

    user_input = f"Current Document Content:\n{current_content}\n\nPlease update the document to match the current state of the codebase. Explore the codebase as needed."

    result = agent.invoke({"messages": [HumanMessage(content=user_input)]})

    content = result["messages"][-1].content

    refine_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert technical writer. Strip any conversational filler or meta-commentary and return only the clean updated markdown content."),
        ("user", "Updated Content:\n{content}")
    ])

    refine_chain = refine_prompt | llm | StrOutputParser()
    return refine_chain.invoke({"content": content})
