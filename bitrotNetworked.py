from hackmudChatAPI import ChatAPI


class InvalidMove(Exception):
    """An invalid move was made."""


class OccupiedSpace(InvalidMove):
    """The invalid move was attempting to take an occupied space."""


class OutOfBounds(InvalidMove):
    """The invalid move was attempting to occupy a space outside the board."""


class Forfeit(InvalidMove):
    """The invalid move was declaring a forfeit."""


class DesyncError(Exception):
    """A state desync has occured."""


DEFAULT = """7    |8    |9
  %s  |  %s  |  %s
     |     |
-----|-----|-----
4    |5    |6
  %s  |  %s  |  %s
     |     |
-----|-----|-----
1    |2    |3
  %s  |  %s  |  %s
     |     |     """


class Networking(ChatAPI):
    def __init__(self):
        super().__init__()
        self.in_game = False
        self.allChats = self.read(600)
        self.waiting = False
        self.curr_user = None

    def fetch(
        self,
        seconds: int | float = 10,
    ):
        fetched: dict[str, list]

        fetched = self.read(after=seconds)

        newChats: dict[str, list[dict]] = {}.copy()
        for user in fetched:
            fetched[user].sort(key=lambda message: message["t"])
            newChats[user] = []
            if user not in self.allChats:
                self.allChats[user] = []
            for msg in fetched[user]:
                if msg not in self.allChats[user] and msg.get("channel") is None:
                    self.allChats[user].append(msg)
                    newChats[user].append(msg)

        return {"fetched": fetched, "new": newChats}

    def challenge(self, user: str, target: str):
        tell = self.tell(user, target, "SYN")
        if tell.content != b"" and tell.json()["ok"] is True:
            self.waiting = True
            self.curr_user = user
            return True
        else:
            return False

    def listen_challenge(self, challenged: str | None = None):
        """Listen for challenge requests and responses.

        Args:
            challenged (str | None, optional): User a challenge has been sent to. Defaults to None.
        """
        pass

    def listen_game(self, opponent: str):
        """Listen for game state updates/opponents move

        Args:
            opponent (str): The current opponent.
        """
        pass


class Match:
    def __init__(self, network: Networking, user: str, opponent: str, team: int):
        self.game = self.Game()
        self.network = network
        self.user = user
        self.opponent = opponent
        self.team = team

    class Game:
        def __init__(self):
            self.board = self.Board()
            self.playing = False
            self.recent_player = ""
            self.recent_op = ""
            self.winner = None

        class Board:
            def __init__(self):
                self.state: dict[int, None | Match.Game.Board.Piece] = {
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
                if 9 < position < 1:
                    raise OutOfBounds(
                        f"position '{position}' is not a space on the board."
                    )
                elif self.state[position] is not None:
                    raise OccupiedSpace(
                        f"position {position} is occupied by the {"attacker" if self.state[position].p == 0 else "defender"}."
                    )
                else:
                    self.state[position] = self.Piece(player)

            def check_move(self, op: str):
                if op == "f":
                    raise Forfeit("A forfeit was declared.")

                try:
                    position = int(op)
                except ValueError:
                    raise InvalidMove("An unknown op was passed.")

                if 9 < position < 1:
                    raise OutOfBounds(
                        f"Position '{position}' is not a space on the board."
                    )
                elif self.state[position] is not None:
                    raise OccupiedSpace(
                        f"Position {position} is occupied by the {"attacker" if self.state[position].p == 0 else "defender"}."
                    )
                else:
                    return True

            def parse(self, state: str, set: bool = False):
                temp_state: dict[int, None | Match.Game.Board.Piece] = {
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
                        pos[i] = " "

                display = DEFAULT % tuple(pos[i] for i in [7, 8, 9, 4, 5, 6, 1, 2, 3])

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
                null_check = False
                for pos in cond:
                    if self.board.state[pos] is None:
                        null_check = True
                if null_check:
                    pass
                elif (
                    self.board.state[cond[0]].p
                    == self.board.state[cond[1]].p
                    == self.board.state[cond[2]].p
                ):
                    return self.board.state[cond[0]].p
            return None

        def do_turn(self, player, op):
            self.recent_player = player
            self.recent_op = op
            try:
                self.board.check_move(op)
                self.board.age_pieces(player)
                self.board.add_piece(player, int(op))
                print(self.board)
            except OccupiedSpace as e:
                self.board.age_pieces(player)
                self.recent_op = "a"
                print(self.board)
                print(e)
            except OutOfBounds as e:
                self.board.age_pieces(player)
                self.recent_op = "b"
                print(self.board)
                print(e)
            except Forfeit as e:
                self.recent_op = "f"
                self.playing = False
                self.winner = abs(player - 1)
                print(self.board)
                print(e)
            except InvalidMove as e:
                self.board.age_pieces(player)
                self.recent_op = "c"
                print(self.board)
                print(e)

            win_check = self.check_win()
            if win_check is not None:
                self.playing = False
                self.winner = win_check
                print(f"{self.winner} has won.")

        def parse_net_state(self, net_state):
            playing = net_state[0]
            board = net_state[1:10]
            p = net_state[10]
            op = net_state[11]
            print(playing, board, p, op)
            if playing == "0":
                self.board.parse(board, True)
                self.playing = True
                print(self.board)
            elif playing == "1":
                curr_board = format(self.board)
                net_board = self.Board()
                net_board.parse(board, True)
                self.do_turn(int(p), op)
                if net_board != self.board:
                    raise DesyncError()

        def __format__(self, format_spec):
            if not self.playing and self.winner is None:
                playwin = 0
            if self.playing and self.winner is None:
                playwin = 1
            if self.winner is not None:
                playwin = self.winner + 2
            return f"{playwin}{format(self.board)}{self.recent_player}{self.recent_op}"


# foo = Match.Game.Board()

# foo.age_pieces(0)
# foo.add_piece(0, 1)
# foo.age_pieces(1)
# foo.add_piece(1, 2)
# foo.age_pieces(0)
# foo.add_piece(0, 3)

# print(foo)
# print(format(foo))

foo = Match.Game()

foo.parse_net_state("01f000000012")

foo.do_turn(0, "3")
foo.do_turn(1, "4")
foo.do_turn(0, "5")
foo.do_turn(1, "6")
foo.do_turn(0, "7")

# print(format(foo))

# foo.parse_net_state("12e1f0000014")
