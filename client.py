from bitrot.networking import Networking
from bitrot.engine import Match, Game
from bitrot.errors import GameAbort
from time import sleep

network = Networking()

CLIENT_MODE_PROMPT = """
Select client mode:

(1) - Send BITROT challenge.
(2) - View and manage recieved BITROT challenges.
(0) - Quit

"""

USER_SELECT_PROMPT = f"Select user to send a challenge as {network.users}: "

CHALLENGE_TARGET_PROMPT = "Enter user to challenge: "

CHALLENGE_RESPONSE_PROMPT = """
Would you like to accept or decline this challenge? (a/d/Return)

"""

DEAD_OPPONENT_MESSAGE = "\nThe opposing client experienced a fatal exception - no winner.\nPress enter to return to main menu."


def print_clear(*args, **kwargs) -> None:
    print("\x1b[2J")
    print(*args, **kwargs)


def input_clear(prompt: str = "", /) -> str:
    print("\x1b[2J")
    return input(prompt)


def input_with_timer(
    prompt: str, timer: int | float, clear: bool = True, error=TimeoutError
):
    import select
    from sys import stdout, stdin
    import time

    if clear:
        print("\x1b[2J")

    stdout.write(prompt)
    stdout.flush()

    start = time.time()
    ready, _, _ = select.select([stdin], [], [], timer)
    if ready:
        entered = time.time()
        usrInput = stdin.readline().rstrip("\n")  # expect stdin to be line-buffered
        time.sleep((start + 5) - entered)
        return usrInput
    else:
        stdout.write("\n")
        stdout.flush()
        raise error


def display_win(game: Game, winner: int):
    print_clear(
        f"{str(game.board)}\n\n{["attacker", "defender"][winner]} wins{f" due to {["attacker", "defender"][int(not winner)]} forfeit" if game.recent_op == "f" else ""}.\nPress enter to return to main menu."
    )


def attacker_match(opponent: str, initial_state: str) -> int | None:
    current_match = Match(network, "", opponent, 0, initial_state)

    try:
        while True:
            current_match.do_self_turn(
                input_clear(
                    f"{str(current_match.game.board)}\n\n{["attacker", "defender"][current_match.team]} ({current_match.team}) op: "
                )
            )
            print_clear(f"{str(current_match.game.board)}\n\nSending move...")
            current_match.send_state()
            win_check = current_match.game.check_win()
            if win_check is not None:
                network.in_game = False
                display_win(current_match.game, win_check)
                return win_check

            print_clear(
                f"{str(current_match.game.board)}\n\nWaiting for opponent move..."
            )
            current_match.do_opponent_turn()
            win_check = current_match.game.check_win()
            if win_check is not None:
                network.in_game = False
                display_win(current_match.game, win_check)
                return win_check
    except KeyboardInterrupt:
        current_match.do_self_turn("f")
        current_match.send_state()
        print("\nForfeit sent - exiting.")
        quit()
    except GameAbort:
        print(DEAD_OPPONENT_MESSAGE)
    except Exception as e:
        network.tell(network.curr_user, opponent, "fffffffffff0")
        raise e


def defender_match(opponent: str) -> int | None:
    current_match = Match(network, "", opponent, 1)

    try:
        while True:
            print_clear(
                f"{str(current_match.game.board)}\n\nWaiting for opponent move..."
            )
            current_match.do_opponent_turn()
            win_check = current_match.game.check_win()
            if win_check is not None:
                network.in_game = False
                display_win(current_match.game, win_check)
                return win_check

            current_match.do_self_turn(
                input_clear(
                    f"{str(current_match.game.board)}\n\n{["attacker", "defender"][current_match.team]} ({current_match.team}) op: "
                )
            )
            print_clear(f"{str(current_match.game.board)}\n\nSending move...")
            current_match.send_state()
            win_check = current_match.game.check_win()
            if win_check is not None:
                network.in_game = False
                display_win(current_match.game, win_check)
                return win_check
    except KeyboardInterrupt:
        current_match.do_self_turn("f")
        current_match.send_state()
        print("\nForfeit sent - exiting.")
        quit()
    except GameAbort:
        print(DEAD_OPPONENT_MESSAGE)
    except Exception as e:
        network.tell(network.curr_user, opponent, "fffffffffff0")
        raise e


while True:
    network.curr_user = ""
    client_mode = input_clear(CLIENT_MODE_PROMPT)

    match client_mode:
        case "1":
            try:
                user = ""
                while user not in network.users:
                    user = input_clear(
                        (f"'{user}' is not one of your users.\n" if user != "" else "")
                        + USER_SELECT_PROMPT
                    )

                challenge_sent = False
                target = ""
                response = None
                while not challenge_sent:
                    target = input_clear(
                        (f"'{target}' is not a valid user.\n" if target != "" else "")
                        + CHALLENGE_TARGET_PROMPT
                    )
                    challenge_sent = (
                        False if user == target else network.challenge(user, target)
                    )

                print_clear(f"Awaiting response from '{target}'...")
                response = network.listen_challenge_response(target)

                if response is None:
                    print_clear("Challenge timed out or was declined.")
                    sleep(3)
                else:
                    print_clear("Challenge accepted.")
                    attacker_match(target, response)
                    input()
            except KeyboardInterrupt:
                pass
        case "2":
            challenges: list[Networking.Challenge] = []
            accepted = None
            try:
                while accepted is None:
                    try:
                        challenges.extend(network.fetch_challenges())
                        challenge_display = "\n".join(
                            map(
                                lambda v: f"({challenges.index(v)+1}) {str(v)}",
                                challenges,
                            )
                        )
                        selected = challenges[
                            (
                                int(
                                    input_with_timer(
                                        f"{challenge_display}\n\nSelect challenge to respond to: ",
                                        5,
                                    )
                                )
                                - 1
                            )
                        ]
                        challenge_response = ""
                        challenge_response = input_clear(
                            f"{str(selected)}\n" + CHALLENGE_RESPONSE_PROMPT
                        )
                        match challenge_response:
                            case "a":
                                accepted = selected
                                challenges.pop(challenges.index(selected))
                                selected = None
                            case "d":
                                selected.decline()
                                challenges.pop(challenges.index(selected))
                                selected = None
                            case _:
                                break

                    except TimeoutError:
                        pass
                    except IndexError, ValueError:
                        pass
            except KeyboardInterrupt:
                accepted = None

            if accepted is not None:
                accepted.accept()
                defender_match(accepted.challenger)
                input()
        case "0":
            print("Exiting BITROT client.")
            quit()
        case _:
            pass
