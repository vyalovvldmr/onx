"""
Server for Noughts & Crosses game.
"""
import asyncio

from aiohttp import web
import simplejson as json

from decorators import context


SERVER_IP = '127.0.0.1'
SERVER_PORT = '8080'


@context
async def game(request, context=None):
    if isinstance(context.turn, int):
        context.game.turn(context.player, context.turn)
    new_condition = await context.player.queue.get()
    return web.Response(text=json.dumps(new_condition))


async def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/game/', game)

    srv = await loop.create_server(
        app.make_handler(), SERVER_IP, SERVER_PORT)
    print('Server started at http://{}:{}'.format(SERVER_IP, SERVER_PORT))
    return srv


loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
