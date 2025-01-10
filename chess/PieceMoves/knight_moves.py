from ..bitboard import set_bit, clear_bit, test_bit, coords_to_square, square_to_coords, in_bounds
from ..move import Move

def generate_knight_moves(game_state, is_white):
    moves = []
    knights = game_state.whiteKnights if is_white else game_state.blackKnights
    opponent_occupancy = game_state.get_black_occupancy() if is_white else game_state.get_white_occupancy()
    own_occupancy = game_state.get_white_occupancy() if is_white else game_state.get_black_occupancy()
    knight_moves = [(-2, -1), (-1, -2), (1, -2), (2, -1), (2, 1), (1, 2), (-1, 2), (-2, 1)]

    for sq in range(64):
        if test_bit(knights, sq):
            row, col = square_to_coords(sq)
            for dr, dc in knight_moves:
                new_row, new_col = row + dr, col + dc
                if in_bounds(new_row, new_col):
                    new_sq = coords_to_square(new_row, new_col)
                    if not test_bit(own_occupancy, new_sq):
                        moves.append(Move('wN' if is_white else 'bN', sq, new_sq, isCapture=test_bit(opponent_occupancy, new_sq)))
    return moves
