"""
Server for Noughts & Crosses game.
"""
import asyncio
import json
import random

import aiohttp
from aiohttp import web
from schema import Schema, Use, And, SchemaError


GRID_SIZE = 3


class BoxType:

    empty = 1
    nought = 2
    cross = 3


class GameStatus:

    # game is waiting for a player
    awaiting = 1
    # game is in progress
    in_progress = 2
    # some player gone
    unfinished = 3
    # game is finished
    finished = 4


class Player:

    __slots__ = ['id', 'ws', 'box_type']

    def __init__(self, id, ws):
        self.id = id
        self.ws = ws
        self.box_type = BoxType.empty


class Game:

    winning_lines = (
        (0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
        (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)
    )

    def __init__(self):
        self.grid = [BoxType.empty] * GRID_SIZE * GRID_SIZE
        self.whose_turn = None
        self.players = []
        self.status = GameStatus.awaiting
        self.winner = None

    def add_player(self, player):
        self.players.append(player)

    def toss(self):
        assert len(self.players) == 2, \
            'Toss is applicable for two players game'
        box_types = [BoxType.nought, BoxType.cross]
        random.shuffle(box_types)
        for box_type, player in zip(box_types, self.players):
            player.box_type = box_type
        self.whose_turn = self.players[random.randint(0, 1)]
        self.status = GameStatus.in_progress

    async def close(self):
        for player in self.players:
            await player.ws.close()

    def to_json(self):
        return {
            'whose_turn': self.whose_turn and self.whose_turn.id or None,
            'grid': self.grid,
            'winner': self.winner and self.winner.id or None,
            'status': self.status,
        }

    def turn(self, player, turn):
        self.grid[turn] = player.box_type
        self.whose_turn = [p for p in self.players if p.id != self.whose_turn.id][0]
        if self.is_winner:
            self.winner = player.id
        elif BoxType.empty not in self.grid:
            self.status = GameStatus.finished

    @property
    def is_winner(self):
        return any(
            map(
                lambda seq: set(seq) in ({BoxType.cross}, {BoxType.nought}),
                map(
                    lambda line: (self.grid[i] for i in line),
                    Game.winning_lines
                )
            )
        )


class GamePool:

    _awaiting = None

    def __init__(self, player):
        self._player = player
        self._game = None

    async def __aenter__(self):
        if GamePool._awaiting:
            self._game = self._awaiting
            GamePool._awaiting = None
            self._game.add_player(self._player)
            self._game.toss()
        else:
            self._game = Game()
            self._game.add_player(self._player)
            GamePool._awaiting = self._game
        return self._game

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if GamePool._awaiting is self._game:
            GamePool._awaiting = None
        await self._game.close()



class WebsocketHandler:

    @staticmethod
    def publish(payload, subscribers):
        for subscriber in subscribers:
            subscriber.ws.send_json(payload)

    @staticmethod
    def send_error(error_message, player):
        player.ws.send_json({
            'event': 'error',
            'payload': {
                'message': error_message,
            }
        })

    def publish_game_state(self, game):
        payload = {
            'event': 'game_state',
            'payload': game.to_json()
        }
        self.publish(payload, game.players)

    @staticmethod
    def validate_request(data, game):
        schema = Schema(
            And(
                Use(json.loads),
                {
                    'operation': And(
                        str,
                        lambda x: x == 'turn',
                        error='Unsupported operation.'
                    ),
                    'payload': {
                        'turn': And(
                            int,
                            Schema(
                                lambda x: x in range(9),
                                error='Please type a number from 1 to 9.'
                            ),
                            Schema(
                                lambda x: game.grid[x] == BoxType.empty,
                                error='Box is not empty. Try again.'
                            ),
                        )
                    },
                }
            )
        )
        return schema.validate(data)

    async def serve(self, request):

        ws = web.WebSocketResponse()
        await ws.prepare(request)
        player = Player(id=request.cookies['player_id'], ws=ws)

        async with GamePool(player) as game:
            self.publish_game_state(game)
            async for message in ws:
                if message.type == aiohttp.WSMsgType.TEXT:
                    try:
                        request = self.validate_request(message.data, game)
                    except SchemaError as error:
                        self.send_error(error.code, player)
                    else:
                        game.turn(player, int(request['payload']['turn']))
                        self.publish_game_state(game)

        print('websocket connection closed')

        return ws


SERVER_IP = '127.0.0.1'
SERVER_PORT = '8080'


async def init(loop):
    app = web.Application(loop=loop)
    ws = WebsocketHandler()
    app.router.add_route('GET', '/ws', ws.serve)

    srv = await loop.create_server(
        app.make_handler(), SERVER_IP, SERVER_PORT)
    print('Server started at http://{}:{}'.format(SERVER_IP, SERVER_PORT))
    return srv


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
