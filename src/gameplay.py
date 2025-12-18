import csv
import os
import random
from typing import List, Optional, Tuple

from src.utils import (
    BOARD_SIZE,
    Coord,
    Ship,
    UNKNOWN,
    MISS,
    HIT,
    coords_to_str,
    get_adjacent_and_diagonal_cells,
    in_bounds,
)


class GameState:
    RANDOM = "random"
    HUNT = "hunt"
    LOCKED = "locked"

    def __init__(self, player_ships: List[Ship], bot_ships: List[Ship]):
        self.turn_number = 1
        self.move_number = 0

        self.player_ships = player_ships
        self.bot_ships = bot_ships

        self.player_board = [[UNKNOWN for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.bot_board = [[UNKNOWN for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]

        self.player_board_ships = self._create_ship_board(player_ships)
        self.bot_board_ships = self._create_ship_board(bot_ships)

        self.current_turn = "player"
        self.player_gets_extra_shot = False
        self.bot_gets_extra_shot = False

        self.bot_mode = GameState.RANDOM
        self.bot_hit_chain: List[Coord] = []
        self.bot_last_hit: Optional[Coord] = None
        self.bot_orientation: Optional[str] = None

        self._log_path: Optional[str] = None
        self._last_move: Optional[Tuple[int, int, str, str]] = None  # (r,c, result, who)

    @staticmethod
    def from_fleets(player_fleet: List[Ship], bot_fleet: List[Ship]) -> "GameState":
        return GameState(player_fleet, bot_fleet)

    def init_log(self, csv_path: str) -> None:
        self._log_path = csv_path
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                "move_number",
                "turn_number",
                "who",
                "coord",
                "result",
                "player_board_serialized",
                "bot_board_serialized",
            ])

    def serialize_board(self, board: List[List[str]]) -> str:
        return "".join("".join(cell for cell in row) for row in board)

    def log_last_move(self) -> None:
        if not self._log_path or not self._last_move:
            return
        r, c, result, who = self._last_move
        self.move_number += 1

        with open(self._log_path, "a", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                self.move_number,
                self.turn_number,
                who,
                self.coord_to_human((r, c)),
                result,
                self.serialize_board(self.player_board),
                self.serialize_board(self.bot_board),
            ])

    def _create_ship_board(self, ships: List[Ship]) -> List[List[str]]:
        b = [[" " for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        for ship in ships:
            for r, c in ship:
                if in_bounds((r, c)):
                    b[r][c] = "S"
        return b

    def coord_to_human(self, coord: Coord) -> str:
        r, c = coord
        return f"{chr(c + ord('A'))}{r + 1}"

    def apply_move(
        self,
        board: List[List[str]],
        ship_board: List[List[str]],
        ships: List[Ship],
        coord: Coord,
    ) -> Tuple[str, bool]:
        r, c = coord
        if not in_bounds(coord):
            return "invalid", False

        if board[r][c] != UNKNOWN:
            return "invalid", False

        if ship_board[r][c] == "S":
            board[r][c] = HIT
            sunk = self.check_if_ship_sunk(coord, ships, board)
            if sunk:
                self.mark_surrounding_cells_as_miss(coord, ships, board)
                return "sink", True
            return "hit", False
        else:
            board[r][c] = MISS
            return "miss", False

    def check_if_ship_sunk(self, coord: Coord, ships: List[Ship], board: List[List[str]]) -> bool:
        for ship in ships:
            if coord in ship:
                return all(board[r][c] == HIT for (r, c) in ship)
        return False

    def mark_surrounding_cells_as_miss(self, coord: Coord, ships: List[Ship], board: List[List[str]]) -> None:
        for ship in ships:
            if coord in ship:
                around = set()
                for rc in ship:
                    for nb in get_adjacent_and_diagonal_cells(rc):
                        around.add(nb)
                for rr, cc in around:
                    if board[rr][cc] == UNKNOWN:
                        board[rr][cc] = MISS
                break

    def all_player_ships_sunk(self) -> bool:
        for ship in self.player_ships:
            if not all(self.player_board[r][c] == HIT for (r, c) in ship):
                return False
        return True

    def all_bot_ships_sunk(self) -> bool:
        for ship in self.bot_ships:
            if not all(self.bot_board[r][c] == HIT for (r, c) in ship):
                return False
        return True

    def next_turn(self):
        self.player_gets_extra_shot = False
        self.bot_gets_extra_shot = False

        if self.current_turn == "player":
            self.current_turn = "bot"
        else:
            self.current_turn = "player"
            self.turn_number += 1

    def player_take_turn(self, coord: Coord) -> Tuple[Coord, str]:
        result, _ = self.apply_move(self.bot_board, self.bot_board_ships, self.bot_ships, coord)

        self.player_gets_extra_shot = result in ("hit", "sink")
        self._last_move = (coord[0], coord[1], result, "player")
        return coord, result

    def bot_take_turn(self) -> Tuple[Coord, str]:
        coord = self._bot_choose_move()
        result, _ = self.apply_move(self.player_board, self.player_board_ships, self.player_ships, coord)

        self.bot_gets_extra_shot = result in ("hit", "sink")
        self._bot_update_state(coord, result)

        self._last_move = (coord[0], coord[1], result, "bot")
        return coord, result

    def _bot_choose_move(self) -> Coord:
        if self.bot_mode == GameState.RANDOM:
            return self._bot_random_pick()

        if self.bot_mode == GameState.HUNT:
            opts = []
            for r, c in self.bot_hit_chain:
                for nr, nc in [(r-1,c), (r+1,c), (r,c-1), (r,c+1)]:
                    if in_bounds((nr, nc)) and self.player_board[nr][nc] == UNKNOWN:
                        opts.append((nr, nc))
            if opts:
                return random.choice(opts)
            self.bot_mode = GameState.RANDOM
            return self._bot_random_pick()

        # LOCKED
        if self.bot_mode == GameState.LOCKED and self.bot_orientation:
            hits = sorted(self.bot_hit_chain)
            if self.bot_orientation == "horizontal":
                r = hits[0][0]
                cols = [c for _, c in hits]
                left = (r, min(cols) - 1)
                right = (r, max(cols) + 1)
                candidates = []
                if in_bounds(left) and self.player_board[left[0]][left[1]] == UNKNOWN:
                    candidates.append(left)
                if in_bounds(right) and self.player_board[right[0]][right[1]] == UNKNOWN:
                    candidates.append(right)
                if candidates:
                    return random.choice(candidates)
            else:
                c = hits[0][1]
                rows = [r for r, _ in hits]
                up = (min(rows) - 1, c)
                down = (max(rows) + 1, c)
                candidates = []
                if in_bounds(up) and self.player_board[up[0]][up[1]] == UNKNOWN:
                    candidates.append(up)
                if in_bounds(down) and self.player_board[down[0]][down[1]] == UNKNOWN:
                    candidates.append(down)
                if candidates:
                    return random.choice(candidates)

            self.bot_mode = GameState.HUNT
            return self._bot_choose_move()

        return self._bot_random_pick()

    def _bot_random_pick(self) -> Coord:
        choices = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.player_board[r][c] == UNKNOWN:
                    choices.append((r, c))
        return random.choice(choices)

    def _infer_orientation(self):
        if len(self.bot_hit_chain) < 2:
            self.bot_orientation = None
            return
        hits = sorted(self.bot_hit_chain)
        if all(r == hits[0][0] for r, _ in hits):
            self.bot_orientation = "horizontal"
        elif all(c == hits[0][1] for _, c in hits):
            self.bot_orientation = "vertical"
        else:
            self.bot_orientation = None

    def _bot_update_state(self, coord: Coord, result: str) -> None:
        if result == "hit":
            if coord not in self.bot_hit_chain:
                self.bot_hit_chain.append(coord)
            self.bot_mode = GameState.HUNT
            self._infer_orientation()
            if self.bot_orientation and len(self.bot_hit_chain) >= 2:
                self.bot_mode = GameState.LOCKED

        elif result == "sink":
            self.bot_hit_chain = []
            self.bot_orientation = None
            self.bot_mode = GameState.RANDOM

        elif result == "miss":
            if self.bot_mode == GameState.HUNT and len(self.bot_hit_chain) >= 2:
                self._infer_orientation()
                if self.bot_orientation:
                    self.bot_mode = GameState.LOCKED

    def print_boards(self) -> None:
        def header():
            return "   " + " ".join([chr(ord("A") + i) for i in range(BOARD_SIZE)])

        print("\n" + "=" * 60)
        print(f"Turn: {self.turn_number} | Next: {self.current_turn}")
        print("=" * 60)

        print("\nYour board (ships visible)".ljust(32) + "Enemy board (fog of war)")
        print(header().ljust(32) + header())

        for r in range(BOARD_SIZE):
            left_cells = []
            for c in range(BOARD_SIZE):
                if self.player_board[r][c] == HIT:
                    left_cells.append(HIT)
                elif self.player_board[r][c] == MISS:
                    left_cells.append(MISS)
                else:
                    left_cells.append("S" if self.player_board_ships[r][c] == "S" else UNKNOWN)

            right_cells = self.bot_board[r]

            left_line = f"{r+1:>2} " + " ".join(left_cells)
            right_line = f"{r+1:>2} " + " ".join(right_cells)
            print(left_line.ljust(32) + right_line)
        print()


def ask_player_for_move(game_state: GameState) -> Coord:
    while True:
        s = input("Move (A1..J10): ").strip().upper()

        if len(s) < 2 or len(s) > 3:
            print("Bad format.")
            continue

        if not (s[0].isalpha() and s[1:].isdigit()):
            print("Bad format.")
            continue

        c = ord(s[0]) - ord("A")
        r = int(s[1:]) - 1

        if not (0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE):
            print(f"Out of bounds. Use A1..J{BOARD_SIZE}.")
            continue

        if game_state.bot_board[r][c] != UNKNOWN:
            print("Already shot there.")
            continue

        return (r, c)
