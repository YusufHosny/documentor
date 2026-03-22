from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config
from documentor.llm.client import get_llm
from .tools import get_tools

def agent_edit_doc(current_content: str, comments: str, config: Config) -> str:
    """Edits an existing document by dynamically exploring the codebase as needed."""
    llm = get_llm(config)
    tools = get_tools(config)

    system_message = f"""You are an expert technical writer. Your goal is to edit an existing markdown document based on user comments.
You can explore the codebase to ensure your edits are accurate using the provided tools.
Follow this style guide:
{config.get_style_guide()}"""

    agent = create_agent(llm, tools, system_prompt=system_message)

    user_input = f"Current Document Content:\n{current_content}\n\nUser Comments:\n{comments}\n\nPlease provide the updated document. Explore the codebase if you need more information to fulfill the user's request."

    result = agent.invoke({"messages": [HumanMessage(content=user_input)]})

    content = result["messages"][-1].content

    refine_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert technical writer. Strip any conversational filler or meta-commentary and return only the clean updated markdown content."),
        ("user", "Updated Content:\n{content}")
    ])

    refine_chain = refine_prompt | llm | StrOutputParser()
    return refine_chain.invoke({"content": content})
