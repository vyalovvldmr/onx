import asyncio
import uuid
from contextlib import suppress
from enum import IntEnum
import logging

import click
import aiohttp
from aiohttp import web
from aiohttp.client_exceptions import ClientConnectionError
from rich.panel import Panel
from rich.console import Console, ConsoleOptions, RenderResult, RenderableType
from rich.text import Text
from rich.align import Align
from rich.table import Table
from pyfiglet import Figlet
from textual.app import App
from textual.views import GridView
from textual.widget import Widget
from textual.widgets import Footer as _Footer, Header as _Header
from textual.reactive import Reactive
from textual import events

from onx.version import VERSION
from onx import settings
from onx.app import get_application
from onx.game import BoxType, GameStatus
from onx.api import WsGameStateEvent, WsEvent, WsOperationPayload, WsOperation


class WebsocketConnectionState(IntEnum):
    CONNECTED = 1
    DISCONNECTED = 2


class Connect(events.Event):
    pass


class Disconnect(events.Event):
    pass


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


class Footer(_Footer):
    def __init__(self) -> None:
        super().__init__()
        self._connection_text: str = "Disconnected"
        self._connection_style: str = "white on dark_red"

    def render(self) -> RenderableType:
        if self._key_text is None:
            self._key_text = self.make_key_text()
            self._key_text.append_text(Text(f"| Websocket: {self._connection_text}"))
            self._key_text.style = self._connection_style
        return self._key_text

    def on_connect(self) -> None:
        self._key_text = None
        self._connection_text = "Connected"
        self._connection_style = "white on dark_green"
        self.refresh()

    def on_disconnect(self) -> None:
        self._key_text = None
        self._connection_text = "Disconnected"
        self._connection_style = "white on dark_red"
        self.refresh()


class FigletText:
    def __init__(self, text: str) -> None:
        self.text: str = text

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


class Tile(Widget):
    mouse_over = Reactive(False)

    def __init__(self, name: str | None = None, num: int | None = None) -> None:
        super().__init__(name)
        self.text: str = ""
        self._num: int = num

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
        await self.app.make_turn(self._num)


class Grid(GridView):
    def __init__(self, *args, grid_size: int = settings.DEFAULT_GRID_SIZE, **kwargs):
        super().__init__(*args, **kwargs)
        self._grid_size = grid_size
        self.tiles: tuple[Tile] = tuple(
            Tile(num=i) for i in range(self._grid_size**2)
        )
        if self._grid_size >= 11:
            self._col_size, self._row_size = 5, 3
        elif self._grid_size >= 9:
            self._col_size, self._row_size = 6, 4
        elif self._grid_size >= 6:
            self._col_size, self._row_size = 8, 5
        elif self._grid_size == 5:
            self._col_size, self._row_size = 15, 8
        else:
            self._col_size, self._row_size = 20, 9

    async def on_mount(self, event: events.Mount) -> None:
        self.grid.set_align("center", "center")
        self.grid.add_column("col", size=self._col_size, repeat=self._grid_size)
        self.grid.add_row("row", size=self._row_size, repeat=self._grid_size)
        self.grid.place(*self.tiles)


class GameApp(App):
    def __init__(
        self,
        *args,
        grid_size: int = settings.DEFAULT_GRID_SIZE,
        winning_length: int = settings.DEFAULT_WINNING_LENGTH,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._header: Header = Header(style="")
        self._footer: Footer = Footer()
        self._grid: Grid = Grid(grid_size=grid_size)
        self._winning_length: int = winning_length
        self._grid_size: int = grid_size
        self._player_id: str = str(uuid.uuid4())
        self._ws: None | web.WebSocketResponse = None
        self._game_status: int = GameStatus.awaiting
        self._whose_turn: str = ""
        self._box_types: dict = {
            BoxType.empty: " ",
            BoxType.nought: "0",
            BoxType.cross: "X",
        }
        self._websocket_connection_state: WebsocketConnectionState = (
            WebsocketConnectionState.DISCONNECTED
        )

    async def on_mount(self) -> None:
        await self.view.dock(self._header, edge="top")
        await self.view.dock(self._footer, edge="bottom")
        await self.view.dock(self._grid)

    async def on_load(self) -> None:
        asyncio.ensure_future(self.keep_connection())
        await self.bind("n", "new_game", "New Game")
        await self.bind("q", "quit", "Quit")

    async def action_new_game(self) -> None:
        await self._ws.close()

    async def keep_connection(self) -> None:
        URL = "ws://{host}:{port}/ws".format(
            host=settings.SERVER_HOST, port=settings.SERVER_PORT
        )
        while True:
            with suppress(ClientConnectionError):
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(
                        URL,
                        heartbeat=settings.WS_HEARTBEAT_TIMEOUT,
                        headers={
                            "Cookie": f"player_id={self._player_id};"
                            f"grid_size={self._grid_size};"
                            f"winning_length={self._winning_length}"
                        },
                    ) as ws:
                        if (
                            self._websocket_connection_state
                            == WebsocketConnectionState.DISCONNECTED
                        ):
                            self._websocket_connection_state = (
                                WebsocketConnectionState.CONNECTED
                            )
                            self._footer.post_message_no_wait(Connect(self))
                        self._ws = ws
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                ws_event = WsEvent.parse_raw(msg.data)
                                await self.on_ws_event(ws_event)
            if self._websocket_connection_state == WebsocketConnectionState.CONNECTED:
                self._websocket_connection_state = WebsocketConnectionState.DISCONNECTED
                self._footer.post_message_no_wait(Disconnect(self))
            await asyncio.sleep(settings.CLIENT_RECONNECT_TIMEOUT)

    async def on_ws_event(self, event: WsEvent) -> None:
        if isinstance(event.data, WsGameStateEvent):
            self._game_status = event.data.payload.status
            self._whose_turn = event.data.payload.whose_turn
            if (
                self._game_status == GameStatus.in_progress
                and self._whose_turn == self._player_id
            ):
                self._header.state = "Your turn"
            elif (
                self._game_status == GameStatus.in_progress
                and self._whose_turn != self._player_id
            ):
                self._header.state = "Waiting"
            elif (
                self._game_status == GameStatus.finished
                and event.data.payload.winner != self._player_id
            ):
                self._header.state = "Looser"
            elif (
                self._game_status == GameStatus.finished
                and event.data.payload.winner == self._player_id
            ):
                self._header.state = "Winner"
            elif self._game_status == GameStatus.awaiting:
                self._header.state = "Waiting"
            for num, box_type in enumerate(event.data.payload.grid):
                self._grid.tiles[num].text = self._box_types[box_type]
                self._grid.tiles[num].refresh()

    async def make_turn(self, tile_num: int) -> None:
        if (
            self._game_status == GameStatus.in_progress
            and self._whose_turn == self._player_id
        ):
            try:
                await self._ws.send_json(
                    WsOperation(payload=WsOperationPayload(turn=tile_num)).dict()
                )
            except ConnectionResetError as err:
                self.log(err)


async def run_server() -> web.Application:
    app = get_application()

    await asyncio.get_event_loop().create_server(
        app.make_handler(), settings.SERVER_HOST, settings.SERVER_PORT
    )

    logging.info(
        "server started at ws://%s:%s", settings.SERVER_HOST, settings.SERVER_PORT
    )

    return app


async def shutdown_server(app: web.Application) -> None:
    for ws in app["websockets"]:
        await ws.close()


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-d", "--daemon", is_flag=True, help="Run server.")
@click.option(
    "-g",
    "--grid-size",
    help="Grid size = 3 by default.",
    default=3,
    type=click.IntRange(min=3, max=14),
)
@click.option(
    "-w",
    "--winning-length",
    help="Winning sequence length = 3 by default.",
    default=3,
    type=click.IntRange(min=3, max=5),
)
def main(daemon: bool, grid_size: int, winning_length: int) -> None:
    """
    Noughts & Crosses game. Client and server command.
    """
    if daemon:
        logging.getLogger().addHandler(logging.StreamHandler())
        logging.getLogger().setLevel(settings.LOGGING_LEVEL)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app = loop.run_until_complete(run_server())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            logging.info("server is shutting down")
        finally:
            loop.run_until_complete(shutdown_server(app))
            loop.close()
    else:
        GameApp.run(
            title=f"Noughts & Crosses v{VERSION}",
            grid_size=grid_size,
            winning_length=winning_length,
        )


if __name__ == "__main__":
    main()
