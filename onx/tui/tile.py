from pyfiglet import Figlet  # type: ignore
from rich.align import Align
from rich.console import Console
from rich.console import ConsoleOptions
from rich.console import RenderResult
from rich.panel import Panel
from rich.text import Text
from textual import events
from textual.reactive import Reactive
from textual.widget import Widget


class FigletText:
    def __init__(self, text: str) -> None:
        self.text: str = text

    def __rich_console__(self, _: Console, options: ConsoleOptions) -> RenderResult:
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


class Tile(Widget):
    mouse_over = Reactive(False)

    def __init__(self, name: str | None = None, num: int | None = None) -> None:
        super().__init__(name)
        self.text: str = ""
        self._num: int | None = num

    def render(self) -> Panel:
        return Panel(
            Align.center(FigletText(self.text), vertical="middle"),
            style=("on red" if self.mouse_over else ""),
        )

    async def on_enter(self) -> None:
        self.mouse_over = True

    async def on_leave(self) -> None:
        self.mouse_over = False

    async def on_click(self, event: events.Click) -> None:
        await self.app.make_turn(self._num)  # type: ignore
