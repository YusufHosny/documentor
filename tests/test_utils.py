import pytest
from documentor.utils.style import load_style_template, get_style_templates

def test_get_style_templates() -> None:
    templates = get_style_templates()
    assert isinstance(templates, list)
    assert "basic.md" in templates

def test_load_style_template() -> None:
    content = load_style_template("basic")
    assert content
    assert "Style Template: Basic" in content

def test_load_invalid_template() -> None:
    with pytest.raises(FileNotFoundError):
        load_style_template("non_existent_template")
