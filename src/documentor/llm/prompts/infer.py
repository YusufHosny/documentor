def get_system_prompt(context_instruction: str) -> str:
    return f"""You are an expert technical documentation architect. {context_instruction}"""

def get_user_prompt(filename_content: str, exploration_findings: str) -> str:
    return f"""{filename_content}
{exploration_findings}
Based on the project context, infer a brief description for the file."""
