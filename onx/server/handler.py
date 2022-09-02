import json
import logging

import aiohttp
from aiohttp import web
from schema import And  # type: ignore
from schema import Schema  # type: ignore
from schema import SchemaError  # type: ignore
from schema import Use  # type: ignore

from onx import settings
from onx.api import WsErrorEvent
from onx.api import WsErrorEventPayload
from onx.api import WsEvent
from onx.server.errors import NotYourTurnError
from onx.server.game import BoxType
from onx.server.game import Game
from onx.server.game import GameContext
from onx.server.game import GamePool
from onx.server.game import Player


class WebsocketHandler(web.View):
    @staticmethod
    def validate_request(data: str, game: Game) -> dict:
        schema = Schema(
            And(
                Use(json.loads),
                {
                    "operation": And(
                        str, lambda x: x == "turn", error="Unsupported operation."
                    ),
                    "payload": {
                        "turn": And(
                            int,
                            Schema(
                                lambda x: x in range(game.context.grid_size**2),
                                error="Invalid turn number.",
                            ),
                            Schema(
                                lambda x: game.grid[x] == BoxType.empty,
                                error="Box is not empty. Try again.",
                            ),
                            Schema(
                                lambda x: len(game.players) == Game.player_amount,
                                error="Turn is applicable for two players game",
                            ),
                        )
                    },
                },
            )
        )
        return schema.validate(data)

    @staticmethod
    async def send_error(error_message: str, ws: web.WebSocketResponse) -> None:
        await ws.send_json(
            WsEvent(
                data=WsErrorEvent(payload=WsErrorEventPayload(message=error_message))
            ).dict()
        )

    async def get(self) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)

        try:
            player_id = self.request.cookies["player_id"]
        except KeyError:
            await self.send_error("player_id cookie required", ws)
        else:
            try:
                greed_size = int(str(self.request.cookies.get("grid_size")))
            except (TypeError, ValueError):
                greed_size = settings.DEFAULT_GRID_SIZE
            try:
                winning_length = int(str(self.request.cookies.get("winning_length")))
            except (TypeError, ValueError):
                winning_length = settings.DEFAULT_WINNING_LENGTH
            player = Player(id=player_id, ws=ws)
            context = GameContext(grid_size=greed_size, winning_length=winning_length)
            async with GamePool(context, player) as game:
                async for message in ws:
                    if message.type == aiohttp.WSMsgType.TEXT:
                        try:
                            request = self.validate_request(message.data, game)
                        except SchemaError as error:
                            await self.send_error(error.code, ws)
                        else:
                            try:
                                game.turn(player, int(request["payload"]["turn"]))
                            except NotYourTurnError:
                                await self.send_error("Not your turn", ws)
                            else:
                                await game.publish_state()
                    if message.type == aiohttp.WSMsgType.ERROR:
                        logging.debug(
                            "Websocket connection closed with exception %s",
                            ws.exception(),
                        )
        logging.debug("Websocket connection closed")
        return ws
