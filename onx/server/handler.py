import json
import logging

import aiohttp
from aiohttp import web
from pydantic.error_wrappers import ValidationError

from onx import settings
from onx.api import WsErrorEvent
from onx.api import WsErrorEventPayload
from onx.api import WsEvent
from onx.api import WsOperation
from onx.server.errors import BoxIsNotEmptyError
from onx.server.errors import InvalidTurnNumberError
from onx.server.errors import NotYourTurnError
from onx.server.errors import TurnWithoutSecondPlayerError
from onx.server.game import GameContext
from onx.server.game import GamePool
from onx.server.game import Player


class WebsocketHandler(web.View):
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
                            operation = WsOperation(**json.loads(message.data))
                        except ValidationError as err:
                            await self.send_error(str(err), ws)
                        else:
                            try:
                                game.turn(player, int(operation.payload.turn))
                            except (
                                NotYourTurnError,
                                InvalidTurnNumberError,
                                BoxIsNotEmptyError,
                                TurnWithoutSecondPlayerError,
                            ) as err:
                                await self.send_error(str(err), ws)
                            else:
                                await game.publish_state()
                    if message.type == aiohttp.WSMsgType.ERROR:
                        logging.debug(
                            "Websocket connection closed with exception %s",
                            ws.exception(),
                        )
        logging.debug("Websocket connection closed")
        return ws
