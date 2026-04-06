from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from documentor.core.config import Config
from documentor.llm.client import get_llm, retryable
from documentor.llm.prompts import get_prompt_parts


def edit_doc(current_content: str, comments: str, config: Config) -> str:
    """Edits an existing document based on user comments."""
    llm = get_llm(config)

    prompts = get_prompt_parts("edit")

    prompt = ChatPromptTemplate.from_messages(
        [("system", prompts["system_prompt"]), ("user", prompts["user_prompt"])]
    )

    chain = retryable(prompt | llm | StrOutputParser())

    return chain.invoke(
        {
            "context_instruction": "",
            "style_guide": config.get_style_guide(),
            "current_content": current_content,
            "comments": comments,
            "agent_instruction": "",
        }
    )
