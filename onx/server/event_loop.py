import asyncio
import logging

from aiohttp import web

from onx import settings
from onx.server.app import get_application


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


def run_event_loop():
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
