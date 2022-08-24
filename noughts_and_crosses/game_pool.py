from types import TracebackType

from noughts_and_crosses.ws_utils import publish_game_state
from noughts_and_crosses.game import Player, Game, GameStatus


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
            await publish_game_state(self._game)
            for player in self._game.players:
                await player.ws.close()
