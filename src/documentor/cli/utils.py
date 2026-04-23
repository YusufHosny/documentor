import typer
import asyncio
from typing import List, Optional
from documentor.core.config import Config, DocItem
from documentor.core.parser import Parser
from documentor.cli.context import ctx
from documentor.llm.chains.agent import async_agent_generate_docs
from pathlib import Path

def handle_cancel(val):
    if val is None:
        ctx.console.print("[red]Initialization cancelled by user.[/red]")
        raise typer.Exit(1)
    return val

def run_generation(docs_to_generate: List[DocItem]):
    """Internal helper to execute the document generation logic."""
    ctx.console.print(
        f"[blue]Generating {len(docs_to_generate)} documentation files using agent mode in parallel...[/blue]"
    )
    generated_files = asyncio.run(
        async_agent_generate_docs(ctx.config, ctx.state_manager, docs_to_generate)
    )

    for file_path in generated_files:
        ctx.state_manager.upsert_doc(filepath=Path(file_path))

    ctx.console.print("[green]Generation complete![/green]")
