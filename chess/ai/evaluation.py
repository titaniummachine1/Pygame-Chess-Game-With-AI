from chess.pieces import ALL_PIECES
from chess.helpers.bitboard_helpers import test_bit
from chess.ai.piece_square_tables import PAWN_TABLE, KNIGHT_TABLE, BISHOP_TABLE, ROOK_TABLE, QUEEN_TABLE, KING_TABLE
from chess.helpers.check_detection import is_square_attacked  # Import the function to check if a square is attacked

PIECE_VALUES = {
    'wP': 1, 'wN': 3, 'wB': 3, 'wR': 5, 'wQ': 9, 'wK': 0,
    'bP': 1, 'bN': 3, 'bB': 3, 'bR': 5, 'bQ': 9, 'bK': 0
}

PIECE_SQUARE_TABLES = {
    'wP': PAWN_TABLE, 'wN': KNIGHT_TABLE, 'wB': BISHOP_TABLE, 'wR': ROOK_TABLE, 'wQ': QUEEN_TABLE, 'wK': KING_TABLE,
    'bP': PAWN_TABLE[::-1], 'bN': KNIGHT_TABLE[::-1], 'bB': BISHOP_TABLE[::-1], 'bR': ROOK_TABLE[::-1], 'bQ': QUEEN_TABLE[::-1], 'bK': KING_TABLE[::-1]
}

def evaluate_board(game_state):
    """
    Evaluate the board based on material count and piece-square tables.
    Return -1000 if the white king is missing and 1000 if the black king is missing.
    Penalize positions where the king is in danger.
    """
    if game_state.whiteKing == 0:
        return -1000  # White king is missing, black wins
    if game_state.blackKing == 0:
        return 1000  # Black king is missing, white wins

    white_material = 0
    black_material = 0

    for piece, bitboard in {
        'wP': game_state.whitePawns,
        'wN': game_state.whiteKnights,
        'wB': game_state.whiteBishops,
        'wR': game_state.whiteRooks,
        'wQ': game_state.whiteQueen,
        'wK': game_state.whiteKing,
        'bP': game_state.blackPawns,
        'bN': game_state.blackKnights,
        'bB': game_state.blackBishops,
        'bR': game_state.blackRooks,
        'bQ': game_state.blackQueen,
        'bK': game_state.blackKing
    }.items():
        piece_value = PIECE_VALUES[piece]
        piece_square_table = PIECE_SQUARE_TABLES[piece]

        for sq in range(64):
            if test_bit(bitboard, sq):
                if piece.startswith('w'):
                    white_material += piece_value + piece_square_table[sq]
                else:
                    black_material += piece_value + piece_square_table[sq]

    # Penalize positions where the king is in danger
    white_king_sq = game_state.whiteKing.bit_length() - 1
    black_king_sq = game_state.blackKing.bit_length() - 1

    if is_square_attacked(game_state, white_king_sq, False):
        white_material -= 50  # Adjust the penalty value as needed
    if is_square_attacked(game_state, black_king_sq, True):
        black_material -= 50  # Adjust the penalty value as needed

    return white_material - black_material
