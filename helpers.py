
import numpy as np

"""
Helpers.py is a collection of functions that primarily make up the Ataxx game logic.
Beyond a few things in the World init, which can be copy/pasted this should be almost
all of what you'll need to simulate games in your search method.

Functions:
    get_directions    - a simple helper to deal with the geometry of Reversi moves
    count_capture     - how many flips does this move make. Game logic defines valid moves as those with >0 returns from this function. #TODO: Change this
    count_capture_dir - a helper for the above, unlikely to be used externally
    execute_move      - update the chess_board by simulating a move
    flip_disks        - a helper for the above, unlikely to be used externally
    check_endgame     - check for termination, who's won but also helpful to score non-terminated games
    get_valid_moves   - use this to get the children in your tree
    random_move       - basis of the random agent and can be used to simulate play

    For all, the chess_board is an np array of integers, size nxn and integer values indicating square occupancies.
    The current player is (1: Blue, 2: Brown), 0's in the board mean empty squares.
    Move pos is a tuple holding [row,col], zero indexed such that valid entries are [0,board_size-1]
"""

class MoveCoordinates:
    def __init__(self, src: tuple[int,int], dest: tuple[int, int]):
        self.row_src = src[0]
        self.col_src = src[1]
        self.row_dest = dest[0]
        self.col_dest = dest[1]

    def get_src(self) -> tuple[int, int]:
        return (self.row_src, self.col_src)
    
    def get_dest(self) -> tuple[int, int]:
        return (self.row_dest, self.col_dest)



def get_directions():
    """
    Get all directions (8 directions: up, down, left, right, and diagonals)

    Returns
    -------
    list of tuple
        List of direction vectors
    """
    return [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

def get_two_tile_directions(): 
    """
    Get all directions (8 directions: up, down, left, right, and diagonals)

    Returns
    -------
    list of tuple
        List of direction vectors
    """
    # TODO: is there a more logical way to organize this lol 
    return [(-2, 0), (2, 0), (0, -2), (0, 2), 
            (-2, 1), (2, 1), (1, -2), (1, 2), 
            (-2, -1), (2, -1), (-1, -2), (-1, 2),
            (-2, -2), (-2, 2), (2, -2), (2, 2)] 

def check_move_validity(chess_board, move_coords: MoveCoordinates, player: int) -> bool:
    src_tile = move_coords.get_src()
    dest_tile = move_coords.get_dest()

    # Check src and dest are on the board
    if not (0 <= src_tile[0] < chess_board.shape[0] and 0 <= src_tile[1] < chess_board.shape[1]):
        return False
    if not (0 <= dest_tile[0] < chess_board.shape[0] and 0 <= dest_tile[1] < chess_board.shape[1]):
        return False

    # Check dest is empty
    if not (chess_board[dest_tile[0], dest_tile[1]] == 0):
        return False 

    # Check src is owned by player
    if not (chess_board[src_tile[0], src_tile[1]] == player):
        return False 
    
    # Check if distance between discs is in the set of valid directions
    valid_distances_list = get_directions()
    valid_distances_list.extend(get_two_tile_directions())

    move_dist = (dest_tile[0] - src_tile[0], dest_tile[1] - src_tile[1])

    if not move_dist in valid_distances_list:
        return False
    
    return True

def count_disc_count_change(chess_board, move_coords: MoveCoordinates, player: int):
    """
    How many discs are gained by the move specified in move_coords. Total = opponent's discs are captured + duplication disc for single tile moves

    Returns
    -------
    int
        The number of stones that will be captured making this move, including all directions.
        -1 indicates any form of invalid move.
    """
    opponent_map = {0: 1, 1: 0} # This lets us quickly access the value corresponding to the opponent on the board based on current player number

    r_dest, c_dest = move_coords.get_dest()

    if not check_move_validity(chess_board, move_coords):
        return -1
    
    discs_gained = 0

    # Check if move captures any opponent discs in any direction
    for dir in get_directions():
        adj_tile = (r_dest + dir[0], c_dest + dir[1])

        # Check if adjacent tile is on the board
        if not (0 <= adj_tile[0] < chess_board.shape[0] and 0 <= adj_tile[1] < chess_board.shape[0]):
            return -1

        # If the tile, is an opponent, count it
        if chess_board[adj_tile[0], adj_tile[1]] == opponent_map(player):
            discs_gained += 1

    # If the move is single tile, count an extra disc for "duplication"
    r_src, c_src = move_coords.get_dest()
    if not ( (np.abs(r_dest - r_src) == 2) or (np.abs(c_dest - c_src) == 2) ):
        discs_gained += 1

    return discs_gained

def execute_move(chess_board, move_coords: MoveCoordinates, player: int):
    """
    Play the move specified by altering the chess_board.
    Note that chess_board is a pass-by-reference in/output parameter.
    Consider copy.deepcopy() of the chess_board if you want to consider numerous possibilities.
    """
    opponent_map = {1: 2, 2: 1} # This lets us quickly access the value corresponding to the opponent on the board based on current player number

    if not check_move_validity(chess_board, move_coords, player): # Throw an exception instead of executing an invalid move. This exception should be handled in the simulator logic
        raise Exception(f"Executing an invalid move! Player {player} is moving from ({move_coords.row_src},{move_coords.col_src}) to ({move_coords.row_dest},{move_coords.col_dest})")

    r_dest, c_dest = move_coords.get_dest()
    chess_board[r_dest, c_dest] = player

    # Flip opponent's discs in all directions where captures occur
    for direction in get_directions():
        adj_tile = (r_dest + direction[0], c_dest + direction[1])

        # Check if tile is on the board
        if not (0 <= adj_tile[0] < chess_board.shape[0] and 0 <= adj_tile[1] < chess_board.shape[0]):
            continue

        # If the tile, is an opponent, flip it
        if chess_board[adj_tile[0], adj_tile[1]] == opponent_map[player]:
            chess_board[adj_tile[0], adj_tile[1]] = player

    # If the move is two-tiles, empty the source tile
    r_src, c_src = move_coords.get_src()
    if (np.abs(r_dest - r_src) == 2) or (np.abs(c_dest - c_src) == 2):
        chess_board[r_src, c_src] = 0


def check_endgame(chess_board,player,opponent):
    """
    Check if the game ends and compute the final score. 
    
    We can actually just check if the board has any zeroes (empty) left

    Returns
    -------
    is_endgame : bool
        Whether the game ends.
    player_1_score : int
        The score of player 1.
    player_2_score : int
        The score of player 2.
    """

    is_endgame = False

    if np.sum(chess_board == 0) == 0:
        is_endgame = True  # When there are no spaces left, the game is over, score is current piece count

    p0_score = np.sum(chess_board == 1)
    p1_score = np.sum(chess_board == 2)
    return is_endgame, p0_score, p1_score

def get_valid_moves(chess_board,player):
    """
    Get all valid moves given the chess board and player.

    Returns

    -------
    valid_moves : [(tuple)]

    """

    board_size = chess_board.shape[0]
    valid_moves = []
    for r in range(board_size):
        for c in range(board_size):
            # Check square has a player's disc
            if chess_board[r, c] == player:
                src = (r,c)
                # loop over all possible moves
                candidate_move_list = get_directions()
                candidate_move_list.extend(get_two_tile_directions())

                for dir in candidate_move_list:
                    dest_tile = (r + dir[0], c + dir[1])
                    valid_move = MoveCoordinates(src=(r,c), dest=dest_tile)
                    if check_move_validity(chess_board, valid_move, player):
                        valid_moves.append(valid_move)

    return valid_moves

def random_move(chess_board, player):
    """
    random move from the list of valid moves.

    Returns

    ------
    (tuple)


    """

    valid_moves = get_valid_moves(chess_board,player)

    if len(valid_moves) == 0:
        # If no valid moves are available, return None
        print(f"No valid moves left for player {player}.")
        return None
    
    return valid_moves[np.random.randint(len(valid_moves))]
