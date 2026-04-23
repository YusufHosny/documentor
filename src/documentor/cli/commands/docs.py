import os
import typer
import asyncio
import questionary
from pathlib import Path
from documentor.core.config import DocItem
from documentor.cli.context import ctx
from documentor.cli.utils import handle_cancel, run_generation
from documentor.llm.chains.agent import agent_generate_plan, async_agent_sync_docs

app = typer.Typer(help="Commands for generating and planning documentation.")

@app.command(name="plan")
def plan():
    """Analyzes the project context and suggests a list of documentation files to be managed."""
    ctx.console.print("[blue]Planning your documentation...[/blue]")

    existing_docs = [
        DocItem(filename=os.path.basename(str(ds.filepath)), description=ds.description)
        for ds in ctx.state_manager.state.managed_docs
    ]

    suggested_files = agent_generate_plan(ctx.config, existing_docs)

    if not suggested_files:
        ctx.console.print("[yellow]No new documentation files suggested.[/yellow]")
        return

    ctx.console.print("\n[blue]Suggested Documentation Files:[/blue]")
    for doc in suggested_files:
        ctx.console.print(f"- [cyan]{doc.filename}[/cyan]: {doc.description}")

    confirm = handle_cancel(
        questionary.confirm(
            "Do you want to add these suggestions to your tracked documentation files?",
            default=True,
        ).ask()
    )
    if confirm:
        for doc in suggested_files:
            ctx.state_manager.upsert_doc(
                filepath=Path(os.path.join(ctx.config.docs_dir, doc.filename)),
                description=doc.description,
            )
    else:
        ctx.console.print("[yellow]Planning cancelled.[/yellow]")
        return

    ctx.console.print(
        "[green]Updated documentor-lock.yaml with the new documentation plan![/green]"
    )

@app.command(name="generate")
def generate(
    force_regenerate: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Force regeneration of all documentation, ignoring tracking state",
    ),
):
    """Generate documentation using LLMs"""
    if not ctx.state_manager.state.managed_docs:
        ctx.console.print(
            "[yellow]No documentation files defined in documentor-lock.yaml.[/yellow]"
        )
        ctx.console.print(
            "[blue]Try running `documentor plan` to automatically suggest documentation files.[/blue]"
        )
        return

    docs_to_generate = []
    managed_docs_items = [
        DocItem(filename=os.path.basename(str(ds.filepath)), description=ds.description)
        for ds in ctx.state_manager.state.managed_docs
    ]

    if force_regenerate:
        docs_to_generate = managed_docs_items
        ctx.console.print("[blue]Force regenerating all documentation...[/blue]")
    else:
        stale_docs = {str(ds.filepath) for ds in ctx.state_manager.get_stale_docs()}
        for doc in managed_docs_items:
            filepath = os.path.join(ctx.config.docs_dir, doc.filename)
            if not os.path.exists(filepath) or filepath in stale_docs:
                docs_to_generate.append(doc)

    if not docs_to_generate:
        ctx.console.print("[green]All documentation is up to date![/green]")
        return

    run_generation(docs_to_generate)

@app.command(name="sync")
def sync():
    """Syncs existing documentation with current source code state."""
    ctx.console.print("[blue]Syncing documentation...[/blue]")

    stale_docs = ctx.state_manager.get_stale_docs()

    if not stale_docs:
        ctx.console.print("[green]All documentation is up to date![/green]")
        return

    ctx.console.print(
        f"[yellow]Found {len(stale_docs)} stale documents. Syncing...[/yellow]"
    )

    docs_to_sync = []
    for ds in stale_docs:
        if not os.path.exists(ds.filepath):
            ctx.console.print(f"[red]Warning: {ds.filepath} not found. Skipping.[/red]")
            continue

        with open(ds.filepath, "r", encoding="utf-8") as f:
            current_content = f.read()

        diff = None
        if ctx.config.use_git and ds.last_source_hash:
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
        ctx.console.print(
            f"[blue]Syncing {len(docs_to_sync)} documentation files using agent mode in parallel...[/blue]"
        )
        final_paths = asyncio.run(
            async_agent_sync_docs(ctx.config, ctx.state_manager, docs_to_sync)
        )

        for i, doc_data in enumerate(docs_to_sync):
            ds = doc_data["stale_doc_state"]
            final_path = final_paths[i]
            ctx.state_manager.upsert_doc(
                filepath=Path(final_path),
                tracking_type=ds.tracking_type,
                source_refs=ds.source_refs,
            )
            ctx.console.print(f"[green]Successfully synced {final_path}![/green]")

    ctx.console.print("[green]Sync complete![/green]")
