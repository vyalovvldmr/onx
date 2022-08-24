import logging


logger = logging.getLogger(__name__)


async def publish(payload, subscribers):
    for subscriber in subscribers:
        try:
            await subscriber.ws.send_json(payload)
        except ConnectionResetError as e:
            logger.warning(e)


async def send_error(error_message, ws):
    await ws.send_json(
        {
            "event": "error",
            "payload": {
                "message": error_message,
            },
        }
    )


async def publish_game_state(game):
    payload = {"event": "game_state", "payload": game.to_json()}
    await publish(payload, game.players)
