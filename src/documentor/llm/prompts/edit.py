def get_system_prompt(context_instruction: str, style_guide: str) -> str:
    return f"""You are an expert technical writer. Your goal is to edit an existing markdown document based on user comments. {context_instruction}
Output ONLY the raw markdown content. NEVER wrap the output in markdown code blocks (guards) like ```markdown, and do not include the filename.
Follow this style guide:
{style_guide}"""

def get_user_prompt(current_content: str, comments: str, agent_instruction: str = "") -> str:
    return f"""Current Document Content:
{current_content}

User Comments:
{comments}

Please provide the updated document. {agent_instruction}"""
