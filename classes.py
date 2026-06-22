class InvalidMove(Exception):
    """An invalid move was made."""


class OccupiedSpace(InvalidMove):
    """The invalid move was attempting to take an occupied space."""


class OutOfBounds(InvalidMove):
    """The invalid move was attempting to occupy a space outside the board."""
