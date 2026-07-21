from hackmudChatAPI import ChatAPI, ChatMessage as ChatMessage

__all__ = ["ChatMessage", "Networking"]

class Networking(ChatAPI):
    in_game: bool
    allChats: dict[str, list[ChatMessage]]
    curr_user: str
    def __init__(
        self,
        *,
        config_file: str = f"{Networking.path[0]}/config.json",
        verbosity: int = 1,
    ): ...

    class Challenge:
        network: Networking
        challenger: str
        challenged: str
        sent_at: float
        def __init__(
            self, network: Networking, challenger: str, challenged: str, sent_at: float
        ) -> None: ...
        @staticmethod
        def challenge_from_message(
            network: Networking, message: ChatMessage
        ) -> Networking.Challenge: ...
        def accept(self) -> None: ...
        def decline(self) -> None: ...

    def fetch(
        self, seconds: int | float = 10
    ) -> dict[str, dict[str, list[ChatMessage]]]: ...
    def challenge(self, user: str, target: str) -> bool: ...
    def fetch_challenges(self) -> list[Networking.Challenge]: ...
    def listen_challenge_response(
        self, challenged: str, rate: int | float = 2
    ) -> str | None: ...
    def listen_game(self, opponent: str) -> str | None: ...
