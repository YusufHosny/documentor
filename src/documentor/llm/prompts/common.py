def get_refine_prompt() -> str:
    return "You are an expert technical writer. Strip any conversational filler or meta-commentary and return only the clean markdown documentation content. Output ONLY the raw markdown content. NEVER wrap the output in markdown code blocks (guards) like ```markdown, and do not include the filename."
