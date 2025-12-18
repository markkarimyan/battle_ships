import csv
import os
from typing import List, Tuple

BOARD_SIZE = 10
SHIP_SIZES = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]

Coord = Tuple[int, int]
Ship = List[Coord]

# Visible-board symbols (what player/bot knows)
UNKNOWN = "."
MISS = "o"
HIT = "X"


def coords_to_str(ship) -> str:
    if ship is None:
        return ""
    if isinstance(ship, tuple):
        return f"{chr(ship[1] + 65)}{ship[0] + 1}"
    return ",".join([f"{chr(c[1] + 65)}{c[0] + 1}" for c in ship])


def str_to_coords(s: str) -> Ship:
    coords = []
    for cell in s.split(","):
        cell = cell.strip()
        row = int(cell[1:]) - 1
        col = ord(cell[0].upper()) - 65
        coords.append((row, col))
    return coords


def in_bounds(coord: Coord) -> bool:
    return 0 <= coord[0] < BOARD_SIZE and 0 <= coord[1] < BOARD_SIZE


def get_adjacent_and_diagonal_cells(coord: Coord) -> List[Coord]:
    row, col = coord
    dirs = [
        (-1, 0), (1, 0), (0, -1), (0, 1),
        (-1, -1), (-1, 1), (1, -1), (1, 1),
    ]
    out = []
    for dr, dc in dirs:
        p = (row + dr, col + dc)
        if in_bounds(p):
            out.append(p)
    return out


def ships_touch_or_overlap(ships: List[Ship]) -> bool:
    for ship in ships:
        for coord in ship:
            for other_ship in ships:
                if coord in other_ship:
                    continue
                around = get_adjacent_and_diagonal_cells(coord)
                if any(cell in other_ship for cell in around):
                    return True
    return False


def validate_ship_fleet(ships: List[Ship]) -> Tuple[bool, str | None]:
    if sorted([len(ship) for ship in ships]) != sorted(SHIP_SIZES):
        return False, "Fleet sizes do not match required configuration."

    for ship in ships:
        if not all(in_bounds(coord) for coord in ship):
            return False, "Ship coordinates out of bounds."

        rows = [coord[0] for coord in ship]
        cols = [coord[1] for coord in ship]

        straight = all(r == rows[0] for r in rows) or all(c == cols[0] for c in cols)
        if not straight:
            return False, "Ship is not a straight line."

        # consecutive check
        if all(r == rows[0] for r in rows):
            if sorted(cols) != list(range(min(cols), max(cols) + 1)):
                return False, "Ship has gaps."
        else:
            if sorted(rows) != list(range(min(rows), max(rows) + 1)):
                return False, "Ship has gaps."

    if ships_touch_or_overlap(ships):
        return False, "Ships cannot touch (even diagonally) or overlap."

    return True, None


def ensure_parent_dir(path: str) -> None:
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)


def write_ships_csv(csv_path: str, ships: List[Ship]) -> None:
    ensure_parent_dir(csv_path)
    with open(csv_path, mode="w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ship_id", "size", "coordinates"])
        for ship_id, ship in enumerate(ships, start=1):
            w.writerow([ship_id, len(ship), coords_to_str(ship)])
