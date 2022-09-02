import asyncio
import uuid
from contextlib import suppress
from enum import IntEnum

import aiohttp
from textual.app import App

from onx import settings
from onx.api import WsEvent
from onx.api import WsGameStateEvent
from onx.api import WsOperation
from onx.api import WsOperationPayload
from onx.server.game import BoxType
from onx.server.game import GameStatus
from onx.tui.events import Connect
from onx.tui.events import Disconnect
from onx.tui.footer import Footer
from onx.tui.grid import Grid
from onx.tui.header import Header


class WebsocketConnectionState(IntEnum):
    CONNECTED = 1
    DISCONNECTED = 2


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
        self._ws: None | aiohttp.client.ClientWebSocketResponse = None
        self._game_status: int = GameStatus.awaiting
        self._whose_turn: None | str = ""
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
        self._player_id = str(uuid.uuid4())
        if self._ws:
            await self._ws.close()

    async def keep_connection(self) -> None:
        url = f"ws://{settings.SERVER_HOST}:{settings.SERVER_PORT}/ws"
        while True:
            with suppress(aiohttp.ClientConnectionError):
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(
                        url,
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
            if self._ws:
                try:
                    await self._ws.send_json(
                        WsOperation(payload=WsOperationPayload(turn=tile_num)).dict()
                    )
                except ConnectionResetError as err:
                    self.log(err)
