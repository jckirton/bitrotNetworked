# Bitrot Gameplay

This document will outline some key facts and decisions regarding the gameplay of bitrot, and how they relate to balance and implementation.

- [Bitrot Gameplay](#bitrot-gameplay)
  - [Gameplay Description](#gameplay-description)
    - [Gameplay loop](#gameplay-loop)
    - [Players](#players)
    - [The board](#the-board)
    - [Pieces \& aging](#pieces--aging)
      - [Pieces](#pieces)
      - [Aging](#aging)
    - [Win conditions](#win-conditions)
  - [Gameplay Notes \& Decisions](#gameplay-notes--decisions)
    - [Bitrot has favorites](#bitrot-has-favorites)
    - [Speed is appreciated, and mandatory](#speed-is-appreciated-and-mandatory)
    - [Bitrot is not forgiving](#bitrot-is-not-forgiving)
    - [This is a private matter](#this-is-a-private-matter)
    - [You are not safe when attacking](#you-are-not-safe-when-attacking)

## Gameplay Description

The setup and gameplay of bitrot goes as follows:

- Players are decided
- A board is made
- The first move of each player is made randomly (more on this later)
- 30s countdown to game start
- Gameplay loop until someone wins or defending system rotates
  - If attacker wins, BINMAT starts as usual

### Gameplay loop

A turn of bitrot and its resolution has the following process:

- Get player input
- Check move validity
- Place piece if valid
- Age that player's pieces
- Check win condition

Turns alternate between attacker and defender until the game ends.

### Players

Bitrot has two players: the attacker and defender.

The attacker plays first.

The attacker's pieces are represented by `0`, and the defender's are represented with `1`

### The board

The bitrot board is identical to a tic-tac-toe board: a 3x3 grid of spaces.

The board layout would be as follows:

```txt
7    |8    |9
     |     |   
     |     |
-----|-----|-----
4    |5    |6
     |     |   
     |     |
-----|-----|-----
1    |2    |3
     |     |   
     |     |     
```

Players reference a position on the board by the number in the top-left corner of that space.

For example, the attacker places a piece in position 7. The board now looks like:

```txt
7    |8    |9
  0  |     |   
     |     |
-----|-----|-----
4    |5    |6
     |     |   
     |     |
-----|-----|-----
1    |2    |3
     |     |   
     |     |     
```

### Pieces & aging

#### Pieces

Pieces in bitrot have two components: ownership, and age.

Ownership refers to who owns the piece (attacker or defender), and determines how the piece is represented.

Age refers to how long the piece has been on the board, and determines what color the piece is represented with.

#### Aging

Pieces in bitrot have a lifetime, and decay away after being on the board for a certain amount time.

Pieces age as part of their owner's turn: the attacker's turn will only age the attacker's pieces, and not age the defender's pieces

Pieces remain on the board for three of its owner's turns, and disappears as part of the fourth turn.

In effect, this means a player can only have up to three of their pieces on the board at any point in time, but cannot replace a disappearing piece.

### Win conditions

A player wins when they manage to get three active pieces in a row on the board at the end of their turn's resolution. Whichever player owns those pieces is declared the winner.

As the board cannot be filled, there is no way to tie via traditional means of the board filling. Instead, a tie occurs if the defending system rotates during the bitrot game.

In summary:

- A player wins by getting three of their pieces in a row.
- A tie occurs if the defending system rotates before a winner is determined.

## Gameplay Notes & Decisions

### Bitrot has favorites

The game favors the first to play. Assuming perfect play from an empty board, the first to play can always guarantee a win, or infinite loop.

This is the reason the first move of both players is made for them at random. It serves to make the game less about the ideal setup, and more about playing the game well.

How this affects player-favoritism is yet to be fully tested, but I suspect it will remain favoring the first player slightly.

### Speed is appreciated, and mandatory

There will be 5s turn timers. If a move is not made in that time, it is treated as an invalid move.

The turn timers will function similarly to BINMAT.

### Bitrot is not forgiving

When an invalid move is made, your turn happens without a new piece being placed. Your currently placed pieces will still decay.

Invalid moves include the following:

- Attempting to place "outside" the board
- Attempting to place in an already occupied space
- Failing to submit a move in time
- Attempting to submit more than one move in the same turn
  - This one is currently just an idea, and not yet decided

### This is a private matter

Bitrot is a one-on-one game. Just you, and your opponent.

Bitrot brain scripts will not be allowed to run any non-bitrot script - trust or otherwise.

### You are not safe when attacking

If you try to breach a user already engaged in a defending game of bitrot, the loc of the attacker will be shown.

While it may be a private matter, you can still crash the party.

In the event of the attacker being breached, they will be immediately removed from the game, and the game will resolve like a tie.

Similar to BINMAT, those engaged in offensive bitrot games will be unable to defend themselves with bitrot or BINMAT, resulting in them being breached when a game of bitrot would otherwise begin.
