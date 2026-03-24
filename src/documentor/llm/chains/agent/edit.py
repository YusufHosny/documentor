from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config
from documentor.llm.client import get_llm
from documentor.llm.prompts import get_prompt_parts
from .tools import get_tools

def agent_edit_doc(current_content: str, comments: str, config: Config) -> str:
    """Edits an existing document by dynamically exploring the codebase as needed."""
    llm = get_llm(config)
    tools = get_tools(config)

    prompts = get_prompt_parts("edit")
    common_prompts = get_prompt_parts("common")

    system_message = prompts["system_prompt"].format(
        context_instruction="You can explore the codebase to ensure your edits are accurate using the provided tools.",
        style_guide=config.get_style_guide()
    )

    agent = create_agent(llm, tools, system_prompt=system_message)

    user_input = prompts["user_prompt"].format(
        current_content=current_content,
        comments=comments,
        agent_instruction="Explore the codebase if you need more information to fulfill the user's request."
    )

    result = agent.invoke({"messages": [HumanMessage(content=user_input)]})

    content = result["messages"][-1].content

    refine_prompt = ChatPromptTemplate.from_messages([
        ("system", common_prompts["refine_prompt"]),
        ("user", "Updated Content:\n{content}")
    ])

    refine_chain = refine_prompt | llm | StrOutputParser()
    return refine_chain.invoke({"content": content})
