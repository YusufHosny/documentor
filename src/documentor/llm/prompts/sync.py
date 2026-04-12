def get_system_prompt(context_instruction: str, style_guide: str) -> str:
    return f"""You are an expert technical writer. You are updating an existing markdown document because the underlying source code has changed. Your goal is to synchronize the document with the new source code state. Maintain the existing structure and style, but update any descriptions, examples, or references that are no longer accurate. {context_instruction}
Output ONLY the raw markdown content. NEVER wrap the output in markdown code blocks (guards) like ```markdown, and do not include the filename.
Follow this style guide:
{style_guide}"""

def get_user_prompt(diff_content: str, current_content: str, context_content: str, agent_instruction: str = "") -> str:
    return f"""{diff_content}
Current Document Content:
{current_content}

New Project Context:
{context_content}

Please provide the updated document. {agent_instruction}"""
