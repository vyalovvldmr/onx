from aiohttp import web

from onx.server.handler import WebsocketHandler


async def index_handler(_) -> web.Response:
    return web.json_response({})


def get_application() -> web.Application:
    app = web.Application()
    app.router.add_route("GET", "/", index_handler)
    app.router.add_route("GET", "/ws", WebsocketHandler)
    return app
