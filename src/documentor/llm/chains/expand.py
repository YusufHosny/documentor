from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from documentor.core.config import Config
from documentor.llm.client import get_llm, retryable
from documentor.llm.prompts import get_prompt_parts


def expand_doc(scrappy_notes: str, doc_type: str, config: Config) -> str:
    """Expands scrappy notes into a full document."""
    llm = get_llm(config)

    prompts = get_prompt_parts("expand")

    prompt = ChatPromptTemplate.from_messages(
        [("system", prompts["system_prompt"]), ("user", prompts["user_prompt"])]
    )

    chain = retryable(prompt | llm | StrOutputParser())

    return chain.invoke(
        {
            "doc_type": doc_type,
            "context_instruction": "",
            "style_guide": config.get_style_guide(),
            "notes": scrappy_notes,
            "agent_instruction": "",
        }
    )
