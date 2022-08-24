"""
Server for Noughts & Crosses game.
"""
import asyncio
import logging

from noughts_and_crosses import settings
from noughts_and_crosses.app import get_application


async def init():
    app = get_application()

    await loop.create_server(
        app.make_handler(), settings.SERVER_IP, settings.SERVER_PORT
    )

    logging.info(
        "server started at ws://%s:%s", settings.SERVER_IP, settings.SERVER_PORT
    )

    return app


async def shutdown(app):
    for ws in app["websockets"]:
        await ws.close()


if __name__ == "__main__":
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.getLogger().setLevel(settings.LOGGING_LEVEL)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app = loop.run_until_complete(init())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("server is shutting down")
    finally:
        loop.run_until_complete(shutdown(app))
        loop.close()
