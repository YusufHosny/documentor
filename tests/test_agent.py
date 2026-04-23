import os
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from documentor.core.config import Config, DocItem, DocList
from documentor.core.state import StateManager
from langchain_core.messages import HumanMessage

from documentor.llm.chains.agent.tools import get_tools
from documentor.llm.chains.agent.generate import agent_generate_docs, async_agent_generate_docs
from documentor.llm.chains.agent.plan import agent_generate_plan, agent_infer_doc_info
from documentor.llm.chains.agent.edit import agent_edit_doc
from documentor.llm.chains.agent.expand import agent_expand_doc
from documentor.llm.chains.agent.sync import agent_sync_doc, async_agent_sync_docs

@pytest.fixture
def mock_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    
    config = Config(
        provider="vertexai",
        model="test-model",
        docs_dir="docs",
        include_footer=False
    )
    
    yield config

@pytest.fixture
def mock_state_manager(mock_config):
    return StateManager(mock_config)

def test_agent_tools(mock_config, tmp_path):
    tools = get_tools(mock_config)
    grep_tool = next(t for t in tools if t.name == "grep_files")
    list_tool = next(t for t in tools if t.name == "list_files")
    read_tool = next(t for t in tools if t.name == "read_file")

    # Create dummy files
    (tmp_path / "main.py").write_text("def hello():\n    print('world')\n")
    (tmp_path / "test.txt").write_text("just some text with world in it")

    # Test grep_files
    matches = grep_tool.invoke({"expression": "world"})
    assert len(matches) == 2
    assert any("main.py" in m for m in matches)
    assert any("test.txt" in m for m in matches)

    # Test invalid regex
    invalid_matches = grep_tool.invoke({"expression": "["})
    assert len(invalid_matches) == 1
    assert "Invalid regular expression" in invalid_matches[0]

    # Test no matches
    no_matches = grep_tool.invoke({"expression": "nonexistent_string"})
    assert len(no_matches) == 1
    assert "No matches found" in no_matches[0]

    # Test list_files
    files = list_tool.invoke({})
    assert "main.py" in files
    assert "test.txt" in files

    # Test read_file
    content = read_tool.invoke({"path": "main.py"})
    assert "def hello():" in content

    # Test read nonexistent file
    error_content = read_tool.invoke({"path": "fake.py"})
    assert "Error: Could not read file" in error_content

def test_agent_generate_docs(mocker, mock_config, mock_state_manager):
    # Mocking
    mock_llm = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.generate.get_llm", return_value=mock_llm)
    
    mock_agent = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.generate.create_retryable_agent", return_value=mock_agent)
    
    mock_refine_chain = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.generate.retryable", return_value=mock_refine_chain)
    
    # Setup mock responses
    mock_agent.invoke.return_value = {"messages": [HumanMessage(content="Exploration data")]}
    mock_refine_chain.invoke.return_value = "Refined Document Content"
    
    mocker.patch("documentor.core.writer.Writer.write", return_value="docs/main.md")
    
    docs_to_generate = [DocItem(filename="main.md", description="Test")]
    result = agent_generate_docs(mock_config, mock_state_manager, docs_to_generate)
    
    assert len(result) == 1
    assert result[0] == "docs/main.md"
    mock_agent.invoke.assert_called()
    mock_refine_chain.invoke.assert_called()

@pytest.mark.asyncio
async def test_async_agent_generate_docs(mocker, mock_config, mock_state_manager):
    mock_llm = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.generate.get_llm", return_value=mock_llm)
    
    mock_agent = AsyncMock()
    mocker.patch("documentor.llm.chains.agent.generate.create_retryable_agent", return_value=mock_agent)
    
    mock_refine_chain = AsyncMock()
    mocker.patch("documentor.llm.chains.agent.generate.retryable", return_value=mock_refine_chain)
    
    mock_agent.ainvoke.return_value = {"messages": [HumanMessage(content="Exploration data")]}
    mock_refine_chain.ainvoke.return_value = "Refined Async Document Content"
    
    mocker.patch("documentor.core.writer.Writer.write", return_value="docs/async.md")
    
    docs_to_generate = [DocItem(filename="async.md", description="Test Async")]
    result = await async_agent_generate_docs(mock_config, mock_state_manager, docs_to_generate)
    
    assert len(result) == 1
    assert result[0] == "docs/async.md"
    mock_agent.ainvoke.assert_called()
    mock_refine_chain.ainvoke.assert_called()

def test_agent_generate_plan(mocker, mock_config):
    mock_llm = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.plan.get_llm", return_value=mock_llm)
    
    mock_agent = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.plan.create_retryable_agent", return_value=mock_agent)
    mock_agent.invoke.return_value = {"messages": [HumanMessage(content="Found api routes")]}
    
    mock_chain = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.plan.retryable", return_value=mock_chain)
    
    mock_chain.invoke.return_value = DocList(files=[
        DocItem(filename="api.md", description="API Reference")
    ])
    
    result = agent_generate_plan(mock_config, [])
    
    assert len(result) == 1
    assert result[0].filename == "api.md"
    assert result[0].description == "API Reference"

def test_agent_generate_plan_error(mocker, mock_config):
    mock_llm = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.plan.get_llm", return_value=mock_llm)
    
    mock_agent = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.plan.create_retryable_agent", return_value=mock_agent)
    mock_agent.invoke.return_value = {"messages": [HumanMessage(content="Found api routes")]}
    
    mock_chain = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.plan.retryable", return_value=mock_chain)
    
    # Simulate LLM failure during parsing
    mock_chain.invoke.side_effect = Exception("LLM Agent Error")
    
    result = agent_generate_plan(mock_config, [])
    assert result == []

def test_agent_infer_doc_info(mocker, mock_config):
    mock_llm = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.plan.get_llm", return_value=mock_llm)
    
    mock_agent = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.plan.create_retryable_agent", return_value=mock_agent)
    mock_agent.invoke.return_value = {"messages": [HumanMessage(content="It's an api file")]}
    
    mock_chain = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.plan.retryable", return_value=mock_chain)
    
    mock_chain.invoke.return_value = DocItem(filename="api.py", description="The main API router")
    
    result = agent_infer_doc_info("api.py", mock_config)
    
    assert result.filename == "api.py"
    assert result.description == "The main API router"

def test_agent_infer_doc_info_error(mocker, mock_config):
    mock_llm = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.plan.get_llm", return_value=mock_llm)
    
    mock_agent = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.plan.create_retryable_agent", return_value=mock_agent)
    mock_agent.invoke.return_value = {"messages": [HumanMessage(content="It's an api file")]}
    
    mock_chain = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.plan.retryable", return_value=mock_chain)
    
    mock_chain.invoke.side_effect = Exception("LLM Agent Error")
    
    result = agent_infer_doc_info("api.py", mock_config)
    
    assert result.filename == "api.py"
    assert result.description == "Auto-inferred documentation"

def test_agent_edit_doc(mocker, mock_config):
    mock_llm = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.edit.get_llm", return_value=mock_llm)
    
    mock_agent = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.edit.create_retryable_agent", return_value=mock_agent)
    mock_agent.invoke.return_value = {"messages": [HumanMessage(content="Explored and found updates")]}
    
    mock_refine_chain = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.edit.retryable", return_value=mock_refine_chain)
    mock_refine_chain.invoke.return_value = "Newly Edited Content"
    
    result = agent_edit_doc("Old Content", "Update this", mock_config)
    
    assert result == "Newly Edited Content"

def test_agent_expand_doc(mocker, mock_config):
    mock_llm = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.expand.get_llm", return_value=mock_llm)
    
    mock_agent = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.expand.create_retryable_agent", return_value=mock_agent)
    mock_agent.invoke.return_value = {"messages": [HumanMessage(content="Expanded details found in code")]}
    
    mock_refine_chain = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.expand.retryable", return_value=mock_refine_chain)
    mock_refine_chain.invoke.return_value = "Expanded Content"
    
    result = agent_expand_doc("Short bullet", "Long description", mock_config)
    
    assert result == "Expanded Content"

def test_agent_sync_doc(mocker, mock_config):
    mock_llm = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.sync.get_llm", return_value=mock_llm)
    
    mock_agent = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.sync.create_retryable_agent", return_value=mock_agent)
    mock_agent.invoke.return_value = {"messages": [HumanMessage(content="Synced based on exploration")]}
    
    mock_refine_chain = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.sync.retryable", return_value=mock_refine_chain)
    mock_refine_chain.invoke.return_value = "Synced Content"
    
    result = agent_sync_doc("Old Content", mock_config, diff="some diff string")
    assert result == "Synced Content"

@pytest.mark.asyncio
async def test_async_agent_sync_docs(mocker, mock_config, mock_state_manager):
    mock_llm = mocker.MagicMock()
    mocker.patch("documentor.llm.chains.agent.sync.get_llm", return_value=mock_llm)
    
    mock_agent = AsyncMock()
    mocker.patch("documentor.llm.chains.agent.sync.create_retryable_agent", return_value=mock_agent)
    mock_agent.ainvoke.return_value = {"messages": [HumanMessage(content="Exploration data sync")]}
    
    mock_refine_chain = AsyncMock()
    mocker.patch("documentor.llm.chains.agent.sync.retryable", return_value=mock_refine_chain)
    mock_refine_chain.ainvoke.return_value = "Refined Async Synced Document"
    
    mocker.patch("documentor.core.writer.Writer.write", return_value="docs/async_sync.md")
    
    docs_to_sync = [
        {
            "filepath": "docs/async_sync.md",
            "current_content": "old content",
            "diff": "some changes",
            "stale_doc_state": mocker.MagicMock()
        }
    ]
    
    result = await async_agent_sync_docs(mock_config, mock_state_manager, docs_to_sync)
    
    assert len(result) == 1
    assert result[0] == "docs/async_sync.md"
    mock_agent.ainvoke.assert_called()
    mock_refine_chain.ainvoke.assert_called()
