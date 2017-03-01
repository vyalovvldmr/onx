import unittest
import json

from schema import SchemaError

from server import WebsocketHandler, Game, BoxType


class GameTestCase(unittest.TestCase):

    maxDiff = False

    def test_is_winner(self):
        game = Game()
        game.grid = [
            BoxType.nought, BoxType.cross, BoxType.cross,
            BoxType.nought, BoxType.empty, BoxType.empty,
            BoxType.nought, BoxType.empty, BoxType.empty,
        ]
        self.assertEqual(game.is_winner, True)
        game.grid = [
            BoxType.nought, BoxType.cross, BoxType.cross,
            BoxType.nought, BoxType.nought, BoxType.empty,
            BoxType.cross, BoxType.nought, BoxType.cross,
        ]
        self.assertEqual(game.is_winner, False)

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
        self.assertEqual(
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
