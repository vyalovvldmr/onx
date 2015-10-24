class GameNotFoundError(Exception):
    pass


class PlayerNotFoundError(Exception):
    pass


class ValidationError(Exception):

    def __init__(self, message):
        self.message = message
