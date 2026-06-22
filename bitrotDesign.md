# Bitrot Design Document

## Gameplay

Decaying tic-tac-toe.
5s turn timer? Shorter?
Python implementation at <https://github.com/jckirton/CompleteP3/blob/master/games/tic_tac_toe_redux.py>

## Implementation Notes

- Acts as extension to BINMAT.
  - Would occur before BINMAT, with a game of BINMAT starting on attacker win.
    - Or, depending on who wins (not via rotation), a game of BINMAT is started with the losing player as the defender, allowing for counterattack.
  - Bitrot game is limited by loc rotation time, but on attacker win rotation timer is reset to ensure BINMAT is not unfairly weighted towards defender.
  - Same BINMAT xfer restrictions would apply.
  - Attacker plays first.
- Win Conditions
  - Attacker
    - Player gets three of their pieces in a row. (standard tic-tac-toe win condition)
  - Defender
    - Player gets three of their pieces in a row. (standard tic-tac-toe win condition)
    - loc rotation
- 1v1 only, balance doesn't support multiple players in one team.
- No ante.

### Game state data format

```ts
{
    // Which player you are. Attacker is player 0, defender is player 1.
    plr: 0 | 1,
    plrs: {
        // Attacker and defender usernames.
        0: "attacker",
        1: "defender"
    },
    s: {
        // Board position. Game board is in a numpad layout.
        1: {
            // piece ownership
            p: 1 | 0,
            // piece age - pieces last three turns, and are deleted on the fourth. Refer to python implementation for clarification.
            a: 0 | 1 | 2
        },
        2: {
            p: 1 | 0,
            a: 0 | 1 | 2
        },
        3: {
            p: 1 | 0,
            a: 0 | 1 | 2
        },
        4: {
            p: 1 | 0,
            a: 0 | 1 | 2
        },
        5: {
            p: 1 | 0,
            a: 0 | 1 | 2
        },
        6: {
            p: 1 | 0,
            a: 0 | 1 | 2
        },
        7: {
            p: 1 | 0,
            a: 0 | 1 | 2
        },
        8: {
            p: 1 | 0,
            a: 0 | 1 | 2
        },
        9: {
            p: 1 | 0,
            a: 0 | 1 | 2
        },
    }
}
```
