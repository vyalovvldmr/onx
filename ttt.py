from random import randint

from noughts_and_crosses.version import version

from rich.panel import Panel
from rich.console import Console, ConsoleOptions, RenderResult, RenderableType
from rich.text import Text
from rich.align import Align
from rich.table import Table
from pyfiglet import Figlet
from textual.app import App
from textual.views import GridView
from textual.widget import Widget
from textual.widgets import Footer, Header as _Header
from textual.reactive import Reactive
from textual import events


class Header(_Header):
    def render(self) -> RenderableType:
        header_table = Table.grid(padding=(0, 1), expand=True)
        header_table.style = self.style
        header_table.add_column("title", justify="center", ratio=1)
        header_table.add_column("clock", justify="right", width=8)
        header_table.add_row(
            self.full_title, self.get_clock() if self.clock else ""
        )
        header: RenderableType
        header = Panel(header_table, style=self.style) if self.tall else header_table
        return header


class FigletText:
    def __init__(self, text: str) -> None:
        self.text = text

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        size = min(options.max_width / 2, options.max_height)
        if size < 4:
            yield Text(self.text, style="bold")
        else:
            if size < 7:
                font_name = "mini"
            elif size < 8:
                font_name = "small"
            elif size < 10:
                font_name = "standard"
            else:
                font_name = "big"
            font = Figlet(font=font_name, width=options.max_width)
            yield Text(font.renderText(self.text).rstrip("\n"), style="bold")


class Hover(Widget):
    mouse_over = Reactive(False)

    def __init__(self, name: str | None = None) -> None:
        super().__init__(name)
        self._state: str | None = None

    def render(self) -> Panel:
        if self._state is None:
            text = ""
        else:
            text = self._state
        return Panel(
            Align.center(FigletText(text), vertical="middle"),
            style=("on red" if self.mouse_over else ""),
        )

    def on_enter(self) -> None:
        self.mouse_over = True

    def on_leave(self) -> None:
        self.mouse_over = False

    def on_click(self, event: events.Click) -> None:
        if self._state is None:
            self._state = "0X"[randint(0, 1)]
            self.refresh()


class Grid(GridView):
    def on_mount(self, event: events.Mount) -> None:
        self.grid.set_gap(1, 0)
        self.grid.set_gutter(10)
        self.grid.set_align("center", "center")

        self.grid.add_column("col", min_size=10, max_size=30, repeat=3)
        self.grid.add_row("row", min_size=10, max_size=30, repeat=3)

        self.grid.place(*(Hover() for _ in range(9)))


class SimpleApp(App):
    async def on_mount(self) -> None:
        await self.view.dock(Header(style="", clock=False), edge="top")
        await self.view.dock(Footer(), edge="bottom")
        await self.view.dock(Grid())

    async def on_load(self) -> None:
        await self.bind("q", "quit", "Quit")


SimpleApp.run(title=f"Noughts & Crosses v{version}")
