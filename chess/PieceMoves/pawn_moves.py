# pawn_moves.py (for example)
# or part of movegen.py, adjusting to your code structure

from ..bitboard import (
    set_bit, clear_bit, test_bit,
    coords_to_square, square_to_coords, in_bounds
)
from ..move import Move

def generate_pawn_moves(game_state, is_white):
    moves = []
    pawns = game_state.whitePawns if is_white else game_state.blackPawns

    # For white, pawns move 'up' => row-1 in normal board terms
    # For black, pawns move 'down' => row+1
    direction = -1 if is_white else +1

    # The occupancy of the opponent's pieces:
    enemy_occ = game_state.get_black_occupancy() if is_white else game_state.get_white_occupancy()

    for sq in range(64):
        if test_bit(pawns, sq):
            row, col = square_to_coords(sq)

            # 1) Single-step forward if empty
            forward_row = row + direction
            if in_bounds(forward_row, col):
                forward_sq = coords_to_square(forward_row, col)
                if not test_bit(game_state.get_occupancy(), forward_sq):
                    # normal forward move
                    moves.append(Move('wP' if is_white else 'bP', sq, forward_sq))

                    # 2) Double-step from starting row (white row=6 or black row=1)
                    start_row = 6 if is_white else 1
                    if row == start_row:
                        double_row = row + 2 * direction
                        double_sq = coords_to_square(double_row, col)
                        if not test_bit(game_state.get_occupancy(), double_sq):
                            moves.append(Move('wP' if is_white else 'bP', sq, double_sq))

            # 3) Diagonal captures (including en passant)
            for dcol in [-1, +1]:
                capture_col = col + dcol
                capture_row = row + direction
                if in_bounds(capture_row, capture_col):
                    cap_sq = coords_to_square(capture_row, capture_col)

                    # normal diagonal capture
                    if test_bit(enemy_occ, cap_sq):
                        moves.append(Move('wP' if is_white else 'bP',
                                          sq, cap_sq, isCapture=True))
                    # en passant check
                    elif cap_sq == game_state.en_passant_target:
                        # The target is "behind" the enemy pawn that just jumped
                        # For the actual capture, you land on 'cap_sq',
                        # but the captured piece is on the row behind 'cap_sq'.
                        # The 'GameState' make_move logic will remove that piece from behind.
                        moves.append(Move('wP' if is_white else 'bP',
                                          sq, cap_sq, isCapture=True))

    return moves
