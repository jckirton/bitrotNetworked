from hackmudChatAPI import ChatAPI, ChatMessage

__all__ = ["Networking", "ChatMessage"]


class Networking(ChatAPI):
    """BITROT's extension of the `hackmudChatAPI.ChatAPI` class."""

    def __init__(self, **kwargs):
        """Create a BITROT networking instance.

        Args:
            **kwargs: Optional arguments that `hackmudChatAPI.ChatAPI` takes.
        """
        super().__init__(**kwargs)
        self.in_game: bool = False
        self.allChats: dict[str, list[ChatMessage]] = self.read(after=600)
        # self.allChats: dict[str, list[ChatMessage]] = self.read(after=600, before=300)
        # self.allChats: dict[str, list[ChatMessage]] = {}
        # self.waiting = False
        self.curr_user: str = ""

    class Challenge:
        """A BITROT challenge.

        Contains the challenger, the challenged, when the challenge was sent, and methods for responding to the challenge.
        """

        def __init__(
            self, network: Networking, challenger: str, challenged: str, sent_at: float
        ):
            self.network: Networking = network
            self.challenger: str = challenger
            self.challenged: str = challenged
            self.sent_at: float = sent_at

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
        from time import sleep
        from re import match

        try:
            state = {"accepted": False, "initial": None}
            loops = 0
            while not state["accepted"] or (state["accepted"] and not state["initial"]):
                new = self.fetch(60)["new"][self.curr_user]
                for message in new:
                    if message["from_user"] == challenged:
                        if message["msg"] in ["OCC", "DEC"]:
                            # print("declined")
                            return None

                        if state["accepted"]:
                            init_state_test = match(
                                r"(0)([01f]{9})([1|0]{1})([1-9]{1})", message["msg"]
                            )
                            if init_state_test is not None:
                                state["initial"] = message["msg"]
                                init_state_message = message
                                break
                        elif message["msg"] in ["ACC"]:
                            # print("accepted")
                            state["accepted"] = True
                            accepting_message = message
                if loops >= 60:
                    self.tell(self.curr_user, challenged, "BAH")
                    return None
                loops += 1
                sleep(rate)
            if state["accepted"]:
                # print(accepting_message)
                # print(init_state_message)
                return init_state_message["msg"]
            else:
                return None
        except KeyboardInterrupt:
            self.tell(self.curr_user, challenged, "BAH")
            return None

    def listen_opponent_move(
        self, opponent: str, rate: int | float = 2, timeout: int = 150
    ) -> str:
        """Listen for game state updates/opponent's move

        Continually fetches messages every `rate` seconds,
        and filters through messages sent to `self.curr_user` from `opponent` until a game state is recieved,
        and returns the recieved state string.

        Raises a TimeoutError after roughly 5 minutes of no state being recieved.

        Args:
            opponent (str): The current opponent.
            rate (int | float, optional): How frequently to read from the chat API in seconds. Defaults to 2.
        """
        from time import sleep
        from re import match

        # GAME_STATE_REGEX = r"([0-f]{1})([01-3f-d]{9})([01f]{1})([0-cf]{1})"
        GAME_STATE_REGEX = r"([0-f]{1})([0-f]{9})([0-f]{1})([0-f]{1})"

        loops = 0
        while not loops >= timeout:
            new = self.fetch(300)["new"][self.curr_user]
            for message in new:
                state_regex_match = match(GAME_STATE_REGEX, message["msg"])
                if (
                    message["from_user"] == opponent
                    and message.get("to_user") == self.curr_user
                    and state_regex_match is not None
                ):
                    # return message["msg"]
                    return state_regex_match.group()
            # if loops >= timeout:
            #     raise TimeoutError("opponent response timeout reached.")
            loops += 1
            sleep(rate)

        raise TimeoutError("opponent response timeout reached.")
