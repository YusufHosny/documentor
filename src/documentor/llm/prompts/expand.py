def get_system_prompt(description: str, context_instruction: str, style_guide: str) -> str:
    return f"""You are an expert technical writer. Your goal is to expand scrappy notes into a complete, well-formatted markdown document with the following description: {description}. Maintain the original intent but improve flow, structure, and professional tone. {context_instruction}
Output ONLY the raw markdown content. NEVER wrap the output in markdown code blocks (guards) like ```markdown, and do not include the filename.
Follow this style guide:
{style_guide}"""

def get_user_prompt(notes: str, agent_instruction: str = "") -> str:
    return f"""Scrappy Notes:
{notes}

Please expand these notes into a full markdown document. {agent_instruction}"""
