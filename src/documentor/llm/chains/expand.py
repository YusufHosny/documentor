from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from documentor.core.config import Config
from documentor.llm.client import get_llm, retryable
from documentor.llm.prompts.expand import get_system_prompt, get_user_prompt


def expand_doc(scrappy_notes: str, description: str, config: Config) -> str:
    """Expands scrappy notes into a full document."""
    llm = get_llm(config)

    system_msg = get_system_prompt(
        description=description,
        context_instruction="",
        style_guide=config.get_style_guide(),
    )
    user_msg = get_user_prompt(notes=scrappy_notes, agent_instruction="")

    prompt = ChatPromptTemplate.from_messages(
        [("system", "{system_msg}"), ("user", "{user_msg}")]
    )

    chain = retryable(prompt | llm | StrOutputParser())

    return chain.invoke({"system_msg": system_msg, "user_msg": user_msg})
