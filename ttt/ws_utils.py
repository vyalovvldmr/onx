import logging
from typing import Literal

from aiohttp import web
from pydantic import BaseModel

from ttt.game import Player, Game


logger = logging.getLogger(__name__)


class WsErrorEventPayload(BaseModel):
    message: str


class WsErrorEvent(BaseModel):
    event: Literal["error"] = "error"
    payload: WsErrorEventPayload


class WsGameStatePayload(BaseModel):
    whose_turn: str | None
    grid: list[int]
    winner: str | None
    status: int


class WsGameStateEvent(BaseModel):
    event: Literal["game_state"] = "game_state"
    payload: WsGameStatePayload


class WsEvent(BaseModel):
    data: WsGameStateEvent | WsErrorEvent


class WsOperationPayload(BaseModel):
    turn: int


class WsOperation(BaseModel):
    operation: str = "turn"
    payload: WsOperationPayload


async def publish(payload: dict, subscribers: list[Player]) -> None:
    for subscriber in subscribers:
        try:
            await subscriber.ws.send_json(payload)
        except ConnectionResetError as err:
            logger.warning(err)


async def send_error(error_message: str, ws: web.WebSocketResponse) -> None:
    await ws.send_json(
        WsEvent(
            data=WsErrorEvent(payload=WsErrorEventPayload(message=error_message))
        ).dict()
    )


async def publish_game_state(game: Game) -> None:
    payload = {"data": {"event": "game_state", "payload": game.to_json()}}
    await publish(payload, game.players)
