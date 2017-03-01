import unittest
import json
import uuid

from schema import SchemaError
from aiohttp import web

from server import WebsocketHandler, Game, BoxType, Player
from errors import NotYourTurnError


class GameTestCase(unittest.TestCase):

    maxDiff = None

    def test_is_winner(self):
        game = Game()
        game.grid = [
            BoxType.nought, BoxType.cross, BoxType.cross,
            BoxType.nought, BoxType.empty, BoxType.empty,
            BoxType.nought, BoxType.empty, BoxType.empty,
        ]
        self.assertTrue(game.is_winner)
        game.grid = [
            BoxType.nought, BoxType.cross, BoxType.cross,
            BoxType.nought, BoxType.nought, BoxType.empty,
            BoxType.cross, BoxType.nought, BoxType.cross,
        ]
        self.assertFalse(game.is_winner)

    def test_turn(self):
        game = Game()
        ws = web.WebSocketResponse()
        game.add_player(Player(id=str(uuid.uuid4()), ws=ws))
        game.add_player(Player(id=str(uuid.uuid4()), ws=ws))
        game.toss()
        player = [p for p in game.players if p.id != game.whose_turn.id][0]

        with self.assertRaises(NotYourTurnError):
            game.turn(player, 0)

        player = game.whose_turn
        game.turn(player, 0)
        self.assertTrue(game.whose_turn.id != player.id)
        self.assertEqual(game.grid[0], player.box_type)


class WebsocketHandlerTestCase(unittest.TestCase):

    maxDiff = None

    def test_validation(self):
        game = Game()
        with self.assertRaises(SchemaError) as error:
            WebsocketHandler.validate_request(
                json.dumps({
                    'operation': 'turn'
                }),
                game
            )
        self.assertEqual(error.exception.code, 'Missing keys: \'payload\'')

        with self.assertRaises(SchemaError) as error:
            WebsocketHandler.validate_request(
                json.dumps({
                    'operation': 'turn',
                    'payload': {
                        'turn': 9,
                    }
                }),
                game
            )
        self.assertEqual(
            error.exception.code,
            'Please type a number from 1 to 9.'
        )

        with self.assertRaises(SchemaError) as error:
            WebsocketHandler.validate_request(
                json.dumps({
                    'operation': 'turn',
                    'payload': {
                        'turn': 0,
                    }
                }),
                game
            )
        self.assertEqual(
            error.exception.code,
            'Turn is applicable for two players game'
        )

        game.players = [Player, Player]

        with self.assertRaises(SchemaError) as error:
            WebsocketHandler.validate_request(
                json.dumps({
                    'operation': 'foo',
                    'payload': {
                        'turn': 0,
                    }
                }),
                game
            )
        self.assertEqual(error.exception.code, 'Unsupported operation.')

        result = WebsocketHandler.validate_request(
            json.dumps({
                'operation': 'turn',
                'payload': {
                    'turn': 0,
                }
            }),
            game
        )
        self.assertDictEqual(
            result,
            {
                'operation': 'turn',
                'payload': {
                    'turn': 0,
                }
            }
        )

        game.grid = [BoxType.nought] * Game.grid_size * Game.grid_size

        with self.assertRaises(SchemaError) as error:
            WebsocketHandler.validate_request(
                json.dumps({
                    'operation': 'turn',
                    'payload': {
                        'turn': 0,
                    }
                }),
                game
            )
        self.assertEqual(error.exception.code, 'Box is not empty. Try again.')


if __name__ == '__main__':
    unittest.main()
