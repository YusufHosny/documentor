import typer
import asyncio
from typing import List, Optional
from documentor.core.config import Config, DocItem
from documentor.core.parser import Parser
from documentor.cli.context import ctx
from documentor.llm.chains.agent import async_agent_generate_docs
from documentor.llm.chains import async_generate_docs
from pathlib import Path

def handle_cancel(val):
    if val is None:
        ctx.console.print("[red]Initialization cancelled by user.[/red]")
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
        ctx.console.print(
            f"[yellow]Project size ({total_size}KB) exceeds agent threshold ({config.agent_threshold_kb}KB). Switching to agent mode.[/yellow]"
        )
        return True

    return False

def run_generation(docs_to_generate: List[DocItem]):
    """Internal helper to execute the document generation logic."""
    if should_use_agent(ctx.config, ctx.parser):
        ctx.console.print(
            f"[blue]Generating {len(docs_to_generate)} documentation files using agent mode in parallel...[/blue]"
        )
        generated_files = asyncio.run(
            async_agent_generate_docs(ctx.config, ctx.state_manager, docs_to_generate)
        )
    else:
        ctx.console.print(
            f"[blue]Generating {len(docs_to_generate)} documentation files in parallel...[/blue]"
        )
        context = ctx.parser.extract_context()
        generated_files = asyncio.run(
            async_generate_docs(context, ctx.config, ctx.state_manager, docs_to_generate)
        )

    for file_path in generated_files:
        ctx.state_manager.upsert_doc(filepath=Path(file_path))

    ctx.console.print("[green]Generation complete![/green]")
