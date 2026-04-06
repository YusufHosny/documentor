from typing import List
from langchain_core.messages import HumanMessage
from documentor.llm.client import get_llm, create_retryable_agent, retryable
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config, DocList, DocItem
from documentor.llm.client import get_llm
from documentor.llm.prompts import get_prompt_parts
from .tools import get_tools


def agent_generate_plan(config: Config) -> List[DocItem]:
    """Determines which documents to generate by dynamically exploring the codebase."""
    llm = get_llm(config)
    tools = get_tools(config)

    prompts = get_prompt_parts("plan")

    required_files_str = "\n".join(
        [f"- {f.filename} (Type: {f.type})" for f in config.required_files]
    )

    system_message = prompts["system_prompt"].format(
        context_instruction="Your goal is to analyze the project codebase and suggest a list of documentation files that should be generated to provide a complete understanding of the codebase. You can explore the codebase using the provided tools.",
        style_guide=config.get_style_guide(),
        required_files=required_files_str,
    )

    agent = create_retryable_agent(llm, tools, system_prompt=system_message)

    user_input = prompts["user_prompt"].format(context_content="")

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
                "Exploration Findings:\n{findings}\n\nRequired Files:\n{required_files}",
            ),
        ]
    )

    chain = retryable(final_prompt | structured_llm)

    try:
        response: DocList = chain.invoke(
            {"findings": findings, "required_files": required_files_str}
        )  # type: ignore

        required_filenames = {f.filename.lower() for f in config.required_files}
        pruned_files = [
            f for f in response.files if f.filename.lower() not in required_filenames
        ]

        return pruned_files
    except Exception:
        return []


def agent_infer_doc_info(filename: str, config: Config) -> DocItem:
    """Infers type and description for a specific file by exploring context agentically."""
    llm = get_llm(config)
    tools = get_tools(config)

    prompts = get_prompt_parts("infer")

    system_message = prompts["system_prompt"].format(
        context_instruction=f"Your goal is to infer the most appropriate documentation type and description for the file: {filename}. You can explore the project codebase using the provided tools to understand what this file should document."
    )

    agent = create_retryable_agent(llm, tools, system_prompt=system_message)

    user_input = (
        prompts["user_prompt"]
        .format(
            filename_content=f"Filename: {filename}",
            exploration_findings="",
        )
        .replace(
            "Based on the project context",
            "Explore the project codebase to understand what the file should document",
        )
    )

    result = agent.invoke({"messages": [HumanMessage(content=user_input)]})
    findings = result["messages"][-1].content

    structured_llm = llm.with_structured_output(DocItem)

    final_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert technical documentation architect. Based on the following exploration, infer the type and description for the document.",
            ),
            ("user", "Filename: {filename}\n\nExploration Findings:\n{findings}"),
        ]
    )

    chain = retryable(final_prompt | structured_llm)

    try:
        response: DocItem = chain.invoke({"filename": filename, "findings": findings})  # type: ignore
        return response
    except Exception:
        return DocItem(
            filename=filename, type="General", description="Auto-inferred documentation"
        )
