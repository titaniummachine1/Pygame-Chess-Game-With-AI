from chess.bitboard import set_bit, clear_bit, test_bit

def move_piece_on_board(piece: str, startSq: int, endSq, game_state):
    """Move a piece on the board."""
    if piece == 'wP':
        game_state.whitePawns = clear_bit(game_state.whitePawns, startSq)
        game_state.whitePawns = set_bit(game_state.whitePawns, endSq)
    elif piece == 'wN':
        game_state.whiteKnights = clear_bit(game_state.whiteKnights, startSq)
        game_state.whiteKnights = set_bit(game_state.whiteKnights, endSq)
    elif piece == 'wB':
        game_state.whiteBishops = clear_bit(game_state.whiteBishops, startSq)
        game_state.whiteBishops = set_bit(game_state.whiteBishops, endSq)
    elif piece == 'wR':
        game_state.whiteRooks = clear_bit(game_state.whiteRooks, startSq)
        game_state.whiteRooks = set_bit(game_state.whiteRooks, endSq)
    elif piece == 'wQ':
        game_state.whiteQueen = clear_bit(game_state.whiteQueen, startSq)
        game_state.whiteQueen = set_bit(game_state.whiteQueen, endSq)
    elif piece == 'wK':
        game_state.whiteKing = clear_bit(game_state.whiteKing, startSq)
        game_state.whiteKing = set_bit(game_state.whiteKing, endSq)
    elif piece == 'bP':
        game_state.blackPawns = clear_bit(game_state.blackPawns, startSq)
        game_state.blackPawns = set_bit(game_state.blackPawns, endSq)
    elif piece == 'bN':
        game_state.blackKnights = clear_bit(game_state.blackKnights, startSq)
        game_state.blackKnights = set_bit(game_state.blackKnights, endSq)
    elif piece == 'bB':
        game_state.blackBishops = clear_bit(game_state.blackBishops, startSq)
        game_state.blackBishops = set_bit(game_state.blackBishops, endSq)
    elif piece == 'bR':
        game_state.blackRooks = clear_bit(game_state.blackRooks, startSq)
        game_state.blackRooks = set_bit(game_state.blackRooks, endSq)
    elif piece == 'bQ':
        game_state.blackQueen = clear_bit(game_state.blackQueen, startSq)
        game_state.blackQueen = set_bit(game_state.blackQueen, endSq)
    elif piece == 'bK':
        game_state.blackKing = clear_bit(game_state.blackKing, startSq)
        game_state.blackKing = set_bit(game_state.blackKing, endSq)

def remove_piece_at_square(sq: int, side_is_white: bool, game_state):
    """Remove the piece at the given square for the specified side."""
    if side_is_white:
        if test_bit(game_state.whitePawns, sq):
            game_state.whitePawns = clear_bit(game_state.whitePawns, sq)
        elif test_bit(game_state.whiteKnights, sq):
            game_state.whiteKnights = clear_bit(game_state.whiteKnights, sq)
        elif test_bit(game_state.whiteBishops, sq):
            game_state.whiteBishops = clear_bit(game_state.whiteBishops, sq)
        elif test_bit(game_state.whiteRooks, sq):
            game_state.whiteRooks = clear_bit(game_state.whiteRooks, sq)
        elif test_bit(game_state.whiteQueen, sq):
            game_state.whiteQueen = clear_bit(game_state.whiteQueen, sq)
        elif test_bit(game_state.whiteKing, sq):
            game_state.whiteKing = clear_bit(game_state.whiteKing, sq)
    else:
        if test_bit(game_state.blackPawns, sq):
            game_state.blackPawns = clear_bit(game_state.blackPawns, sq)
        elif test_bit(game_state.blackKnights, sq):
            game_state.blackKnights = clear_bit(game_state.blackKnights, sq)
        elif test_bit(game_state.blackBishops, sq):
            game_state.blackBishops = clear_bit(game_state.blackBishops, sq)
        elif test_bit(game_state.blackRooks, sq):
            game_state.blackRooks = clear_bit(game_state.blackRooks, sq)
        elif test_bit(game_state.blackQueen, sq):
            game_state.blackQueen = clear_bit(game_state.blackQueen, sq)
        elif test_bit(game_state.blackKing, sq):
            game_state.blackKing = clear_bit(game_state.blackKing, sq)
