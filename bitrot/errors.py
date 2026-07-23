__all__ = [
    "InvalidMove",
    "OccupiedSpace",
    "OutOfBounds",
    "Forfeit",
    "UnknownState",
    "DesyncError",
    "GameAbort",
    "NullOp",
]


class InvalidMove(Exception):
    """An invalid move was made."""


class OccupiedSpace(InvalidMove):
    """The invalid move was attempting to take an occupied space."""


class OutOfBounds(InvalidMove):
    """The invalid move was attempting to occupy a space outside the board."""


class Forfeit(InvalidMove):
    """The invalid move was declaring a forfeit."""


class NullOp(InvalidMove):
    """The invalid move was a null operation."""


class UnknownState(Exception):
    """An erroneous or invalid game state was parsed."""


class DesyncError(UnknownState):
    """A state desync has occured."""


class GameAbort(Exception):
    """The current game is to be aborted."""
