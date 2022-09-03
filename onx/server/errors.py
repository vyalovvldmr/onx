import re


class BaseGameValidationError(Exception):
    regexp = re.compile("(?!^)([A-Z]+)")

    def __str__(self):
        return self.regexp.sub(r" \1", self.__class__.__name__).lower()


class NotYourTurnError(BaseGameValidationError):
    pass


class InvalidTurnNumberError(BaseGameValidationError):
    pass


class BoxIsNotEmptyError(BaseGameValidationError):
    pass


class TurnWithoutSecondPlayerError(BaseGameValidationError):
    pass
