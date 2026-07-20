# BITROT Networking Spec

- Game state will be sent as a string of 12 hex characters.
  - In the event of a fatal client exception mid-game, `fffffffffff0` will attempt to be sent.
- "Challenge" queries and responses will be SYN-ACK style.

## State Data

### Bytes Chart

```txt

                          |player|
                              |
                              |--|
                                 |
                  |----0123456789ab----|
                  |     |       |      |
|playing/winner|--|     |-------|      |--|op|
                            |
                      |board state|


```

### Bytes Definition

#### Playing/Winner \[`0`]

This character says if the game is active, and who won (if game finished).

- `0` - game inactive
- `1` - game active
- `2` - attacker won
- `3` - defender won

#### Board State \[`1`-`9`]

These characters represent the current state of the board, with board positions 1-9 being in characters 1-9 respectively.

`0` indicates an empty space.

Attacker pieces start at `1`, and increase by their age.
Defender pieces start at `f`, and decrease by their age.

- `0` - empty space
- `1`-`3` - attacker piece
- `f`-`d` - defender piece

#### Player \[`a`]

The player who made the latest move.

- `0` - attacker
- `1` - defender

#### Op \[`b`]

The most recent move.

- `0` - no-op
- `1`-`9` - valid op
- `a` - occupied space
- `b` - out of range
- `c` - unknown
- `f` - forfeit

### Reserved Sequences

The below sequences are reserved for client communication,
and should be impossible to reach in a game.

| Sequence       | Meaning                                        | Notes & Behaviour                                                                                                                                                    |
| -------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fffffffffff0` | Fatal client exception occurred (no recovery). | Sending client experienced a fatal exception. The match is to be discarded - no win/loss.                                                                            |
| `fffffffffff1` | Fatal client exception occurred (recovery).    | Sending client experienced a fatal exception, but believes it can recover and continue playing. Recieving client will reset its match timeout, and behave as normal. |
| `f000000000fc` | Provide game state.                            | Sending client is requesting current game state. Recieving client will respond with its current game state.                                                          |
| `f000000000fb` | Timeout reached.                               | Recieving client took too long to make a move, and the sending client is declaring the match as dead.                                                                |
<!-- | `f0000000002a` | 42                                             | 42                                                                                                                                                                   | -->

## Challenging (requesting & starting a game)

### Terms

- `CHA`
  - "I challenge thee!"
- `ACK`
  - "I have received your challenge."
- `ACC`
  - "I accept. Initial state incoming..."
- `DEC`
  - "I decline your challenge."
- `OCC`
  - "I am currently occupied."
- `BAH`
  - "I grow tired of waiting. The challenge is null."

### Notes

After accepting a challenge with `ACC`, the challenged should generate and send an initial game state with "playing" set to `0`.

`BAH` invalidates a pending challenge.

In the event of `DEC`, the challenge is immediately invalidated, and the challenger will be unable to send another challenge to the same user for 2 minutes.

`OCC` is sent when the challenged is currently in a game, and immediately invalidates the challenge.

Challenges will time out after 2 minutes of no response, automatically sending `BAH`.

Active games will time out after 5 minutes of no response.
