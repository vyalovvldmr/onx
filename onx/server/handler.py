import json
import logging

import aiohttp
from aiohttp import web
from pydantic.error_wrappers import ValidationError

from onx.api import WsCookie
from onx.api import WsErrorEvent
from onx.api import WsErrorEventPayload
from onx.api import WsEvent
from onx.api import WsOperation
from onx.server.errors import BaseGameValidationError
from onx.server.game import GameContext
from onx.server.game import GamePool
from onx.server.game import Player

logger = logging.getLogger(__name__)


class WebsocketHandler(web.View):
    async def get(self) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(self.request)
        try:
            cookie = WsCookie(**self.request.cookies)
        except ValidationError as err:
            await self.send_error(err, ws)
            return ws
        player = Player(id=cookie.player_id, ws=ws)
        context = GameContext(
            grid_size=cookie.grid_size, winning_length=cookie.winning_length
        )
        async with GamePool(context, player) as game:
            async for message in ws:
                if message.type == aiohttp.WSMsgType.TEXT:
                    try:
                        operation = WsOperation(**json.loads(message.data))
                    except ValidationError as err:
                        await self.send_error(err, ws)
                        return ws
                    try:
                        game.turn(player, int(operation.payload.turn))
                    except BaseGameValidationError as err:
                        await self.send_error(err, ws)
                        return ws
                    await game.publish_state()
                if message.type == aiohttp.WSMsgType.ERROR:
                    logger.debug(
                        "Websocket connection closed with exception %s",
                        ws.exception(),
                    )
        logger.debug("Websocket connection closed")
        return ws

    @staticmethod
    async def send_error(error: Exception, ws: web.WebSocketResponse) -> None:
        if isinstance(error, ValidationError):
            message = str(
                ";".join(" ".join(map(str, e.values())) for e in error.errors())
            )
        else:
            message = str(error)
        logger.warning(message)
        await ws.send_json(
            WsEvent(
                data=WsErrorEvent(payload=WsErrorEventPayload(message=message))
            ).dict()
        )
