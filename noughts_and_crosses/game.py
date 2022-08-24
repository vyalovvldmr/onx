import random

from noughts_and_crosses.errors import NotYourTurnError


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

    __slots__ = ["id", "ws", "box_type"]

    def __init__(self, id, ws):
        self.id = id
        self.ws = ws
        self.box_type = BoxType.empty


class Game:

    grid_size = 3

    winning_lines = (
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6),
    )

    player_amount = 2

    def __init__(self):
        self.grid = [BoxType.empty] * Game.grid_size * Game.grid_size
        self.whose_turn = None
        self.players = []
        self.status = GameStatus.awaiting
        self.winner = None

    def add_player(self, player):
        assert len(self.players) < Game.player_amount, "Max player amount reached."
        self.players.append(player)

    def toss(self):
        assert (
            len(self.players) == Game.player_amount
        ), "Toss is applicable for two players game"
        box_types = [BoxType.nought, BoxType.cross]
        random.shuffle(box_types)
        for box_type, player in zip(box_types, self.players):
            player.box_type = box_type
        self.whose_turn = self.players[random.randint(0, 1)]
        self.status = GameStatus.in_progress

    def to_json(self):
        return {
            "whose_turn": self.whose_turn and self.whose_turn.id or None,
            "grid": self.grid,
            "winner": self.winner and self.winner.id or None,
            "status": self.status,
        }

    def turn(self, player, turn):
        assert (
            len(self.players) == Game.player_amount
        ), "Turn is applicable for two players game"
        if self.whose_turn.id != player.id:
            raise NotYourTurnError()

        self.grid[turn] = player.box_type
        self.whose_turn = [p for p in self.players if p.id != self.whose_turn.id][0]
        if self.is_winner:
            self.winner = player
            self.status = GameStatus.finished
        elif BoxType.empty not in self.grid:
            self.status = GameStatus.finished

    @property
    def is_winner(self):
        return any(
            map(
                lambda seq: set(seq) in ({BoxType.cross}, {BoxType.nought}),
                map(lambda line: (self.grid[i] for i in line), Game.winning_lines),
            )
        )
