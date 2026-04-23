import os
import pytest
from pathlib import Path
import subprocess
from documentor.core.config import Config, ConfigManager, DocItem
from documentor.core.state import StateManager, DocState
from documentor.core.parser import Parser
from documentor.core.writer import Writer

def test_writer_write(temp_config_dir):
    config = Config(docs_dir="my_docs", include_footer=True)
    manager = StateManager(config)
    writer = Writer(config, manager)
    
    # write relative to docs_dir
    res1 = writer.write("foo.md", "hello world")
    assert "my_docs/foo.md" in res1
    assert "hello world" in Path(res1).read_text()
    assert "Docs generated with [documentor]" in Path(res1).read_text()
    
    # write absolute inside project
    res2 = writer.write(str(temp_config_dir / "my_docs" / "bar.md"), "hello bar")
    assert "my_docs/bar.md" in res2
    assert "hello bar" in Path(res2).read_text()
    
    # write absolute outside project (should fallback)
    res3 = writer.write("outside.md", "hello outside")
    # it forces it relative to docs_dir
    assert "my_docs/outside.md" in res3
    assert "hello outside" in Path(res3).read_text()
    
    # test no footer
    config_no_foot = Config(docs_dir="my_docs", include_footer=False)
    writer_no_foot = Writer(config_no_foot, manager)
    res4 = writer_no_foot.write("baz.md", "hello baz")
    assert "Docs generated with [documentor]" not in Path(res4).read_text()

@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield tmp_path

def test_config_manager(temp_config_dir):
    manager = ConfigManager()
    assert not manager.config_exists()

    config = Config(docs_dir="custom_docs", include_footer=False)
    manager.save_config(config)

    assert manager.config_exists()

    loaded = manager.load_config()
    assert loaded.docs_dir == "custom_docs"
    assert loaded.include_footer is False
    assert loaded.provider == "vertexai" # default

    manager.clear_config()
    assert not manager.config_exists()

def test_state_manager(temp_config_dir):
    config = Config(use_git=False)
    manager = StateManager(config)

    assert not manager.statefile_exists()
    assert len(manager.state.managed_docs) == 0

    doc_path = Path("docs/readme.md")

    original_get_hash = manager.get_current_hash
    manager.get_current_hash = lambda x: "hash1" # type: ignore

    manager.upsert_doc(filepath=doc_path, description="Main README")

    assert manager.statefile_exists()
    assert len(manager.state.managed_docs) == 1
    assert manager.state.managed_docs[0].description == "Main README"

    manager.get_current_hash = lambda x: "hash2" # type: ignore
    stale = manager.get_stale_docs()

    assert len(stale) == 1
    assert stale[0].filepath == doc_path

    manager.get_current_hash = original_get_hash

    manager.remove_doc(doc_path)
    assert len(manager.state.managed_docs) == 0

def test_state_manager_git_hash_clean(temp_config_dir, mocker):
    config = Config(use_git=True)
    manager = StateManager(config)
    
    mock_run = mocker.patch('subprocess.run')
    # First call: git rev-parse HEAD
    # Second call: git status --porcelain
    mock_run.side_effect = [
        mocker.MagicMock(stdout="commit123\n", returncode=0),
        mocker.MagicMock(stdout="", returncode=0) # No uncommitted changes
    ]
    
    hash_val = manager.get_current_hash()
    assert hash_val == "commit123"

def test_state_manager_git_hash_dirty(temp_config_dir, mocker):
    config = Config(use_git=True)
    manager = StateManager(config)
    
    mock_run = mocker.patch('subprocess.run')
    # Calls: rev-parse, status, diff, ls-files
    mock_run.side_effect = [
        mocker.MagicMock(stdout="commit123\n", returncode=0),
        mocker.MagicMock(stdout=" M somefile.py\n", returncode=0), # Dirty
        mocker.MagicMock(stdout=b"diff content", returncode=0), # git diff
        mocker.MagicMock(stdout="untracked.py\n", returncode=0), # ls-files
    ]
    
    # Mock file hash to prevent looking for 'untracked.py' on disk
    mocker.patch.object(manager, '_hash_files', return_value="hash_of_untracked")
    
    hash_val = manager.get_current_hash()
    assert "commit123-dirty-" in hash_val

def test_state_manager_git_error(temp_config_dir, mocker):
    config = Config(use_git=True)
    manager = StateManager(config)
    
    # Simulate not a git repo
    mocker.patch('subprocess.run', side_effect=subprocess.CalledProcessError(128, []))
    
    with pytest.raises(RuntimeError) as exc:
        manager.get_current_hash()
        
    assert "not a git repository" in str(exc.value)

def test_parser_extract_context(temp_config_dir):
    config = Config(ignore_patterns=["*.txt"], ignore_above_size_kb=1)
    
    # Write a .gitignore file
    (temp_config_dir / ".gitignore").write_text("*.log")
    
    parser = Parser(config)

    src_dir = temp_config_dir / "src"
    src_dir.mkdir()
    
    (src_dir / "main.py").write_text("print('hello')")
    (src_dir / "test.txt").write_text("ignore me")
    (src_dir / "test.log").write_text("ignore me log")
    
    # Large file test > 1KB
    large_file = src_dir / "large.py"
    large_file.write_text("a" * 2048)

    context = parser.extract_context(target=str(src_dir))

    paths = [c["path"] for c in context]
    assert any("main.py" in p for p in paths)
    assert not any("test.txt" in p for p in paths)
    assert not any("test.log" in p for p in paths) # Ignored via .gitignore
    assert not any("large.py" in p for p in paths) # Ignored via size threshold
    
def test_parser_binary_file(temp_config_dir):
    config = Config()
    parser = Parser(config)
    
    # write some invalid unicode
    bad_file = temp_config_dir / "bad.bin"
    bad_file.write_bytes(b"\x80\x81\x82")
    
    content = parser.read_file(str(bad_file))
    assert content is None

def test_parser_size_calculation(temp_config_dir):
    config = Config()
    parser = Parser(config)

    src_dir = temp_config_dir / "src"
    src_dir.mkdir()
    content = "a" * 1024 # 1KB
    (src_dir / "file1.py").write_text(content)
    (src_dir / "file2.py").write_text(content)

    size_kb = parser.get_total_context_size_kb(target=str(src_dir))
    assert size_kb >= 2

