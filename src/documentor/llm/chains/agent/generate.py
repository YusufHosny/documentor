from typing import List
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config, DocItem
from documentor.llm.client import get_llm
from documentor.core.writer import Writer
from documentor.llm.prompts import get_prompt_parts
from .tools import get_tools

def agent_generate_docs(config: Config, docs_to_generate: List[DocItem]) -> List[str]:
    """Generates documentation by dynamically exploring the codebase for each document."""
    llm = get_llm(config)
    tools = get_tools(config)
    writer = Writer(config)
    generated_files = []

    prompts = get_prompt_parts("generate")
    common_prompts = get_prompt_parts("common")

    system_message_base = prompts["system_prompt"].format(
        context_instruction="Your goal is to explore the codebase to find relevant information. You can use the provided tools to browse the files.",
        style_guide=config.get_style_guide()
    )

    agent = create_agent(llm, tools, system_prompt=system_message_base)

    for doc in docs_to_generate:
        user_input = prompts["user_prompt"].format(
            context_content="",
            filename=doc.filename,
            doc_type=doc.type,
            description=doc.description,
            agent_instruction="Explore the codebase as needed."
        )

        result = agent.invoke({"messages": [HumanMessage(content=user_input)]})
        content = result["messages"][-1].content

        refine_prompt = ChatPromptTemplate.from_messages([
            ("system", common_prompts["refine_prompt"]),
            ("user", "Documentation Content:\n{content}")
        ])

        refine_chain = refine_prompt | llm | StrOutputParser()
        final_content = refine_chain.invoke({"content": content})

        final_path = writer.write(doc.filename, final_content)
        generated_files.append(final_path)

    return generated_files
