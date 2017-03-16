import unittest
import json

from schema import SchemaError

from noughts_and_crosses.game import (
    Game, BoxType, Player
)
from noughts_and_crosses.ws_handler import WebsocketHandler


class ValidationTestCase(unittest.TestCase):

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
