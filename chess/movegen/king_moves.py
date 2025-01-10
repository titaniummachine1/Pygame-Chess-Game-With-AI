from ..bitboard import set_bit, clear_bit, test_bit, coords_to_square, square_to_coords, in_bounds
from ..move import Move

def generate_king_moves(game_state, is_white):
    moves = []
    king = game_state.whiteKing if is_white else game_state.blackKing
    opponent_occupancy = game_state.get_black_occupancy() if is_white else game_state.get_white_occupancy()
    own_occupancy = game_state.get_white_occupancy() if is_white else game_state.get_black_occupancy()
    king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    for sq in range(64):
        if test_bit(king, sq):
            row, col = square_to_coords(sq)
            for dr, dc in king_moves:
                new_row, new_col = row + dr, col + dc
                if in_bounds(new_row, new_col):
                    new_sq = coords_to_square(new_row, new_col)
                    if not test_bit(own_occupancy, new_sq):
                        moves.append(Move('wK' if is_white else 'bK', sq, new_sq, isCapture=test_bit(opponent_occupancy, new_sq)))
            # Castling moves
            if is_white and not game_state.whiteKingMoved:
                if not game_state.whiteRookHMoved and not any(test_bit(game_state.get_occupancy(), coords_to_square(7, c)) for c in range(5, 7)):
                    moves.append(Move('wK', sq, coords_to_square(7, 6), isCastle=True))
                if not game_state.whiteRookAMoved and not any(test_bit(game_state.get_occupancy(), coords_to_square(7, c)) for c in range(1, 4)):
                    moves.append(Move('wK', sq, coords_to_square(7, 2), isCastle=True))
            elif not is_white and not game_state.blackKingMoved:
                if not game_state.blackRookHMoved and not any(test_bit(game_state.get_occupancy(), coords_to_square(0, c)) for c in range(5, 7)):
                    moves.append(Move('bK', sq, coords_to_square(0, 6), isCastle=True))
                if not game_state.blackRookAMoved and not any(test_bit(game_state.get_occupancy(), coords_to_square(0, c)) for c in range(1, 4)):
                    moves.append(Move('bK', sq, coords_to_square(0, 2), isCastle=True))
    return moves
