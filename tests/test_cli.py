import os
from pathlib import Path
import pytest
from unittest.mock import MagicMock, AsyncMock
from typer.testing import CliRunner
from documentor.cli.app import app
from documentor.core.config import Config, DocItem
from documentor.core.state import StateManager, ProjectState, DocState

runner = CliRunner()

@pytest.fixture
def cli_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = Config(docs_dir="docs", provider="vertexai", model="test-model", include_footer=False)
    # mock config manager to return this config
    return config

def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "Documentor version:" in result.stdout

def test_remove_nonexistent(mocker, cli_config):
    # Ensure state manager has no docs
    mock_state_manager = mocker.MagicMock()
    mock_state_manager.state.managed_docs = []
    mocker.patch('documentor.cli.app.state_manager', mock_state_manager)
    
    result = runner.invoke(app, ["remove", "nonexistent.md", "--force"])
    assert result.exit_code == 0
    assert "Warning: nonexistent.md is not currently tracked" in result.stdout
    assert "Successfully removed nonexistent.md" in result.stdout

def test_remove_existing(mocker, cli_config, tmp_path):
    doc_path = tmp_path / "docs" / "test.md"
    doc_path.parent.mkdir()
    doc_path.write_text("content")
    
    mock_state_manager = mocker.MagicMock()
    ds = DocState(filepath=Path("docs/test.md"), tracking_type="file", source_refs=[], last_source_hash="")
    mock_state_manager.state.managed_docs = [ds]
    mocker.patch('documentor.cli.app.state_manager', mock_state_manager)
    
    # Needs to match the relative path correctly to be found in state_manager
    os.chdir(tmp_path) # monkeypatch fixture isn't available to runner directly, so chdir just in case
    
    result = runner.invoke(app, ["remove", "docs/test.md", "--force"])
    assert result.exit_code == 0
    assert "Deleted file: docs/test.md" in result.stdout
    assert "Untracked docs/test.md from Documentor lock state" in result.stdout
    mock_state_manager.remove_doc.assert_called_once()
    assert not doc_path.exists()

def test_destroy_command_abort(mocker):
    mock_prompt = mocker.MagicMock()
    mock_prompt.ask.return_value = False
    mocker.patch('questionary.confirm', return_value=mock_prompt)
    mocker.patch('documentor.cli.app.state_manager')

    result = runner.invoke(app, ["destroy"])
    assert result.exit_code == 0
    assert "Destruction cancelled." in result.stdout

def test_destroy_command_success(mocker, cli_config, tmp_path):
    mock_prompt = mocker.MagicMock()
    mock_prompt.ask.return_value = True
    mocker.patch('questionary.confirm', return_value=mock_prompt)
    
    doc_path = tmp_path / "docs" / "test.md"
    doc_path.parent.mkdir()
    doc_path.write_text("content")
    
    mock_state_manager = mocker.MagicMock()
    ds = DocState(filepath=doc_path, tracking_type="file", source_refs=[], last_source_hash="")
    mock_state_manager.state.managed_docs = [ds]
    mock_state_manager.statefile_exists.return_value = True
    mocker.patch('documentor.cli.app.state_manager', mock_state_manager)
    
    mock_config_manager = mocker.MagicMock()
    mock_config_manager.config_exists.return_value = True
    mocker.patch('documentor.cli.app.config_manager', mock_config_manager)
    mocker.patch('os.remove')
    
    result = runner.invoke(app, ["destroy", "--with-files"])
    assert result.exit_code == 0
    assert "Deleting tracked documentation files" in result.stdout
    assert "Deleted documentor.yaml" in result.stdout
    assert "Deleted documentor-lock.yaml" in result.stdout
    
    mock_state_manager.clear_statefile.assert_called_once()
    
def test_add_command(mocker):
    mocker.patch('os.path.exists', return_value=True)

    mock_state_manager = mocker.MagicMock()
    mock_state_manager.state.managed_docs = []
    mocker.patch('documentor.cli.app.state_manager', mock_state_manager)

    result = runner.invoke(app, ["add", "docs/new.md", "-d", "new file"])
    assert result.exit_code == 0
    assert "Successfully added docs/new.md to tracking!" in result.stdout
    mock_state_manager.upsert_doc.assert_called_once()

def test_generate_command_no_docs(mocker):
    mock_state_manager = mocker.MagicMock()
    mock_state_manager.state.managed_docs = []
    mocker.patch('documentor.cli.app.state_manager', mock_state_manager)
    
    result = runner.invoke(app, ["generate"])
    assert result.exit_code == 0
    assert "No documentation files defined" in result.stdout
    
def test_generate_command_all_updated(mocker, cli_config):
    mock_state_manager = mocker.MagicMock()
    ds = DocState(filepath=Path("docs/test.md"), tracking_type="file", source_refs=[], last_source_hash="")
    mock_state_manager.state.managed_docs = [ds]
    mock_state_manager.get_stale_docs.return_value = []
    mocker.patch('documentor.cli.app.state_manager', mock_state_manager)
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('documentor.cli.app.config', cli_config)
    
    result = runner.invoke(app, ["generate"])
    assert result.exit_code == 0
    assert "All documentation is up to date" in result.stdout
    
def test_generate_command_force(mocker, cli_config):
    mock_state_manager = mocker.MagicMock()
    ds = DocState(filepath=Path("docs/test.md"), tracking_type="file", source_refs=[], last_source_hash="")
    mock_state_manager.state.managed_docs = [ds]
    mocker.patch('documentor.cli.app.state_manager', mock_state_manager)
    mocker.patch('documentor.cli.app.config', cli_config)
    mocker.patch('documentor.cli.app.should_use_agent', return_value=False)
    
    mock_run_generation = mocker.patch('documentor.cli.app._run_generation')
    
    result = runner.invoke(app, ["generate", "--force"])
    assert result.exit_code == 0
    mock_run_generation.assert_called_once()
    args = mock_run_generation.call_args[0][0]
    assert len(args) == 1
    assert args[0].filename == "test.md"

def test_sync_command_no_stale(mocker, cli_config):
    mock_state_manager = mocker.MagicMock()
    mock_state_manager.get_stale_docs.return_value = []
    mocker.patch('documentor.cli.app.state_manager', mock_state_manager)
    
    result = runner.invoke(app, ["sync"])
    assert result.exit_code == 0
    assert "All documentation is up to date" in result.stdout

def test_sync_command_with_stale(mocker, cli_config, tmp_path):
    doc_path = tmp_path / "docs" / "test.md"
    doc_path.parent.mkdir()
    doc_path.write_text("old content")
    
    ds = DocState(filepath=doc_path, tracking_type="file", source_refs=[], last_source_hash="hash")
    
    mock_state_manager = mocker.MagicMock()
    mock_state_manager.get_stale_docs.return_value = [ds]
    mocker.patch('documentor.cli.app.state_manager', mock_state_manager)
    mocker.patch('documentor.cli.app.config', cli_config)
    mocker.patch('documentor.cli.app.should_use_agent', return_value=False)
    
    mock_async_sync = mocker.patch('documentor.cli.app.async_sync_docs', new_callable=AsyncMock)
    mock_async_sync.return_value = ["docs/test.md"]
    mocker.patch('documentor.cli.app.parser.extract_context', return_value=[])
    
    result = runner.invoke(app, ["sync"])
    assert result.exit_code == 0
    assert "Sync complete!" in result.stdout
    mock_async_sync.assert_called_once()
    mock_state_manager.upsert_doc.assert_called_once()

def test_plan_command_agent_mode(mocker, cli_config):
    mock_state_manager = mocker.MagicMock()
    mock_state_manager.state.managed_docs = []
    mocker.patch('documentor.cli.app.state_manager', mock_state_manager)
    mocker.patch('documentor.cli.app.config', cli_config)
    mocker.patch('documentor.cli.app.should_use_agent', return_value=True)
    
    mock_agent_plan = mocker.patch('documentor.cli.app.agent_generate_plan')
    mock_agent_plan.return_value = [DocItem(filename="new_api.md", description="API docs")]
    
    mock_prompt = mocker.MagicMock()
    mock_prompt.ask.return_value = True
    mocker.patch('questionary.confirm', return_value=mock_prompt)
    
    result = runner.invoke(app, ["plan"])
    assert result.exit_code == 0
    assert "new_api.md" in result.stdout
    assert "Updated documentor-lock.yaml" in result.stdout
    mock_state_manager.upsert_doc.assert_called_once()

def test_edit_command(mocker, cli_config, tmp_path):
    doc_path = tmp_path / "docs" / "test.md"
    doc_path.parent.mkdir()
    doc_path.write_text("old content")
    
    mocker.patch('documentor.cli.app.config', cli_config)
    mocker.patch('documentor.cli.app.should_use_agent', return_value=False)
    mocker.patch('typer.prompt', return_value="Make it better")
    
    mock_edit_doc = mocker.patch('documentor.cli.app.edit_doc', return_value="new content")
    mock_writer = mocker.patch('documentor.cli.app.writer.write', return_value=str(doc_path))
    mock_state_manager = mocker.patch('documentor.cli.app.state_manager')
    
    result = runner.invoke(app, ["edit", str(doc_path)])
    assert result.exit_code == 0
    assert "Successfully edited" in result.stdout
    mock_edit_doc.assert_called_once_with("old content", "Make it better", cli_config)
    mock_writer.assert_called_once_with(str(doc_path), "new content")
    mock_state_manager.upsert_doc.assert_called_once()

def test_expand_command(mocker, cli_config, tmp_path):
    doc_path = tmp_path / "docs" / "test.md"
    doc_path.parent.mkdir()
    doc_path.write_text("- bullet 1")
    
    mocker.patch('documentor.cli.app.config', cli_config)
    mocker.patch('documentor.cli.app.should_use_agent', return_value=False)
    mocker.patch('documentor.cli.app.parser.extract_context', return_value=[])
    
    mock_infer = mocker.patch('documentor.cli.app.infer_doc_info')
    mock_infer.return_value = DocItem(filename="test.md", description="Inferred desc")
    
    mock_expand = mocker.patch('documentor.cli.app.expand_doc', return_value="Full content")
    mock_writer = mocker.patch('documentor.cli.app.writer.write', return_value=str(doc_path))
    mock_state_manager = mocker.patch('documentor.cli.app.state_manager')
    mock_state_manager.state.managed_docs = []
    
    result = runner.invoke(app, ["expand", str(doc_path)])
    assert result.exit_code == 0
    assert "Successfully expanded" in result.stdout
    mock_expand.assert_called_once()
    mock_writer.assert_called_once()
    mock_state_manager.upsert_doc.assert_called_once()

def test_init_command_interactive(mocker, cli_config, tmp_path):
    mocker.patch('documentor.cli.app.config_manager.config_exists', return_value=False)
    mocker.patch('documentor.cli.app.state_manager.statefile_exists', return_value=False)
    
    # Mocking questionary prompts
    mock_confirm = mocker.MagicMock()
    mock_confirm.ask.side_effect = [
        True,  # Use default output
        True,  # Use git tracking
        True,  # default model
        True,  # default ignores
        False, # DONT create style md to skip that branch
    ]
    mocker.patch('questionary.confirm', return_value=mock_confirm)
    
    mock_text = mocker.MagicMock()
    mock_text.ask.return_value = "docs/style.md"
    mocker.patch('questionary.text', return_value=mock_text)
    
    mock_select = mocker.MagicMock()
    mock_select.ask.return_value = "never" # Agent choice
    mocker.patch('questionary.select', return_value=mock_select)
    
    mock_save = mocker.patch('documentor.cli.app.config_manager.save_config')
    
    # mock plan generation inside init
    mocker.patch('documentor.cli.app.should_use_agent', return_value=False)
    mocker.patch('documentor.cli.app.parser.extract_context', return_value=[])
    mocker.patch('documentor.cli.app.generate_plan', return_value=[])
    
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    assert "Created documentor.yaml successfully!" in result.stdout
    mock_save.assert_called_once()

