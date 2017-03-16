from aiohttp import web

from noughts_and_crosses.ws_handler import WebsocketHandler


def get_application(loop):
    app = web.Application(loop=loop)
    app['websockets'] = []
    app.router.add_route('GET', '/ws', WebsocketHandler)
    return app
