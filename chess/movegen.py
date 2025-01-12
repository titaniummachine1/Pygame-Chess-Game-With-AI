# chess/game.py

from .bitboard import set_bit, clear_bit, test_bit, coords_to_square, square_to_coords, in_bounds
from .pieces import *
from .move import Move
from .PieceMoves.pawn_moves import generate_pawn_moves
from .PieceMoves.knight_moves import generate_knight_moves
from .PieceMoves.bishop_moves import generate_bishop_moves
from .PieceMoves.rook_moves import generate_rook_moves
from .PieceMoves.queen_moves import generate_queen_moves
from .PieceMoves.king_moves import generate_king_moves

class GameState:
    """
    GameState holds all piece bitboards and manages:
     - Tracking which side to move
     - Movement flags for king/rooks (for castling)
     - 'kingGhostSquares' for 'king en passant' capturing
     - A move history for undo/redo
     - Make/unmake logic for standard or castle moves
    """

    def __init__(self):
        # Bitboards for each piece type, White & Black
        self.whitePawns   = 0
        self.whiteKnights = 0
        self.whiteBishops = 0
        self.whiteRooks   = 0
        self.whiteQueen   = 0
        self.whiteKing    = 0

        self.blackPawns   = 0
        self.blackKnights = 0
        self.blackBishops = 0
        self.blackRooks   = 0
        self.blackQueen   = 0
        self.blackKing    = 0

        # True => White to move, False => Black
        self.whiteToMove = True

        # For capturing a king that castled out/through check
        self.kingGhostSquares = []

        # Move history (stack) for undo
        self.move_history = []

        # Movement flags for castling logic:
        self.whiteKingMoved    = False
        self.whiteRookAMoved   = False  # a1
        self.whiteRookHMoved   = False  # h1
        self.blackKingMoved    = False
        self.blackRookAMoved   = False  # a8
        self.blackRookHMoved   = False  # h8

    def init_standard_position(self):
        """
        Initialize a standard chess arrangement for White/Black pieces.
        Pawns on rows 6/1, rooks/knights/bishops/queen/king on rows 7/0.
        Resets all movement flags and move history.
        """
        # Clear piece bitboards
        self.whitePawns = self.whiteKnights = self.whiteBishops = 0
        self.whiteRooks = self.whiteQueen = self.whiteKing = 0
        self.blackPawns = self.blackKnights = self.blackBishops = 0
        self.blackRooks = self.blackQueen = self.blackKing = 0

        # White moves first
        self.whiteToMove = True
        self.kingGhostSquares.clear()
        self.move_history.clear()

        # Reset king/rook movement flags
        self.whiteKingMoved   = False
        self.whiteRookAMoved  = False
        self.whiteRookHMoved  = False
        self.blackKingMoved   = False
        self.blackRookAMoved  = False
        self.blackRookHMoved  = False

        # White pawns on row=6
        for col in range(8):
            sq = coords_to_square(6, col)
            self.whitePawns = set_bit(self.whitePawns, sq)

        # White rooks, knights, bishops, queen, king on row=7
        # Rooks
        self.whiteRooks = set_bit(self.whiteRooks, coords_to_square(7, 0))  # a1
        self.whiteRooks = set_bit(self.whiteRooks, coords_to_square(7, 7))  # h1
        # Knights
        self.whiteKnights = set_bit(self.whiteKnights, coords_to_square(7, 1))
        self.whiteKnights = set_bit(self.whiteKnights, coords_to_square(7, 6))
        # Bishops
        self.whiteBishops = set_bit(self.whiteBishops, coords_to_square(7, 2))
        self.whiteBishops = set_bit(self.whiteBishops, coords_to_square(7, 5))
        # Queen
        self.whiteQueen = set_bit(self.whiteQueen, coords_to_square(7, 3))
        # King
        self.whiteKing = set_bit(self.whiteKing, coords_to_square(7, 4))

        # Black pawns on row=1
        for col in range(8):
            sq = coords_to_square(1, col)
            self.blackPawns = set_bit(self.blackPawns, sq)

        # Black rooks, knights, bishops, queen, king on row=0
        self.blackRooks = set_bit(self.blackRooks, coords_to_square(0, 0))  # a8
        self.blackRooks = set_bit(self.blackRooks, coords_to_square(0, 7))  # h8
        self.blackKnights = set_bit(self.blackKnights, coords_to_square(0, 1))
        self.blackKnights = set_bit(self.blackKnights, coords_to_square(0, 6))
        self.blackBishops = set_bit(self.blackBishops, coords_to_square(0, 2))
        self.blackBishops = set_bit(self.blackBishops, coords_to_square(0, 5))
        self.blackQueen = set_bit(self.blackQueen, coords_to_square(0, 3))
        self.blackKing = set_bit(self.blackKing, coords_to_square(0, 4))

    # ------------------------------------------------------------------
    # Occupancy checks
    # ------------------------------------------------------------------
    def get_white_occupancy(self) -> int:
        return (self.whitePawns | self.whiteKnights | self.whiteBishops |
                self.whiteRooks | self.whiteQueen | self.whiteKing)

    def get_black_occupancy(self) -> int:
        return (self.blackPawns | self.blackKnights | self.blackBishops |
                self.blackRooks | self.blackQueen | self.blackKing)

    def get_occupancy(self) -> int:
        return self.get_white_occupancy() | self.get_black_occupancy()

    # ------------------------------------------------------------------
    # Move / unmove
    # ------------------------------------------------------------------
    def make_move(self, move: Move):
        """
        Apply 'move' on the board. If it's a capture, remove the target.
        If it's castling, record the squares for 'king en passant' and move the rook.
        Then toggle side to move.
        """
        # 1) Save old snapshot for undo
        old_pos = self._snapshot()
        self.move_history.append((move, old_pos))

        # 2) If capture => remove the piece from that square
        if move.isCapture:
            self._remove_piece_at_square(move.endSq, self._opposite_side())

        # 3) Move the piece on the board
        self._move_piece_on_board(move.piece, move.startSq, move.endSq)

        # 4) Update king/rook movement flags if needed
        self._update_move_flags(move)

        # 5) Handle castling => record ghost squares + move the rook
        self.kingGhostSquares.clear()
        if move.isCastle:
            path = self._king_castle_path(move.startSq, move.endSq)
            self.kingGhostSquares = path
            self._move_rook_for_castle(move)

        # 6) Switch side
        self.whiteToMove = not self.whiteToMove

    def unmake_move(self, move: Move):
        """
        Revert the last move from the move_history. 
        This resets the board to before that move.
        """
        if not self.move_history:
            return
        lastMove, old_state = self.move_history.pop()
        if lastMove != move:
            # user tries to revert a move that's not last => do nothing
            return
        # restore from snapshot
        self._restore_snapshot(old_state)

    # ------------------------------------------------------------------
    # Internal snapshot & restore
    # ------------------------------------------------------------------
    def _snapshot(self):
        return (
            self.whitePawns, self.whiteKnights, self.whiteBishops, self.whiteRooks,
            self.whiteQueen, self.whiteKing,
            self.blackPawns, self.blackKnights, self.blackBishops, self.blackRooks,
            self.blackQueen, self.blackKing,
            self.whiteToMove,
            list(self.kingGhostSquares),  # copy
            # add the movement flags too
            self.whiteKingMoved, self.whiteRookAMoved, self.whiteRookHMoved,
            self.blackKingMoved, self.blackRookAMoved, self.blackRookHMoved
        )

    def _restore_snapshot(self, snap):
        ( self.whitePawns, self.whiteKnights, self.whiteBishops, self.whiteRooks,
          self.whiteQueen, self.whiteKing,
          self.blackPawns, self.blackKnights, self.blackBishops, self.blackRooks,
          self.blackQueen, self.blackKing,
          self.whiteToMove,
          king_ghost_list,
          self.whiteKingMoved, self.whiteRookAMoved, self.whiteRookHMoved,
          self.blackKingMoved, self.blackRookAMoved, self.blackRookHMoved
        ) = snap

        self.kingGhostSquares = king_ghost_list

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _opposite_side(self) -> bool:
        """Return True if the opposite side is 'white', False if 'black'."""
        return not self.whiteToMove

    def _remove_piece_at_square(self, sq: int, side_is_white: bool):
        """
        Remove whichever piece is at 'sq' from that side's bitboard.
        """
        if side_is_white:
            # White piece is captured
            if test_bit(self.whitePawns, sq):
                self.whitePawns = clear_bit(self.whitePawns, sq)
            elif test_bit(self.whiteKnights, sq):
                self.whiteKnights = clear_bit(self.whiteKnights, sq)
            elif test_bit(self.whiteBishops, sq):
                self.whiteBishops = clear_bit(self.whiteBishops, sq)
            elif test_bit(self.whiteRooks, sq):
                self.whiteRooks = clear_bit(self.whiteRooks, sq)
            elif test_bit(self.whiteQueen, sq):
                self.whiteQueen = clear_bit(self.whiteQueen, sq)
            elif test_bit(self.whiteKing, sq):
                self.whiteKing = clear_bit(self.whiteKing, sq)
        else:
            # Black piece is captured
            if test_bit(self.blackPawns, sq):
                self.blackPawns = clear_bit(self.blackPawns, sq)
            elif test_bit(self.blackKnights, sq):
                self.blackKnights = clear_bit(self.blackKnights, sq)
            elif test_bit(self.blackBishops, sq):
                self.blackBishops = clear_bit(self.blackBishops, sq)
            elif test_bit(self.blackRooks, sq):
                self.blackRooks = clear_bit(self.blackRooks, sq)
            elif test_bit(self.blackQueen, sq):
                self.blackQueen = clear_bit(self.blackQueen, sq)
            elif test_bit(self.blackKing, sq):
                self.blackKing = clear_bit(self.blackKing, sq)

    def _move_piece_on_board(self, piece: str, startSq: int, endSq: int):
        """
        Clear bit at startSq, set bit at endSq for the correct piece bitboard.
        """
        if piece == WHITE_PAWN:
            self.whitePawns = clear_bit(self.whitePawns, startSq)
            self.whitePawns = set_bit(self.whitePawns, endSq)
        elif piece == WHITE_KNIGHT:
            self.whiteKnights = clear_bit(self.whiteKnights, startSq)
            self.whiteKnights = set_bit(self.whiteKnights, endSq)
        elif piece == WHITE_BISHOP:
            self.whiteBishops = clear_bit(self.whiteBishops, startSq)
            self.whiteBishops = set_bit(self.whiteBishops, endSq)
        elif piece == WHITE_ROOK:
            self.whiteRooks = clear_bit(self.whiteRooks, startSq)
            self.whiteRooks = set_bit(self.whiteRooks, endSq)
        elif piece == WHITE_QUEEN:
            self.whiteQueen = clear_bit(self.whiteQueen, startSq)
            self.whiteQueen = set_bit(self.whiteQueen, endSq)
        elif piece == WHITE_KING:
            self.whiteKing = clear_bit(self.whiteKing, startSq)
            self.whiteKing = set_bit(self.whiteKing, endSq)
        elif piece == BLACK_PAWN:
            self.blackPawns = clear_bit(self.blackPawns, startSq)
            self.blackPawns = set_bit(self.blackPawns, endSq)
        elif piece == BLACK_KNIGHT:
            self.blackKnights = clear_bit(self.blackKnights, startSq)
            self.blackKnights = set_bit(self.blackKnights, endSq)
        elif piece == BLACK_BISHOP:
            self.blackBishops = clear_bit(self.blackBishops, startSq)
            self.blackBishops = set_bit(self.blackBishops, endSq)
        elif piece == BLACK_ROOK:
            self.blackRooks = clear_bit(self.blackRooks, startSq)
            self.blackRooks = set_bit(self.blackRooks, endSq)
        elif piece == BLACK_QUEEN:
            self.blackQueen = clear_bit(self.blackQueen, startSq)
            self.blackQueen = set_bit(self.blackQueen, endSq)
        elif piece == BLACK_KING:
            self.blackKing = clear_bit(self.blackKing, startSq)
            self.blackKing = set_bit(self.blackKing, endSq)

    def _king_castle_path(self, startSq: int, endSq: int) -> list:
        """
        Return squares the king passes through (excluding the final).
        e.g. e1->g1 => [60,61]. We pop off the last to exclude 'g1'.
        This is used for 'king en passant' capturing next turn if the king castled through check.
        """
        path = []
        step = 1 if endSq > startSq else -1
        current = startSq
        while current != endSq:
            path.append(current)
            current += step
        # remove the final square from path
        if path:
            path.pop()
        return path

    def _move_rook_for_castle(self, move: Move):
        """
        Once the king has moved from e1->g1, we move the rook from h1->f1, etc.
        Also sets the rook's 'moved' flag so no further castling is allowed with that rook.
        """
        start_row, start_col = square_to_coords(move.startSq)
        end_row, end_col = square_to_coords(move.endSq)

        if move.piece == WHITE_KING:
            # e1->g1 => rook h1->f1
            if (start_row, start_col) == (7, 4) and (end_row, end_col) == (7, 6):
                oldSq = coords_to_square(7, 7)  # h1
                newSq = coords_to_square(7, 5)  # f1
                if test_bit(self.whiteRooks, oldSq):
                    self.whiteRooks = clear_bit(self.whiteRooks, oldSq)
                    self.whiteRooks = set_bit(self.whiteRooks, newSq)
                self.whiteRookHMoved = True
            # e1->c1 => rook a1->d1
            elif (start_row, start_col) == (7, 4) and (end_row, end_col) == (7, 2):
                oldSq = coords_to_square(7, 0)  # a1
                newSq = coords_to_square(7, 3)  # d1
                if test_bit(self.whiteRooks, oldSq):
                    self.whiteRooks = clear_bit(self.whiteRooks, oldSq)
                    self.whiteRooks = set_bit(self.whiteRooks, newSq)
                self.whiteRookAMoved = True

        elif move.piece == BLACK_KING:
            # e8->g8 => rook h8->f8
            if (start_row, start_col) == (0, 4) and (end_row, end_col) == (0, 6):
                oldSq = coords_to_square(0, 7)  # h8
                newSq = coords_to_square(0, 5)  # f8
                if test_bit(self.blackRooks, oldSq):
                    self.blackRooks = clear_bit(self.blackRooks, oldSq)
                    self.blackRooks = set_bit(self.blackRooks, newSq)
                self.blackRookHMoved = True
            # e8->c8 => rook a8->d8
            elif (start_row, start_col) == (0, 4) and (end_row, end_col) == (0, 2):
                oldSq = coords_to_square(0, 0)  # a8
                newSq = coords_to_square(0, 3)  # d8
                if test_bit(self.blackRooks, oldSq):
                    self.blackRooks = clear_bit(self.blackRooks, oldSq)
                    self.blackRooks = set_bit(self.blackRooks, newSq)
                self.blackRookAMoved = True

    def _update_move_flags(self, move: Move):
        """
        If the piece is the king or rook, mark that it has moved
        so we can't castle that piece again.
        """
        piece = move.piece
        if piece == WHITE_KING:
            self.whiteKingMoved = True
        elif piece == BLACK_KING:
            self.blackKingMoved = True
        elif piece == WHITE_ROOK:
            # Distinguish a1 from h1
            if move.startSq == coords_to_square(7, 0):
                self.whiteRookAMoved = True
            elif move.startSq == coords_to_square(7, 7):
                self.whiteRookHMoved = True
        elif piece == BLACK_ROOK:
            # Distinguish a8 from h8
            if move.startSq == coords_to_square(0, 0):
                self.blackRookAMoved = True
            elif move.startSq == coords_to_square(0, 7):
                self.blackRookHMoved = True

def generate_all_moves(game_state):
    """
    Generate all possible moves for the given game state.
    """
    moves = []

    # Check if the current player has their king
    if game_state.whiteToMove and game_state.whiteKing == 0:
        return moves  # No moves if white king is missing
    if not game_state.whiteToMove and game_state.blackKing == 0:
        return moves  # No moves if black king is missing

    if game_state.whiteToMove:
        # Generate moves for white pieces
        moves.extend(generate_pawn_moves(game_state, True))
        moves.extend(generate_knight_moves(game_state, True))
        moves.extend(generate_bishop_moves(game_state, True))
        moves.extend(generate_rook_moves(game_state, True))
        moves.extend(generate_queen_moves(game_state, True))
        moves.extend(generate_king_moves(game_state, True))
    else:
        # Generate moves for black pieces
        moves.extend(generate_pawn_moves(game_state, False))
        moves.extend(generate_knight_moves(game_state, False))
        moves.extend(generate_bishop_moves(game_state, False))
        moves.extend(generate_rook_moves(game_state, False))
        moves.extend(generate_queen_moves(game_state, False))
        moves.extend(generate_king_moves(game_state, False))
    
    # Prune moves based on drawbacks
    moves = game_state.prune_moves(moves)
    return moves
