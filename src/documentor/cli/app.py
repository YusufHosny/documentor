import os
import asyncio
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
import questionary
from documentor.core.config import Config, ConfigManager, DocItem
from documentor.core.state import StateManager
from documentor.llm.chains import (
    async_generate_docs,
    edit_doc,
    expand_doc,
    async_sync_docs,
    generate_plan,
    infer_doc_info,
)
from documentor.llm.chains.agent import (
    async_agent_generate_docs,
    agent_edit_doc,
    agent_expand_doc,
    async_agent_sync_docs,
    agent_generate_plan,
    agent_infer_doc_info,
)
from documentor.core.parser import Parser
from documentor.core.writer import Writer
from documentor.utils.style import load_style_template, get_style_templates

__version__ = "1.0.0"

env_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
if os.path.exists(env_file):
    from dotenv import load_dotenv

    load_dotenv(env_file)

app = typer.Typer(
    help="Documentor: A CLI tool for automatic documentation generation and management"
)
console = Console()

config_manager = ConfigManager()
config = config_manager.load_config()
state_manager = StateManager(config)
parser = Parser(config)
writer = Writer(config, state_manager)


def version_callback(value: bool):
    if value:
        console.print(f"Documentor version: {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show the application's version and exit.",
    ),
):
    pass


def handle_cancel(val):
    if val is None:
        console.print("[red]Initialization cancelled by user.[/red]")
        raise typer.Exit(1)
    return val


def should_use_agent(config: Config, parser: Parser) -> bool:
    """Centralized logic to decide if agent mode should be used."""
    if config.agent_threshold_kb == 0:
        return True

    if config.agent_threshold_kb == -1:
        return False

    total_size = parser.get_total_context_size_kb()
    if total_size > config.agent_threshold_kb:
        console.print(
            f"[yellow]Project size ({total_size}KB) exceeds agent threshold ({config.agent_threshold_kb}KB). Switching to agent mode.[/yellow]"
        )
        return True

    return False


@app.command()
def plan():
    """Analyzes the project context and suggests a list of documentation files to be managed."""
    console.print("[blue]Planning your documentation...[/blue]")

    existing_docs = [
        DocItem(filename=os.path.basename(str(ds.filepath)), description=ds.description)
        for ds in state_manager.state.managed_docs
    ]

    if should_use_agent(config, parser):
        suggested_files = agent_generate_plan(config, existing_docs)
    else:
        context = parser.extract_context()
        suggested_files = generate_plan(context, config, existing_docs)

    if not suggested_files:
        console.print("[yellow]No new documentation files suggested.[/yellow]")
        return

    console.print("\n[blue]Suggested Documentation Files:[/blue]")
    for doc in suggested_files:
        console.print(f"- [cyan]{doc.filename}[/cyan]: {doc.description}")

    confirm = handle_cancel(
        questionary.confirm(
            "Do you want to add these suggestions to your tracked documentation files?",
            default=True,
        ).ask()
    )
    if confirm:
        for doc in suggested_files:
            state_manager.upsert_doc(
                filepath=Path(os.path.join(config.docs_dir, doc.filename)),
                description=doc.description,
            )
    else:
        console.print("[yellow]Planning cancelled.[/yellow]")
        return

    console.print(
        "[green]Updated documentor-lock.yaml with the new documentation plan![/green]"
    )


@app.command()
def init():
    """Interactive setup to initialize documentor configuration."""
    global config, state_manager, parser, writer
    console.print("[blue]Welcome to Documentor![/blue]")

    if config_manager.config_exists() or state_manager.statefile_exists():
        overwrite = handle_cancel(
            questionary.confirm(
                "It seems this project was already initialized. Do you want to clear the existing configuration and start over?",
                default=False,
            ).ask()
        )
        if not overwrite:
            console.print(
                "[yellow]Initialization cancelled to prevent overwriting existing config.[/yellow]"
            )
            raise typer.Exit(0)
        else:
            config_manager.clear_config()
            state_manager.clear_statefile()
            console.print(
                "[green]Existing configuration cleared. Starting fresh initialization.[/green]"
            )

    config_data = {}

    # choose doc directory
    default_output = handle_cancel(
        questionary.confirm(
            "Use default output settings (docs directory, no footer)?", default=True
        ).ask()
    )
    if not default_output:
        config_data["docs_dir"] = handle_cancel(
            questionary.text("Enter output directory for docs:", default="docs").ask()
        )
        config_data["include_footer"] = handle_cancel(
            questionary.confirm(
                "Include 'Generated by Documentor' footer in markdown?", default=False
            ).ask()
        )

    # tracking options
    config_data["use_git"] = handle_cancel(
        questionary.confirm(
            "Use git-based tracking for incremental updates?", default=True
        ).ask()
    )

    # style md setup
    config_data["style_md_path"] = handle_cancel(
        questionary.text(
            "Enter the path to use for style.md (leave empty to skip):",
            default=f"{config_data.get('docs_dir', 'docs')}/style.md",
        ).ask()
    ).strip()

    # llm setup
    default_model = handle_cancel(
        questionary.confirm(
            "Use default model (Google Vertex AI with gemini-3.1-pro)?", default=True
        ).ask()
    )
    if not default_model:
        config_data["provider"] = handle_cancel(
            questionary.select(
                "Choose LLM provider:",
                choices=["vertexai", "openai", "ollama"],
                default="vertexai",
            ).ask()
        )
        config_data["model"] = handle_cancel(
            questionary.text(
                "Enter model name:", default="gemini-3.1-pro-preview"
            ).ask()
        )

    # file ignores setup
    default_ignore = handle_cancel(
        questionary.confirm(
            "Use default ignore setup (ignore common dirs like .git, venv, and files > 100KB)?",
            default=True,
        ).ask()
    )
    if not default_ignore:
        size_str = handle_cancel(
            questionary.text("Ignore files above size (KB):", default="100").ask()
        )
        config_data["ignore_above_size_kb"] = (
            int(size_str) if size_str.isdigit() else 100
        )
        ignore_patterns_str = handle_cancel(
            questionary.text(
                "Enter ignore patterns (comma-separated):",
                default=".git, __pycache__, venv, .venv, env, node_modules, .env, *.pyc, *.pyo",
            ).ask()
        )
        config_data["ignore_patterns"] = [
            p.strip() for p in ignore_patterns_str.split(",")
        ]

    # agent setup
    agent_choice = handle_cancel(
        questionary.select(
            "Use agent-mode (An agent will dynamcially handle your files instead of full-project context)?",
            choices=[
                questionary.Choice("Enable agent-mode always", value="always"),
                questionary.Choice(
                    "Enable agent-mode if project context exceeds a threshold",
                    value="threshold",
                ),
                questionary.Choice("Disable agent-mode", value="never"),
            ],
        ).ask()
    )

    if agent_choice == "always":
        config_data["agent_threshold_kb"] = 0
    elif agent_choice == "threshold":
        threshold_str = handle_cancel(
            questionary.text(
                "Threshold in KB for automatic agent mode:", default="1000"
            ).ask()
        )
        config_data["agent_threshold_kb"] = (
            int(threshold_str) if threshold_str.isdigit() else 1000
        )
    else:
        config_data["agent_threshold_kb"] = -1

    config = Config(**config_data)
    config_manager.save_config(config)

    # Re-initialize globals with the new config
    state_manager = StateManager(config)
    parser = Parser(config)
    writer = Writer(config, state_manager)

    console.print("[green]Created documentor.yaml successfully![/green]")

    # style.md setup
    # TODO style md generation with questionnaire
    if config.style_md_path:
        create_style = handle_cancel(
            questionary.confirm(
                f"Do you want to create and initialize {config.style_md_path}?",
                default=True,
            ).ask()
        )
        if create_style:
            style_path = config.style_md_path or os.path.join(
                config.docs_dir or "docs", "style.md"
            )
            os.makedirs(os.path.dirname(style_path) or ".", exist_ok=True)

            # select a template
            choices = [f.replace(".md", "") for f in get_style_templates()] + ["empty"]
            selected_template = handle_cancel(
                questionary.select(
                    "Choose a style template to initialize with:",
                    choices=choices,
                    default="empty",
                ).ask()
            )

            if not os.path.exists(style_path):
                if selected_template == "empty":
                    content = "# Documentation Style Guide\n\nAdd your formatting and style instructions here. These will be used by Documentor when generating your docs.\n"
                else:
                    content = load_style_template(selected_template)

                with open(style_path, "w", encoding="utf-8") as f:
                    f.write(content)
                console.print(
                    f"[green]Created {style_path} using {selected_template} template![/green]"
                )
            else:
                console.print(
                    f"[yellow]{style_path} already exists. Skipping initialization.[/yellow]"
                )

    # plan setup (documentor plan)
    console.print("[blue]Analyzing project context to generate plan...[/blue]")
    existing_docs = []

    if should_use_agent(config, parser):
        suggested_files = agent_generate_plan(config, existing_docs)
    else:
        context = parser.extract_context()
        suggested_files = generate_plan(context, config, existing_docs)

    console.print(
        f"[green]AI suggested {len(suggested_files)} files based on project context.[/green]"
    )

    if suggested_files:
        for doc in suggested_files:
            state_manager.upsert_doc(
                filepath=Path(os.path.join(config.docs_dir, doc.filename)),
                description=doc.description,
            )

    console.print(
        "[blue]Initialization complete! Run `documentor generate` to generate your documentation.[/blue]"
    )


@app.command()
def generate(
    force_regenerate: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force regeneration of all documentation, ignoring tracking state",
    ),
):
    """Generate documentation using LLMs"""
    if not state_manager.state.managed_docs:
        console.print(
            "[yellow]No documentation files defined in documentor-lock.yaml.[/yellow]"
        )
        console.print(
            "[blue]Try running `documentor plan` to automatically suggest documentation files.[/blue]"
        )
        return

    docs_to_generate = []
    managed_docs_items = [
        DocItem(filename=os.path.basename(str(ds.filepath)), description=ds.description)
        for ds in state_manager.state.managed_docs
    ]

    if force_regenerate:
        docs_to_generate = managed_docs_items
        console.print("[blue]Force regenerating all documentation...[/blue]")
    else:
        stale_docs = {str(ds.filepath) for ds in state_manager.get_stale_docs()}
        for doc in managed_docs_items:
            filepath = os.path.join(config.docs_dir, doc.filename)
            if not os.path.exists(filepath) or filepath in stale_docs:
                docs_to_generate.append(doc)

    if not docs_to_generate:
        console.print("[green]All documentation is up to date![/green]")
        return

    if should_use_agent(config, parser):
        console.print(
            f"[blue]Generating {len(docs_to_generate)} documentation files using agent mode in parallel...[/blue]"
        )
        generated_files = asyncio.run(
            async_agent_generate_docs(config, state_manager, docs_to_generate)
        )
    else:
        console.print(
            f"[blue]Generating {len(docs_to_generate)} documentation files in parallel...[/blue]"
        )
        context = parser.extract_context()
        generated_files = asyncio.run(
            async_generate_docs(context, config, state_manager, docs_to_generate)
        )

    for file_path in generated_files:
        state_manager.upsert_doc(filepath=Path(file_path))

    console.print("[green]Generation complete![/green]")


@app.command()
def edit(target_file: str):
    """Iterates on an existing markdown document using an LLM based on user comments."""
    console.print(f"[blue]Editing {target_file}...[/blue]")

    if not os.path.exists(target_file):
        console.print(f"[red]Error: {target_file} not found.[/red]")
        raise typer.Exit(1)

    comments = typer.prompt("Please enter your comments for the AI")

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    if should_use_agent(config, parser):
        new_content = agent_edit_doc(content, comments, config)
    else:
        new_content = edit_doc(content, comments, config)

    final_path = writer.write(target_file, new_content)

    state_manager.upsert_doc(filepath=Path(final_path))

    console.print(f"[green]Successfully edited {target_file}![/green]")


@app.command()
def expand(target_file: str):
    """Turns scrappy bullet points into a coherent, well-formatted document using an LLM."""
    console.print(f"[blue]Expanding {target_file}...[/blue]")

    if not os.path.exists(target_file):
        console.print(f"[red]Error: {target_file} not found.[/red]")
        raise typer.Exit(1)

    filename = os.path.basename(target_file)

    if should_use_agent(config, parser):
        doc_info = agent_infer_doc_info(filename, config)
    else:
        context = parser.extract_context()
        doc_info = infer_doc_info(filename, context, config)

    console.print(f"[blue]Inferred Description: {doc_info.description}[/blue]")

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    if should_use_agent(config, parser):
        new_content = agent_expand_doc(content, doc_info.description, config)
    else:
        new_content = expand_doc(content, doc_info.description, config)

    final_path = writer.write(target_file, new_content)

    existing_filenames = {
        os.path.basename(str(ds.filepath)).lower()
        for ds in state_manager.state.managed_docs
    }
    if (
        filename.lower() not in existing_filenames
        and target_file.lower() not in existing_filenames
    ):
        state_manager.upsert_doc(
            filepath=Path(final_path), description=doc_info.description
        )
    else:
        state_manager.upsert_doc(filepath=Path(final_path))

    console.print(f"[green]Successfully expanded {target_file}![/green]")


@app.command()
def add(
    target_file: str,
    description: Optional[str] = typer.Option(
        None,
        "-d",
        "--description",
        help="Optional description for the added documentation file.",
    ),
):
    """Adds an existing documentation file to documentor tracking."""
    console.print(f"[blue]Adding {target_file} to tracking...[/blue]")

    if not os.path.exists(target_file):
        console.print(f"[red]Error: {target_file} not found.[/red]")
        raise typer.Exit(1)

    filename = os.path.basename(target_file)
    existing_filenames = {
        os.path.basename(str(ds.filepath)).lower()
        for ds in state_manager.state.managed_docs
    }

    if filename.lower() not in existing_filenames:
        state_manager.upsert_doc(
            filepath=Path(target_file),
            description=description or "Manually added documentation file",
        )
        console.print(
            f"[green]Added {filename} to managed docs in documentor-lock.yaml[/green]"
        )
    else:
        state_manager.upsert_doc(filepath=Path(target_file), description=description)

    console.print(f"[green]Successfully added {target_file} to tracking![/green]")


@app.command()
def sync():
    """Syncs existing documentation with current source code state."""
    console.print("[blue]Syncing documentation...[/blue]")

    stale_docs = state_manager.get_stale_docs()

    if not stale_docs:
        console.print("[green]All documentation is up to date![/green]")
        return

    console.print(
        f"[yellow]Found {len(stale_docs)} stale documents. Syncing...[/yellow]"
    )

    use_agent = should_use_agent(config, parser)

    docs_to_sync = []
    for ds in stale_docs:
        if not os.path.exists(ds.filepath):
            console.print(f"[red]Warning: {ds.filepath} not found. Skipping.[/red]")
            continue

        with open(ds.filepath, "r", encoding="utf-8") as f:
            current_content = f.read()

        diff = None
        if config.use_git and ds.last_source_hash:
            try:
                base_hash = ds.last_source_hash.split("-dirty-")[0]
                import subprocess

                result = subprocess.run(
                    [
                        "git",
                        "diff",
                        base_hash,
                        "HEAD",
                        "--",
                        ".",
                        ":!documentor.yaml",
                        ":!documentor-lock.yaml",
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    diff = result.stdout
            except Exception:
                pass

        docs_to_sync.append(
            {
                "filepath": ds.filepath,
                "current_content": current_content,
                "diff": diff,
                "stale_doc_state": ds,
            }
        )

    if docs_to_sync:
        if use_agent:
            console.print(
                f"[blue]Syncing {len(docs_to_sync)} documentation files using agent mode in parallel...[/blue]"
            )
            final_paths = asyncio.run(
                async_agent_sync_docs(config, state_manager, docs_to_sync)
            )
        else:
            console.print(
                f"[blue]Syncing {len(docs_to_sync)} documentation files in parallel...[/blue]"
            )
            context = parser.extract_context()
            final_paths = asyncio.run(
                async_sync_docs(context, config, state_manager, docs_to_sync)
            )

        # Update states
        for i, doc_data in enumerate(docs_to_sync):
            ds = doc_data["stale_doc_state"]
            final_path = final_paths[i]
            state_manager.upsert_doc(
                filepath=Path(final_path),
                tracking_type=ds.tracking_type,
                source_refs=ds.source_refs,
            )
            console.print(f"[green]Successfully synced {final_path}![/green]")

    console.print("[green]Sync complete![/green]")


if __name__ == "__main__":
    app()
