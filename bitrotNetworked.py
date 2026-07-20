from hackmudChatAPI import ChatAPI, ChatMessage
import re


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


from time import sleep


class Networking(ChatAPI):
    """BITROT's extension of the `hackmudChatAPI.ChatAPI` class."""

    def __init__(self, **kwargs):
        """Create a BITROT networking instance.

        Args:
            **kwargs: Optional arguments that `hackmudChatAPI.ChatAPI` takes.
        """
        super().__init__(**kwargs)
        self.in_game = False
        self.allChats = self.read(after=600, before=300)
        # self.allChats: dict[str, list[ChatMessage]] = {}
        # self.waiting = False
        self.curr_user = ""

    class Challenge:
        """A BITROT challenge.

        Contains the challenger, the challenged, when the challenge was sent, and methods for responding to the challenge.
        """

        def __init__(
            self, network: Networking, challenger: str, challenged: str, sent_at: float
        ):
            self.network = network
            self.challenger = challenger
            self.challenged = challenged
            self.sent_at = sent_at

        @staticmethod
        def challenge_from_message(
            network: Networking, message: ChatMessage
        ) -> Networking.Challenge:
            return Networking.Challenge(
                network, message["from_user"], message.get("to_user", ""), message["t"]
            )

        def accept(self):
            self.network.curr_user = self.challenged
            self.network.tell(self.challenged, self.challenger, "ACC")

        def decline(self):
            self.network.tell(self.challenged, self.challenger, "DEC")

        def __repr__(self) -> str:
            return f"{self.challenger} -> {self.challenged} @ {self.sent_at}"

    def fetch(
        self,
        seconds: int | float = 10,
    ) -> dict[str, dict[str, list[ChatMessage]]]:
        fetched: dict[str, list[ChatMessage]]

        fetched = self.read(after=seconds)

        newChats: dict[str, list[ChatMessage]] = {}.copy()
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

    def challenge(self, user: str, target: str) -> bool:
        """Send a challenge request to `target` as `user`.

        Sends `"CHA"` as a tell to `target` as `user`.
        If sent successfully, sets `self.curr_user` to `user` and returns `True`.
        Returns `False` otherwise.

        Does not listen for a response - use the `Networking.listen_challenge_response` method.

        Args:
            user (str): The user to send a challenge request as.
            target (str): The user to send a challenge request to.
        """

        tell = self.tell(user, target, "CHA")
        if tell.content != b"" and tell.json()["ok"] is True:
            # self.waiting = True
            self.curr_user = user
            return True
        else:
            return False

    def fetch_challenges(self) -> list[Networking.Challenge]:
        """Fetch recieved challenge requests.

        Filters through new chat messages recieved in the last 10 minutes for `"CHA"` requests,
        and returns a list of challenges.

        Automatically sends `"ACK"` to seen challengers, or `"OCC"` if `self.in_game` is `True`.

        Does not automatically loop like `Network.listen_challenge_response`.
        """
        new_challenges = []
        new_chats = self.fetch(500)["new"]

        for user in new_chats:
            for message in new_chats[user]:
                if (
                    message.get("to_user") == user
                    and message["msg"] == "CHA"
                    and message["from_user"] != user
                ):
                    new_challenges.append(
                        self.Challenge.challenge_from_message(self, message)
                    )
                    self.tell(
                        user, message["from_user"], "OCC" if self.in_game else "ACK"
                    )

        return new_challenges

    def listen_challenge_response(
        self, challenged: str, rate: int | float = 2
    ) -> str | None:
        """Listen for a response from a challenged user.

        Starts a loop of fetching the past 60 seconds of messages from the chat API every `rate` seconds,
        and filtering through new tells recieved by `self.curr_user` and sent by `challenged` for a response.

        If the challenge is accepted, returns the initial BITROT game state string supplied by `challenged`.
        Returns `None` otherwise.

        After roughly 2 minutes or when interrupted, sends `"BAH"` to `challenged` and returns `None`.

        Args:
            challenged (str): User a challenge has been sent to.
            rate (int | float, optional): How frequently to read from the chat API in seconds. Defaults to 2.
        """

        try:
            state = {"accepted": False, "initial": None}
            loops = 0
            while not state["accepted"] or (state["accepted"] and not state["initial"]):
                new = self.fetch(60)["new"][self.curr_user]
                for message in new:
                    if message["from_user"] == challenged:
                        if message["msg"] in ["OCC", "DEC"]:
                            print("declined")
                            return None

                        if state["accepted"]:
                            init_state_test = re.match(
                                r"(0)([01f]{9})([1|0]{1})([1-9]{1})", message["msg"]
                            )
                            if (
                                len(message["msg"]) == 12
                                and init_state_test is not None
                            ):
                                state["initial"] = message["msg"]
                                init_state_message = message
                                break
                        elif message["msg"] in ["ACC"]:
                            print("accepted")
                            state["accepted"] = True
                            accepting_message = message
                if loops >= 60:
                    self.tell(self.curr_user, challenged, "BAH")
                    return None
                loops += 1
                sleep(rate)
            if state["accepted"]:
                print(accepting_message)
                print(init_state_message)
                return init_state_message["msg"]
            else:
                return None
        except KeyboardInterrupt:
            self.tell(self.curr_user, challenged, "BAH")
            return None

    def listen_game(self, opponent: str) -> str | None:
        """Listen for game state updates/opponent's move

        Args:
            opponent (str): The current opponent.
        """
        while True:
            self.fetch(300)


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
            if 9 < position < 1:
                raise OutOfBounds(f"position '{position}' is not a space on the board.")
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
                raise OutOfBounds(f"Position '{position}' is not a space on the board.")
            elif self.state[position] is not None:
                raise OccupiedSpace(
                    f"Position {position} is occupied by the {"attacker" if self.state[position].p == 0 else "defender"}."
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
        net_playing = net_state[0]
        net_board = net_state[1:10]
        net_p = net_state[10]
        net_op = net_state[11]
        print(net_playing, net_board, net_p, net_op)

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
                print(f"Board state mismatch; game state reverted to '{format(self)}'.")
                raise DesyncError(
                    f"board state mismatch - game state reverted to '{format(self)}'."
                )
            else:
                if not self.playing:
                    self.playing = True
                self.do_turn(int(net_p), net_op)

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
            temp_game.do_turn(0, move)

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

    def send_state(self) -> ChatAPI.Response:
        return self.network.tell(self.user, self.opponent, format(self.game))

    def play(self): ...


# foo = Game.Board()

# foo.age_pieces(0)
# foo.add_piece(0, 1)
# foo.age_pieces(1)
# foo.add_piece(1, 2)
# foo.age_pieces(0)
# foo.add_piece(0, 3)

# print(foo)
# print(format(foo))

# foo = Game()

# foo.parse_net_state("01f000000012")
# 11f000000012
# foo.do_turn(0, "3")
# 12f100000003
# foo.do_turn(1, "4")
# 12e1f0000014
# foo.do_turn(0, "5")
# 13e2f1000005
# foo.do_turn(1, "6")
# 13d2e1f00016
# foo.do_turn(0, "7")
# 20d3e2f10007

# print(format(foo))

# foo.parse_net_state("12e1f0000014")
# Game.instance_from_state("ffffffffffff")

net = Networking()

# net.challenge("http", "burn")
# print(net.listen_challenge_response("burn"))

challenges: list[Networking.Challenge] = []
while True:
    challenges.extend(net.fetch_challenges())
    print(challenges)
    sleep(2)
