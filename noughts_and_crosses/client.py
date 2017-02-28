"""
Command line client for Noughts & Crosses game.
"""
import asyncio
import json
import uuid

import websockets


URL = 'ws://localhost:8080/ws'


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
        BoxType.empty: ' ',
        BoxType.nought: '0',
        BoxType.cross: 'X',
    }
    print(grid_template.format(*[box_types[i] for i in grid]))


async def make_turn(game_state, player_id, ws):
    if game_state.get('whose_turn') == player_id:
        turn = input('Your turn (Type a number for 1 to 9): ')
        payload = {'operation': 'turn', 'payload': {'turn': int(turn) - 1}}
        await ws.send(json.dumps(payload))
    else:
        print('Waiting for the opponent...')


async def main():
    player_id = str(uuid.uuid4())
    ws = await websockets.connect(
        URL,
        extra_headers={
            'Cookie': 'player_id={player_id}'.format(
                player_id=player_id
            )
        }
    )
    game_state = None
    while True:
        message = json.loads(await ws.recv())
        payload = message['payload']
        if message['event'] == 'error':
            print(payload['message'])
            await make_turn(game_state, player_id, ws)
        elif message['event'] == 'game_state':
            game_state = payload
            print_grid(payload['grid'])
            if payload['status'] == GameStatus.awaiting:
                print('Waiting for the opponent...')
            elif payload['status'] == GameStatus.in_progress:
                await make_turn(game_state, player_id, ws)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
