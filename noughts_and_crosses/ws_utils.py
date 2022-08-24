import logging

from aiohttp import web

from noughts_and_crosses.game import Player, Game


logger = logging.getLogger(__name__)


async def publish(payload: dict, subscribers: list[Player]) -> None:
    for subscriber in subscribers:
        try:
            await subscriber.ws.send_json(payload)
        except ConnectionResetError as e:
            logger.warning(e)


async def send_error(error_message: str, ws: web.WebSocketResponse) -> None:
    await ws.send_json(
        {
            "event": "error",
            "payload": {
                "message": error_message,
            },
        }
    )


async def publish_game_state(game: Game) -> None:
    payload = {"event": "game_state", "payload": game.to_json()}
    await publish(payload, game.players)
