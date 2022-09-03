import re


class BaseError(Exception):
    regexp = re.compile("(?!^)([A-Z]+)")

    def __str__(self):
        return self.regexp.sub(r" \1", self.__class__.__name__).lower()


class NotYourTurnError(BaseError):
    pass


class InvalidTurnNumberError(BaseError):
    pass


class BoxIsNotEmptyError(BaseError):
    pass


class TurnWithoutSecondPlayerError(BaseError):
    pass
