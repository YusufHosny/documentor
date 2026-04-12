def get_system_prompt(context_instruction: str, style_guide: str) -> str:
    return f"""You are an expert technical writer. Create a comprehensive, well-structured markdown document. {context_instruction}
Output ONLY the raw markdown content. NEVER wrap the output in markdown code blocks (guards) like ```markdown, and do not include the filename.
Follow this style guide:
{style_guide}"""

def get_user_prompt(context_content: str, filename: str, description: str, agent_instruction: str = "") -> str:
    return f"""{context_content}
Please generate the {filename} file based on the following description: '{description}'. {agent_instruction}"""
