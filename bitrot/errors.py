__all__ = [
    "InvalidMove",
    "OccupiedSpace",
    "OutOfBounds",
    "Forfeit",
    "UnknownState",
    "DesyncError",
]


class InvalidMove(Exception):
    """An invalid move was made."""


class OccupiedSpace(InvalidMove):
    """The invalid move was attempting to take an occupied space."""


class OutOfBounds(InvalidMove):
    """The invalid move was attempting to occupy a space outside the board."""


class Forfeit(InvalidMove):
    """The invalid move was declaring a forfeit."""


class UnknownState(Exception):
    """An erroneous or invalid game state was parsed."""


class DesyncError(UnknownState):
    """A state desync has occured."""
