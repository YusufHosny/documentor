from typing import List
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config, DocItem
from documentor.llm.client import get_llm
from documentor.core.writer import Writer
from .tools import get_tools

def agent_generate_docs(config: Config, docs_to_generate: List[DocItem]) -> List[str]:
    """Generates documentation by dynamically exploring the codebase for each document."""
    llm = get_llm(config)
    tools = get_tools(config)
    writer = Writer(config)
    generated_files = []

    system_message_base = f"""You are an expert technical writer. Your goal is to create a comprehensive, well-structured markdown document by exploring the codebase to find relevant information.
You can use the provided tools to browse the files.
Follow this style guide:
{config.get_style_guide()}"""

    agent = create_agent(llm, tools, system_prompt=system_message_base)

    for doc in docs_to_generate:
        user_input = f"Please generate the {doc.filename} file with the following type '{doc.type}' and description: '{doc.description}'. Explore the codebase as needed."

        result = agent.invoke({"messages": [HumanMessage(content=user_input)]})
        content = result["messages"][-1].content

        refine_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert technical writer. Strip any conversational filler or meta-commentary and return only the clean markdown documentation content."),
            ("user", "Documentation Content:\n{content}")
        ])

        refine_chain = refine_prompt | llm | StrOutputParser()
        final_content = refine_chain.invoke({"content": content})

        final_path = writer.write(doc.filename, final_content)
        generated_files.append(final_path)

    return generated_files
