import os
import typer
import questionary
from typing import Optional
from pathlib import Path
from documentor.cli.context import ctx
from documentor.cli.utils import should_use_agent
from documentor.llm.chains.agent import agent_edit_doc, agent_expand_doc, agent_infer_doc_info
from documentor.llm.chains import edit_doc, expand_doc, infer_doc_info

app = typer.Typer(help="Commands to manage individual documents.")

@app.command(name="add")
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
    ctx.console.print(f"[blue]Adding {target_file} to tracking...[/blue]")

    if not os.path.exists(target_file):
        ctx.console.print(f"[red]Error: {target_file} not found.[/red]")
        raise typer.Exit(1)

    filename = os.path.basename(target_file)
    existing_filenames = {
        os.path.basename(str(ds.filepath)).lower()
        for ds in ctx.state_manager.state.managed_docs
    }

    if filename.lower() not in existing_filenames:
        ctx.state_manager.upsert_doc(
            filepath=Path(target_file),
            description=description or "Manually added documentation file",
        )
        ctx.console.print(
            f"[green]Added {filename} to managed docs in documentor-lock.yaml[/green]"
        )
    else:
        ctx.state_manager.upsert_doc(filepath=Path(target_file), description=description)

    ctx.console.print(f"[green]Successfully added {target_file} to tracking![/green]")


@app.command(name="remove")
def remove(
    target_file: str,
    force: bool = typer.Option(
        False, "-f", "--force", help="Skip confirmation prompt"
    ),
):
    """Removes a documentation file and untracks it from Documentor."""
    ctx.console.print(f"[blue]Removing {target_file}...[/blue]")

    filepath = Path(target_file)
    is_tracked = any(ds.filepath == filepath for ds in ctx.state_manager.state.managed_docs)

    if not is_tracked:
        ctx.console.print(f"[yellow]Warning: {target_file} is not currently tracked by Documentor.[/yellow]")

    if not force:
        confirm = questionary.confirm(
            f"Are you sure you want to delete {target_file} and stop tracking it?",
            default=False,
        ).ask()
        if not confirm:
            ctx.console.print("[yellow]Removal cancelled.[/yellow]")
            raise typer.Exit(0)

    if os.path.exists(target_file):
        try:
            os.remove(target_file)
            ctx.console.print(f"[green]Deleted file: {target_file}[/green]")
        except Exception as e:
            ctx.console.print(f"[red]Error deleting file {target_file}: {e}[/red]")

    if is_tracked:
        ctx.state_manager.remove_doc(filepath)
        ctx.console.print(f"[green]Untracked {target_file} from Documentor lock state.[/green]")

    ctx.console.print(f"[green]Successfully removed {target_file}.[/green]")


@app.command(name="edit")
def edit(target_file: str):
    """Iterates on an existing markdown document using an LLM based on user comments."""
    ctx.console.print(f"[blue]Editing {target_file}...[/blue]")

    if not os.path.exists(target_file):
        ctx.console.print(f"[red]Error: {target_file} not found.[/red]")
        raise typer.Exit(1)

    comments = typer.prompt("Please enter your comments for the AI")

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    if should_use_agent(ctx.config, ctx.parser):
        new_content = agent_edit_doc(content, comments, ctx.config)
    else:
        new_content = edit_doc(content, comments, ctx.config)

    final_path = ctx.writer.write(target_file, new_content)

    ctx.state_manager.upsert_doc(filepath=Path(final_path))

    ctx.console.print(f"[green]Successfully edited {target_file}![/green]")


@app.command(name="expand")
def expand(target_file: str):
    """Turns scrappy bullet points into a coherent, well-formatted document using an LLM."""
    ctx.console.print(f"[blue]Expanding {target_file}...[/blue]")

    if not os.path.exists(target_file):
        ctx.console.print(f"[red]Error: {target_file} not found.[/red]")
        raise typer.Exit(1)

    filename = os.path.basename(target_file)

    if should_use_agent(ctx.config, ctx.parser):
        doc_info = agent_infer_doc_info(filename, ctx.config)
    else:
        context = ctx.parser.extract_context()
        doc_info = infer_doc_info(filename, context, ctx.config)

    ctx.console.print(f"[blue]Inferred Description: {doc_info.description}[/blue]")

    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    if should_use_agent(ctx.config, ctx.parser):
        new_content = agent_expand_doc(content, doc_info.description, ctx.config)
    else:
        new_content = expand_doc(content, doc_info.description, ctx.config)

    final_path = ctx.writer.write(target_file, new_content)

    existing_filenames = {
        os.path.basename(str(ds.filepath)).lower()
        for ds in ctx.state_manager.state.managed_docs
    }
    if (
        filename.lower() not in existing_filenames
        and target_file.lower() not in existing_filenames
    ):
        ctx.state_manager.upsert_doc(
            filepath=Path(final_path), description=doc_info.description
        )
    else:
        ctx.state_manager.upsert_doc(filepath=Path(final_path))

    ctx.console.print(f"[green]Successfully expanded {target_file}![/green]")
