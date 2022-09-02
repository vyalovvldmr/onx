import logging
import random
from dataclasses import dataclass
from types import TracebackType

from aiohttp import web
from cachetools import TTLCache

from onx import settings
from onx.api import WsEvent
from onx.api import WsGameStateEvent
from onx.api import WsGameStatePayload
from onx.server.errors import NotYourTurnError

logger = logging.getLogger(__name__)


class BoxType:
    empty: int = 1
    nought: int = 2
    cross: int = 3
    opposite: dict = {cross: nought, nought: cross}


class GameStatus:
    # game is waiting for a player
    awaiting: int = 100
    # game is in progress
    in_progress: int = 200
    # game is finished
    finished: int = 300


@dataclass
class Player:
    id: str
    ws: web.WebSocketResponse
    box_type: int = BoxType.empty


@dataclass(eq=True, frozen=True)
class GameContext:
    winning_length: int = settings.DEFAULT_WINNING_LENGTH
    grid_size: int = settings.DEFAULT_GRID_SIZE


class Game:
    player_amount: int = 2

    def __init__(self, context: GameContext) -> None:
        self.grid: list[int] = [BoxType.empty] * context.grid_size**2
        self.context = context
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

    def substitute_player(self, player: Player) -> None:
        for num, plr in enumerate(self.players):
            if plr.id == player.id:
                player.box_type = plr.box_type
                self.players[num] = player
                break

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
        if self.is_winner(player, turn):
            self.winner = player
            self.status = GameStatus.finished
            logger.debug("Game finished")
        elif BoxType.empty not in self.grid:
            self.status = GameStatus.finished
            logger.debug("Game finished")

    def gen_winning_lines(self, turn: int) -> list[list[int]]:
        row_num = turn // self.context.grid_size
        return list(
            filter(
                lambda x: len(x) >= self.context.winning_length,
                [
                    # horizontal
                    [
                        num
                        for num in range(
                            turn - self.context.winning_length + 1,
                            turn + self.context.winning_length,
                        )
                        if num // self.context.grid_size == row_num
                    ],
                    # vertical
                    [
                        num
                        for num in range(
                            turn
                            - (self.context.winning_length - 1)
                            * self.context.grid_size,
                            turn + self.context.winning_length * self.context.grid_size,
                            self.context.grid_size,
                        )
                        if 0 <= num < self.context.grid_size**2
                    ],
                    # main diagonal
                    [
                        num
                        for shift, num in enumerate(
                            range(
                                turn
                                - (self.context.winning_length - 1)
                                * (self.context.grid_size + 1),
                                turn
                                + self.context.winning_length
                                * (self.context.grid_size + 1),
                                self.context.grid_size + 1,
                            ),
                            start=-self.context.winning_length + 1,
                        )
                        if 0 <= num < self.context.grid_size**2
                        and num // self.context.grid_size == row_num + shift
                    ],
                    # minor diagonal
                    [
                        num
                        for shift, num in enumerate(
                            range(
                                turn
                                - (self.context.winning_length - 1)
                                * (self.context.grid_size - 1),
                                turn
                                + self.context.winning_length
                                * (self.context.grid_size - 1),
                                self.context.grid_size - 1,
                            ),
                            start=-self.context.winning_length + 1,
                        )
                        if 0 <= num < self.context.grid_size**2
                        and num // self.context.grid_size == row_num + shift
                    ],
                ],
            )
        )

    def is_winner(self, player: Player, turn: int) -> bool:
        return any(
            any(
                len(s.replace(str(BoxType.empty), "")) == self.context.winning_length
                for s in "".join(
                    map(lambda x: str(self.grid[x]), line),
                ).split(str(BoxType.opposite[player.box_type]))
            )
            for line in self.gen_winning_lines(turn)
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

    _awaiting: dict[GameContext, Game] = {}
    _active_games: TTLCache[str, Game] = TTLCache(maxsize=10**6, ttl=60 * 60)

    def __init__(self, context: GameContext, player: Player):
        self._context: GameContext = context
        self._player: Player = player
        self._game: Game | None = None

    async def __aenter__(self) -> Game:
        if (
            self._player.id in GamePool._active_games
            and GamePool._active_games[self._player.id].status == GameStatus.in_progress
        ):
            self._game = GamePool._active_games[self._player.id]
            self._game.substitute_player(self._player)
            logger.debug(
                "Game retrieved after disconnection for player_id=%s", self._player.id
            )
        elif self._context in GamePool._awaiting:
            self._game = GamePool._awaiting[self._context]
            del GamePool._awaiting[self._context]
            self._game.add_player(self._player)
            GamePool._active_games[self._player.id] = self._game
            self._game.toss()
            logger.debug("Game started")
        else:
            self._game = Game(self._context)
            self._game.add_player(self._player)
            GamePool._active_games[self._player.id] = self._game
            GamePool._awaiting[self._context] = self._game
            logger.debug("Game created")
        await self._game.publish_state()
        return self._game

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if (
            self._context in GamePool._awaiting
            and GamePool._awaiting[self._context] is self._game
        ):
            del GamePool._awaiting[self._context]
