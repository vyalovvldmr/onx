import unittest
import json

from schema import SchemaError

from ttt.game import Game, BoxType, Player
from ttt.ws_handler import WebsocketHandler


class ValidationTestCase(unittest.TestCase):

    maxDiff = None

    def test_missing_key_validation(self):
        game = Game()
        with self.assertRaises(SchemaError) as error:
            WebsocketHandler.validate_request(json.dumps({"operation": "turn"}), game)
        self.assertEqual(error.exception.code, "Missing key: 'payload'")

    def test_wrong_turn_number_validation(self):
        game = Game()
        with self.assertRaises(SchemaError) as error:
            WebsocketHandler.validate_request(
                json.dumps(
                    {
                        "operation": "turn",
                        "payload": {
                            "turn": 9,
                        },
                    }
                ),
                game,
            )
        self.assertEqual(error.exception.code, "Please type a number from 1 to 9.")

    def test_turn_without_second_player_validation(self):
        game = Game()
        with self.assertRaises(SchemaError) as error:
            WebsocketHandler.validate_request(
                json.dumps(
                    {
                        "operation": "turn",
                        "payload": {
                            "turn": 0,
                        },
                    }
                ),
                game,
            )
        self.assertEqual(
            error.exception.code, "Turn is applicable for two players game"
        )

    def test_unsupported_operation_validation(self):
        game = Game()
        game.players = [Player, Player]

        with self.assertRaises(SchemaError) as error:
            WebsocketHandler.validate_request(
                json.dumps(
                    {
                        "operation": "foo",
                        "payload": {
                            "turn": 0,
                        },
                    }
                ),
                game,
            )
        self.assertEqual(error.exception.code, "Unsupported operation.")

        result = WebsocketHandler.validate_request(
            json.dumps(
                {
                    "operation": "turn",
                    "payload": {
                        "turn": 0,
                    },
                }
            ),
            game,
        )
        self.assertDictEqual(
            result,
            {
                "operation": "turn",
                "payload": {
                    "turn": 0,
                },
            },
        )

    def test_bo_is_not_empty_validation(self):
        game = Game()
        game.grid = [BoxType.nought] * Game.grid_size * Game.grid_size

        with self.assertRaises(SchemaError) as error:
            WebsocketHandler.validate_request(
                json.dumps(
                    {
                        "operation": "turn",
                        "payload": {
                            "turn": 0,
                        },
                    }
                ),
                game,
            )
        self.assertEqual(error.exception.code, "Box is not empty. Try again.")


if __name__ == "__main__":
    unittest.main()
