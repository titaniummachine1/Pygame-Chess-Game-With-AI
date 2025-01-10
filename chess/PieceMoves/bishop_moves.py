from ..bitboard import set_bit, clear_bit, test_bit, coords_to_square, square_to_coords, in_bounds
from ..move import Move

def generate_bishop_moves(game_state, is_white):
    moves = []
    bishops = game_state.whiteBishops if is_white else game_state.blackBishops
    opponent_occupancy = game_state.get_black_occupancy() if is_white else game_state.get_white_occupancy()
    own_occupancy = game_state.get_white_occupancy() if is_white else game_state.get_black_occupancy()
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    for sq in range(64):
        if test_bit(bishops, sq):
            row, col = square_to_coords(sq)
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                while in_bounds(new_row, new_col):
                    new_sq = coords_to_square(new_row, new_col)
                    if test_bit(own_occupancy, new_sq):
                        break
                    moves.append(Move('wB' if is_white else 'bB', sq, new_sq, isCapture=test_bit(opponent_occupancy, new_sq)))
                    if test_bit(opponent_occupancy, new_sq):
                        break
                    new_row += dr
                    new_col += dc
    return moves
