import pytest
from unittest.mock import AsyncMock
from documentor.core.config import Config, DocItem
from documentor.core.state import StateManager
from documentor.llm.chains import (
    async_generate_docs,
    generate_plan,
    edit_doc,
    expand_doc,
    infer_doc_info,
    async_sync_docs,
)

@pytest.fixture
def mock_config():
    return Config(
        provider="vertexai",
        model="test-model",
        docs_dir="docs",
        include_footer=False
    )

@pytest.fixture
def mock_state_manager(mock_config):
    return StateManager(mock_config)

@pytest.fixture
def sample_context():
    return [
        {"path": "src/main.py", "content": "def main(): pass"},
        {"path": "src/utils.py", "content": "def helper(): pass"}
    ]

from documentor.llm.client import get_llm, retryable, create_retryable_agent
import sys

def test_client_get_llm(mocker):
    config_openai = Config(provider="openai", model="gpt-4o")
    
    mock_openai = mocker.patch("langchain_openai.ChatOpenAI")
    
    mocker.patch.object(sys, 'argv', ['documentor', 'plan'])
    
    llm1 = get_llm(config_openai)
    mock_openai.assert_called_once_with(model="gpt-4o")
    
    # check that tags and metadata were injected by checking the with_config call (mocked out implicitly if we mock the llm class correctly, but let's just make sure no exceptions happen)

    config_google = Config(provider="vertexai", model="gemini-pro")
    mock_google = mocker.patch("langchain_google_genai.ChatGoogleGenerativeAI")
    
    llm2 = get_llm(config_google)
    mock_google.assert_called_once_with(model="gemini-pro", vertexai=True)

    config_ollama = Config(provider="ollama", model="llama3")
    mock_ollama = mocker.patch("langchain_ollama.ChatOllama")
    
    llm3 = get_llm(config_ollama)
    mock_ollama.assert_called_once_with(model="llama3")

def test_client_get_llm_unsupported():
    config = Config(provider="openai", model="test")
    config.provider = "fake_provider" # bypass pydantic literal checking for the sake of covering the ValueError
    with pytest.raises(ValueError):
        get_llm(config)

def test_generate_plan_error(mocker, mock_config, sample_context):
    mock_llm = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.plan.get_llm", return_value=mock_llm)
    
    mock_chain = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.plan.retryable", return_value=mock_chain)
    
    # Simulate an error during invocation
    mock_chain.invoke.side_effect = Exception("LLM Error")
    
    docs = generate_plan(sample_context, mock_config, [])
    assert docs == []

def test_expand_doc(mocker, mock_config):
    mock_llm = mocker.MagicMock()
    mock_chain = mocker.MagicMock()

    mocker.patch("documentor.llm.chains.expand.get_llm", return_value=mock_llm)
    mocker.patch("documentor.llm.chains.expand.retryable", return_value=mock_chain)

    mock_chain.invoke.return_value = "Expanded Document Content"

    result = expand_doc("- bullet point", "make it long", mock_config)
    assert result == "Expanded Document Content"

def test_infer_doc_info(mocker, mock_config, sample_context):
    mock_llm = mocker.MagicMock()
    mock_structured = mocker.MagicMock()
    mock_chain = mocker.MagicMock()

    mocker.patch("documentor.llm.chains.plan.get_llm", return_value=mock_llm)
    mock_llm.with_structured_output.return_value = mock_structured

    mocker.patch("documentor.llm.chains.plan.retryable", return_value=mock_chain)

    from documentor.core.config import DocItem
    mock_chain.invoke.return_value = DocItem(filename="src/main.py", description="Main entry point")

    doc = infer_doc_info("src/main.py", sample_context, mock_config)

    assert doc.filename == "src/main.py"
    assert doc.description == "Main entry point"

def test_infer_doc_info_error(mocker, mock_config, sample_context):
    mock_llm = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.plan.get_llm", return_value=mock_llm)
    
    mock_chain = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.plan.retryable", return_value=mock_chain)
    
    mock_chain.invoke.side_effect = Exception("LLM Error")
    
    doc = infer_doc_info("src/main.py", sample_context, mock_config)
    
    assert doc.filename == "src/main.py"
    assert doc.description == "Auto-inferred documentation"

@pytest.mark.asyncio
async def test_async_sync_docs(mocker, mock_config, mock_state_manager, sample_context):
    mock_llm = mocker.MagicMock()
    mock_chain = AsyncMock()

    mocker.patch("documentor.llm.chains.sync.get_llm", return_value=mock_llm)
    mocker.patch("documentor.llm.chains.sync.retryable", return_value=mock_chain)

    mock_response = mocker.MagicMock()
    mock_response.content = "Synced Doc"
    mock_chain.ainvoke.return_value = mock_response

    mocker.patch("documentor.core.writer.Writer.write", return_value="docs/test.md")

    docs_to_sync = [
        {
            "filepath": "docs/test.md",
            "current_content": "old content",
            "diff": "some changes",
            "stale_doc_state": mocker.MagicMock()
        }
    ]

    synced_files = await async_sync_docs(
        context=sample_context,
        config=mock_config,
        state_manager=mock_state_manager,
        docs_to_sync=docs_to_sync
    )

    assert len(synced_files) == 1
    assert synced_files[0] == "docs/test.md"
    mock_chain.ainvoke.assert_called()
    mock_llm = mocker.MagicMock()
    mock_structured = mocker.MagicMock()
    mock_chain = mocker.MagicMock()

    mocker.patch("documentor.llm.chains.plan.get_llm", return_value=mock_llm)
    mock_llm.with_structured_output.return_value = mock_structured

    mocker.patch("documentor.llm.chains.plan.retryable", return_value=mock_chain)

    from documentor.core.config import DocList
    mock_chain.invoke.return_value = DocList(files=[
        DocItem(filename="api.md", description="API Reference")
    ])

    docs = generate_plan(sample_context, mock_config, [])

    assert len(docs) == 1
    assert docs[0].filename == "api.md"
    assert docs[0].description == "API Reference"

def test_edit_doc(mocker, mock_config):
    mock_llm = mocker.MagicMock()
    mock_chain = mocker.MagicMock()

    mocker.patch("documentor.llm.chains.edit.get_llm", return_value=mock_llm)
    mocker.patch("documentor.llm.chains.edit.retryable", return_value=mock_chain)

    mock_chain.invoke.return_value = "New Document Content"

    result = edit_doc("Old Content", "Make it better", mock_config)
    assert result == "New Document Content"

@pytest.mark.asyncio
async def test_async_generate_docs(mocker, mock_config, mock_state_manager, sample_context):
    mock_llm = mocker.MagicMock()
    mock_chain = AsyncMock()

    mocker.patch("documentor.llm.chains.generate.get_llm", return_value=mock_llm)
    mocker.patch("documentor.llm.chains.generate.retryable", return_value=mock_chain)

    mock_response = mocker.MagicMock()
    mock_response.content = "# Autogenerated Doc"
    mock_chain.ainvoke.return_value = mock_response

    mocker.patch("documentor.core.writer.Writer.write", return_value="docs/main.md")

    docs_to_generate = [DocItem(filename="main.md", description="Test Description")]

    generated_files = await async_generate_docs(
        context=sample_context,
        config=mock_config,
        state_manager=mock_state_manager,
        docs_to_generate=docs_to_generate
    )

    assert len(generated_files) == 1
    assert generated_files[0] == "docs/main.md"
    mock_chain.ainvoke.assert_called()
