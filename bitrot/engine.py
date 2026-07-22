from .errors import *
from .constants import DEFAULT_BOARD

__all__ = ["Match", "Game"]


class Game:
    def __init__(self):
        self.board = self.Board()
        self.playing = False
        self.recent_player = ""
        self.recent_op = ""
        self.winner: int | None = None

    class Board:
        def __init__(self):
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
            def __init__(self, player: int, age: int = 0):
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
            for pos in self.state:
                piece = self.state[pos]
                if isinstance(piece, self.Piece):
                    if piece.p == player:
                        piece.a += 1
                    if piece.a >= 3:
                        self.state[pos] = None

        def add_piece(self, player: int, position: int):
            self.state[position] = self.Piece(player)

        def check_move(self, op: str):
            if op == "f":
                raise Forfeit("A forfeit was declared.")

            try:
                position = int(op)
                piece = self.state[position]
            except ValueError:
                raise InvalidMove("An unknown op was passed.")

            if 9 < position < 1:
                raise OutOfBounds(f"Position '{position}' is not a space on the board.")
            elif piece is not None:
                raise OccupiedSpace(
                    f"Position {position} is occupied by the {"attacker" if piece.p == 0 else "defender"}."
                )
            else:
                return True

        def parse(self, state: str, set: bool = False):
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
            for pos in state:
                piece = int(pos, base=16)
                if 1 <= piece <= 3:
                    temp_state[i] = self.Piece(0, piece - 1)
                elif 13 <= piece <= 15:
                    temp_state[i] = self.Piece(1, abs(piece - 15))
                i += 1
            if set:
                self.state = temp_state
            return temp_state

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
        self.recent_player: str = str(player)
        self.recent_op: str = op
        try:
            self.board.check_move(op)
            self.board.age_pieces(player)
            self.board.add_piece(player, int(op))
            # print(self.board)
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
            raise UnknownState(f"erroneous/unknown state '{state}'")

        return new_instance

    @staticmethod
    def generate_initial_state() -> str:
        from random import choices

        moves = choices(range(1, 10), k=2)
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
    from .networking import Networking

    def __init__(
        self,
        network: Networking,
        user: str,
        opponent: str,
        team: int,
        state: str | None = None,
    ):
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
        # return self.network.tell(self.user, self.opponent, format(self.game))
        return self.network.tell(
            self.network.curr_user, self.opponent, format(self.game)
        )

    def do_self_turn(self, op: str):
        self.game.do_turn(self.team, op)

    def do_opponent_turn(self):
        net_state = self.network.listen_opponent_move(self.opponent)
        self.game.parse_net_state(net_state)
