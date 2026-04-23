import os
import typer
from rich.console import Console
from documentor.core.config import ConfigManager
from documentor.core.state import StateManager
from documentor.core.parser import Parser
from documentor.core.writer import Writer

class AppContext:
    def __init__(self):
        self.console = Console()
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load_config()
        self.state_manager = StateManager(self.config)
        self.parser = Parser(self.config)
        self.writer = Writer(self.config, self.state_manager)

    def reload(self):
        """Reloads the context after configuration changes."""
        self.config = self.config_manager.load_config()
        self.state_manager = StateManager(self.config)
        self.parser = Parser(self.config)
        self.writer = Writer(self.config, self.state_manager)

# Global context instance
ctx = AppContext()
