import os
import sys
import uuid
from typing import Any, Sequence
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain.agents.middleware import model_retry
from langchain.agents import create_agent as _create_agent
from documentor.core.config import Config

CLI_RUN_ID = str(uuid.uuid4())


def retryable(chain: Runnable) -> Runnable:
    """Wraps a LangChain chain/Runnable to retry automatically on failure."""
    return chain.with_retry(stop_after_attempt=6)


def create_retryable_agent(
    llm: BaseChatModel, tools: Sequence[Any], system_prompt: Any
) -> Runnable:
    """Wraps create_agent to automatically inject model retry middleware."""
    middleware = [model_retry.ModelRetryMiddleware(max_retries=6)]
    return _create_agent(llm, tools, system_prompt=system_prompt, middleware=middleware)


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
    )  # type: ignore
