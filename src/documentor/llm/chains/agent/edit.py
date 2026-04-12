from langchain_core.messages import HumanMessage
from documentor.llm.client import get_llm, create_retryable_agent, retryable
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config
from documentor.llm.client import get_llm
from documentor.llm.prompts.edit import get_system_prompt, get_user_prompt
from documentor.llm.prompts.common import get_refine_prompt
from .tools import get_tools


def agent_edit_doc(current_content: str, comments: str, config: Config) -> str:
    """Edits an existing document by dynamically exploring the codebase as needed."""
    llm = get_llm(config)
    tools = get_tools(config)

    system_message = get_system_prompt(
        context_instruction="You can explore the codebase to ensure your edits are accurate using the provided tools.",
        style_guide=config.get_style_guide(),
    )

    agent = create_retryable_agent(llm, tools, system_prompt=system_message)

    user_input = get_user_prompt(
        current_content=current_content,
        comments=comments,
        agent_instruction="Explore the codebase if you need more information to fulfill the user's request.",
    )

    result = agent.invoke({"messages": [HumanMessage(content=user_input)]})

    content = result["messages"][-1].content

    refine_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system_msg}"),
            ("user", "Updated Content:\n{content}"),
        ]
    )

    refine_chain = retryable(refine_prompt | llm | StrOutputParser())
    return refine_chain.invoke({"system_msg": get_refine_prompt(), "content": content})
