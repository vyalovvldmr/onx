from noughts_and_crosses.game import Game, GameStatus
from noughts_and_crosses.ws_utils import publish_game_state


class GamePool:

    _awaiting = None

    def __init__(self, player):
        self._player = player
        self._game = None

    async def __aenter__(self):
        if GamePool._awaiting:
            self._game = self._awaiting
            GamePool._awaiting = None
            self._game.add_player(self._player)
            self._game.toss()
        else:
            self._game = Game()
            self._game.add_player(self._player)
            GamePool._awaiting = self._game
        return self._game

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if GamePool._awaiting is self._game:
            GamePool._awaiting = None
        if self._game.status == GameStatus.in_progress:
            self._game.status = GameStatus.unfinished
        publish_game_state(self._game)
        for player in self._game.players:
            await player.ws.close()
