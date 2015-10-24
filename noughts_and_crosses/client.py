"""
Command line client for Noughts & Crosses game.
"""
import uuid
from enum import Enum

import requests


URL = 'http://127.0.0.1:8080/game/'


class Box(Enum):
    empty = 1
    nought = 2
    cross = 3


def print_grid(grid):
    grid_template = """
        ┌─┬─┬─┐
        │{}│{}│{}│
        ├─┼─┼─┤
        │{}│{}│{}│
        ├─┼─┼─┤
        │{}│{}│{}│
        └─┴─┴─┘
    """
    box_types = {
        Box.empty.value: ' ',
        Box.nought.value: '0',
        Box.cross.value: 'X',
    }
    print(grid_template.format(*[box_types[i] for i in grid]))


def main():
    player_id = uuid.uuid4().hex
    print('Waiting for the opponent...')

    payload = {'player_id': player_id}
    response = requests.get(URL, payload).json()

    payload.update({'game_id': response['game_id']})

    while True:
        error_message = response.get('error_message')
        if error_message:
            print(error_message)
        else:
            print_grid(response['grid'])

        game_result = response.get('game_result')
        if game_result:
            if game_result == player_id:
                print('You won the game!')
            elif game_result == 'drawn game':
                print('Drawn game.')
            else:
                print('Lost the game.')
            break
        else:
            turn = input('Your turn (Type a number for 1 to 9): ')
            payload.update({'turn': turn})
            print('Waiting for the opponent...')
            response = requests.get(URL, payload).json()


if __name__ == '__main__':
    main()
