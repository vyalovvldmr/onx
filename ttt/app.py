from aiohttp import web

from ttt.handler import WebsocketHandler


def get_application() -> web.Application:
    app = web.Application()
    app["websockets"] = []
    app.router.add_route("GET", "/ws", WebsocketHandler)
    return app
