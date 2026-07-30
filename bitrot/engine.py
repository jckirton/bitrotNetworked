from .errors import *
from .constants import DEFAULT_BOARD

__all__ = ["Match", "Game"]


class Game:
    """A BITROT game.

    Contains the board, game state, and methods for turns and state strings.
    """

    def __init__(self):
        """Create a BITROT game."""
        self.board = self.Board()
        self.playing = False
        self.recent_player = ""
        self.recent_op = ""
        self.winner: int | None = None

    class Board:
        """A BITROT board.

        Contains the current board state,
        and methods for updating the board state.
        """

        def __init__(self):
            """Create a BITROT board."""
            self.state: dict[int, None | Game.Board.Piece] = {
                1: None,
                2: None,
                3: None,
                4: None,
                5: None,
                6: None,
                7: None,
                8: None,
                9: None,
            }

        class Piece:
            """A BITROT piece.

            Contains an owner and age.
            """

            def __init__(self, player: int, age: int = 0):
                """Create a BITROT piece.

                Args:
                    player (int): The piece's owner. `0` is attacker, `1` is defender.
                    age (int, optional): The age of the piece from 0-2. Defaults to 0.
                """
                self.p = player
                self.a = age
                self.AGE_COLORS = {
                    "clear": "\x1b[0m",  # Clear
                    "red": "\x1b[0;31m",  # Red
                    "yellow": "\x1b[1;33m",  # Yellow
                    "green": "\x1b[0;32m",
                }

            def __str__(self):
                if self.p == -1:
                    return " "
                if self.a == 1:
                    return f"{self.AGE_COLORS["yellow"]}{str(self.p)}{self.AGE_COLORS["clear"]}"
                if self.a == 2:
                    return f"{self.AGE_COLORS["red"]}{str(self.p)}{self.AGE_COLORS["clear"]}"
                return str(self.p)

            def __format__(self, format_spec):
                if self.p == 0:
                    return hex(1 + self.a)[2:]
                else:
                    return hex(15 - self.a)[2:]

        def age_pieces(self, player: int):
            """Increment the age of a player's pieces on the board.

            Args:
                player (int): Which player's pieces to age.
            """
            for pos in self.state:
                piece = self.state[pos]
                if isinstance(piece, self.Piece):
                    if piece.p == player:
                        piece.a += 1
                    if piece.a >= 3:
                        self.state[pos] = None

        def add_piece(self, player: int, position: int):
            """Add a new piece to the board at position.

            Args:
                player (int): The piece's player.
                position (int): The position on the board to put the piece, from 1-9.
            """
            self.state[position] = self.Piece(player)

        def check_move(self, op: str) -> bool:
            """Return if a given operation is valid.

            Args:
                op (str): The operation to check.

            Raises:
                Forfeit: The given operation is a forfeit (`"f"`).
                NullOp: The given operation is null (`""` or `"0"`).
                OutOfBounds: The given operation is beyond the valid board range (`op<1`, `op>9`).
                OccupiedSpace: The given operation is a space that is already taken.
                InvalidMove: The given operation is unknown or miscellaneously invalid.
            """
            if op == "f":
                raise Forfeit("a forfeit was declared.")
            if op in "0":
                raise NullOp("a null operation was submitted.")

            try:
                position = int(op)
                piece = self.state[position]
            except ValueError:
                raise InvalidMove("an unknown op was passed.")

            if 9 < position < 1:
                raise OutOfBounds(f"position '{position}' is not a space on the board.")
            elif piece is not None:
                raise OccupiedSpace(
                    f"position {position} is occupied by the {"attacker" if piece.p == 0 else "defender"}."
                )
            else:
                return True

        def parse(
            self, state: str, set: bool = False
        ) -> dict[int, None | Game.Board.Piece]:
            """Parse a BITROT board state string into an internal board state.

            If `set` is `True`, also sets `self.state` to the output.

            Args:
                state (str): The board state string to parse.
                set (bool, optional): If `self.state` should be set to the parsed state. Defaults to False.

            Raises:
                UnknownState: The given state could not be parsed.

            Returns:
                dict[int, None | Game.Board.Piece]: The parsed state.
            """

            temp_state: dict[int, None | Game.Board.Piece] = {
                1: None,
                2: None,
                3: None,
                4: None,
                5: None,
                6: None,
                7: None,
                8: None,
                9: None,
            }
            i = 1
            try:
                for pos in state:
                    piece = int(pos, base=16)
                    if 1 <= piece <= 3:
                        temp_state[i] = self.Piece(0, piece - 1)
                    elif 13 <= piece <= 15:
                        temp_state[i] = self.Piece(1, abs(piece - 15))
                    elif piece == 0:
                        pass
                    else:
                        raise ValueError(f"invalid piece identifier '{pos}'")
                    i += 1
                if set:
                    self.state = temp_state
                return temp_state
            except Exception:
                raise UnknownState(f"erroneous/unknown board state '{state}'")

        def __str__(self):
            from copy import copy

            # return f"{self.state}"
            # return self.display
            pos = copy(self.state)
            for i in pos:
                if pos[i] is None:
                    pos[i] = self.Piece(-1)

            display = DEFAULT_BOARD % tuple(pos[i] for i in [7, 8, 9, 4, 5, 6, 1, 2, 3])

            return display

        def __format__(self, format_spec):
            out = ""
            for pos in self.state:
                if isinstance(self.state[pos], self.Piece):
                    out += format(self.state[pos])
                else:
                    out += "0"

            return out

        def __eq__(self, value):
            return format(self) == format(value)

    def check_win(self) -> int | None:
        """Return if a player has won based on the current game state.

        Returns:
            int: The winning player. `0` for attacker, `1` for defender.
            None: No player has met a win condition.
        """
        if self.recent_op == "f":
            return self.winner

        win_conditions = [
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9],
            [7, 4, 1],
            [8, 5, 2],
            [9, 6, 3],
            [7, 5, 3],
            [1, 5, 9],
        ]

        for cond in win_conditions:
            prospecting_winner = None
            for pos in cond:
                curr_piece = self.board.state[pos]
                if curr_piece is None:
                    prospecting_winner = None
                    break
                elif prospecting_winner is None:
                    prospecting_winner = curr_piece
                elif curr_piece.p != prospecting_winner.p:
                    prospecting_winner = None
                    break
            if prospecting_winner is not None:
                return prospecting_winner.p
        return None

    def do_turn(self, player: int, op: str):
        """Do a BITROT turn.

        Does all the components of checking validity and updating game state,
        including checking for a winning player.

        Args:
            player (int): The acting player.
            op (str): The player's operation.
        """
        self.recent_player: str = str(player)
        self.recent_op: str = op
        try:
            self.board.check_move(op)
            self.board.age_pieces(player)
            self.board.add_piece(player, int(op))
            # print(self.board)
        except NullOp as e:
            self.board.age_pieces(player)
            self.recent_op = "0"
            # print(self.board)
            # print(e)
        except OccupiedSpace as e:
            self.board.age_pieces(player)
            self.recent_op = "a"
            # print(self.board)
            # print(e)
        except OutOfBounds as e:
            self.board.age_pieces(player)
            self.recent_op = "b"
            # print(self.board)
            # print(e)
        except Forfeit as e:
            self.recent_op = "f"
            self.playing = False
            self.winner = abs(player - 1)
            # print(self.board)
            # print(e)
        except InvalidMove as e:
            self.board.age_pieces(player)
            self.recent_op = "c"
            # print(self.board)
            # print(e)

        win_check = self.check_win()
        if win_check is not None:
            self.playing = False
            self.winner = win_check
            # print(f"{self.winner} has won.")

    def parse_net_state(self, net_state: str):
        """Parse a given BITROT game state string.

        Generally used for doing the networked opponents turn,
        or recieving initial state.

        Args:
            net_state (str): The BITROT state string to parse.

        Raises:
            Forfeit: The operation was a forfeit.
            DesyncError: The two clients' states have become desynced.
            GameAbort: The opposing client crashed and the active game is dead.
        """
        net_playing = net_state[0]
        net_board = net_state[1:10]
        net_p = net_state[10]
        net_op = net_state[11]
        # print(net_playing, net_board, net_p, net_op)

        if net_playing == "0":
            print("Initial board state recieved; applying state.")
            self.board.parse(net_board, True)
            self.playing = True
            print(self.board)
        elif net_playing in "123":
            # curr_state = format(self)
            temp_state = Game.instance_from_state(format(self))
            temp_state.do_turn(int(net_p), net_op)

            if net_board != format(temp_state.board):
                if net_op == "f":
                    raise Forfeit("opponent forfeit during local turn.")
                    self.do_turn(int(net_p), net_op)
                print(f"Board state mismatch; game state reverted to '{format(self)}'.")
                raise DesyncError(
                    f"board state mismatch - game state reverted to '{format(self)}'."
                )
            else:
                if not self.playing:
                    self.playing = True
                self.do_turn(int(net_p), net_op)
        else:
            if net_state in ["fffffffffff0", "fffffffffff1"]:
                raise GameAbort("opposing client experienced a fatal exception.")

    @staticmethod
    def instance_from_state(state: str) -> Game:
        """Return a new Game instance from a given BITROT state string.

        Args:
            state (str): The BITROT state string.

        Raises:
            UnknownState: The given state is unknown or not a valid game state.
        """
        try:
            playing = state[0]
            board = state[1:10]
            p = state[10]
            op = state[11]

            new_instance = Game()
            new_instance.board.parse(board, True)
            new_instance.recent_player = p
            new_instance.recent_op = op

            if playing in "01":
                new_instance.playing = bool(int(playing))
                new_instance.winner = None
            elif playing in "23":
                new_instance.playing = False
                new_instance.winner = int(playing) - 2
            else:
                raise UnknownState(f"unknown/invalid playing state '{playing}'")

            return new_instance
        except Exception:
            raise UnknownState(f"erroneous/unknown state '{state}'")

    @staticmethod
    def generate_initial_state() -> str:
        """Return a randomised valid initial BITROT state string."""
        from random import sample

        moves = sample(range(1, 10), k=2)
        temp_game = Game()

        for move in moves:
            temp_game.do_turn(moves.index(move), str(move))

        return format(temp_game)

    def __format__(self, format_spec):
        playwin = 0
        if not self.playing and self.winner is None:
            playwin = 0
        if self.playing and self.winner is None:
            playwin = 1
        if self.winner is not None:
            playwin = self.winner + 2
        return f"{playwin}{format(self.board)}{self.recent_player}{self.recent_op}"


class Match:
    """A BITROT match.

    Contains a Game instance, a given Networking instance, player information,
    methods for doing local/networked turns, and communicating state."""

    from .networking import Networking

    def __init__(
        self,
        network: Networking,
        user: str,
        opponent: str,
        team: int,
        state: str | None = None,
    ):
        """Create a new BITROT match with the given information.

        Args:
            network (Networking): The current `bitrot.Networking` instance.
            user (str): The name of the user the local user is playing as.
            opponent (str): The name of the opponent's user,
            team (int): The team of the local user. `0` is attacker, `1` is defender.
            state (str | None, optional): The initial game state.
              Needed when the initial state is given by the opponent.
              Defaults to None.
        """
        self.game: Game
        self.network = network
        self.user = user
        self.opponent = opponent
        self.team = team

        if state is not None:
            self.game = Game()
            self.game.parse_net_state(state)
            self.network.in_game = True
        else:
            self.game = Game.instance_from_state(Game.generate_initial_state())
            self.send_state()
            self.game.playing = True
            self.network.in_game = True

    def send_state(self) -> Networking.Response:
        """Send the current game state to the opponent.

        Returns:
            Networking.Response: The response of the `Network.tell` call.
        """
        # return self.network.tell(self.user, self.opponent, format(self.game))
        return self.network.tell(
            self.network.curr_user, self.opponent, format(self.game)
        )

    def do_self_turn(self, op: str):
        """Do local turn.

        Args:
            op (str): The submitted operation.
        """
        self.game.do_turn(self.team, op)

    def do_opponent_turn(self):
        """Listen and perform networked opponent turn."""
        done = False

        while not done:
            net_state = self.network.listen_opponent_move(self.opponent)
            if net_state == "f000000000fc":
                self.send_state()
            else:
                self.game.parse_net_state(net_state)
                done = True
