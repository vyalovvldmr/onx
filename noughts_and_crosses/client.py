"""
Command line client for Noughts & Crosses game.
"""
import json
import uuid
from contextlib import suppress

import websocket

import settings


URL = 'ws://{host}:{port}/ws'.format(
    host=settings.SERVER_IP,
    port=settings.SERVER_PORT
)
print(URL)

GRID_TEMPLATE = """
┌─┬─┬─┐
│{}│{}│{}│
├─┼─┼─┤
│{}│{}│{}│
├─┼─┼─┤
│{}│{}│{}│
└─┴─┴─┘
"""


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


def print_grid(grid):
    box_types = {
        BoxType.empty: ' ',
        BoxType.nought: '0',
        BoxType.cross: 'X',
    }
    print(GRID_TEMPLATE.format(*[box_types[i] for i in grid]))


def make_turn(game_state, player_id, ws):
    if game_state.get('whose_turn') == player_id:
        turn = input('Your turn (Type a number for 1 to 9): ')
        try:
            payload = {'operation': 'turn', 'payload': {'turn': int(turn) - 1}}
        except (ValueError, TypeError):
            make_turn(game_state, player_id, ws)
        else:
            ws.send(json.dumps(payload))
    else:
        print('Waiting for opponent...')


def main():
    player_id = str(uuid.uuid4())
    ws = websocket.create_connection(
        URL,
        header={
            'Cookie': 'player_id={player_id}'.format(
                player_id=player_id
            )
        }
    )
    game_state = None
    while True:
        message = json.loads(ws.recv())
        payload = message['payload']
        if message['event'] == 'error':
            print(payload['message'])
            make_turn(game_state, player_id, ws)
        elif message['event'] == 'game_state':
            game_state = payload
            print_grid(payload['grid'])
            if payload['status'] == GameStatus.awaiting:
                print('Waiting for opponent...')
            if payload['status'] == GameStatus.finished:
                if payload['winner'] == None:
                    print('Drawn game')
                elif payload['winner'] == player_id:
                    print('Winner!')
                else:
                    print('Loser :(')
                break
            elif payload['status'] == GameStatus.in_progress:
                make_turn(game_state, player_id, ws)
            elif payload['status'] == GameStatus.unfinished:
                print('Opponent gone')
                break
    ws.close()


if __name__ == '__main__':
    with suppress(KeyboardInterrupt):
        main()
