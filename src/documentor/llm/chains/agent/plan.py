from typing import List
from langchain_core.messages import HumanMessage
from documentor.llm.client import get_llm, create_retryable_agent, retryable
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config, DocList, DocItem
from documentor.llm.client import get_llm
from documentor.llm.prompts.plan import get_system_prompt as plan_system, get_user_prompt as plan_user
from documentor.llm.prompts.infer import get_system_prompt as infer_system, get_user_prompt as infer_user
from .tools import get_tools


def agent_generate_plan(config: Config, existing_docs: List[DocItem]) -> List[DocItem]:
    """Determines which documents to generate by dynamically exploring the codebase."""
    llm = get_llm(config)
    tools = get_tools(config)

    existing_docs_str = "\n".join(
        [f"- {f.filename} ({f.description})" for f in existing_docs]
    )

    system_message = plan_system(
        context_instruction="Your goal is to analyze the project codebase and suggest a list of documentation files that should be generated to provide a complete understanding of the codebase. You can explore the codebase using the provided tools.",
        style_guide=config.get_style_guide(),
        existing_docs=existing_docs_str,
    )

    agent = create_retryable_agent(llm, tools, system_prompt=system_message)

    user_input = plan_user(context_content="")

    result = agent.invoke({"messages": [HumanMessage(content=user_input)]})
    findings = result["messages"][-1].content

    structured_llm = llm.with_structured_output(DocList)

    final_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert technical documentation architect. Based on the exploration findings, suggest a list of documentation files.",
            ),
            (
                "user",
                "Exploration Findings:\n{findings}\n\nExisting Docs:\n{existing_docs}",
            ),
        ]
    )

    chain = retryable(final_prompt | structured_llm)

    try:
        response: DocList = chain.invoke(
            {"findings": findings, "existing_docs": existing_docs_str}
        )  # type: ignore

        existing_filenames = {f.filename.lower() for f in existing_docs}
        pruned_files = [
            f for f in response.files if f.filename.lower() not in existing_filenames
        ]

        return pruned_files
    except Exception:
        return []


def agent_infer_doc_info(filename: str, config: Config) -> DocItem:
    """Infers description for a specific file by exploring context agentically."""
    llm = get_llm(config)
    tools = get_tools(config)

    system_message = infer_system(
        context_instruction=f"Your goal is to infer a description for the file: {filename}. You can explore the project codebase using the provided tools to understand what this file should document."
    )

    agent = create_retryable_agent(llm, tools, system_prompt=system_message)

    user_input = infer_user(
        filename_content=f"Filename: {filename}",
        exploration_findings="",
    ).replace(
        "Based on the project context",
        "Explore the project codebase to understand what the file should document",
    )

    result = agent.invoke({"messages": [HumanMessage(content=user_input)]})
    findings = result["messages"][-1].content

    structured_llm = llm.with_structured_output(DocItem)

    final_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert technical documentation architect. Based on the following exploration, infer the description for the document.",
            ),
            ("user", "Filename: {filename}\n\nExploration Findings:\n{findings}"),
        ]
    )

    chain = retryable(final_prompt | structured_llm)

    try:
        response: DocItem = chain.invoke({"filename": filename, "findings": findings})  # type: ignore
        return response
    except Exception:
        return DocItem(filename=filename, description="Auto-inferred documentation")
