import random
import logging
from types import TracebackType

from aiohttp import web

from ttt.errors import NotYourTurnError
from ttt import settings
from ttt.api import WsEvent, WsGameStateEvent, WsGameStatePayload


logger = logging.getLogger(__name__)


class BoxType:
    empty: int = 1
    nought: int = 2
    cross: int = 3


class GameStatus:

    # game is waiting for a player
    awaiting: int = 1
    # game is in progress
    in_progress: int = 2
    # some player gone
    unfinished: int = 3
    # game is finished
    finished: int = 4


class Player:

    __slots__ = ["id", "ws", "box_type"]

    def __init__(self, id, ws):  # pylint: disable=W0622
        self.id: int = id
        self.ws: web.WebSocketResponse = ws
        self.box_type: int = BoxType.empty


class Game:

    grid_size: int = settings.GRID_SIZE

    winning_lines: tuple[tuple[int, ...], ...] = (
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        (0, 4, 8),
        (2, 4, 6),
    )

    player_amount: int = 2

    def __init__(self) -> None:
        self.grid: list[int] = [BoxType.empty] * Game.grid_size * Game.grid_size
        self.whose_turn: Player | None = None
        self.players: list[Player] = []
        self.status: int = GameStatus.awaiting
        self.winner: Player | None = None

    def add_player(self, player: Player) -> None:
        assert len(self.players) < Game.player_amount, "Max player amount reached."
        self.players.append(player)

    def toss(self) -> None:
        assert (
            len(self.players) == Game.player_amount
        ), "Toss is applicable for two players game"
        box_types = [BoxType.nought, BoxType.cross]
        random.shuffle(box_types)
        for box_type, player in zip(box_types, self.players):
            player.box_type = box_type
        self.whose_turn = self.players[random.randint(0, 1)]
        self.status = GameStatus.in_progress

    def to_dict(self) -> dict:
        return {
            "whose_turn": self.whose_turn and self.whose_turn.id or None,
            "grid": self.grid,
            "winner": self.winner and self.winner.id or None,
            "status": self.status,
        }

    def turn(self, player: Player, turn: int) -> None:
        assert (
            len(self.players) == Game.player_amount
        ), "Turn is applicable for two players game"
        if self.whose_turn is None or self.whose_turn.id != player.id:
            raise NotYourTurnError()

        self.grid[turn] = player.box_type
        self.whose_turn = [p for p in self.players if p.id != self.whose_turn.id][0]
        if self.is_winner:
            self.winner = player
            self.status = GameStatus.finished
        elif BoxType.empty not in self.grid:
            self.status = GameStatus.finished

    @property
    def is_winner(self) -> bool:
        return any(
            map(
                lambda seq: set(seq) in ({BoxType.cross}, {BoxType.nought}),
                map(lambda line: (self.grid[i] for i in line), Game.winning_lines),
            )
        )

    async def publish_state(self) -> None:
        payload = WsEvent(
            data=WsGameStateEvent(payload=WsGameStatePayload(**self.to_dict()))
        )
        for subscriber in self.players:
            try:
                await subscriber.ws.send_json(payload.dict())
            except ConnectionResetError as err:
                logger.warning(err)


class GamePool:

    _awaiting: Game | None = None

    def __init__(self, player: Player):
        self._player: Player = player
        self._game: Game | None = None

    async def __aenter__(self) -> Game:
        if GamePool._awaiting:
            self._game, GamePool._awaiting = GamePool._awaiting, None
            self._game.add_player(self._player)
            self._game.toss()
        else:
            self._game = Game()
            self._game.add_player(self._player)
            GamePool._awaiting = self._game
        return self._game

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if GamePool._awaiting is self._game:
            GamePool._awaiting = None
        if self._game is not None:
            if self._game.status == GameStatus.in_progress:
                self._game.status = GameStatus.unfinished
            await self._game.publish_state()
            for player in self._game.players:
                await player.ws.close()