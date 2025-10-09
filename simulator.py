from world import World, PLAYER_1_NAME, PLAYER_2_NAME
import argparse
from utils import all_logging_disabled
import logging
import numpy as np
import datetime

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

logger = logging.getLogger(__name__)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--player_1", type=str, default="random_agent")
    parser.add_argument("--player_2", type=str, default="random_agent")
    parser.add_argument(
        "--board_size",
        type=int,
        default=None,
        help="Board size. If not specified, chooses a random size within the range."
    )
    parser.add_argument(
        "--board_size_min",
        type=int,
        default=6,
        help="The minimum board size for autoplay mode",
    )
    parser.add_argument(
        "--board_size_max",
        type=int,
        default=12,
        help="The maximum board size for autoplay mode",
    )
    parser.add_argument("--display", action="store_true", default=False)
    parser.add_argument("--display_delay", type=float, default=0.4)
    parser.add_argument("--display_save", action="store_true", default=False)
    parser.add_argument("--display_save_path", type=str, default="plots/")
    parser.add_argument("--autoplay", action="store_true", default=False)
    parser.add_argument("--autoplay_runs", type=int, default=100)
    args = parser.parse_args()
    return args


class Simulator:
    """
    Entry point of the game simulator.

    Parameters
    ----------
    args : argparse.Namespace
    """

    def __init__(self, args):
        self.args = args
        # Only play on even-sized boards
        self.valid_board_sizes = [
            i for i in range(self.args.board_size_min, self.args.board_size_max+1)
            if i % 2 == 0
        ]

    def reset(self, swap_players=False, board_size=None):
        """
        Resets the game.

        Parameters
        ----------
        swap_players : bool
            Flag to swap the players
        board_size : int
            Sets the board size
        """
        player_1, player_2 = (
            (self.args.player_1, self.args.player_2)
            if swap_players else
            (self.args.player_2, self.args.player_1)
        )

        self.world = World(
            player_1=player_1,
            player_2=player_2,
            board_size=self.args.board_size if board_size is None else board_size,
            display_ui=self.args.display,
            display_delay=self.args.display_delay,
            display_save=self.args.display_save,
            display_save_path=self.args.display_save_path,
            autoplay=self.args.autoplay,
        )

    def run(self, swap_players=False, board_size=None):
        """
        Run the game for one iteration.

        Parameters
        ----------
        swap_players : bool
            Flag to swap the players
        board_size : int
            Sets the board size

        Outputs
        ----------
        p1_score: int
            The game score for player 1.
        p2_score: int
            The game score for player 2.
        p1_time: List[float]
            All the times that player 1 took.
        p2_time: List[float]
            All the times that player 2 took.
        """
        self.reset(swap_players=swap_players, board_size=board_size)
        is_end, p1_score, p2_score = self.world.step()
        while not is_end:
            is_end, p1_score, p2_score = self.world.step()

        logger.info(
            f'''Run finished.
            {PLAYER_1_NAME} player, agent "{self.args.player_1}" score: {p1_score}.
            {PLAYER_2_NAME} player, agent "{self.args.player_2}" score: {p2_score}.
            '''
        )

        if swap_players:
            return p2_score, p1_score, self.world.p2_time, self.world.p1_time

        return p1_score, p2_score, self.world.p1_time, self.world.p2_time

    def autoplay(self):
        """
        Run multiple simulations of the gameplay and aggregate win %
        """
        if self.args.display:
            logger.warning("Since running autoplay mode, display will be disabled")
        self.args.display = False

        p1_win_count = 0
        p2_win_count = 0
        p1_times = []
        p2_times = []
        with all_logging_disabled():
            for i in range(self.args.autoplay_runs):
                swap_players = i % 2 == 0
                board_size = self.valid_board_sizes[
                    np.random.randint(len(self.valid_board_sizes))
                ]
                p1_score, p2_score, p1_time, p2_time = self.run(
                    swap_players=swap_players, board_size=board_size
                )

                if p1_score > p2_score:
                    p1_win_count += 1
                elif p1_score < p2_score:
                    p2_win_count += 1
                else:  # Tie
                    p1_win_count += 0.5
                    p2_win_count += 0.5

                p1_times.extend(p1_time)
                p2_times.extend(p2_time)

        logger.info(
            f"Player 1, agent {self.args.player_1}, win percentage: {p1_win_count / self.args.autoplay_runs}. Maximum turn time was {np.round(np.max(p1_times),5)} seconds."
        )
        logger.info(
            f"Player 2, agent {self.args.player_2}, win percentage: {p2_win_count / self.args.autoplay_runs}. Maximum turn time was {np.round(np.max(p2_times),5)} seconds."
        )

        """
        The code in this comment will be part of the book-keeping that we use to score the end-of-term tournament. FYI. 
        Uncomment and use it if you find this book-keeping helpful.
        fname = (
            "tournament_results/"
            + self.world.player_1_name
            + "_vs_"
            + self.world.player_2_name
            + "_at_"
            + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            + ".csv"
        )
        with open(fname, "w") as fo:
            fo.write(f"P1Name,P2Name,NumRuns,P1WinPercent,P2WinPercent,P1RunTime,P2RunTime\n")
            fo.write(
                f"{self.world.player_1_name},{self.world.player_2_name},{self.args.autoplay_runs},{p1_win_count / self.args.autoplay_runs},{p2_win_count / self.args.autoplay_runs},{np.round(np.max(p1_times),5)},{np.round(np.max(p2_times),5)}\n"
            )
        """

if __name__ == "__main__":
    args = get_args()
    simulator = Simulator(args)
    if args.autoplay:
        simulator.autoplay()
    else:
        simulator.run()
