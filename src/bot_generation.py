import csv
import os
import random
from typing import List

from src.utils import (
    BOARD_SIZE,
    SHIP_SIZES,
    Ship,
    coords_to_str,
    in_bounds,
    ships_touch_or_overlap,
    validate_ship_fleet,
)


def _rand_orientation() -> str:
    return random.choice(["horizontal", "vertical"])


def _build_ship(size: int) -> Ship:
    while True:
        orient = _rand_orientation()

        if orient == "horizontal":
            r = random.randint(0, BOARD_SIZE - 1)
            c = random.randint(0, BOARD_SIZE - size)
            ship = [(r, c + i) for i in range(size)]
        else:
            r = random.randint(0, BOARD_SIZE - size)
            c = random.randint(0, BOARD_SIZE - 1)
            ship = [(r + i, c) for i in range(size)]

        if all(in_bounds(x) for x in ship):
            return ship


def generate_bot_ships() -> List[Ship]:
    while True:
        ships: List[Ship] = []

        for size in SHIP_SIZES:
            # try a bunch of placements for this ship
            for _ in range(5000):
                candidate = _build_ship(size)
                if not ships_touch_or_overlap(ships + [candidate]):
                    ships.append(candidate)
                    break
            else:
                ships = []
                break

        if not ships:
            continue

        ok, _ = validate_ship_fleet(ships)
        if ok:
            return ships


def generate_and_save_bot_ships(csv_path: str = "data/bot_ships.csv") -> List[Ship]:
    ships = generate_bot_ships()

    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, mode="w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ship_id", "size", "coordinates"])
        for ship_id, ship in enumerate(ships, start=1):
            w.writerow([ship_id, len(ship), coords_to_str(ship)])

    return ships
