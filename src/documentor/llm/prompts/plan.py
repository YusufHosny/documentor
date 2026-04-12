def get_system_prompt(context_instruction: str, style_guide: str, existing_docs: str) -> str:
    return f"""You are an expert technical documentation architect. Your goal is to analyze the project codebase and suggest a list of documentation files that should be generated to provide a complete understanding of the codebase. {context_instruction}
The current documentation style guide is:
{style_guide}

The following files are already documented and you should NOT duplicate them:
{existing_docs}"""

def get_user_prompt(context_content: str) -> str:
    return f"""{context_content}
Please explore the codebase and suggest documentation files. When you have a good understanding of the project, provide a summary of your suggestions."""
