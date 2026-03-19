import os
from typing import Optional
import typer
from rich.console import Console
from documentor.core.config import ConfigManager
from documentor.llm.chains import generate_docs, edit_doc, expand_doc
from documentor.core.parser import Parser
from documentor.core.writer import Writer

app = typer.Typer(help="Documentor: A CLI tool for automatic documentation generation and management")
console = Console()

@app.command()
def init():
    """Scans the project, creates documentor.yaml, and generates the initial documentation suite."""
    console.print("[blue]Initializing documentor...[/blue]")
    config_manager = ConfigManager()
    if not os.path.exists("documentor.yaml"):
        config_manager.create_default_config()
        console.print("[green]Created default documentor.yaml[/green]")
    else:
        console.print("[yellow]documentor.yaml already exists. Skipping creation.[/yellow]")

    config = config_manager.load_config()
    parser = Parser(config)
    context = parser.extract_context()

    console.print("[blue]Generating initial documentation suite...[/blue]")
    generate_docs(context, config)
    console.print("[green]Initialization complete![/green]")

@app.command()
def generate(target: Optional[str] = typer.Option(None, help="Specific target to generate docs for")):
    """On-demand generation based on documentor.yaml."""
    console.print("[blue]Generating documentation...[/blue]")
    config_manager = ConfigManager()
    config = config_manager.load_config()

    parser = Parser(config)
    context = parser.extract_context(target)

    generate_docs(context, config, target)
    console.print("[green]Generation complete![/green]")

@app.command()
def edit(target_file: str, comments: str = typer.Option(..., "--comments", "-c", help="Comments for AI to iterate on the document")):
    """Iterates on an existing markdown document using AI based on user comments."""
    console.print(f"[blue]Editing {target_file}...[/blue]")
    config_manager = ConfigManager()
    config = config_manager.load_config()

    if not os.path.exists(target_file):
        console.print(f"[red]Error: {target_file} not found.[/red]")
        raise typer.Exit(1)

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = edit_doc(content, comments, config)

    writer = Writer(config)
    writer.write(target_file, new_content)
    console.print(f"[green]Successfully edited {target_file}![/green]")

@app.command()
def expand(target_file: str, doc_type: str = typer.Option("functional", "--type", "-t", help="Type of document (functional, decision, etc.)")):
    """Turns scrappy bullet points into a coherent, well-formatted document."""
    console.print(f"[blue]Expanding {target_file}...[/blue]")
    config_manager = ConfigManager()
    config = config_manager.load_config()

    if not os.path.exists(target_file):
        console.print(f"[red]Error: {target_file} not found.[/red]")
        raise typer.Exit(1)

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = expand_doc(content, doc_type, config)

    writer = Writer(config)
    writer.write(target_file, new_content)
    console.print(f"[green]Successfully expanded {target_file}![/green]")

if __name__ == "__main__":
    app()
