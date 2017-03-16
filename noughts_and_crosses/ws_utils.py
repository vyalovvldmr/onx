def publish(payload, subscribers):
    for subscriber in subscribers:
        subscriber.ws.send_json(payload)


def send_error(error_message, ws):
    ws.send_json({
        'event': 'error',
        'payload': {
            'message': error_message,
        }
    })


def publish_game_state(game):
    payload = {
        'event': 'game_state',
        'payload': game.to_json()
    }
    publish(payload, game.players)
