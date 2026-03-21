from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from documentor.core.config import Config
from documentor.llm.client import get_llm

def edit_doc(current_content: str, comments: str, config: Config) -> str:
    """Edits an existing document based on user comments."""
    llm = get_llm(config)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert technical writer. You are reviewing an existing markdown document. Update it based on the user's comments. Output ONLY the updated markdown content, without any extra conversation or markdown formatting ticks (unless they are part of the content itself)."),
        ("system", "This is the style guide to follow:\n{style_guide}"),
        ("user", "Current Document:\n{current_content}\n\nUser Comments:\n{comments}\n\nPlease provide the updated document.")
    ])

    chain = prompt | llm | StrOutputParser()

    return chain.invoke({
        "current_content": current_content,
        "style_guide": config.get_style_guide(),
        "comments": comments
    })
