from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from documentor.core.config import Config
from documentor.llm.client import get_llm

def expand_doc(scrappy_notes: str, doc_type: str, config: Config) -> str:
    """Expands scrappy notes into a full document."""
    llm = get_llm(config)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert technical writer. Expand the following scrappy notes into a complete, well-formatted markdown document of type: {doc_type}. Maintain the original intent but improve flow, structure, and professional tone. Output ONLY the markdown content, without any extra conversation or markdown formatting ticks."),
        ("user", "Scrappy Notes:\n{notes}\n\nPlease expand into a full document.")
    ])

    chain = prompt | llm | StrOutputParser()

    return chain.invoke({
        "doc_type": doc_type,
        "notes": scrappy_notes
    })
