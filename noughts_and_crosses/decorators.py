from collections import namedtuple

from aiohttp import web
import simplejson as json

from game_pool import game_pool
from errors import GameNotFoundError, PlayerNotFoundError, ValidationError


Context = namedtuple('Context', 'game, player, turn')


def context(func):
    """Provides some validation and passes context to the handler."""
    async def wrapper(request, *args, **kwargs):
        game_id = request.GET.get('game_id')
        player_id = request.GET.get('player_id')
        turn = request.GET.get('turn')

        try:
            game = game_pool.retrieve_game(game_id, player_id)
        except GameNotFoundError:
            response = {'error_message': 'Game Not Found.'}
            return web.Response(text=json.dumps(response))
        except PlayerNotFoundError:
            response = {'error_message': 'Access Denied.'}
            return web.Response(text=json.dumps(response))

        player = game.get_player(player_id)

        if isinstance(turn, str):
            try:
                turn = game.validate_turn(player, turn)
            except ValidationError as e:
                response = game.as_dict({'error_message': e.message})
                return web.Response(text=json.dumps(response))

        context = Context(game=game, player=player, turn=turn)
        return await func(request, context=context, *args, **kwargs)
    return wrapper
