import unittest
import uuid

from aiohttp import web

from noughts_and_crosses.game import (
    Game, BoxType, Player, GameStatus
)
from noughts_and_crosses.errors import NotYourTurnError


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

    def test_toss(self):
        game = Game()
        ws = web.WebSocketResponse()
        game.add_player(Player(id=str(uuid.uuid4()), ws=ws))
        game.add_player(Player(id=str(uuid.uuid4()), ws=ws))
        game.toss()
        for player in game.players:
            self.assertNotEqual(player.box_type, BoxType.empty)
        self.assertIn(game.whose_turn, game.players)
        self.assertEqual(game.status, GameStatus.in_progress)

    def test_to_json(self):
        game = Game()
        self.assertDictEqual(
            game.to_json(),
            {
                'whose_turn': None,
                'grid': [BoxType.empty] * Game.grid_size * Game.grid_size,
                'winner': None,
                'status': GameStatus.awaiting,
            }
        )

if __name__ == '__main__':
    unittest.main()
