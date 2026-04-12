from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate
from documentor.core.config import Config, DocList, DocItem
from documentor.llm.client import get_llm, retryable
from documentor.llm.prompts.plan import get_system_prompt as plan_system, get_user_prompt as plan_user
from documentor.llm.prompts.infer import get_system_prompt as infer_system, get_user_prompt as infer_user


def generate_plan(
    context: List[Dict[str, str]], config: Config, existing_docs: List[DocItem]
) -> List[DocItem]:
    """Determines which documents to generate based on project context."""
    context_str = "\n\n".join(
        [f"--- File: {f['path']} ---\n{f['content']}" for f in context]
    )
    existing_docs_str = "\n".join(
        [f"- {f.filename} ({f.description})" for f in existing_docs]
    )

    system_msg = plan_system(
        context_instruction="Analyze the project context and suggest a list of documentation files that should be generated to provide a complete understanding of the codebase.",
        style_guide=config.get_style_guide(),
        existing_docs=existing_docs_str
    )
    user_msg = plan_user(
        context_content=f"Here is the project context:\n{context_str}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_msg}"),
        ("user", "{user_msg}")
    ])

    llm = get_llm(config)
    structured = llm.with_structured_output(DocList)
    chain = retryable(prompt | structured)

    try:
        response: DocList = chain.invoke({"system_msg": system_msg, "user_msg": user_msg})  # type: ignore

        existing_filenames = {f.filename.lower() for f in existing_docs}
        pruned_files = [
            f for f in response.files if f.filename.lower() not in existing_filenames
        ]

        return pruned_files
    except Exception:
        return []


def infer_doc_info(
    filename: str, context: List[Dict[str, str]], config: Config
) -> DocItem:
    """Infers description for a specific file based on context."""
    context_str = "\n\n".join(
        [f"--- File: {f['path']} ---\n{f['content']}" for f in context]
    )

    system_msg = infer_system(
        context_instruction="Based on the project context, infer a brief description for the file."
    )
    user_msg = infer_user(
        filename_content=f"Filename: {filename}",
        exploration_findings=f"Here is the project context:\n{context_str}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_msg}"),
        ("user", "{user_msg}")
    ])

    llm = get_llm(config)
    structured = llm.with_structured_output(DocItem)
    chain = retryable(prompt | structured)

    try:
        response: DocItem = chain.invoke({"system_msg": system_msg, "user_msg": user_msg})  # type: ignore
        return response
    except Exception:
        return DocItem(filename=filename, description="Auto-inferred documentation")
