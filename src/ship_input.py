import csv
import os
from typing import List

from src.utils import (
    BOARD_SIZE,
    SHIP_SIZES,
    Ship,
    coords_to_str,
    get_adjacent_and_diagonal_cells,
    in_bounds,
    str_to_coords,
    validate_ship_fleet,
)


def prompt_ship_input(size: int, ship_index: int = 1) -> Ship:
    while True:
        raw = input(f"Ship #{ship_index} (size {size}). Enter coords: ").strip().upper()

        try:
            # "A1 A2 A3"
            if " " in raw:
                parts = raw.split()
                ship_coords = [str_to_coords(p)[0] for p in parts]

            # "B4-B6"
            elif "-" in raw:
                a, b = raw.split("-")
                (r1, c1) = str_to_coords(a)[0]
                (r2, c2) = str_to_coords(b)[0]

                if r1 == r2:
                    step = 1 if c2 >= c1 else -1
                    ship_coords = [(r1, c) for c in range(c1, c2 + step, step)]
                elif c1 == c2:
                    step = 1 if r2 >= r1 else -1
                    ship_coords = [(r, c1) for r in range(r1, r2 + step, step)]
                else:
                    raise ValueError("Ship must be horizontal or vertical.")

            # "A10" for size 1
            elif raw and raw[0].isalpha() and raw[1:].isdigit():
                ship_coords = [str_to_coords(raw)[0]]

            else:
                raise ValueError("Bad format.")

        except Exception as e:
            print(f"Error: {e}. Try again.")
            continue

        if len(ship_coords) != size:
            print(f"Error: expected {size} cells, got {len(ship_coords)}.")
            continue

        if not all(in_bounds(c) for c in ship_coords):
            print(f"Error: out of bounds. Use A1..J{BOARD_SIZE}.")
            continue

        return ship_coords


def are_ships_adjacent(ships: List[Ship]) -> bool:
    for ship in ships:
        for coord in ship:
            around = get_adjacent_and_diagonal_cells(coord)
            for other in ships:
                if other is ship:
                    continue
                if any(cell in other for cell in around):
                    return True
    return False


def get_and_save_player_ships(csv_path: str = "data/player_ships.csv") -> List[Ship]:
    print(
        f"""
Place your ships on a {BOARD_SIZE}x{BOARD_SIZE} board (A1–J10).

Allowed formats:
- Space list:   A1 A2 A3
- Range:        B4-B6
- Single cell:  J10   (only for size 1 ships)

Ships must not touch each other (even diagonally).
"""
    )

    ships: List[Ship] = []
    ship_index = 1

    for size in SHIP_SIZES:
        ships.append(prompt_ship_input(size, ship_index))
        ship_index += 1

    ok, msg = validate_ship_fleet(ships)
    if not ok:
        print(f"Fleet invalid: {msg}")
        print("Re-enter the whole fleet.\n")
        return get_and_save_player_ships(csv_path)

    if are_ships_adjacent(ships):
        print("Fleet invalid: ships touch diagonally/adjacent.")
        print("Re-enter the whole fleet.\n")
        return get_and_save_player_ships(csv_path)

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, mode="w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ship_id", "size", "coordinates"])
        for ship_id, ship in enumerate(ships, start=1):
            w.writerow([ship_id, len(ship), coords_to_str(ship)])

    return ships
