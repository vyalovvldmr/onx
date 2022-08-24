from aiohttp import web

from noughts_and_crosses.ws_handler import WebsocketHandler


def get_application() -> web.Application:
    app = web.Application()
    app["websockets"] = []
    app.router.add_route("GET", "/ws", WebsocketHandler)
    return app
