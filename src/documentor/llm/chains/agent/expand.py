from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config
from documentor.llm.client import get_llm
from .tools import get_tools

def agent_expand_doc(scrappy_notes: str, doc_type: str, config: Config) -> str:
    """Expands scrappy notes into a full document by dynamically exploring context."""
    llm = get_llm(config)
    tools = get_tools(config)

    system_message = f"""You are an expert technical writer. Your goal is to expand scrappy notes into a full markdown document of a specific type.
You can explore the codebase to ensure your expansion is accurate and comprehensive using the provided tools.
Follow this style guide:
{config.get_style_guide()}"""

    agent = create_agent(llm, tools, system_prompt=system_message)

    user_input = f"Scrappy Notes:\n{scrappy_notes}\n\nTarget Type: {doc_type}\n\nPlease expand these notes into a full markdown document. Explore the codebase if you need more information to fulfill the user's request."

    result = agent.invoke({"messages": [HumanMessage(content=user_input)]})

    content = result["messages"][-1].content

    refine_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert technical writer. Strip any conversational filler or meta-commentary and return only the clean expanded markdown content."),
        ("user", "Expanded Content:\n{content}")
    ])

    refine_chain = refine_prompt | llm | StrOutputParser()
    return refine_chain.invoke({"content": content})
