import os
import sys
import uuid
from langchain_core.language_models.chat_models import BaseChatModel
from documentor.core.config import Config

CLI_RUN_ID = str(uuid.uuid4())

def get_llm(config: Config) -> BaseChatModel:
    """Initializes the appropriate LangChain LLM based on config with tracing metadata."""
    if "LANGCHAIN_PROJECT" not in os.environ:
        os.environ["LANGCHAIN_PROJECT"] = "documentor"

    provider = config.provider.lower()

    command = "unknown"
    if len(sys.argv) > 1:
        command = sys.argv[1]

    llm: BaseChatModel
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=config.model)

    elif provider in ["google", "vertexai"]:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model=config.model, vertexai=True)

    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=config.model)

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

    return llm.with_config(
        config={
            "tags": [command, provider],
            "metadata": {
                "command": command,
                "cli_run_id": CLI_RUN_ID,
                "provider": provider,
                "model": config.model,
                "project_name": "documentor",
            },
        }
    ) # type: ignore
