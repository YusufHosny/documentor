from langchain_core.language_models.chat_models import BaseChatModel
from documentor.core.config import Config

def get_llm(config: Config) -> BaseChatModel:
    """Initializes the appropriate LangChain LLM based on config."""
    provider = config.provider.lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=config.model)

    elif provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=config.model, vertexai=True)

    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=config.model)

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
