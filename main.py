import os
import sys
import time

from src.bot_generation import generate_and_save_bot_ships
from src.gameplay import GameState, ask_player_for_move
from src.ship_input import get_and_save_player_ships


def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)

    print("Welcome to Battleship!")
    player_ships = get_and_save_player_ships(csv_path="data/player_ships.csv")
    bot_ships = generate_and_save_bot_ships(csv_path="data/bot_ships.csv")

    game_state = GameState.from_fleets(player_ships, bot_ships)
    game_state.init_log(csv_path="data/game_state.csv")

    try:
        while True:
            game_state.print_boards()

            if game_state.current_turn == "player":
                print("\n=== Your turn ===")
                while game_state.current_turn == "player":
                    mv = ask_player_for_move(game_state)
                    coord, result = game_state.player_take_turn(mv)

                    print(f"Result: {result}")
                    game_state.log_last_move()

                    if game_state.all_bot_ships_sunk():
                        game_state.print_boards()
                        print("\nYou win! All bot ships are destroyed.")
                        return

                    if not game_state.player_gets_extra_shot:
                        game_state.next_turn()
                        break

                    print("Hit! Extra shot.")
                    time.sleep(0.4)

            else:
                print("\n=== Bot turn ===")
                while game_state.current_turn == "bot":
                    coord, result = game_state.bot_take_turn()
                    print(f"Bot shot {game_state.coord_to_human(coord)} -> {result}")

                    game_state.log_last_move()

                    if game_state.all_player_ships_sunk():
                        game_state.print_boards()
                        print("\nGame over. Bot destroyed your fleet.")
                        return

                    if not game_state.bot_gets_extra_shot:
                        game_state.next_turn()
                        break

                    print("Bot hit! Bot gets extra shot.")
                    time.sleep(0.8)

    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
