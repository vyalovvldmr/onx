import uuid
import asyncio
from enum import Enum

from errors import GameNotFoundError, PlayerNotFoundError, ValidationError


# Different size of grid isn't supported actually :(
GRID_SIZE = 3


class Box(Enum):
    empty = 1
    nought = 2
    cross = 3


class Player:
    __slots__ = ['id', 'queue', 'type']

    def __init__(self, player_id, player_type):
        self.id = player_id
        self.type = player_type
        self.queue = asyncio.Queue()


class Game:
    """Manages game condition and players."""
    __slots__ = ['id', 'players', 'grid', 'current_turn']

    def __init__(self):
        self.id = uuid.uuid4().hex
        self.players = {}
        self.grid = [Box.empty.value] * GRID_SIZE * GRID_SIZE
        self.current_turn = None

    def get_player(self, player_id):
        """Gets player by player ID.

        Args:
            player_id (str): Player ID.

        Returns:
            An instance of Player() class.

        """
        return self.players.get(player_id)

    def get_opponent(self, player_id):
        """Gets the opposite player to given player ID.

        Args:
            player_id (str): Player ID.

        Returns:
            An instance of Player() class.

        """
        opponent_id = (set(self.players.keys()) - {player_id}).pop()
        return self.players.get(opponent_id)

    def init(self, player_id):
        """Creates and adds first player to the game.

        Args:
            player_id (str): Player ID.

        """
        player = Player(player_id, Box.nought.value)
        self.players.update({player_id: player})
        self.current_turn = player_id

    def activate(self, player_id):
        """Creates and adds second player to the game. Notify first player.

        Args:
            player_id (str): Player ID.

        """
        player = Player(player_id, Box.cross.value)
        self.players.update({player_id: player})
        opponent = self.get_opponent(player_id)
        opponent.queue.put_nowait(self.as_dict())

    def validate_turn(self, player, turn):
        """Validates user input.

        Args:
            player (Player): Instanse of Player() class.
            turn (str): User input. Box number is expected.

        Returns:
            Valid box number of player's turn (int).

        Raises:
            ValidationError: An error occurred in case of invalid user input.

        """
        try:
            turn = int(turn)
        except ValueError:
            raise ValidationError('Invalid input. Please type '
                                  'a number from 1 to 9.')

        if not 1 <= turn <= 9:
            raise ValidationError('Please type '
                                  'a number from 1 to 9.')

        turn -= 1
        if not self.grid[turn] == Box.empty.value:
            raise ValidationError('Box is not empty. '
                                  'Try another one.')

        if not player.id == self.current_turn:
            raise ValidationError('It\'s not your turn.')

        return turn

    def turn(self, player, turn):
        """Changes game condition.

        Adds a new player's mark to the grid. Checks grid.
        Notifies the opponent if the game can be continued.
        Spreads game results if the game is finished.

        Args:
            player (Player): Instanse of Player() class.
            turn (int): User input. Valid box number is expected.

        """
        self.grid[turn] = player.type
        game_result = self.check_grid(player)
        opponent = self.get_opponent(player.id)
        if game_result:
            response = self.as_dict()
            response.update({'game_result': game_result})
            opponent.queue.put_nowait(response)
            player.queue.put_nowait(response)
            game_pool.finish_game(self.id)
        else:
            self.current_turn = opponent.id
            opponent.queue.put_nowait(self.as_dict())

    def check_grid(self, player):
        """Checks grid.

        Args:
            player (Player): Instanse of Player() class.

        Returns:
            Player ID if player is winner or loser.
            'drawn game' value if game is drawn.
            None otherwise.

        """
        grid = self.grid
        lines = (
            (0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
            (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)
        )
        for line in lines:
            if (grid[line[0]] == grid[line[1]] == grid[line[2]] and
                    not grid[line[0]] == Box.empty.value):
                if grid[line[0]] == player.type:
                    return player.id
                else:
                    opponent = self.get_opponent(player.id)
                    return opponent.id

        if Box.empty.value not in grid:
            return 'drawn game'

    def as_dict(self, extra=None):
        """Serializes game state to dictionary.

        Args:
            extra (dict): Some addition parameters.

        Returns:
            A dict with game parameters and extra data.

        """
        out = {
            'grid': self.grid,
            'game_id': self.id,
        }
        if isinstance(extra, dict):
            out.update(extra)
        return out


class GamePool:
    """
    Pool of games. Not thread safe. Keep all games in memory.
    """
    def __init__(self):
        self._pool = {}
        self._awaiting = None

    def retrieve_game(self, game_id, player_id):
        """Retrieves a game from the pool. Creates a new one if not exists.

        Args:
            game_id (str): Game ID.
            player_id (str): Player ID.

        Returns:
            Instanse of Game() class.

        Raises:
            GameNotFoundError: An error occurred accessing unexistent game.
            PlayerNotFoundError: An error occurred if
                passed player_id not found in the game.

        """
        if game_id:
            try:
                game = self._pool[game_id]
            except KeyError:
                raise GameNotFoundError()

            if player_id not in game.players:
                raise PlayerNotFoundError()
            else:
                return game
        else:
            if self._awaiting:
                game = self._awaiting
                game.activate(player_id)

                self._pool[game.id] = game
                self._awaiting = None
                return game
            else:
                game = Game()
                game.init(player_id)

                self._awaiting = game
                return game

    def finish_game(self, game_id):
        """Remove finished game from the pool.

        Args:
            game_id (str): Game ID.

        """
        del self._pool[game_id]


game_pool = GamePool()
