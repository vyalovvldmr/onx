import json
import logging

import aiohttp
from aiohttp import web
from schema import Schema, Use, And, SchemaError  # type: ignore

from ttt.game import BoxType, Player, Game, GamePool
from ttt.errors import NotYourTurnError
from ttt.api import WsErrorEventPayload, WsErrorEvent, WsEvent


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
                                lambda x: x in range(9),
                                error="Please type a number from 1 to 9.",
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
        self.request.app["websockets"].append(ws)

        try:
            player_id = self.request.cookies["player_id"]
        except KeyError:
            await self.send_error("player_id cookie required", ws)
        else:
            player = Player(id=player_id, ws=ws)

            async with GamePool(player) as game:
                await game.publish_state()
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
                            "ws connection closed with exception %s", ws.exception()
                        )

        logging.debug("websocket connection closed")
        self.request.app["websockets"].remove(ws)

        return ws
