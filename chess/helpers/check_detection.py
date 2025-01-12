from chess.bitboard import test_bit, coords_to_square, square_to_coords, in_bounds
from chess.movegen import generate_all_moves

def is_square_attacked(game_state, square, by_white):
    """
    Check if a square is attacked by the opponent.
    """
    opponent_moves = generate_all_moves(game_state)
    for move in opponent_moves:
        if move.endSq == square:
            return True
    return False

def get_attackers(sq: int, by_white: bool, game_state) -> list:
    """Get a list of pieces attacking the specified square."""
    attackers = []
    if by_white:
        if is_attacked_by_pawn(sq, True, game_state):
            attackers.append('wP')
        if is_attacked_by_knight(sq, True, game_state):
            attackers.append('wN')
        if is_attacked_by_bishop(sq, True, game_state):
            attackers.append('wB')
        if is_attacked_by_rook(sq, True, game_state):
            attackers.append('wR')
        if is_attacked_by_queen(sq, True, game_state):
            attackers.append('wQ')
        if is_attacked_by_king(sq, True, game_state):
            attackers.append('wK')
    else:
        if is_attacked_by_pawn(sq, False, game_state):
            attackers.append('bP')
        if is_attacked_by_knight(sq, False, game_state):
            attackers.append('bN')
        if is_attacked_by_bishop(sq, False, game_state):
            attackers.append('bB')
        if is_attacked_by_rook(sq, False, game_state):
            attackers.append('bR')
        if is_attacked_by_queen(sq, False, game_state):
            attackers.append('bQ')
        if is_attacked_by_king(sq, False, game_state):
            attackers.append('bK')
    return attackers

def is_attacked_by_pawn(sq: int, by_white: bool, game_state) -> bool:
    """Check if the square is attacked by a pawn."""
    row, col = square_to_coords(sq)
    if by_white:
        return (in_bounds(row - 1, col - 1) and test_bit(game_state.whitePawns, coords_to_square(row - 1, col - 1))) or \
               (in_bounds(row - 1, col + 1) and test_bit(game_state.whitePawns, coords_to_square(row - 1, col + 1)))
    else:
        return (in_bounds(row + 1, col - 1) and test_bit(game_state.blackPawns, coords_to_square(row + 1, col - 1))) or \
               (in_bounds(row + 1, col + 1) and test_bit(game_state.blackPawns, coords_to_square(row + 1, col + 1)))

def is_attacked_by_knight(sq: int, by_white: bool, game_state) -> bool:
    """Check if the square is attacked by a knight."""
    row, col = square_to_coords(sq)
    knight_moves = [
        (row + 2, col + 1), (row + 2, col - 1), (row - 2, col + 1), (row - 2, col - 1),
        (row + 1, col + 2), (row + 1, col - 2), (row - 1, col + 2), (row - 1, col - 2)
    ]
    for r, c in knight_moves:
        if in_bounds(r, c):
            if by_white and test_bit(game_state.whiteKnights, coords_to_square(r, c)):
                return True
            if not by_white and test_bit(game_state.blackKnights, coords_to_square(r, c)):
                return True
    return False

def is_attacked_by_bishop(sq: int, by_white: bool, game_state) -> bool:
    """Check if the square is attacked by a bishop."""
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    return is_attacked_by_sliding_piece(sq, by_white, directions, game_state.whiteBishops, game_state.blackBishops, game_state)

def is_attacked_by_rook(sq: int, by_white: bool, game_state) -> bool:
    """Check if the square is attacked by a rook."""
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    return is_attacked_by_sliding_piece(sq, by_white, directions, game_state.whiteRooks, game_state.blackRooks, game_state)

def is_attacked_by_queen(sq: int, by_white: bool, game_state) -> bool:
    """Check if the square is attacked by a queen."""
    directions = [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]
    return is_attacked_by_sliding_piece(sq, by_white, directions, game_state.whiteQueen, game_state.blackQueen, game_state)

def is_attacked_by_king(sq: int, by_white: bool, game_state) -> bool:
    """Check if the square is attacked by a king."""
    row, col = square_to_coords(sq)
    king_moves = [
        (row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1),
        (row + 1, col + 1), (row + 1, col - 1), (row - 1, col + 1), (row - 1, col - 1)
    ]
    for r, c in king_moves:
        if in_bounds(r, c):
            if by_white and test_bit(game_state.whiteKing, coords_to_square(r, c)):
                return True
            if not by_white and test_bit(game_state.blackKing, coords_to_square(r, c)):
                return True
    return False

def is_attacked_by_sliding_piece(sq: int, by_white: bool, directions: list, white_bitboard: int, black_bitboard: int, game_state) -> bool:
    """Check if the square is attacked by a sliding piece (bishop, rook, queen)."""
    row, col = square_to_coords(sq)
    for dr, dc in directions:
        r, c = row + dr, col + dc
        while in_bounds(r, c):
            target_sq = coords_to_square(r, c)
            if by_white and test_bit(white_bitboard, target_sq):
                return True
            if not by_white and test_bit(black_bitboard, target_sq):
                return True
            if test_bit(game_state.get_occupancy(), target_sq):
                break
            r += dr
            c += dc
    return False
