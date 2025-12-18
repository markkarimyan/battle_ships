# Battleship Game – Project Report

## Overview

This project is a terminal-based implementation of the classic **Battleship** game played on a **10×10 grid**.  
A human player competes against a computer-controlled opponent with a simple but structured AI.

The implementation focuses on:

- strict rule validation
- clear game-state tracking
- readable terminal output
- detailed CSV logging of gameplay

---

## Coordinate System and Input

### Board Coordinates

The board uses standard Battleship notation:

- Columns: `A` to `J`
- Rows: `1` to `10`

Internally, all coordinates are converted to **0-based `(row, column)` indices**.

---

## Ship Placement Input

Ships are placed manually by the player before the game starts.

### Supported input formats

#### 1. Space-separated coordinates

Used for ships larger than size 1.

```
A1 A2 A3
```

#### 2. Range format

Automatically expands into consecutive coordinates.  
Must be horizontal or vertical.

```
B4-B6
```

#### 3. Single-cell format

Used only for ships of size 1.

```
J10
```

If an invalid format is entered, the player is prompted again.

---

## Gameplay Move Input

During the game, the player enters moves in the following format:

```
A1
J10
```

Each move is validated to ensure:

- correct coordinate format
- within board bounds
- the cell has not already been targeted

---

## Ship Placement Validation

Before gameplay begins, the entire fleet is validated.

### Required Fleet Configuration

Both the player and the bot must have exactly:

- 1 ship of size 4
- 2 ships of size 3
- 3 ships of size 2
- 4 ships of size 1

---

### Validation Rules

Each ship placement must satisfy all of the following:

- **Board bounds**  
  All ship cells must lie within the 10×10 grid.

- **Straight alignment**  
  Ships must be placed horizontally or vertically.

- **Consecutive cells**  
  Ships must consist of adjacent cells with no gaps.

- **No overlap**  
  Ships may not share any cells.

- **No adjacency**  
  Ships must not touch each other, even diagonally.

Adjacency is checked by inspecting all 8 surrounding cells of every ship segment.

If validation fails, the player is required to re-enter the entire fleet.

---

## Game State Representation

### Boards

Each side maintains two logical boards:

1. **Visible board** – what the opponent is known to have
2. **Hidden ship board** – actual ship positions, used internally for hit detection

Boards are implemented as simple 10×10 two-dimensional lists.

---

### Cell Symbols

The visible boards use the following symbols:

| Symbol | Meaning                                     |
| ------ | ------------------------------------------- |
| `.`    | Unknown cell                                |
| `o`    | Miss                                        |
| `X`    | Hit                                         |
| `S`    | Ship (shown only on the player’s own board) |

When a ship is fully destroyed, all surrounding cells (in all 8 directions) are automatically marked as misses (`o`).

---

## Turn Logic and Extra Shots

Gameplay follows the classic Battleship rule:

- A **hit or a sink grants an extra shot**
- A **miss ends the current turn**

This rule applies to both the player and the bot.

As a result, a single turn may contain multiple shots by the same side.

---

## Bot AI Design

The bot uses a simple **state-based strategy** with three modes:

### RANDOM

- Selects a random unexplored cell.

### HUNT

- Activated after the first hit.
- Attacks adjacent cells (up, down, left, right).

### LOCKED

- Activated after multiple aligned hits.
- Determines ship orientation (horizontal or vertical).
- Continues attacking along the detected axis.

When a ship is sunk, the bot resets back to RANDOM mode.

---

## Game State Logging

All gameplay is logged to:

```
data/game_state.csv
```

### Logging Strategy

- The CSV file is updated **after every single shot**, including extra shots.
- Each row represents **one move**, not an entire turn.

### Logged Fields

- `move_number` – strictly increasing counter (every shot)
- `turn_number` – increases only when control returns to the player
- `who` – player or bot
- `coord` – human-readable coordinate (for example `B7`)
- `result` – miss / hit / sink
- `player_board_serialized`
- `bot_board_serialized`

Boards are serialized into compact 100-character strings using:

- `.` for unknown cells
- `o` for misses
- `X` for hits

---

## Design Decisions and Trade-offs

### Readability over Optimization

- Simple data structures (lists and loops) were chosen over complex ones.
- This improves clarity and ease of debugging.

### Flexible Input

- Multiple ship input formats improve usability.
- Validation logic is centralized to reduce duplication.

### Deterministic Bot Logic

- The bot uses rule-based behavior rather than probability-heavy logic.
- This makes its decisions predictable and explainable.

### Full Fleet Re-entry on Error

- Restarting fleet input simplifies validation.
- This slightly reduces convenience but improves correctness.

---

## Conclusion

This project provides a complete terminal-based Battleship game with:

- strict rule enforcement
- clear and readable gameplay output
- structured bot AI behavior
- detailed per-move CSV logging
- clean and maintainable code structure

The primary goal was correctness, clarity, and adherence to the game rules rather than advanced optimization or complex AI techniques.
