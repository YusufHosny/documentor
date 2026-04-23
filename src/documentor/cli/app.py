import os
from typing import Optional
import typer

env_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
if os.path.exists(env_file):
    from dotenv import load_dotenv

    load_dotenv(env_file)

from documentor.cli.context import ctx
from documentor.cli.commands.setup import app as setup_app
from documentor.cli.commands.docs import app as docs_app
from documentor.cli.commands.manage import app as manage_app

__version__ = "1.0.0"

app = typer.Typer(
    help="Documentor: A CLI tool for automatic documentation generation and management"
)

def version_callback(value: bool):
    if value:
        ctx.console.print(f"Documentor version: {__version__}")
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

for command in setup_app.registered_commands:
    app.registered_commands.append(command)

for command in docs_app.registered_commands:
    app.registered_commands.append(command)

for command in manage_app.registered_commands:
    app.registered_commands.append(command)

if __name__ == "__main__":
    app()
