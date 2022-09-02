import asyncio
import logging

from aiohttp import web

from onx import settings
from onx.server.app import get_application


async def run_server() -> None:
    app = get_application()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.SERVER_HOST, settings.SERVER_PORT)
    logging.info(
        "Server started at ws://%s:%s", settings.SERVER_HOST, settings.SERVER_PORT
    )
    await site.start()


def run_event_loop():
    logging.getLogger().addHandler(logging.StreamHandler())
    logging.getLogger().setLevel(settings.LOGGING_LEVEL)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_server())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info("Server is shutting down")
