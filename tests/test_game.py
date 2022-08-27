import unittest
import uuid

from aiohttp import web

from ttt.game import Game, BoxType, Player, GameStatus, GameContext
from ttt.errors import NotYourTurnError


class GameTestCase(unittest.TestCase):

    maxDiff = None

    def test_is_winner(self):
        game = Game(GameContext())
        ws = web.WebSocketResponse()
        player = Player(id=str(uuid.uuid4()), ws=ws)
        player.box_type = BoxType.nought
        game.grid = [
            BoxType.nought,
            BoxType.cross,
            BoxType.cross,
            BoxType.nought,
            BoxType.empty,
            BoxType.empty,
            BoxType.nought,
            BoxType.empty,
            BoxType.empty,
        ]
        self.assertTrue(game.is_winner(player, 0))
        game.grid = [
            BoxType.nought,
            BoxType.cross,
            BoxType.cross,
            BoxType.nought,
            BoxType.nought,
            BoxType.empty,
            BoxType.cross,
            BoxType.nought,
            BoxType.cross,
        ]
        self.assertFalse(game.is_winner(player, 0))

    def test_gen_winning_lines(self):
        game = Game(GameContext(grid_size=4))
        self.assertEqual(
            game.gen_winning_lines(14), [[12, 13, 14, 15], [6, 10, 14], [4, 9, 14]]
        )
        self.assertEqual(
            game.gen_winning_lines(5),
            [[4, 5, 6, 7], [1, 5, 9, 13], [0, 5, 10, 15], [2, 5, 8]],
        )
        game = Game(GameContext(grid_size=3))
        self.assertEqual(
            game.gen_winning_lines(7),
            [[6, 7, 8], [1, 4, 7]],
        )

    def test_turn(self):
        game = Game(GameContext())
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
        game = Game(GameContext())
        ws = web.WebSocketResponse()
        game.add_player(Player(id=str(uuid.uuid4()), ws=ws))
        game.add_player(Player(id=str(uuid.uuid4()), ws=ws))
        game.toss()
        for player in game.players:
            self.assertNotEqual(player.box_type, BoxType.empty)
        self.assertIn(game.whose_turn, game.players)
        self.assertEqual(game.status, GameStatus.in_progress)

    def test_to_dict(self):
        game = Game(GameContext())
        self.assertDictEqual(
            game.to_dict(),
            {
                "whose_turn": None,
                "grid": [BoxType.empty] * game.context.grid_size**2,
                "winner": None,
                "status": GameStatus.awaiting,
            },
        )


if __name__ == "__main__":
    unittest.main()
