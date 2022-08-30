from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from textual.reactive import Reactive
from textual.widgets import Header as _Header


class Header(_Header):
    state: Reactive = Reactive("Waiting")

    def render(self) -> RenderableType:
        header_table = Table.grid(padding=(0, 1), expand=True)
        header_table.style = self.style
        header_table.add_column("title", justify="center", ratio=1)
        header_table.add_column("state", justify="right", width=8)
        header_table.add_row(self.full_title, self.state)
        header: RenderableType
        header = Panel(header_table, style=self.style) if self.tall else header_table
        return header
